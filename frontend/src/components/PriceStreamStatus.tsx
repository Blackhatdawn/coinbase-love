/**
 * PriceStreamStatus Component
 * Shows real-time price stream connection status
 * Displays "LIVE" indicator, connection state, and data source
 */

import React from 'react';
import { Zap, AlertCircle, Loader } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ConnectionStatus } from '@/hooks/usePriceWebSocket';

interface PriceStreamStatusProps {
  status: ConnectionStatus;
  showDetails?: boolean;
  className?: string;
}

export function PriceStreamStatus({
  status,
  showDetails = false,
  className = '',
}: PriceStreamStatusProps) {
  const isLive = status.isConnected && !status.error;

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {/* Live Indicator */}
      <div className="flex items-center gap-1.5">
        {status.isConnecting ? (
          <Loader className="h-4 w-4 text-yellow-400 animate-spin" />
        ) : isLive ? (
          <>
            <div className="h-2.5 w-2.5 rounded-full bg-green-500 animate-pulse" />
            <span className="text-xs font-bold text-green-400 uppercase tracking-wider">
              Live
            </span>
          </>
        ) : (
          <>
            <AlertCircle className="h-4 w-4 text-red-400" />
            <span className="text-xs font-bold text-red-400 uppercase">Offline</span>
          </>
        )}
      </div>

      {/* Source Badge */}
      {isLive && status.source && (
        <div className="text-[10px] bg-blue-500/20 text-blue-300 px-1.5 py-0.5 rounded">
          {status.source.toUpperCase()}
        </div>
      )}

      {/* Reconnecting State */}
      {status.isConnecting && (
        <div className="text-[10px] bg-yellow-500/20 text-yellow-300 px-1.5 py-0.5 rounded">
          Reconnecting...
        </div>
      )}

      {/* Error State */}
      {status.error && (
        <div className="text-[10px] bg-red-500/20 text-red-300 px-1.5 py-0.5 rounded">
          {status.error}
        </div>
      )}

      {/* Details */}
      {showDetails && (
        <div className="ml-auto text-right">
          <div className="text-[10px] text-muted-foreground">
            {status.pricesCached > 0 && `${status.pricesCached} prices`}
            {status.lastUpdate && (
              <div>
                Updated:{' '}
                {new Date(status.lastUpdate).toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit',
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default PriceStreamStatus;
