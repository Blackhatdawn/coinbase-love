/**
 * Debug API Status Component
 * Shows API connection status and health check information in development mode
 * Only visible when VITE_NODE_ENV=development
 */

import { useState, useEffect } from 'react';
import { healthCheckService } from '@/services/healthCheck';
import { ChevronDown, ChevronUp, Zap, AlertCircle } from 'lucide-react';

export function DebugApiStatus() {
  const [isOpen, setIsOpen] = useState(false);
  const [status, setStatus] = useState(healthCheckService.getStatus());
  const [apiBaseUrl, setApiBaseUrl] = useState('');

  useEffect(() => {
    // Get API base URL from environment
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'Not configured';
    setApiBaseUrl(baseUrl);
  }, []);

  useEffect(() => {
    // Update health check status every second
    const interval = setInterval(() => {
      setStatus(healthCheckService.getStatus());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Only show in development mode
  if (import.meta.env.PROD) {
    return null;
  }

  const formatTime = (ms: number) => {
    if (ms < 0) return 'Never';
    if (ms < 1000) return `${ms.toFixed(0)}ms ago`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s ago`;
    return `${(ms / 60000).toFixed(1)}m ago`;
  };

  const healthColor = status.isHealthy
    ? 'border-emerald-500/50 bg-emerald-500/10'
    : 'border-red-500/50 bg-red-500/10';

  const healthIcon = status.isHealthy ? '✅' : '⚠️';

  return (
    <div
      className="fixed bottom-4 right-4 z-50 text-xs font-mono max-w-sm"
      style={{ pointerEvents: 'auto' }}
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          w-full px-3 py-2 rounded-lg border flex items-center gap-2
          transition-all duration-200 hover:shadow-lg
          ${healthColor}
          ${isOpen ? 'rounded-b-none border-b-0' : ''}
        `}
      >
        <Zap className="h-4 w-4" />
        <span className="flex-1 text-left">
          {healthIcon} API: {status.isEnabled ? 'Active' : 'Inactive'}
        </span>
        {isOpen ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
      </button>

      {isOpen && (
        <div
          className={`
            w-full px-3 py-3 rounded-lg rounded-t-none border border-t-0
            space-y-2 bg-background/95 backdrop-blur-sm overflow-auto max-h-80
            ${healthColor}
          `}
        >
          {/* Base URL */}
          <div className="space-y-1">
            <div className="text-muted-foreground">API Base URL:</div>
            <div className="break-all bg-background/50 p-2 rounded border border-border/50">
              {apiBaseUrl.length > 50 ? (
                <>
                  <div>{apiBaseUrl.substring(0, 50)}...</div>
                  <div className="text-[10px] mt-1 text-muted-foreground">
                    (Full: {apiBaseUrl})
                  </div>
                </>
              ) : (
                apiBaseUrl
              )}
            </div>
          </div>

          {/* Health Status */}
          <div className="space-y-1">
            <div className="text-muted-foreground">Health Check:</div>
            <div className="space-y-1 bg-background/50 p-2 rounded border border-border/50">
              <div className="flex justify-between">
                <span>Status:</span>
                <span className={status.isHealthy ? 'text-emerald-400' : 'text-red-400'}>
                  {status.isHealthy ? 'Healthy' : 'Unhealthy'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Enabled:</span>
                <span>{status.isEnabled ? 'Yes' : 'No'}</span>
              </div>
              <div className="flex justify-between">
                <span>Last Ping:</span>
                <span>{formatTime(status.timeSinceLastPing)}</span>
              </div>
              <div className="flex justify-between">
                <span>Failures:</span>
                <span className={status.consecutiveFailures > 0 ? 'text-yellow-400' : ''}>
                  {status.consecutiveFailures}
                </span>
              </div>
            </div>

            {/* Rate Limit Info */}
            <div className="space-y-1">
              <div className="text-muted-foreground">Rate Limit:</div>
              <div className="space-y-1 bg-background/50 p-2 rounded border border-border/50">
                <div className="flex justify-between">
                  <span>Remaining:</span>
                  <span className={
                    status.rateLimitRemaining < 10 ? 'text-red-400' :
                    status.rateLimitRemaining < 20 ? 'text-yellow-400' :
                    'text-emerald-400'
                  }>
                    {status.rateLimitRemaining}/60
                  </span>
                </div>
                <div className="w-full bg-background/50 rounded h-1.5">
                  <div
                    className={`h-full rounded transition-all ${
                      status.rateLimitRemaining < 10 ? 'bg-red-500' :
                      status.rateLimitRemaining < 20 ? 'bg-yellow-500' :
                      'bg-emerald-500'
                    }`}
                    style={{ width: `${(status.rateLimitRemaining / 60) * 100}%` }}
                  />
                </div>
                {status.rateLimitRemaining < 20 && (
                  <div className="text-[10px] text-yellow-300 mt-1">
                    ⚠️ Approaching rate limit
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Warning if not healthy */}
          {!status.isHealthy && (
            <div className="flex gap-2 p-2 rounded bg-red-500/10 border border-red-500/30">
              <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="text-red-300 text-[10px]">
                Backend connection issues detected. Check console for details and ensure
                VITE_API_BASE_URL is correctly configured.
              </div>
            </div>
          )}

          {/* Help text */}
          <div className="text-[10px] text-muted-foreground pt-2 border-t border-border/50">
            Health checks keep the serverless backend active. If disabled, check browser
            console for connection errors.
          </div>
        </div>
      )}
    </div>
  );
}

export default DebugApiStatus;
