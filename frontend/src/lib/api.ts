/**
 * API Client Configuration
 *
 * Development: Uses /api proxy in vite.config.ts → http://localhost:8001
 * Production: Uses VITE_API_URL environment variable → Render backend
 *
 * The API base URL is determined by:
 * 1. VITE_API_URL env var (production Render URL)
 * 2. Falls back to '/api' for local development
 *
 * IMPORTANT: VITE_API_URL must be set in Vercel dashboard:
 * https://coinbase-love.onrender.com
 */

const API_BASE = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api';

// Log API configuration (development only)
if (import.meta.env.DEV) {
  console.log('🔌 API Configuration:', {
    base: API_BASE,
    mode: import.meta.env.MODE,
    viteApiUrl: import.meta.env.VITE_API_URL
  });
}

/**
 * Retry configuration for Render free tier spin-down
 * - Render spins down after 15 min inactivity
 * - First request can take 30-60 seconds
 * - We retry with exponential backoff
 */
const RETRY_CONFIG = {
  maxRetries: 3,
  delays: [2000, 5000, 10000], // 2s, 5s, 10s
};

export class APIError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

/**
 * Token refresh state to prevent multiple concurrent refresh attempts
 */
let isRefreshing = false;
let refreshPromise: Promise<void> | null = null;

/**
 * Generic request handler with authentication, error handling, and retry logic
 * Uses HttpOnly cookies for authentication (automatically sent with credentials)
 * Implements automatic token refresh on 401 responses
 * Retries on network errors (for Render spin-down handling)
 */
const request = async (
  endpoint: string,
  options: RequestInit = {},
  retryCount = 0
): Promise<any> => {
  const url = `${API_BASE}${endpoint}`;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  try {
    let response = await fetch(url, {
      ...options,
      headers,
      // IMPORTANT: Set to 'include' for cookie-based auth, or 'omit' if not using cookies
      credentials: 'include',
    });

    // Handle 401 - token expired, attempt refresh
    if (response.status === 401 && endpoint !== '/auth/refresh' && endpoint !== '/auth/login' && endpoint !== '/auth/signup') {
      // If already refreshing, wait for the refresh to complete
      if (isRefreshing && refreshPromise) {
        await refreshPromise;
        // Retry original request with refreshed token
        response = await fetch(url, {
          ...options,
          headers,
          credentials: 'include',
        });
      } else if (!isRefreshing) {
        // Start refresh process
        isRefreshing = true;
        refreshPromise = (async () => {
          try {
            await fetch(`${API_BASE}/auth/refresh`, {
              method: 'POST',
              credentials: 'include',
              headers: { 'Content-Type': 'application/json' },
            });
          } catch (error) {
            console.error('Token refresh failed:', error);
          } finally {
            isRefreshing = false;
            refreshPromise = null;
          }
        })();

        await refreshPromise;

        // Retry original request
        response = await fetch(url, {
          ...options,
          headers,
          credentials: 'include',
        });
      }
    }

    // Handle non-2xx responses
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));

      throw new APIError(response.status, error.error || error.detail || 'Request failed');
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) throw error;
    
    // Network error - could be Render spin-down
    // Retry with exponential backoff
    if (retryCount < RETRY_CONFIG.maxRetries) {
      const delay = RETRY_CONFIG.delays[retryCount];
      console.log(`🔄 Retrying request (attempt ${retryCount + 1}/${RETRY_CONFIG.maxRetries}) after ${delay}ms...`);
      
      // Show user-friendly message for first retry (likely spin-down)
      if (retryCount === 0) {
        console.log('⏳ Backend is waking up... (Render free tier spin-down, may take 30-60s)');
      }
      
      await new Promise(resolve => setTimeout(resolve, delay));
      return request(endpoint, options, retryCount + 1);
    }
    
    throw new APIError(0, error instanceof Error ? error.message : 'Network error');
  }
};

export const api = {
  // Authentication & Auth-related
  auth: {
    // Basic auth
    signup: (email: string, password: string, name: string) =>
      request('/auth/signup', {
        method: 'POST',
        body: JSON.stringify({ email, password, name }),
      }),
    login: (email: string, password: string) =>
      request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    logout: () =>
      request('/auth/logout', { method: 'POST' }),
    getProfile: () =>
      request('/auth/me'),
    refresh: () =>
      request('/auth/refresh', { method: 'POST' }),
    verifyEmail: (token: string, email: string) =>
      request('/auth/verify-email', {
        method: 'POST',
        body: JSON.stringify({ token, email }),
      }),

    // Two-Factor Authentication
    setup2FA: () =>
      request('/auth/2fa/setup', { method: 'POST' }),
    verify2FA: (code: string) =>
      request('/auth/2fa/verify', {
        method: 'POST',
        body: JSON.stringify({ code }),
      }),
    get2FAStatus: () =>
      request('/auth/2fa/status'),
    disable2FA: (password: string) =>
      request('/auth/2fa/disable', {
        method: 'POST',
        body: JSON.stringify({ password }),
      }),
    getBackupCodes: () =>
      request('/auth/2fa/backup-codes', { method: 'POST' }),
  },

  // Cryptocurrencies
  crypto: {
    getAll: () =>
      request('/crypto'),
    getOne: (coinId: string) =>
      request(`/crypto/${coinId}`),
    getHistory: (coinId: string, days: number = 7) =>
      request(`/crypto/${coinId}/history?days=${days}`),
  },

  // Portfolio
  portfolio: {
    get: () =>
      request('/portfolio'),
    getHolding: (symbol: string) =>
      request(`/portfolio/holding/${symbol}`),
    addHolding: (symbol: string, name: string, amount: number) =>
      request('/portfolio/holding', {
        method: 'POST',
        body: JSON.stringify({ symbol, name, amount }),
      }),
    deleteHolding: (symbol: string) =>
      request(`/portfolio/holding/${symbol}`, { method: 'DELETE' }),
  },

  // Orders
  orders: {
    getAll: () =>
      request('/orders'),
    create: (trading_pair: string, order_type: string, side: string, amount: number, price: number) =>
      request('/orders', {
        method: 'POST',
        body: JSON.stringify({ trading_pair, order_type, side, amount, price }),
      }),
    getOne: (id: string) =>
      request(`/orders/${id}`),
    cancel: (id: string) =>
      request(`/orders/${id}/cancel`, { method: 'POST' }),
  },

  // Transactions
  transactions: {
    getAll: (limit = 50, offset = 0) =>
      request(`/transactions?limit=${limit}&offset=${offset}`),
    getOne: (id: string) =>
      request(`/transactions/${id}`),
    create: (type: string, amount: number, symbol?: string, description?: string) =>
      request('/transactions', {
        method: 'POST',
        body: JSON.stringify({ type, amount, symbol, description }),
      }),
    getStats: () =>
      request('/transactions/stats/overview'),
  },

  // Audit Logs
  auditLogs: {
    getLogs: (limit = 50, offset = 0, action?: string) => {
      let url = `/audit-logs?limit=${limit}&offset=${offset}`;
      if (action) url += `&action=${action}`;
      return request(url);
    },
    getSummary: (days = 30) =>
      request(`/audit-logs/summary?days=${days}`),
    exportLogs: (days = 90) =>
      request(`/audit-logs/export?days=${days}`),
    getLog: (id: string) =>
      request(`/audit-logs/${id}`),
  },
};
