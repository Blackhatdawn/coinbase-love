/**
 * Health Check and Heartbeat Service
 * Keeps the backend server alive by sending periodic ping requests
 * Prevents serverless backends (Render, Vercel, etc.) from becoming idle
 */

import { api } from '@/lib/apiClient';

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
      const startTime = performance.now();

      // Try health endpoint first, fallback to crypto endpoint
      try {
        await api.health();
      } catch {
        // Fallback: try crypto endpoint (always available)
        await api.crypto.getAll();
      }

      const duration = performance.now() - startTime;
      this.lastPingTime = Date.now();
      this.consecutiveFailures = 0;

      this.logInfo(`✅ Health check passed (${duration.toFixed(0)}ms)`);
      return true;
    } catch (error: any) {
      this.consecutiveFailures++;

      const isNetworkError = !error?.statusCode || error?.statusCode === 0;
      const errorType = isNetworkError ? 'NETWORK' : error?.code || 'UNKNOWN';
      const errorMsg = error?.message || 'Unknown error';

      this.logWarn(
        `❌ Health check failed (${this.consecutiveFailures}/${this.config.retries}): [${errorType}] ${errorMsg}`
      );

      // If too many consecutive failures, disable the service
      if (this.consecutiveFailures >= this.config.retries) {
        this.logError(
          `Health check disabled after ${this.config.retries} consecutive failures`
        );
        this.stop();
        return false;
      }

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
   * Get health status
   */
  getStatus(): {
    isEnabled: boolean;
    lastPingTime: number;
    timeSinceLastPing: number;
    consecutiveFailures: number;
    isHealthy: boolean;
  } {
    const timeSinceLastPing = this.lastPingTime ? Date.now() - this.lastPingTime : -1;

    return {
      isEnabled: this.isEnabled,
      lastPingTime: this.lastPingTime,
      timeSinceLastPing,
      consecutiveFailures: this.consecutiveFailures,
      isHealthy: this.consecutiveFailures < this.config.retries,
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

// Create singleton instance
export const healthCheckService = new HealthCheckService({
  interval: 4 * 60 * 1000, // 4 minutes
  timeout: 5000,
  retries: 3,
  verbose: import.meta.env.DEV,
});

export default healthCheckService;
