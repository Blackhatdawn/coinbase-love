/**
 * CryptoVault API Client - Production-Grade Configuration
 * 
 * ARCHITECTURE:
 * - Fully decoupled Frontend/Backend
 * - Dynamic environment-based URL configuration
 * - Robust error handling with retry logic
 * - HTTP-Only cookie authentication with CSRF protection
 * - Health check with connection spinner
 * 
 * ENVIRONMENT VARIABLES:
 * - VITE_API_BASE_URL: Full backend URL (e.g., https://api.cryptovault.com)
 * - Required in production, optional in development (uses proxy)
 */

import { create } from 'zustand';

// ============================================
// ENVIRONMENT CONFIGURATION
// ============================================

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const IS_PRODUCTION = import.meta.env.PROD;
const IS_DEVELOPMENT = import.meta.env.DEV;

// Build-time validation
if (IS_PRODUCTION && !VITE_API_BASE_URL) {
  console.error(`
╔════════════════════════════════════════════════════════════════╗
║  ❌ CRITICAL CONFIGURATION ERROR                               ║
║                                                                 ║
║  VITE_API_BASE_URL is not set in production!                   ║
║                                                                 ║
║  Set this in your deployment platform (Vercel/Netlify):        ║
║    Key: VITE_API_BASE_URL                                      ║
║    Value: https://your-backend-domain.com                      ║
║                                                                 ║
║  The application cannot connect to the backend without this.   ║
╚════════════════════════════════════════════════════════════════╝
  `);
}

// Determine API base URL
let API_BASE: string;

if (VITE_API_BASE_URL) {
  // Production or explicitly configured: use environment variable
  API_BASE = `${VITE_API_BASE_URL.replace(/\/$/, '')}/api`;
} else if (IS_DEVELOPMENT) {
  // Development: use Vite proxy
  API_BASE = '/api';
} else {
  // Production fallback (will fail but provides clear error)
  API_BASE = '/api';
}

// Log configuration (non-sensitive)
if (IS_DEVELOPMENT) {
  console.log('🔌 CryptoVault API Configuration:', {
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
// RETRY & ERROR HANDLING CONFIGURATION
// ============================================

const RETRY_CONFIG = {
  maxRetries: 3,
  delays: [2000, 5000, 10000], // Exponential backoff
  healthCheckTimeout: 30000, // 30s for cold start (Render)
};

export class APIError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// ============================================
// HEALTH CHECK
// ============================================

let healthCheckPromise: Promise<boolean> | null = null;

export const checkBackendHealth = async (): Promise<boolean> => {
  // Prevent concurrent health checks
  if (healthCheckPromise) return healthCheckPromise;
  
  const store = useConnectionStore.getState();
  store.setConnecting(true);
  
  healthCheckPromise = (async () => {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), RETRY_CONFIG.healthCheckTimeout);
      
      const response = await fetch(`${API_BASE}/health`, {
        method: 'GET',
        signal: controller.signal,
        credentials: 'include',
      });
      
      clearTimeout(timeout);
      
      if (response.ok) {
        const data = await response.json();
        store.setConnected(true);
        store.setConnecting(false);
        store.resetRetry();
        console.log('✅ Backend connected:', data);
        return true;
      }
      
      throw new Error(`Health check failed: ${response.status}`);
    } catch (error: any) {
      const errorMessage = error.name === 'AbortError' 
        ? 'Backend is starting up (cold start)...'
        : error.message;
      
      store.setError(errorMessage);
      store.setConnecting(false);
      console.error('❌ Backend health check failed:', errorMessage);
      return false;
    } finally {
      healthCheckPromise = null;
    }
  })();
  
  return healthCheckPromise;
};

// ============================================
// TOKEN REFRESH STATE
// ============================================

let isRefreshing = false;
let refreshPromise: Promise<void> | null = null;
let refreshSubscribers: ((success: boolean) => void)[] = [];

const onRefreshed = (success: boolean) => {
  refreshSubscribers.forEach((callback) => callback(success));
  refreshSubscribers = [];
};

const addRefreshSubscriber = (callback: (success: boolean) => void) => {
  refreshSubscribers.push(callback);
};

// ============================================
// CORE REQUEST HANDLER
// ============================================

