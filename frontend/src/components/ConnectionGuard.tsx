import { useState, useEffect, ReactNode } from 'react';
import { Loader2, WifiOff, RefreshCw, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { checkBackendHealth, useConnectionStore } from '@/lib/apiClient';
import { cn } from '@/lib/utils';

interface ConnectionGuardProps {
  children: ReactNode;
}

/**
 * ConnectionGuard - Shows a professional loading spinner while backend connects
 * Handles Render cold-start delays gracefully
 */
export function ConnectionGuard({ children }: ConnectionGuardProps) {
  const { isConnected, isConnecting, connectionError, retryCount } = useConnectionStore();
  const [manualRetry, setManualRetry] = useState(false);

  useEffect(() => {
    checkBackendHealth();
  }, []);

  const handleRetry = async () => {
    setManualRetry(true);
    await checkBackendHealth();
    setManualRetry(false);
  };

  if (isConnected) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8 text-center">
        {/* Logo */}
        <div className="flex justify-center">
          <div className="relative">
            <div className={cn(
              "w-20 h-20 rounded-2xl flex items-center justify-center",
              "bg-gradient-to-br from-[#C5A049] to-[#8B7355]",
              isConnecting && "animate-pulse"
            )}>
              <Shield className="h-10 w-10 text-background" />
            </div>
            {isConnecting && (
              <div className="absolute -inset-2 rounded-3xl border-2 border-[#C5A049]/30 animate-ping" />
            )}
          </div>
        </div>

        {/* Title */}
        <div>
          <h1 className="font-display text-3xl font-bold text-foreground">CryptoVault</h1>
          <p className="text-sm text-muted-foreground mt-1">Secure Digital Asset Management</p>
        </div>

        {/* Status */}
        <div className="glass-card p-6 space-y-4">
          {isConnecting ? (
            <>
              <div className="flex items-center justify-center gap-3">
                <Loader2 className="h-5 w-5 animate-spin text-[#C5A049]" />
                <span className="text-foreground font-medium">Connecting to Secure Server...</span>
              </div>
              <p className="text-sm text-muted-foreground">
                {retryCount === 0
                  ? 'Establishing encrypted connection...'
                  : `Retry attempt ${retryCount}/3... The server may be waking up.`}
              </p>
              <div className="w-full bg-secondary rounded-full h-2 overflow-hidden">
                <div className="bg-[#C5A049] h-full rounded-full animate-pulse" style={{ width: '60%' }} />
              </div>
            </>
          ) : connectionError ? (
            <>
              <div className="flex items-center justify-center gap-3 text-destructive">
                <WifiOff className="h-5 w-5" />
                <span className="font-medium">Connection Failed</span>
              </div>
              <p className="text-sm text-muted-foreground">
                {connectionError.includes('cold start')
                  ? 'Server is starting up. This may take up to 60 seconds on free hosting plans.'
                  : connectionError}
              </p>
              <Button
                onClick={handleRetry}
                disabled={manualRetry}
                className="w-full bg-[#C5A049] hover:bg-[#B8933F] text-background"
              >
                {manualRetry ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Retrying...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Try Again
                  </>
                )}
              </Button>
            </>
          ) : null}
        </div>

        {/* Security Notice */}
        <p className="text-xs text-muted-foreground">
          🔒 All connections are secured with TLS encryption
        </p>
      </div>
    </div>
  );
}

export default ConnectionGuard;
