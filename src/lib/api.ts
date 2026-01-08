/**
 * API Client Configuration
 *
 * In development: Uses /api proxy defined in vite.config.ts (targets localhost:5000)
 * In production: Uses relative /api path (requests go to same domain where frontend is hosted)
 *
 * For separate domain deployments, update API_BASE environment variable
 */

const API_BASE = import.meta.env.VITE_API_URL || '/api';

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
 * Generic request handler with authentication and error handling
 * Uses HttpOnly cookies for authentication (automatically sent with credentials)
 * Implements automatic token refresh on 401 responses
 */
const request = async (
  endpoint: string,
  options: RequestInit = {}
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
      // IMPORTANT: Include credentials so cookies are sent with requests
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

      throw new APIError(response.status, error.error || 'Request failed');
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(0, error instanceof Error ? error.message : 'Network error');
  }
};

export const api = {
  // Auth
  auth: {
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
  },

  // Cryptocurrencies
  crypto: {
    getAll: () =>
      request('/crypto'),
    getOne: (symbol: string) =>
      request(`/crypto/${symbol}`),
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
};