const request = async (
  endpoint: string,
  options: RequestInit = {},
  retryCount = 0
): Promise<any> => {
  const url = `${API_BASE}${endpoint}`;
  
  // Get CSRF token from cookie
  const csrfToken = document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrf_token='))
    ?.split('=')[1];
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(csrfToken && { 'X-CSRF-Token': csrfToken }),
    ...options.headers,
  };
  
  try {
    let response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include', // Send cookies
    });
    
    // Handle 401 - Token expired
    if (
      response.status === 401 &&
      !endpoint.includes('/auth/login') &&
      !endpoint.includes('/auth/signup') &&
      !endpoint.includes('/auth/refresh')
    ) {
      if (isRefreshing) {
        // Wait for ongoing refresh
        const success = await new Promise<boolean>((resolve) => {
          addRefreshSubscriber(resolve);
        });
        
        if (success) {
          // Retry with new token
          response = await fetch(url, {
            ...options,
            headers,
            credentials: 'include',
          });
        } else {
          throw new APIError(401, 'Session expired. Please log in again.', 'SESSION_EXPIRED');
        }
      } else {
        // Initiate refresh
        isRefreshing = true;
        
        try {
          const refreshResponse = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
          });
          
          if (refreshResponse.ok) {
            isRefreshing = false;
            onRefreshed(true);
            
            // Retry original request
            response = await fetch(url, {
              ...options,
              headers,
              credentials: 'include',
            });
          } else {
            isRefreshing = false;
            onRefreshed(false);
            throw new APIError(401, 'Session expired. Please log in again.', 'SESSION_EXPIRED');
          }
        } catch (refreshError) {
          isRefreshing = false;
          onRefreshed(false);
          throw refreshError;
        }
      }
    }
    
    // Handle non-2xx responses
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new APIError(
        response.status,
        error.error || error.detail || error.message || 'Request failed',
        error.code
      );
    }
    
    return await response.json();
  } catch (error) {
    if (error instanceof APIError) throw error;
    
    const isNetworkError = error instanceof TypeError;
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    
    // Retry on network errors (Render cold start)
    if (retryCount < RETRY_CONFIG.maxRetries && isNetworkError) {
      const delay = RETRY_CONFIG.delays[retryCount];
      console.log(`🔄 Retry ${retryCount + 1}/${RETRY_CONFIG.maxRetries} after ${delay}ms`);
      
      if (retryCount === 0) {
        console.log('⏳ Backend may be waking up from idle state...');
      }
      
      await new Promise((resolve) => setTimeout(resolve, delay));
      return request(endpoint, options, retryCount + 1);
    }
    
    // Connection failed
    if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
      throw new APIError(
        0,
        'Unable to connect to server. Please check your internet connection.',
        'NETWORK_ERROR'
      );
    }
    
    throw new APIError(0, errorMessage, 'UNKNOWN_ERROR');
  }
};

// ============================================
// API ENDPOINTS
// ============================================

