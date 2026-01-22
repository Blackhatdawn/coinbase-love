/**
 * API Client with automatic token refresh and error handling
 * Production-ready HTTP client for CryptoVault API
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import { create } from 'zustand';
import { resolveApiBaseUrl } from '@/lib/runtimeConfig';

// Get base URL from environment or use proxy in development
const resolveBaseUrl = () => resolveApiBaseUrl();
const BASE_URL = resolveBaseUrl();

// Log API configuration in development
if (import.meta.env.DEV) {
  console.log(
    `[API Client] Initialized with BASE_URL: ${BASE_URL || '(empty - using relative paths)'}`
  );
  if (!BASE_URL) {
    console.warn(
      '[API Client] API base URL not configured. Using relative paths. ' +
      'Ensure /api/config responds or set VITE_API_BASE_URL for bootstrap.'
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
  private csrfToken: string | null = null;
  private failedQueue: Array<{
    resolve: (value?: any) => void;
    reject: (reason?: any) => void;
  }> = [];

  constructor() {
    this.client = createAxiosInstance();
    this.setupInterceptors();
    this.initializeCSRFToken();
  }

  /**
   * Initialize CSRF token on app load
   * Fetches from /csrf endpoint which sets it as a cookie
   */
  private async initializeCSRFToken(): Promise<void> {
    try {
      await this.client.get('/csrf');
      if (import.meta.env.DEV) {
        console.log('[API Client] CSRF token initialized');
      }
    } catch (error) {
      // CSRF protection is optional; don't block app initialization
      if (import.meta.env.DEV) {
        console.warn('[API Client] Failed to initialize CSRF token:', error);
      }
    }
  }

  /**
   * Get CSRF token from browser cookies
   */
  private getCSRFTokenFromCookie(): string | null {
    if (typeof document === 'undefined') {
      return null;
    }

    const name = 'csrf_token=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookieArray = decodedCookie.split(';');

    for (let cookie of cookieArray) {
      cookie = cookie.trim();
      if (cookie.indexOf(name) === 0) {
        return cookie.substring(name.length, cookie.length);
      }
    }

    return null;
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Update base URL at request time (runtime config override)
        config.baseURL = resolveBaseUrl() || config.baseURL;

        // Add CSRF token header for mutating requests (POST, PUT, PATCH, DELETE)
        const mutatingMethods = ['post', 'put', 'patch', 'delete'];
        if (config.method && mutatingMethods.includes(config.method.toLowerCase())) {
          // Get CSRF token from cookie
          const csrfToken = this.getCSRFTokenFromCookie();
          if (csrfToken) {
            config.headers['X-CSRF-Token'] = csrfToken;
          }
        }

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
  const requestId = error.response?.headers['x-request-id'] as string || undefined;

  // Try structured error format first (backend custom error handler)
  if (error.response?.data?.error) {
    const apiError = error.response.data.error;
    return new APIClientError(
      apiError.message,
      apiError.code,
      error.response.status,
      requestId,
      apiError.details
    );
  }

  // Handle FastAPI default error format {"detail": "..."}
  if (error.response?.data) {
    const data = error.response.data as any;

    // Check for "detail" field (FastAPI default validation errors and HTTPException)
    if (data.detail) {
      const message = typeof data.detail === 'string'
        ? data.detail
        : typeof data.detail === 'object' && data.detail.msg
        ? data.detail.msg
        : 'An error occurred';

      return new APIClientError(
        message,
        'BACKEND_ERROR',
        error.response.status,
        requestId,
        data
      );
    }

    // Handle validation error format ({"loc": [...], "msg": "...", "type": "..."}[])
    if (Array.isArray(data)) {
      const messages = data
        .map((err: any) => err.msg || err.detail || 'Unknown error')
        .join('; ');

      return new APIClientError(
        messages || 'Validation error',
        'VALIDATION_ERROR',
        error.response.status,
        requestId,
        data
      );
    }

    // Fallback: stringify the response
    const message = typeof data === 'string' ? data : JSON.stringify(data);
    return new APIClientError(
      message || 'An error occurred',
      'BACKEND_ERROR',
      error.response.status,
      requestId,
      data
    );
  }

  // Handle rate limiting (429 Too Many Requests)
  if (error.response?.status === 429) {
    const rateLimitReset = error.response.headers['x-ratelimit-reset'] as string;
    const retryAfter = error.response.headers['retry-after'] as string;

    let message = 'Rate limit exceeded (60 requests per minute). Please try again later.';
    if (rateLimitReset) {
      message = `Rate limit exceeded. Try again after ${new Date(parseInt(rateLimitReset) * 1000).toLocaleTimeString()}`;
    } else if (retryAfter) {
      message = `Rate limit exceeded. Retry after ${retryAfter} seconds`;
    }

    return new APIClientError(message, 'RATE_LIMIT_ERROR', 429, requestId);
  }

  // Network or other errors
  if (error.code === 'ECONNABORTED') {
    return new APIClientError(
      'Request timeout (30 seconds). Backend may be slow or overloaded.',
      'TIMEOUT_ERROR',
      408,
      requestId
    );
  }

  if (!error.response) {
    return new APIClientError(
      'Network error. Please check your internet connection and ensure the backend is accessible.',
      'NETWORK_ERROR',
      0
    );
  }

  return new APIClientError(
    error.message || 'An unexpected error occurred',
    'UNKNOWN_ERROR',
    error.response?.status || 500,
    requestId
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
    transfer: (data: { recipient_email: string; amount: number; currency: string; note?: string }) =>
      apiClient.post('/api/wallet/transfer', data),
    getTransfers: (skip: number = 0, limit: number = 50) =>
      apiClient.get(`/api/wallet/transfers?skip=${skip}&limit=${limit}`),
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

  // User Search
  users: {
    search: (email: string) =>
      apiClient.get(`/api/users/search?email=${encodeURIComponent(email)}`),
    getProfile: (userId: string) =>
      apiClient.get(`/api/users/${userId}`),
  },

  // P2P Transfers
  transfers: {
    p2p: (data: {
      recipient_email: string;
      amount: number;
      currency: string;
      note?: string;
    }) =>
      apiClient.post('/api/transfers/p2p', data),
    getHistory: (skip: number = 0, limit: number = 50) =>
      apiClient.get(`/api/transfers/p2p/history?skip=${skip}&limit=${limit}`),
  },

  // Notifications
  notifications: {
    getAll: (skip: number = 0, limit: number = 50) =>
      apiClient.get(`/api/notifications?skip=${skip}&limit=${limit}`),
    create: (data: {
      title: string;
      message: string;
      type?: string;
      link?: string;
    }) =>
      apiClient.post('/api/notifications', data),
    markAsRead: (notificationId: string) =>
      apiClient.patch(`/api/notifications/${notificationId}/read`),
    markAllAsRead: () =>
      apiClient.post('/api/notifications/mark-all-read'),
    delete: (notificationId: string) =>
      apiClient.delete(`/api/notifications/${notificationId}`),
  },

  // Prices (real-time price data)
  prices: {
    getAll: () =>
      apiClient.get('/api/prices'),
    get: (symbol: string) =>
      apiClient.get(`/api/prices/${symbol}`),
    getHealth: () =>
      apiClient.get('/api/prices/status/health'),
    getBulk: (symbols: string) =>
      apiClient.get(`/api/prices/bulk/${symbols}`),
    getMetrics: () =>
      apiClient.get('/api/prices/metrics'),
    resetMetrics: () =>
      apiClient.post('/api/prices/metrics/reset'),
  },

  // Audit Logs (alias for admin.getAuditLogs for backward compatibility)
  auditLogs: {
    getLogs: (limit: number, offset: number, filter?: string) => {
      let url = `/api/admin/audit-logs?skip=${offset}&limit=${limit}`;
      if (filter) url += `&action=${filter}`;
      return apiClient.get(url);
    },
    exportLogs: (options?: { action?: string; userId?: string; limit?: number }) => {
      const params = new URLSearchParams({ export: 'true' });
      if (options?.limit) params.set('limit', String(options.limit));
      if (options?.action) params.set('action', options.action);
      if (options?.userId) params.set('user_id', options.userId);
      const query = params.toString();
      return apiClient.get(`/api/admin/audit-logs?${query}`, {
        responseType: 'blob',
      });
    },
  },

  // Health check
  health: {
    ping: () => apiClient.get('/ping'),
    health: () => apiClient.get('/health'),
  },

  // Simple ping (no database required)
  ping: () =>
    apiClient.get('/ping'),
};

// ============================================
// CONNECTION STATE MANAGEMENT
// ============================================

interface ConnectionState {
  isConnected: boolean;
  isConnecting: boolean;
  connectionError: string | null;
  retryCount: number;
  setConnected: (connected: boolean) => void;
  setConnecting: (connecting: boolean) => void;
  setError: (error: string | null) => void;
  incrementRetry: () => void;
  resetRetry: () => void;
}

export const useConnectionStore = create<ConnectionState>((set) => ({
  isConnected: false,
  isConnecting: true,
  connectionError: null,
  retryCount: 0,
  setConnected: (connected) => set({ isConnected: connected, connectionError: null }),
  setConnecting: (connecting) => set({ isConnecting: connecting }),
  setError: (error) => set({ connectionError: error, isConnected: false }),
  incrementRetry: () => set((state) => ({ retryCount: state.retryCount + 1 })),
  resetRetry: () => set({ retryCount: 0 }),
}));

// ============================================
// BACKEND HEALTH CHECK
// ============================================

const HEALTH_CHECK_RETRY_CONFIG = {
  maxRetries: 3,
  delays: [1000, 2000, 4000],
};

/**
 * Check backend health with automatic retry and connection state management
 */
export async function checkBackendHealth(): Promise<boolean> {
  const store = useConnectionStore.getState();

  if (store.isConnecting) {
    return false; // Already checking
  }

  store.setConnecting(true);
  store.resetRetry();

  for (let attempt = 0; attempt < HEALTH_CHECK_RETRY_CONFIG.maxRetries; attempt++) {
    try {
      await api.health();
      store.setConnected(true);
      store.setConnecting(false);
      return true;
    } catch (error: any) {
      store.incrementRetry();

      // Check if it's a "cold start" error (503 Service Unavailable or network error)
      const isColdStart = error?.statusCode === 503 || error?.code === 'ECONNREFUSED' || !error?.statusCode;

      if (attempt < HEALTH_CHECK_RETRY_CONFIG.maxRetries - 1) {
        const delay = HEALTH_CHECK_RETRY_CONFIG.delays[attempt] || 4000;

        if (isColdStart) {
          store.setError('Server is starting up (cold start). Retrying...');
        } else {
          store.setError(`Connection failed. Retry ${store.retryCount}/${HEALTH_CHECK_RETRY_CONFIG.maxRetries}`);
        }

        await new Promise((resolve) => setTimeout(resolve, delay));
      } else {
        // Final attempt failed
        store.setError(
          isColdStart
            ? 'Server is starting up (cold start). This may take up to 60 seconds on free hosting.'
            : 'Unable to connect to backend. Please check your connection and try again.'
        );
        store.setConnecting(false);
        return false;
      }
    }
  }

  store.setConnecting(false);
  return false;
}
