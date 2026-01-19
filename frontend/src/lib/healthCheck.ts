/**
 * Frontend Health Check Utility
 * Validates all API endpoints and frontend routes
 */

import { api } from '@/lib/apiClient';

interface HealthCheckResult {
  endpoint: string;
  status: 'success' | 'error' | 'warning';
  message: string;
  responseTime?: number;
}

export class FrontendHealthCheck {
  private results: HealthCheckResult[] = [];

  /**
   * Run all health checks
   */
  async runAll(): Promise<HealthCheckResult[]> {
    this.results = [];

    console.log('🔍 Starting frontend health checks...');

    // Core endpoints
    await this.checkEndpoint('Backend Health', () => api.health());
    await this.checkEndpoint('Auth Profile', () => api.auth.getProfile());
    await this.checkEndpoint('Crypto Prices', () => api.crypto.getAll());
    await this.checkEndpoint('Portfolio', () => api.portfolio.get());
    await this.checkEndpoint('Transactions', () => api.transactions.getAll(0, 10));
    await this.checkEndpoint('Wallet Balance', () => api.wallet.getBalance());
    await this.checkEndpoint('Price Alerts', () => api.alerts.getAll());
    
    // Print results
    this.printResults();
    
    return this.results;
  }

  /**
   * Check a single endpoint
   */
  private async checkEndpoint(
    name: string,
    apiCall: () => Promise<any>
  ): Promise<void> {
    const startTime = performance.now();
    
    try {
      await apiCall();
      const responseTime = Math.round(performance.now() - startTime);
      
      this.results.push({
        endpoint: name,
        status: responseTime > 2000 ? 'warning' : 'success',
        message: responseTime > 2000 ? `Slow response (${responseTime}ms)` : 'OK',
        responseTime,
      });
    } catch (error: any) {
      // 401 is expected if not authenticated
      if (error?.statusCode === 401) {
        this.results.push({
          endpoint: name,
          status: 'warning',
          message: 'Requires authentication (expected)',
        });
      } else {
        this.results.push({
          endpoint: name,
          status: 'error',
          message: error?.message || 'Failed',
        });
      }
    }
  }

  /**
   * Print results to console
   */
  private printResults(): void {
    console.log('\n📊 Frontend Health Check Results:');
    console.log('================================');
    
    this.results.forEach((result) => {
      const icon = result.status === 'success' ? '✅' : result.status === 'warning' ? '⚠️' : '❌';
      const time = result.responseTime ? ` (${result.responseTime}ms)` : '';
      console.log(`${icon} ${result.endpoint}: ${result.message}${time}`);
    });
    
    const successCount = this.results.filter(r => r.status === 'success').length;
    const totalCount = this.results.length;
    const successRate = ((successCount / totalCount) * 100).toFixed(1);
    
    console.log('================================');
    console.log(`✅ Success rate: ${successRate}% (${successCount}/${totalCount})`);
  }

  /**
   * Get summary
   */
  getSummary(): { total: number; success: number; warning: number; error: number } {
    return {
      total: this.results.length,
      success: this.results.filter(r => r.status === 'success').length,
      warning: this.results.filter(r => r.status === 'warning').length,
      error: this.results.filter(r => r.status === 'error').length,
    };
  }
}

// Export singleton instance
export const healthCheck = new FrontendHealthCheck();
