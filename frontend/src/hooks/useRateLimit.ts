import { useEffect, useCallback, useRef, useState } from 'react';
import { toast } from 'sonner';

interface RateLimitInfo {
  remaining: number;
  limit: number;
  reset: number;
  retryAfter?: number;
}

/**
 * Hook for monitoring and handling rate limits
 * Provides user-facing warnings before hitting limits
 */
export function useRateLimitMonitor() {
  const [rateLimitInfo, setRateLimitInfo] = useState<RateLimitInfo | null>(null);
  const [isWarningShown, setIsWarningShown] = useState(false);
  const lastWarningTime = useRef<number>(0);
  const WARNING_COOLDOWN = 60000; // 1 minute between warnings

  /**
   * Update rate limit information from response headers
   */
  const updateRateLimitInfo = useCallback((headers: Headers) => {
    const remaining = headers.get('X-RateLimit-Remaining');
    const limit = headers.get('X-RateLimit-Limit');
    const reset = headers.get('X-RateLimit-Reset');
    const retryAfter = headers.get('Retry-After');

    if (remaining && limit) {
      const info: RateLimitInfo = {
        remaining: parseInt(remaining, 10),
        limit: parseInt(limit, 10),
        reset: reset ? parseInt(reset, 10) * 1000 : Date.now() + 60000,
        retryAfter: retryAfter ? parseInt(retryAfter, 10) : undefined,
      };

      setRateLimitInfo(info);

      // Show warning when approaching limit
      const WARNING_THRESHOLD = Math.max(10, info.limit * 0.2); // 20% or 10 requests, whichever is higher
      
      if (info.remaining <= WARNING_THRESHOLD && info.remaining > 0) {
        const now = Date.now();
        
        // Only show warning if cooldown has passed
        if (now - lastWarningTime.current > WARNING_COOLDOWN) {
          lastWarningTime.current = now;
          setIsWarningShown(true);
          
          toast.warning(
            `Rate Limit Approaching`,
            {
              description: `You have ${info.remaining} requests remaining. Slow down to avoid being rate limited.`,
              duration: 5000,
              action: {
                label: 'Learn More',
                onClick: () => window.open('/help/rate-limits', '_blank'),
              },
            }
          );
        }
      }

      // Reset warning flag when back to safe levels
      if (info.remaining > WARNING_THRESHOLD) {
        setIsWarningShown(false);
      }
    }
  }, []);

  /**
   * Handle rate limit exceeded (429) response
   */
  const handleRateLimitExceeded = useCallback((headers: Headers) => {
    const retryAfter = headers.get('Retry-After');
    const reset = headers.get('X-RateLimit-Reset');

    let waitTime = 60; // Default 60 seconds

    if (retryAfter) {
      waitTime = parseInt(retryAfter, 10);
    } else if (reset) {
      waitTime = Math.max(1, Math.ceil((parseInt(reset, 10) * 1000 - Date.now()) / 1000));
    }

    const resetTime = new Date(Date.now() + waitTime * 1000).toLocaleTimeString();

    toast.error(
      'Rate Limit Exceeded',
      {
        description: `Too many requests. Please wait ${waitTime} seconds (until ${resetTime}) before trying again.`,
        duration: 10000,
      }
    );

    setRateLimitInfo(prev => prev ? {
      ...prev,
      remaining: 0,
      retryAfter: waitTime,
    } : null);
  }, []);

  /**
   * Get remaining time until rate limit resets
   */
  const getTimeUntilReset = useCallback((): string => {
    if (!rateLimitInfo) return '';

    const remaining = Math.max(0, rateLimitInfo.reset - Date.now());
    const seconds = Math.ceil(remaining / 1000);

    if (seconds < 60) {
      return `${seconds}s`;
    } else if (seconds < 3600) {
      return `${Math.ceil(seconds / 60)}m`;
    } else {
      return `${Math.ceil(seconds / 3600)}h`;
    }
  }, [rateLimitInfo]);

  /**
   * Check if rate limit is critical (less than 5 requests remaining)
   */
  const isRateLimitCritical = useCallback((): boolean => {
    return rateLimitInfo !== null && rateLimitInfo.remaining <= 5 && rateLimitInfo.remaining > 0;
  }, [rateLimitInfo]);

  /**
   * Check if rate limit is exceeded
   */
  const isRateLimitExceeded = useCallback((): boolean => {
    return rateLimitInfo !== null && rateLimitInfo.remaining === 0;
  }, [rateLimitInfo]);

  return {
    rateLimitInfo,
    isWarningShown,
    updateRateLimitInfo,
    handleRateLimitExceeded,
    getTimeUntilReset,
    isRateLimitCritical,
    isRateLimitExceeded,
  };
}

export default useRateLimitMonitor;