export const api = {
  // Health Check
  health: {
    check: () => request('/health'),
  },
  
  // Authentication
  auth: {
    signup: (email: string, password: string, name: string) =>
      request('/auth/signup', {
        method: 'POST',
        body: JSON.stringify({ email, password, name }),
      }),
    login: (email: string, password: string, totp_code?: string) =>
      request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password, totp_code }),
      }),
    logout: () => request('/auth/logout', { method: 'POST' }),
    getProfile: () => request('/auth/me'),
    refresh: () => request('/auth/refresh', { method: 'POST' }),
    verifyEmail: (token: string, email: string) =>
      request('/auth/verify-email', {
        method: 'POST',
        body: JSON.stringify({ token, email }),
      }),
    resendVerification: (email: string) =>
      request('/auth/resend-verification', {
        method: 'POST',
        body: JSON.stringify({ email }),
      }),
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
    
    // Two-Factor Authentication
    setup2FA: () => request('/auth/2fa/setup', { method: 'POST' }),
    verify2FA: (code: string) =>
      request('/auth/2fa/verify', {
        method: 'POST',
        body: JSON.stringify({ code }),
      }),
    get2FAStatus: () => request('/auth/2fa/status'),
    disable2FA: (password: string) =>
      request('/auth/2fa/disable', {
        method: 'POST',
        body: JSON.stringify({ password }),
      }),
    getBackupCodes: () => request('/auth/2fa/backup-codes', { method: 'POST' }),
    
    // Session Management
    getSessions: () => request('/auth/sessions'),
    revokeSession: (sessionId: string) =>
      request(`/auth/sessions/${sessionId}`, { method: 'DELETE' }),
    revokeAllSessions: () =>
      request('/auth/sessions/revoke-all', { method: 'POST' }),
  },
  
  // Cryptocurrencies
  crypto: {
    getAll: () => request('/crypto'),
    getOne: (coinId: string) => request(`/crypto/${coinId}`),
    getHistory: (coinId: string, days = 7) =>
      request(`/crypto/${coinId}/history?days=${days}`),
  },
  
  // Portfolio
  portfolio: {
    get: () => request('/portfolio'),
    getHolding: (symbol: string) => request(`/portfolio/holding/${symbol}`),
    addHolding: (symbol: string, name: string, amount: number) =>
      request('/portfolio/holding', {
        method: 'POST',
        body: JSON.stringify({ symbol, name, amount }),
      }),
    deleteHolding: (symbol: string) =>
      request(`/portfolio/holding/${symbol}`, { method: 'DELETE' }),
  },
  
  // Wallet
  wallet: {
    getBalances: () => request('/wallet/balances'),
    getDepositAddress: (asset: string) =>
      request(`/wallet/deposit-address/${asset}`),
    createDeposit: (asset: string, amount: number, txHash?: string) =>
      request('/wallet/deposit', {
        method: 'POST',
        body: JSON.stringify({ asset, amount, tx_hash: txHash }),
      }),
    confirmDeposit: (depositId: string) =>
      request(`/wallet/deposit/${depositId}/confirm`, { method: 'POST' }),
    createWithdrawal: (asset: string, amount: number, address: string) =>
      request('/wallet/withdraw', {
        method: 'POST',
        body: JSON.stringify({ asset, amount, address }),
      }),
    getWithdrawalLimits: () => request('/wallet/withdrawal-limits'),
  },
  
  // P2P Transfers
  transfers: {
    p2p: (data: { recipient_email: string; amount: number; currency?: string; note?: string }) =>
      request('/transfers/p2p', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    getHistory: (limit = 50, offset = 0) =>
      request(`/transfers/p2p/history?limit=${limit}&offset=${offset}`),
  },
  
  // Staking/Vault
  staking: {
    getProducts: () => request('/staking/products'),
    stake: (productId: string, amount: number) =>
      request('/staking/stake', {
        method: 'POST',
        body: JSON.stringify({ product_id: productId, amount }),
      }),
    unstake: (stakeId: string) =>
      request(`/staking/${stakeId}/unstake`, { method: 'POST' }),
    getMyStakes: () => request('/staking/my-stakes'),
    getRewards: () => request('/staking/rewards'),
  },
  
  // Orders
  orders: {
    getAll: () => request('/orders'),
    create: (
      trading_pair: string,
      order_type: string,
      side: string,
      amount: number,
      price: number
    ) =>
      request('/orders', {
        method: 'POST',
        body: JSON.stringify({ trading_pair, order_type, side, amount, price }),
      }),
    getOne: (id: string) => request(`/orders/${id}`),
    cancel: (id: string) => request(`/orders/${id}/cancel`, { method: 'POST' }),
  },
  
  // Transactions
  transactions: {
    getAll: (limit = 50, offset = 0, filters?: { type?: string; status?: string; startDate?: string; endDate?: string }) => {
      let url = `/transactions?limit=${limit}&offset=${offset}`;
      if (filters?.type) url += `&type=${filters.type}`;
      if (filters?.status) url += `&status=${filters.status}`;
      if (filters?.startDate) url += `&start_date=${filters.startDate}`;
      if (filters?.endDate) url += `&end_date=${filters.endDate}`;
      return request(url);
    },
    getOne: (id: string) => request(`/transactions/${id}`),
    create: (type: string, amount: number, symbol?: string, description?: string) =>
      request('/transactions', {
        method: 'POST',
        body: JSON.stringify({ type, amount, symbol, description }),
      }),
    getStats: () => request('/transactions/stats/overview'),
  },
  
  // User Search
  users: {
    search: (email: string) =>
      request(`/users/search?email=${encodeURIComponent(email)}`),
  },
  
  // Referrals
  referrals: {
    getCode: () => request('/referrals/code'),
    getStats: () => request('/referrals/stats'),
    applyCode: (code: string) =>
      request('/referrals/apply', {
        method: 'POST',
        body: JSON.stringify({ code }),
      }),
  },
  
  // KYC
  kyc: {
    getStatus: () => request('/kyc/status'),
    submitLevel1: (data: { full_name: string; date_of_birth: string; country: string }) =>
      request('/kyc/level1', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    submitLevel2: (formData: FormData) =>
      fetch(`${API_BASE}/kyc/level2`, {
        method: 'POST',
        body: formData,
        credentials: 'include',
      }).then((r) => r.json()),
  },
  
  // Audit Logs
  auditLogs: {
    getLogs: (limit = 50, offset = 0, action?: string) => {
      let url = `/audit-logs?limit=${limit}&offset=${offset}`;
      if (action) url += `&action=${action}`;
      return request(url);
    },
    getSummary: (days = 30) => request(`/audit-logs/summary?days=${days}`),
    exportLogs: (days = 90) => request(`/audit-logs/export?days=${days}`),
  },
  
  // Admin (protected by super-admin flag)
  admin: {
    getUsers: (limit = 50, offset = 0) =>
      request(`/admin/users?limit=${limit}&offset=${offset}`),
    getUser: (userId: string) => request(`/admin/users/${userId}`),
    updateUser: (userId: string, data: { status?: string; kyc_level?: number; is_frozen?: boolean }) =>
      request(`/admin/users/${userId}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    getPendingDeposits: () => request('/admin/deposits/pending'),
    approveDeposit: (depositId: string) =>
      request(`/admin/deposits/${depositId}/approve`, { method: 'POST' }),
    rejectDeposit: (depositId: string, reason: string) =>
      request(`/admin/deposits/${depositId}/reject`, {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }),
    freezeAccount: (userId: string, reason: string) =>
      request(`/admin/users/${userId}/freeze`, {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }),
  },
};

export { API_BASE };
export default api;
