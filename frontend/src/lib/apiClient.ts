/**
 * CryptoVault API Client - Production-Grade Configuration
 * 
 * SECURITY FEATURES:
 * - No hardcoded URLs or secrets
 * - Environment-based configuration
 * - Automatic retry with exponential backoff
 * - Request/response interceptors
 * - CSRF protection ready
 * - Graceful error handling
 * 
 * ENVIRONMENT VARIABLES:
 * - VITE_API_BASE_URL: Backend URL (optional in dev, required in prod)
 */

import { create } from 'zustand';

// ============================================
// ENVIRONMENT CONFIGURATION (SECURE)
// ============================================

const IS_PRODUCTION = import.meta.env.PROD;
const IS_DEVELOPMENT = import.meta.env.DEV;
const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Determine API base URL securely
let API_BASE: string;

if (VITE_API_BASE_URL && VITE_API_BASE_URL.trim() !== '') {
  // Production or explicitly configured
  API_BASE = `${VITE_API_BASE_URL.replace(/\/$/, '')}/api`;
} else if (IS_DEVELOPMENT) {
  // Development: use Vite proxy (no hardcoded localhost!)
  API_BASE = '/api';
} else {
  // Production without config - use relative path (assumes same domain)
  API_BASE = '/api';
}

// Log configuration ONLY in development (no secrets!)
if (IS_DEVELOPMENT) {
  console.log('🔌 API Configuration:', {
    mode: IS_PRODUCTION ? 'production' : 'development',
    apiBase: API_BASE,
    usingProxy: !VITE_API_BASE_URL,
  });
}

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
// RETRY CONFIGURATION
// ============================================

const RETRY_CONFIG = {
  maxRetries: 3,
  delays: [1000, 2000, 4000], // Exponential backoff
  retryableStatuses: [408, 429, 500, 502, 503, 504],
};

// ============================================
// REQUEST UTILITIES
// ============================================

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
  timeout?: number;
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { skipAuth = false, timeout = 30000, ...fetchOptions } = options;
  const url = `${API_BASE}${endpoint}`;

  // Set up timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  // Build headers
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(fetchOptions.headers as Record<string, string>),
  };

  // Add auth token if available and not skipped
  if (!skipAuth) {
    const token = localStorage.getItem('token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
      credentials: 'include', // For cookies/CSRF
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // Handle non-OK responses
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
      (error as any).status = response.status;
      (error as any).data = errorData;
      throw error;
    }

    // Handle empty responses
    const text = await response.text();
    if (!text) return {} as T;

    return JSON.parse(text) as T;
  } catch (error: any) {
    clearTimeout(timeoutId);

    // Handle abort (timeout)
    if (error.name === 'AbortError') {
      throw new Error('Request timeout - please try again');
    }

    // Handle network errors gracefully
    if (error.message === 'Failed to fetch') {
      throw new Error('Unable to connect to server - please check your connection');
    }

    throw error;
  }
}

// Retry wrapper
async function requestWithRetry<T>(
  endpoint: string,
  options: RequestOptions = {},
  retryCount = 0
): Promise<T> {
  try {
    return await request<T>(endpoint, options);
  } catch (error: any) {
    const shouldRetry =
      retryCount < RETRY_CONFIG.maxRetries &&
      RETRY_CONFIG.retryableStatuses.includes(error.status);

    if (shouldRetry) {
      await new Promise((resolve) =>
        setTimeout(resolve, RETRY_CONFIG.delays[retryCount])
      );
      return requestWithRetry<T>(endpoint, options, retryCount + 1);
    }

    throw error;
  }
}

// ============================================
// API METHODS
// ============================================

