/**
 * API Client with automatic token refresh and error handling
 * Production-ready HTTP client for CryptoVault API
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';

// Get base URL from environment or use proxy in development
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// Log API configuration in development
if (import.meta.env.DEV) {
  console.log(
    `[API Client] Initialized with BASE_URL: ${BASE_URL || '(empty - using relative paths)'}`
  );
  if (!BASE_URL) {
    console.warn(
      '[API Client] VITE_API_BASE_URL is not configured. Using relative paths. ' +
      'Make sure your backend is running and accessible.'
    );
  }
}

/**
 * Error response structure from backend
 */
interface APIError {
  error: {
    code: string;
    message: string;
    request_id?: string;
    timestamp?: string;
    details?: Record<string, any>;
  };
}

/**
 * Custom error class for API errors
 */
export class APIClientError extends Error {
  code: string;
  statusCode: number;
  requestId?: string;
  details?: Record<string, any>;

  constructor(message: string, code: string, statusCode: number, requestId?: string, details?: Record<string, any>) {
    super(message);
    this.name = 'APIClientError';
    this.code = code;
    this.statusCode = statusCode;
    this.requestId = requestId;
    this.details = details;
  }
}

/**
 * Create axios instance with default configuration
 */
const createAxiosInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: BASE_URL,
    timeout: 30000, // 30 seconds
    withCredentials: true, // Send cookies with requests
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return instance;
};

/**
 * API Client with token refresh and error handling
 */
class APIClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (value?: any) => void;
    reject: (reason?: any) => void;
  }> = [];

  constructor() {
    this.client = createAxiosInstance();
    this.setupInterceptors();
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add any request-level logic here
        // Cookies are automatically sent with withCredentials: true
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<APIError>) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

        // If error is 401 and we haven't retried yet
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            // If already refreshing, queue this request
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            })
              .then(() => {
                return this.client(originalRequest);
              })
              .catch((err) => {
                return Promise.reject(err);
              });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            // Attempt to refresh token
            await this.refreshToken();

            // Process failed queue
            this.failedQueue.forEach((promise) => {
              promise.resolve();
            });
            this.failedQueue = [];

            // Retry original request
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed, clear queue and reject all
            this.failedQueue.forEach((promise) => {
              promise.reject(refreshError);
            });
            this.failedQueue = [];

            // Clear auth state and redirect to login
            this.handleAuthFailure();

            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        // Transform error to APIClientError
        return Promise.reject(this.transformError(error));
      }
    );
  }

  /**
   * Refresh access token
   */
  private async refreshToken(): Promise<void> {
    try {
      await this.client.post('/api/auth/refresh');
    } catch (error) {
      throw new Error('Token refresh failed');
    }
  }

  /**
   * Handle authentication failure
   */
  private handleAuthFailure(): void {
    // Clear any stored auth state
    // You can emit an event here or use a global state manager
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('auth:logout'));
      // Redirect to login page
      window.location.href = '/auth';
    }
  }

  /**
   * Transform Axios error to APIClientError
   */
  private transformError(error: AxiosError<APIError>): APIClientError {
    if (error.response?.data?.error) {
      const apiError = error.response.data.error;
      return new APIClientError(
        apiError.message,
        apiError.code,
        error.response.status,
        apiError.request_id,
        apiError.details
      );
    }

    // Network or other errors
    if (error.code === 'ECONNABORTED') {
      return new APIClientError(
        'Request timeout',
        'TIMEOUT_ERROR',
        408
      );
    }

    if (!error.response) {
      return new APIClientError(
        'Network error. Please check your internet connection.',
        'NETWORK_ERROR',
        0
      );
    }

    return new APIClientError(
      error.message || 'An unexpected error occurred',
      'UNKNOWN_ERROR',
      error.response?.status || 500
    );
  }

  /**
   * GET request
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.get(url, config);
    return response.data;
  }

  /**
   * POST request
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.post(url, data, config);
    return response.data;
  }

  /**
   * PUT request
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.put(url, data, config);
    return response.data;
  }

  /**
   * PATCH request
   */
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.patch(url, data, config);
    return response.data;
  }

  /**
   * DELETE request
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.delete(url, config);
    return response.data;
  }
}

// Create and export singleton instance
const apiClient = new APIClient();
export default apiClient;

// Export API endpoints as typed functions
export const api = {
  // Authentication
  auth: {
    signup: (data: { email: string; password: string; name: string }) =>
      apiClient.post('/api/auth/signup', data),
    login: (data: { email: string; password: string }) =>
      apiClient.post('/api/auth/login', data),
    logout: () =>
      apiClient.post('/api/auth/logout'),
    verifyEmail: (token: string) =>
      apiClient.post('/api/auth/verify-email', { token }),
    resendVerification: (email: string) =>
      apiClient.post('/api/auth/resend-verification', { email }),
    forgotPassword: (email: string) =>
      apiClient.post('/api/auth/forgot-password', { email }),
    resetPassword: (token: string, newPassword: string) =>
      apiClient.post('/api/auth/reset-password', { token, new_password: newPassword }),
    validateResetToken: (token: string) =>
      apiClient.get(`/api/auth/validate-reset-token/${token}`),
    getMe: () =>
      apiClient.get('/api/auth/me'),
    getProfile: () =>
      apiClient.get('/api/auth/me'),
    updateProfile: (data: { name: string }) =>
      apiClient.put('/api/auth/profile', data),
    changePassword: (data: { current_password: string; new_password: string }) =>
      apiClient.post('/api/auth/change-password', data),
    refresh: () =>
      apiClient.post('/api/auth/refresh'),
    // 2FA endpoints
    setup2FA: () =>
      apiClient.post('/api/auth/2fa/setup'),
    verify2FA: (data: { code: string }) =>
      apiClient.post('/api/auth/2fa/verify', data),
    get2FAStatus: () =>
      apiClient.get('/api/auth/2fa/status'),
    disable2FA: () =>
      apiClient.post('/api/auth/2fa/disable', {}),
    getBackupCodes: () =>
      apiClient.post('/api/auth/2fa/backup-codes'),
  },

  // Portfolio
  portfolio: {
    get: () =>
      apiClient.get('/api/portfolio'),
    addHolding: (data: { symbol: string; name: string; amount: number }) =>
      apiClient.post('/api/portfolio/holding', data),
    deleteHolding: (symbol: string) =>
      apiClient.delete(`/api/portfolio/holding/${symbol}`),
    getHolding: (symbol: string) =>
      apiClient.get(`/api/portfolio/holding/${symbol}`),
  },

  // Trading
  trading: {
    getOrders: () =>
      apiClient.get('/api/orders'),
    createOrder: (data: {
      trading_pair: string;
      order_type: string;
      side: string;
      amount: number;
      price: number;
    }) =>
      apiClient.post('/api/orders', data),
    getOrder: (orderId: string) =>
      apiClient.get(`/api/orders/${orderId}`),
  },

  // Legacy orders API (alias for trading)
  orders: {
    get: () =>
      apiClient.get('/api/orders'),
    create: (data: {
      trading_pair: string;
      order_type: string;
      side: string;
      amount: number;
      price: number;
    }) =>
      apiClient.post('/api/orders', data),
    getById: (orderId: string) =>
      apiClient.get(`/api/orders/${orderId}`),
  },

  // Cryptocurrency market data
  crypto: {
    getAll: () =>
      apiClient.get('/api/crypto'),
    get: (coinId: string) =>
      apiClient.get(`/api/crypto/${coinId}`),
    getHistory: (coinId: string, days: number = 7) =>
      apiClient.get(`/api/crypto/${coinId}/history?days=${days}`),
  },

  // Wallet and deposits
  wallet: {
    getBalance: () =>
      apiClient.get('/api/wallet/balance'),
    createDeposit: (data: { amount: number; currency: string }) =>
      apiClient.post('/api/wallet/deposit/create', data),
    getDeposit: (orderId: string) =>
      apiClient.get(`/api/wallet/deposit/${orderId}`),
    getDeposits: (skip: number = 0, limit: number = 20) =>
      apiClient.get(`/api/wallet/deposits?skip=${skip}&limit=${limit}`),
    withdraw: (data: { amount: number; currency: string; address: string }) =>
      apiClient.post('/api/wallet/withdraw', data),
    getWithdrawals: (skip: number = 0, limit: number = 20) =>
      apiClient.get(`/api/wallet/withdrawals?skip=${skip}&limit=${limit}`),
    getWithdrawal: (withdrawalId: string) =>
      apiClient.get(`/api/wallet/withdraw/${withdrawalId}`),
  },

  // Price alerts
  alerts: {
    getAll: () =>
      apiClient.get('/api/alerts'),
    get: (alertId: string) =>
      apiClient.get(`/api/alerts/${alertId}`),
    create: (data: {
      symbol: string;
      targetPrice: number;
      condition: string;
      notifyPush?: boolean;
      notifyEmail?: boolean;
    }) =>
      apiClient.post('/api/alerts', data),
    update: (alertId: string, data: {
      isActive?: boolean;
      targetPrice?: number;
      condition?: string;
      notifyPush?: boolean;
      notifyEmail?: boolean;
    }) =>
      apiClient.patch(`/api/alerts/${alertId}`, data),
    delete: (alertId: string) =>
      apiClient.delete(`/api/alerts/${alertId}`),
  },

  // Transactions
  transactions: {
    getAll: (skip: number = 0, limit: number = 50, type?: string) => {
      let url = `/api/transactions?skip=${skip}&limit=${limit}`;
      if (type) url += `&type=${type}`;
      return apiClient.get(url);
    },
    get: (transactionId: string) =>
      apiClient.get(`/api/transactions/${transactionId}`),
    getStats: () =>
      apiClient.get('/api/transactions/summary/stats'),
  },

  // Admin (requires admin privileges)
  admin: {
    getStats: () =>
      apiClient.get('/api/admin/stats'),
    getUsers: (skip: number = 0, limit: number = 50) =>
      apiClient.get(`/api/admin/users?skip=${skip}&limit=${limit}`),
    getTrades: (skip: number = 0, limit: number = 100) =>
      apiClient.get(`/api/admin/trades?skip=${skip}&limit=${limit}`),
    getAuditLogs: (skip: number = 0, limit: number = 100, userId?: string, action?: string) => {
      let url = `/api/admin/audit-logs?skip=${skip}&limit=${limit}`;
      if (userId) url += `&user_id=${userId}`;
      if (action) url += `&action=${action}`;
      return apiClient.get(url);
    },
    setupFirstAdmin: (email: string) =>
      apiClient.post('/api/admin/setup-first-admin', { email }),
    getWithdrawals: (skip: number = 0, limit: number = 50, status?: string) => {
      let url = `/api/admin/withdrawals?skip=${skip}&limit=${limit}`;
      if (status) url += `&status=${status}`;
      return apiClient.get(url);
    },
    approveWithdrawal: (withdrawalId: string) =>
      apiClient.post(`/api/admin/withdrawals/${withdrawalId}/approve`),
    completeWithdrawal: (withdrawalId: string, transactionHash: string) =>
      apiClient.post(`/api/admin/withdrawals/${withdrawalId}/complete`, { transaction_hash: transactionHash }),
    rejectWithdrawal: (withdrawalId: string, reason: string) =>
      apiClient.post(`/api/admin/withdrawals/${withdrawalId}/reject`, { reason }),
  },

  // Health check
  health: () =>
    apiClient.get('/health'),
};
