import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  eventId: string | null;
}

/**
 * Production-grade Error Boundary for CryptoVault
 * 
 * Features:
 * - Catches all React component errors
 * - Displays branded fallback UI
 * - Logs errors for monitoring
 * - Integrates with Sentry for error tracking
 * - Provides recovery options
 * - No sensitive data exposed
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null, eventId: null };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error details
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught an error:', error);
      console.error('Component stack:', errorInfo.componentStack);
    }

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo);

    this.setState({ errorInfo });

    // Send to Sentry in production (if configured)
    this.reportToSentry(error, errorInfo);
  }

  private async reportToSentry(error: Error, errorInfo: ErrorInfo) {
    // Only attempt Sentry reporting in production with DSN configured
    // Note: Install @sentry/react when deploying to production with Sentry
    if (import.meta.env.PROD && import.meta.env.VITE_SENTRY_DSN) {
      try {
        // Use dynamic import that Vite won't pre-analyze
        const sentryModule = '@sentry/react';
        const Sentry = await import(/* @vite-ignore */ sentryModule);
        const eventId = Sentry.captureException(error, {
          extra: {
            componentStack: errorInfo.componentStack,
          },
          tags: {
            type: 'react_error_boundary',
          },
        });
        this.setState({ eventId });
      } catch (e) {
        // Sentry not installed or not available, fail silently
        if (import.meta.env.DEV) {
          console.warn('Sentry reporting skipped (not installed):', e);
        }
      }
    }
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null, eventId: null });
  };

  handleReportFeedback = async () => {
    // Open Sentry feedback dialog if available
    if (this.state.eventId && import.meta.env.PROD && import.meta.env.VITE_SENTRY_DSN) {
      try {
        const Sentry = await import('@sentry/react');
        Sentry.showReportDialog({ eventId: this.state.eventId });
      } catch (e) {
        // Fallback to email
        window.location.href = 'mailto:support@cryptovault.financial?subject=Error Report';
      }
    } else {
      window.location.href = 'mailto:support@cryptovault.financial?subject=Error Report';
    }
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default branded error UI
      return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
          <div className="max-w-md w-full text-center">
            {/* Error Icon */}
            <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-destructive/10 flex items-center justify-center">
              <AlertTriangle className="w-10 h-10 text-destructive" />
            </div>

            {/* Brand */}
            <h1 className="font-display text-2xl font-bold mb-2">
              Crypto<span className="text-gold-400">Vault</span>
            </h1>

            {/* Message */}
            <h2 className="text-xl font-semibold mb-2">Something went wrong</h2>
            <p className="text-muted-foreground mb-6">
              We encountered an unexpected error. Our team has been notified and is working on a fix.
            </p>

            {/* Error details (only in development) */}
            {import.meta.env.DEV && this.state.error && (
              <div className="mb-6 p-4 bg-destructive/10 rounded-lg text-left">
                <p className="text-sm font-mono text-destructive break-all">
                  {this.state.error.message}
                </p>
              </div>
            )}

            {/* Event ID for support (production only) */}
            {this.state.eventId && (
              <p className="text-xs text-muted-foreground mb-4">
                Error ID: <code className="bg-muted px-1 py-0.5 rounded">{this.state.eventId}</code>
              </p>
            )}

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button
                onClick={this.handleReset}
                variant="outline"
                className="border-gold-500/30 hover:border-gold-400"
                data-testid="error-try-again-btn"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Try Again
              </Button>
              <Button
                onClick={this.handleGoHome}
                className="bg-gradient-to-r from-gold-500 to-gold-600 text-black"
                data-testid="error-go-home-btn"
              >
                <Home className="w-4 h-4 mr-2" />
                Go Home
              </Button>
            </div>

            {/* Support link */}
            <p className="mt-8 text-sm text-muted-foreground">
              Need help?{' '}
              <button
                onClick={this.handleReportFeedback}
                className="text-gold-400 hover:underline inline-flex items-center gap-1"
                data-testid="error-contact-support"
              >
                <Mail className="w-3 h-3" />
                Contact Support
              </button>
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Hook version for functional components
 */
export function useErrorBoundary() {
  const [error, setError] = React.useState<Error | null>(null);

  const resetError = () => setError(null);

  const captureError = async (error: Error) => {
    setError(error);
    
    // Report to Sentry in production
    if (import.meta.env.PROD && import.meta.env.VITE_SENTRY_DSN) {
      try {
        const Sentry = await import('@sentry/react');
        Sentry.captureException(error);
      } catch (e) {
        console.warn('Sentry reporting failed:', e);
      }
    }
    
    if (import.meta.env.DEV) {
      console.error('useErrorBoundary captured:', error);
    }
  };

  return { error, resetError, captureError };
}

/**
 * Simple fallback component for less critical sections
 */
export function ErrorFallback({
  error,
  resetError,
}: {
  error?: Error | null;
  resetError?: () => void;
}) {
  return (
    <div className="p-6 text-center border border-destructive/20 rounded-lg bg-destructive/5" data-testid="error-fallback">
      <AlertTriangle className="w-8 h-8 text-destructive mx-auto mb-3" />
      <h3 className="font-semibold mb-2">Unable to load this section</h3>
      <p className="text-sm text-muted-foreground mb-4">
        {error?.message || 'An unexpected error occurred'}
      </p>
      {resetError && (
        <Button variant="outline" size="sm" onClick={resetError} data-testid="error-fallback-retry">
          <RefreshCw className="w-3 h-3 mr-2" />
          Retry
        </Button>
      )}
    </div>
  );
}

export default ErrorBoundary;
