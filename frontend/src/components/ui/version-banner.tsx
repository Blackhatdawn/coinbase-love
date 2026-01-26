/**
 * Version Mismatch Banner
 * 
 * Displays a banner when frontend-backend versions are incompatible
 */

import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface VersionBannerProps {
  serverVersion: string;
  clientVersion: string;
  onRefresh: () => void;
  className?: string;
}

export function VersionMismatchBanner({
  serverVersion,
  clientVersion,
  onRefresh,
  className,
}: VersionBannerProps) {
  return (
    <div
      className={cn(
        'fixed top-0 left-0 right-0 z-[100]',
        'bg-destructive/95 backdrop-blur-sm',
        'px-4 py-3',
        'animate-in slide-in-from-top duration-300',
        className
      )}
      role="alert"
      data-testid="version-mismatch-banner"
    >
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-3 text-destructive-foreground">
          <AlertTriangle className="h-5 w-5 flex-shrink-0" />
          <div className="text-sm sm:text-base">
            <span className="font-semibold">Update Required:</span>{' '}
            <span className="hidden sm:inline">
              Your app version ({clientVersion}) is outdated. Server version: {serverVersion}.
            </span>
            <span className="sm:hidden">
              Please refresh to get the latest version.
            </span>
          </div>
        </div>
        <Button
          onClick={onRefresh}
          size="sm"
          variant="secondary"
          className="bg-white/20 hover:bg-white/30 text-white border-0 flex-shrink-0"
          data-testid="refresh-app-button"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh Now
        </Button>
      </div>
    </div>
  );
}

/**
 * Connection Status Indicator
 * Shows API connection status
 */

interface ConnectionStatusProps {
  isConnected: boolean;
  isLoading?: boolean;
  className?: string;
}

export function ConnectionStatus({ isConnected, isLoading, className }: ConnectionStatusProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-2 text-xs font-medium',
        className
      )}
      data-testid="connection-status"
    >
      <div
        className={cn(
          'h-2 w-2 rounded-full transition-colors duration-300',
          isLoading && 'bg-yellow-500 animate-pulse',
          !isLoading && isConnected && 'bg-success',
          !isLoading && !isConnected && 'bg-destructive'
        )}
      />
      <span className="text-muted-foreground">
        {isLoading ? 'Connecting...' : isConnected ? 'API: Active' : 'API: Offline'}
      </span>
    </div>
  );
}
