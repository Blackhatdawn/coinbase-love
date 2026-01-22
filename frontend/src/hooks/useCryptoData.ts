/**
 * useCryptoData - React hook for fetching live cryptocurrency data
 * 
 * Features:
 * - Fetches from backend (which proxies CoinCap API with caching)
 * - Auto-refresh every 60 seconds
 * - Loading, error, and data states
 * - Retry mechanism with exponential backoff
 * - SSR-safe (no window access during initial render)
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '@/lib/apiClient';

export interface CryptoData {
  id: string;
  symbol: string;
  name: string;
  price: number;
  market_cap: number;
  volume_24h: number;
  change_24h: number;
  image?: string;
  last_updated?: string;
}

interface UseCryptoDataOptions {
  refreshInterval?: number; // in milliseconds
  autoRefresh?: boolean;
  limit?: number;
}

interface UseCryptoDataReturn {
  data: CryptoData[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  refetch: () => Promise<void>;
  isRefreshing: boolean;
}

const DEFAULT_REFRESH_INTERVAL = 60000; // 60 seconds

export function useCryptoData(options: UseCryptoDataOptions = {}): UseCryptoDataReturn {
  const {
    refreshInterval = DEFAULT_REFRESH_INTERVAL,
    autoRefresh = true,
    limit,
  } = options;

  const [data, setData] = useState<CryptoData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const retryCount = useRef(0);
  const mounted = useRef(true);

  const fetchData = useCallback(async (isBackground = false) => {
    try {
      if (!isBackground) {
        setIsLoading(true);
      } else {
        setIsRefreshing(true);
      }

      const response = await api.crypto.getAll(limit);
      
      if (!mounted.current) return;

      // Handle various response structures from backend
      let cryptoList: CryptoData[] = [];
      
      if (response?.cryptocurrencies?.value) {
        // Backend returns JSON string in cache value format
        try {
          const parsed = typeof response.cryptocurrencies.value === 'string' 
            ? JSON.parse(response.cryptocurrencies.value)
            : response.cryptocurrencies.value;
          cryptoList = Array.isArray(parsed) ? parsed : [];
        } catch {
          cryptoList = [];
        }
      } else if (Array.isArray(response?.cryptocurrencies)) {
        cryptoList = response.cryptocurrencies;
      } else if (Array.isArray(response)) {
        cryptoList = response;
      }
      
      // Normalize data format
      cryptoList = cryptoList.map(crypto => ({
        ...crypto,
        change_24h: crypto.change_24h ?? crypto.priceChangePercentage24h ?? 0,
        market_cap: crypto.market_cap ?? crypto.marketCap ?? 0,
        volume_24h: crypto.volume_24h ?? crypto.totalVolume ?? 0,
      }));

      setData(cryptoList);
      setError(null);
      setLastUpdated(new Date());
      retryCount.current = 0;
    } catch (err: any) {
      if (!mounted.current) return;

      const errorMessage = err.message || 'Failed to load market data';
      setError(errorMessage);
      
      // Exponential backoff retry (max 3 retries)
      if (retryCount.current < 3) {
        retryCount.current++;
        const delay = Math.pow(2, retryCount.current) * 1000; // 2s, 4s, 8s
        console.log(`Retry ${retryCount.current}/3 in ${delay}ms`);
        setTimeout(() => fetchData(isBackground), delay);
      }
    } finally {
      if (mounted.current) {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    mounted.current = true;
    fetchData();

    return () => {
      mounted.current = false;
    };
  }, [fetchData]);

  // Auto-refresh interval
  useEffect(() => {
    if (!autoRefresh || refreshInterval <= 0) return;

    const interval = setInterval(() => {
      fetchData(true); // Background refresh
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchData]);

  const refetch = useCallback(async () => {
    retryCount.current = 0;
    await fetchData();
  }, [fetchData]);

  return {
    data,
    isLoading,
    error,
    lastUpdated,
    refetch,
    isRefreshing,
  };
}

/**
 * Format price with appropriate decimal places
 */
export function formatPrice(price: number): string {
  if (price >= 1000) {
    return price.toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  } else if (price >= 1) {
    return price.toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    });
  } else {
    return price.toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4,
      maximumFractionDigits: 8,
    });
  }
}

/**
 * Format market cap / volume (e.g., $1.2T, $456B, $12M)
 */
export function formatCompactNumber(num: number): string {
  if (num >= 1e12) {
    return `$${(num / 1e12).toFixed(2)}T`;
  } else if (num >= 1e9) {
    return `$${(num / 1e9).toFixed(2)}B`;
  } else if (num >= 1e6) {
    return `$${(num / 1e6).toFixed(2)}M`;
  } else {
    return `$${num.toLocaleString()}`;
  }
}

/**
 * Format percentage change
 */
export function formatPercentage(change: number): string {
  const sign = change >= 0 ? '+' : '';
  return `${sign}${change.toFixed(2)}%`;
}

export default useCryptoData;
