/**
 * Health Check and Heartbeat Service
 * Keeps the backend server alive by sending periodic ping requests
 * Prevents serverless backends (Render, Vercel, etc.) from becoming idle
 */

import { api } from '@/lib/apiClient';
import { resolveApiBaseUrl, resolveAppUrl } from '@/lib/runtimeConfig';

interface HealthCheckConfig {
  interval?: number; // ms between pings (default: 4 minutes)
  timeout?: number; // ms to wait for response (default: 5 seconds)
  retries?: number; // number of retries on failure (default: 3)
  verbose?: boolean; // log to console in dev mode
}

class HealthCheckService {
  private intervalId: NodeJS.Timeout | null = null;
  private lastPingTime: number = 0;
  private consecutiveFailures: number = 0;
  private isEnabled: boolean = false;
  private config: Required<HealthCheckConfig>;
  private rateLimitRemaining: number = 60;
  private rateLimitReset: number = 0;

  constructor(config: HealthCheckConfig = {}) {
    this.config = {
      interval: config.interval || 4 * 60 * 1000, // 4 minutes (Render free tier idle timeout is 15 min)
      timeout: config.timeout || 5000,
      retries: config.retries || 3,
      verbose: config.verbose ?? import.meta.env.DEV,
    };

    this.logInfo('HealthCheckService initialized', {
      interval: `${this.config.interval / 1000 / 60} minutes`,
      timeout: `${this.config.timeout / 1000} seconds`,
      retries: this.config.retries,
    });
  }

  /**
   * Start the health check heartbeat
   */
  start(): void {
    if (this.isEnabled) {
      this.logWarn('HealthCheckService already running');
      return;
    }

    this.isEnabled = true;
    this.consecutiveFailures = 0;

    // Initial ping after short delay to let app initialize
    this.scheduleNextPing(2000);

    this.logInfo('HealthCheckService started');
  }

  /**
   * Stop the health check heartbeat
   */
  stop(): void {
    if (this.intervalId) {
      clearTimeout(this.intervalId);
      this.intervalId = null;
    }
    this.isEnabled = false;
    this.logInfo('HealthCheckService stopped');
  }

