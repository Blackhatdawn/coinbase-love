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
 * Generic request handler with authentication and error handling
 */
const request = async (
  endpoint: string,
  options: RequestInit = {}
) => {
  const url = `${API_BASE}${endpoint}`;
  const token = localStorage.getItem('auth_token');

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add authorization token if available
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle non-2xx responses
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));

      // Handle 401 - likely token expired, clear localStorage
      if (response.status === 401) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        // Optionally redirect to login
        if (typeof window !== 'undefined' && window.location.pathname !== '/auth') {
          // Don't redirect here, let components handle it
        }
      }

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