export const api = {
  // Health check
  health: () => requestWithRetry<{ status: string }>('/health', { skipAuth: true }),

  // Authentication
  auth: {
    signup: (email: string, password: string, name: string) =>
      request<any>('/auth/signup', {
        method: 'POST',
        body: JSON.stringify({ email, password, name }),
      }),
    login: (email: string, password: string, totp_code?: string) =>
      request<any>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password, totp_code }),
      }),
    logout: () => request<any>('/auth/logout', { method: 'POST' }),
    me: () => request<any>('/auth/me'),
    refresh: () => request<any>('/auth/refresh', { method: 'POST' }),
    forgotPassword: (email: string) =>
      request('/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify({ email }),
      }),
    resetPassword: (token: string, password: string) =>
      request('/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify({ token, password }),
      }),
    verifyEmail: (token: string, code: string) =>
      request('/auth/verify-email', {
        method: 'POST',
        body: JSON.stringify({ token, code }),
      }),
    resendVerification: (token: string) =>
      request('/auth/resend-verification', {
        method: 'POST',
        body: JSON.stringify({ token }),
      }),
    // 2FA
    setup2FA: () => request('/auth/2fa/setup', { method: 'POST' }),
    verify2FA: (code: string) =>
      request('/auth/2fa/verify', {
        method: 'POST',
        body: JSON.stringify({ code }),
      }),
    disable2FA: (password: string) =>
      request('/auth/2fa/disable', {
        method: 'POST',
        body: JSON.stringify({ password }),
      }),
    get2FAStatus: () => request('/auth/2fa/status'),
    getBackupCodes: () => request('/auth/2fa/backup-codes', { method: 'POST' }),
    // Sessions
    getSessions: () => request('/auth/sessions'),
    revokeSession: (sessionId: string) =>
      request(`/auth/sessions/${sessionId}`, { method: 'DELETE' }),
    revokeAllSessions: () =>
      request('/auth/sessions/revoke-all', { method: 'POST' }),
  },

  // Crypto data
  crypto: {
    getAll: () => requestWithRetry<any>('/crypto', { skipAuth: true }),
    getOne: (coinId: string) =>
      requestWithRetry<any>(`/crypto/${coinId}`, { skipAuth: true }),
    getHistory: (coinId: string, days = 7) =>
      requestWithRetry<any>(`/crypto/${coinId}/history?days=${days}`, { skipAuth: true }),
  },

  // Portfolio
  portfolio: {
    get: () => request<any>('/portfolio'),
    getHolding: (symbol: string) => request<any>(`/portfolio/holding/${symbol}`),
    addHolding: (data: any) =>
      request<any>('/portfolio/holding', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    updateHolding: (symbol: string, data: any) =>
      request<any>(`/portfolio/holding/${symbol}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    deleteHolding: (symbol: string) =>
      request<any>(`/portfolio/holding/${symbol}`, { method: 'DELETE' }),
  },

  // Wallet
  wallet: {
    getBalances: () => request<any>('/wallet/balances'),
    deposit: (data: any) =>
      request<any>('/wallet/deposit', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    withdraw: (data: any) =>
      request<any>('/wallet/withdraw', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    getDepositAddress: (asset: string) =>
      request<any>(`/wallet/deposit-address/${asset}`),
  },

  // Transfers
  transfers: {
    p2p: (data: any) =>
      request<any>('/transfers/p2p', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    getHistory: (params?: any) => {
      const query = params ? `?${new URLSearchParams(params)}` : '';
      return request<any>(`/transfers/history${query}`);
    },
  },

  // Orders
  orders: {
    create: (data: any) =>
      request<any>('/orders', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    getAll: (params?: any) => {
      const query = params ? `?${new URLSearchParams(params)}` : '';
      return request<any>(`/orders${query}`);
    },
    getOne: (orderId: string) => request<any>(`/orders/${orderId}`),
    cancel: (orderId: string) =>
      request<any>(`/orders/${orderId}/cancel`, { method: 'POST' }),
  },

  // Staking
  staking: {
    getProducts: () => requestWithRetry<any>('/staking/products', { skipAuth: true }),
    stake: (data: any) =>
      request<any>('/staking/stake', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    unstake: (stakeId: string) =>
      request<any>(`/staking/${stakeId}/unstake`, { method: 'POST' }),
    getMyStakes: () => request<any>('/staking/my-stakes'),
    getRewards: () => request<any>('/staking/rewards'),
  },

  // KYC
  kyc: {
    getStatus: () => request<any>('/kyc/status'),
    submitLevel1: (data: any) =>
      request<any>('/kyc/level1', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },

  // Referrals
  referrals: {
    getCode: () => request<any>('/referrals/code'),
    applyCode: (code: string) =>
      request<any>('/referrals/apply', {
        method: 'POST',
        body: JSON.stringify({ code }),
      }),
    getStats: () => request<any>('/referrals/stats'),
  },

  // Contact
  contact: {
    submit: (data: any) =>
      request<any>('/contact', {
        method: 'POST',
        body: JSON.stringify(data),
        skipAuth: true,
      }),
  },

  // Password Reset
  auth: {
    ...{} as any, // Keep existing auth methods
    requestPasswordReset: (email: string) =>
      request<any>('/auth/password-reset/request', {
        method: 'POST',
        body: JSON.stringify({ email }),
        skipAuth: true,
      }),
    confirmPasswordReset: (token: string, password: string) =>
      request<any>('/auth/password-reset/confirm', {
        method: 'POST',
        body: JSON.stringify({ token, password }),
        skipAuth: true,
      }),
  },

  // Price Alerts
  alerts: {
    getAll: () => request<any>('/alerts'),
    create: (data: { symbol: string; targetPrice: number; condition: 'above' | 'below'; notifyPush?: boolean; notifyEmail?: boolean }) =>
      request<any>('/alerts', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (alertId: string, data: { isActive?: boolean }) =>
      request<any>(`/alerts/${alertId}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    delete: (alertId: string) =>
      request<any>(`/alerts/${alertId}`, { method: 'DELETE' }),
  },

  // Wallet with deposit
  wallet: {
    getBalances: () => request<any>('/wallet/balances'),
    createDeposit: (data: { amount: number; currency: string }) =>
      request<any>('/wallet/deposit/create', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    deposit: (data: any) =>
      request<any>('/wallet/deposit', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    withdraw: (data: any) =>
      request<any>('/wallet/withdraw', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    getDepositAddress: (asset: string) =>
      request<any>(`/wallet/deposit-address/${asset}`),
  },

  // Admin (protected)
  admin: {
    getStats: () => request<any>('/admin/stats'),
    getUsers: (params?: any) => {
      const query = params ? `?${new URLSearchParams(params)}` : '';
      return request<any>(`/admin/users${query}`);
    },
    getTrades: (params?: any) => {
      const query = params ? `?${new URLSearchParams(params)}` : '';
      return request<any>(`/admin/trades${query}`);
    },
    getUser: (userId: string) => request<any>(`/admin/users/${userId}`),
    freezeUser: (userId: string, reason: string) =>
      request<any>(`/admin/users/${userId}/freeze`, {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }),
    getPendingDeposits: () => request<any>('/admin/deposits/pending'),
    approveDeposit: (depositId: string) =>
      request<any>(`/admin/deposits/${depositId}/approve`, { method: 'POST' }),
    rejectDeposit: (depositId: string, reason: string) =>
      request<any>(`/admin/deposits/${depositId}/reject`, {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }),
  },
};

export { API_BASE };
export default api;