  /**
   * Perform a single health check ping
   */
  private async ping(): Promise<boolean> {
    try {
      // Check if we're rate limited
      if (this.rateLimitRemaining <= 10) {
        const now = Date.now();
        const timeUntilReset = Math.max(0, this.rateLimitReset - now);

        if (timeUntilReset > 0) {
          this.logWarn(
            `⏳ Approaching rate limit (${this.rateLimitRemaining} remaining). ` +
            `Delaying health check for ${(timeUntilReset / 1000).toFixed(0)}s`
          );
          // Reschedule for when rate limit resets
          this.scheduleNextPing(Math.max(this.config.interval, timeUntilReset + 1000));
          return true;
        }
      }

      const startTime = performance.now();
      const baseUrl = resolveApiBaseUrl();
      const isDevelopment = import.meta.env.DEV;

      // In development with no BASE_URL, use relative paths (Vite proxy)
      const useRelativePaths = isDevelopment && !baseUrl;

      // Try multiple endpoints in order of preference
      let success = false;
      let lastError: any = null;

      // 1. Try simple ping endpoint (no database required)
      try {
        const pingUrl = useRelativePaths ? '/api/ping' : `${baseUrl}/api/ping`;
        const response = await fetch(pingUrl, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          signal: AbortSignal.timeout(this.config.timeout)
        });

        if (response.ok) {
          success = true;
        }
      } catch (e) {
        lastError = e;
      }

      // 2. Fallback to health endpoint
      if (!success) {
        try {
          await api.health();
          success = true;
        } catch (e) {
          lastError = e;
        }
      }

      // 3. Last resort: try crypto endpoint
      if (!success) {
        try {
          await api.crypto.getAll();
          success = true;
        } catch (e) {
          lastError = e;
        }
      }

      if (success) {
        const duration = performance.now() - startTime;
        this.lastPingTime = Date.now();
        this.consecutiveFailures = 0;

        this.logInfo(`✅ Health check passed (${duration.toFixed(0)}ms) | Rate limit: ${this.rateLimitRemaining}/60`);
        return true;
      } else {
        throw lastError || new Error('All health check endpoints failed');
      }

    } catch (error: any) {
      this.consecutiveFailures++;

      // Extract rate limit info from error headers if available
      if (error?.statusCode === 429) {
        this.logWarn('⏱️ Rate limited! Health check will be paused temporarily.');
        // Don't stop completely, just wait longer
        const backoffTime = Math.min(this.config.interval * 3, 15 * 60 * 1000); // Max 15 minutes
        this.scheduleNextPing(backoffTime);
        return false;
      }

      const isNetworkError = !error?.statusCode || error?.statusCode === 0;
      const errorType = isNetworkError ? 'NETWORK' : error?.code || 'UNKNOWN';
      const errorMsg = error?.message || 'Unknown error';
      const baseUrl = resolveApiBaseUrl() || '(using Vite proxy)';
      const isDevelopment = import.meta.env.DEV;

      // Use exponential backoff for retries
      const backoffMultiplier = Math.min(Math.pow(2, this.consecutiveFailures - 1), 8);
      const backoffTime = this.config.interval * backoffMultiplier;

      // Provide helpful diagnostic info
      let diagnosticMsg = '';
      if (isNetworkError) {
        if (isDevelopment) {
          const appUrl = resolveAppUrl() || 'http://localhost:3000';
          diagnosticMsg = '\n💡 Tips for local development:\n' +
            '  - Make sure backend is running: python run_server.py\n' +
            '  - Check backend URL: ' + baseUrl + '\n' +
            '  - Backend should match your /api/config response\n' +
            '  - Frontend dev server should be on ' + appUrl;
        } else {
          diagnosticMsg = '\n💡 Production backend may be sleeping (cold start on free hosting). ' +
            'It will wake up on the next request.';
        }
      }

      this.logWarn(
        `❌ Health check failed (${this.consecutiveFailures}/${this.config.retries}): [${errorType}] ${errorMsg}. ` +
        `Next retry in ${(backoffTime / 1000 / 60).toFixed(1)} minutes` +
        diagnosticMsg
      );

      // If too many consecutive failures, use longer backoff but don't disable completely
      if (this.consecutiveFailures >= this.config.retries) {
        const warningMsg = isDevelopment
          ? `⚠️ Cannot reach backend after ${this.config.retries} attempts. ` +
            `Make sure your backend is running on ${baseUrl}. ` +
            `Will keep trying with extended backoff.`
          : `⚠️ Health check experiencing issues after ${this.config.retries} failures. ` +
            `Backend may be sleeping on free hosting (normal). ` +
            `Will continue with extended backoff (${(backoffTime / 1000 / 60).toFixed(1)} min).`;

        this.logError(warningMsg);

        // Schedule with longer backoff instead of stopping
        this.scheduleNextPing(backoffTime);
        return false;
      }

      // Schedule next ping with exponential backoff
      this.scheduleNextPing(backoffTime);
      return false;
    }
  }

  /**
   * Schedule the next ping
   */
  private scheduleNextPing(delay: number = this.config.interval): void {
    if (!this.isEnabled) return;

    this.intervalId = setTimeout(() => {
      this.ping().then(() => {
        if (this.isEnabled) {
          this.scheduleNextPing();
        }
      });
    }, delay);
  }

  /**
   * Update rate limit information from response headers
   */
  updateRateLimit(remaining: number, reset: number): void {
    this.rateLimitRemaining = Math.max(0, remaining);
    this.rateLimitReset = reset;

    if (import.meta.env.DEV && remaining < 20) {
      this.logInfo(`Rate limit: ${remaining}/60 requests remaining`);
    }
  }

  /**
   * Get health status
   */
  getStatus(): {
    isEnabled: boolean;
    lastPingTime: number;
    timeSinceLastPing: number;
    consecutiveFailures: number;
    isHealthy: boolean;
    rateLimitRemaining: number;
    rateLimitReset: number;
  } {
    const timeSinceLastPing = this.lastPingTime ? Date.now() - this.lastPingTime : -1;

    return {
      isEnabled: this.isEnabled,
      lastPingTime: this.lastPingTime,
      timeSinceLastPing,
      consecutiveFailures: this.consecutiveFailures,
      isHealthy: this.consecutiveFailures < this.config.retries,
      rateLimitRemaining: this.rateLimitRemaining,
      rateLimitReset: this.rateLimitReset,
    };
  }

  /**
   * Logging utilities
   */
  private logInfo(message: string, data?: any): void {
    if (this.config.verbose) {
      console.log(`[HealthCheck] ${message}`, data || '');
    }
  }

  private logWarn(message: string, data?: any): void {
    if (this.config.verbose) {
      console.warn(`[HealthCheck] ${message}`, data || '');
    }
  }

  private logError(message: string, data?: any): void {
    console.error(`[HealthCheck] ${message}`, data || '');
  }
}

// Create singleton instance with more forgiving configuration
export const healthCheckService = new HealthCheckService({
  interval: 4 * 60 * 1000, // 4 minutes (keeps backend warm on free hosting)
  timeout: 10000, // Increased to 10 seconds for cold starts
  retries: 5, // More retries before backing off
  verbose: import.meta.env.DEV,
});

export default healthCheckService;
