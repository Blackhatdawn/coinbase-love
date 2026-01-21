/**
 * PriceStreamStatusV2 Component - Enterprise Edition
 * 
 * Enhanced real-time price stream connection status display with:
 * - Connection quality metrics (latency, stability)
 * - Network status indicator
 * - Detailed debugging information
 * - Reconnection progress
 */

import React from 'react';
import { Zap, AlertCircle, Loader, Wifi, WifiOff, Activity, Signal, SignalLow, SignalMedium, SignalHigh } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ConnectionStatus, ConnectionQuality } from '@/hooks/usePriceWebSocketV2';

interface PriceStreamStatusV2Props {
  status: ConnectionStatus;
  showDetails?: boolean;
  showQuality?: boolean;
  className?: string;
}

/**
 * Get signal strength icon based on latency
 */
function getSignalIcon(latency: number) {
  if (latency < 100) {
    return <SignalHigh className="h-4 w-4 text-green-400" />;
  } else if (latency < 300) {
    return <SignalMedium className="h-4 w-4 text-yellow-400" />;
  } else if (latency < 500) {
    return <SignalLow className="h-4 w-4 text-orange-400" />;
  } else {
    return <Signal className="h-4 w-4 text-red-400" />;
  }
}

/**
 * Get quality badge color based on metrics
 */
function getQualityBadge(quality: ConnectionQuality | null): {
  color: string;
  label: string;
} {
  if (!quality) {
    return { color: 'bg-gray-500/20 text-gray-300', label: 'Unknown' };
  }

  if (quality.isStable && quality.latency < 100) {
    return { color: 'bg-green-500/20 text-green-300', label: 'Excellent' };
  } else if (quality.isStable && quality.latency < 300) {
    return { color: 'bg-blue-500/20 text-blue-300', label: 'Good' };
  } else if (quality.latency < 500) {
    return { color: 'bg-yellow-500/20 text-yellow-300', label: 'Fair' };
  } else {
    return { color: 'bg-red-500/20 text-red-300', label: 'Poor' };
  }
}

export function PriceStreamStatusV2({
  status,
  showDetails = false,
  showQuality = false,
  className = '',
}: PriceStreamStatusV2Props) {
  const isLive = status.isConnected && !status.error;
  const qualityBadge = getQualityBadge(status.quality);

  return (
    <div className={cn('flex items-center gap-2 flex-wrap', className)}>
      {/* Network Status */}
      {!status.isOnline && (
        <div className="flex items-center gap-1">
          <WifiOff className="h-4 w-4 text-red-400" />
          <span className="text-xs font-bold text-red-400">Offline</span>
        </div>
      )}

      {/* Connection Status */}
      {status.isOnline && (
        <div className="flex items-center gap-1.5">
          {status.isConnecting ? (
            <>
              <Loader className="h-4 w-4 text-yellow-400 animate-spin" />
              <span className="text-xs font-bold text-yellow-400 uppercase tracking-wider">
                Connecting
                {status.reconnectAttempt > 0 && ` (${status.reconnectAttempt})`}
              </span>
            </>
          ) : isLive ? (
            <>
              <div className="relative">
                <div className="h-2.5 w-2.5 rounded-full bg-green-500" />
                <div className="absolute inset-0 h-2.5 w-2.5 rounded-full bg-green-500 animate-ping opacity-75" />
              </div>
              <span className="text-xs font-bold text-green-400 uppercase tracking-wider">
                Live
              </span>
            </>
          ) : (
            <>
              <AlertCircle className="h-4 w-4 text-red-400" />
              <span className="text-xs font-bold text-red-400 uppercase">
                Disconnected
              </span>
            </>
          )}
        </div>
      )}

      {/* Source Badge */}
      {isLive && status.source && (
        <div className="text-[10px] bg-blue-500/20 text-blue-300 px-1.5 py-0.5 rounded font-medium">
          {status.source.toUpperCase()}
        </div>
      )}

      {/* Quality Badge */}
      {showQuality && isLive && status.quality && (
        <div className={cn('flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded', qualityBadge.color)}>
          {getSignalIcon(status.quality.latency)}
          <span>{qualityBadge.label}</span>
        </div>
      )}

      {/* Reconnecting State */}
      {status.isConnecting && status.reconnectAttempt > 0 && (
        <div className="text-[10px] bg-yellow-500/20 text-yellow-300 px-1.5 py-0.5 rounded">
          Reconnecting...
        </div>
      )}

      {/* Error State */}
      {status.error && !status.isConnecting && (
        <div className="text-[10px] bg-red-500/20 text-red-300 px-1.5 py-0.5 rounded max-w-[150px] truncate" title={status.error}>
          {status.error}
        </div>
      )}

      {/* Detailed Stats */}
      {showDetails && (
        <div className="ml-auto flex items-center gap-3 text-right">
          {/* Price Count */}
          {status.pricesCached > 0 && (
            <div className="text-[10px] text-muted-foreground flex items-center gap-1">
              <Activity className="h-3 w-3" />
              {status.pricesCached} prices
            </div>
          )}

          {/* Latency */}
          {status.quality && (
            <div className="text-[10px] text-muted-foreground flex items-center gap-1">
              <Zap className="h-3 w-3" />
              {status.quality.latency}ms
            </div>
          )}

          {/* Messages/sec */}
          {status.quality && status.quality.messagesPerSecond > 0 && (
            <div className="text-[10px] text-muted-foreground">
              {status.quality.messagesPerSecond} msg/s
            </div>
          )}

          {/* Last Update */}
          {status.lastUpdate && (
            <div className="text-[10px] text-muted-foreground">
              Updated:{' '}
              {new Date(status.lastUpdate).toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Compact status indicator for headers/toolbars
 */
export function PriceStreamIndicator({
  status,
  className = '',
}: {
  status: ConnectionStatus;
  className?: string;
}) {
  const isLive = status.isConnected && !status.error;

  return (
    <div
      className={cn('flex items-center gap-1', className)}
      title={
        isLive
          ? `Connected to ${status.source || 'price stream'} - ${status.pricesCached} prices`
          : status.isConnecting
          ? 'Connecting...'
          : status.error || 'Disconnected'
      }
    >
      {status.isConnecting ? (
        <Loader className="h-3 w-3 text-yellow-400 animate-spin" />
      ) : isLive ? (
        <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
      ) : !status.isOnline ? (
        <WifiOff className="h-3 w-3 text-gray-400" />
      ) : (
        <div className="h-2 w-2 rounded-full bg-red-500" />
      )}
    </div>
  );
}

export default PriceStreamStatusV2;
