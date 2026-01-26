/**
 * Sentry configuration for production error tracking
 */

import * as Sentry from '@sentry/react';
import { getRuntimeConfig, resolveSentryConfig } from '@/lib/runtimeConfig';

// Initialize Sentry only in production and when DSN is available
export const initSentry = () => {
  const runtimeConfig = getRuntimeConfig();
  const sentryConfig = resolveSentryConfig();
  const sentryDsn = sentryConfig?.dsn || import.meta.env.VITE_SENTRY_DSN;
  const enableSentry = sentryConfig?.enabled ?? (import.meta.env.VITE_ENABLE_SENTRY === 'true');
  const environment = sentryConfig?.environment || import.meta.env.MODE;
  const isProduction = environment === 'production';
  const releaseVersion = runtimeConfig?.version || import.meta.env.VITE_APP_VERSION || '1.0.0';

  if (isProduction && enableSentry && sentryDsn) {
    Sentry.init({
      dsn: sentryDsn,
      environment,
      release: `cryptovault@${releaseVersion}`,
      
      // Performance monitoring
      integrations: [
        Sentry.browserTracingIntegration({
          // Only trace requests to our own API - prevents CSP issues with external APIs
          // This setting controls which URLs Sentry adds trace headers to
          tracePropagationTargets: [
            'localhost',
            /^https?:\/\/[^/]+\.financial/,  // Match any .financial domain
            /^https?:\/\/[^/]+\.fly\.dev/,   // Match any .fly.dev domain
            /^\/api\//,  // Relative API paths
          ],
        }),
      ],
      
      // Performance monitoring sample rate (10% of transactions)
      tracesSampleRate: 0.1,
      
      // Sample rate for profiling (5% of transactions)
      profilesSampleRate: 0.05,
      
      // Session replay sample rate (10% of sessions)
      replaysSessionSampleRate: 0.1,
      
      // Replay sample rate on error (100% of error sessions)
      replaysOnErrorSampleRate: 1.0,
      
      // Ignore common non-critical errors
      beforeSend(event) {
        // Filter out network errors from ad blockers
        if (event.exception) {
          const error = event.exception.values?.[0];
          if (error?.type === 'NetworkError' || 
              error?.value?.includes('Failed to fetch') ||
              error?.value?.includes('Load failed')) {
            return null;
          }
        }
        
        // Filter out React hydration warnings in development
        if (event.message?.includes('Warning:') && 
            event.message?.includes('hydration')) {
          return null;
        }
        
        return event;
      },
      
      // Set user context
      initialScope: {
        tags: {
          component: 'frontend',
        },
      },
    });

    console.log('Sentry initialized for production error tracking');
  } else {
    console.log('Sentry disabled: not in production or missing configuration');
  }
};

// Error boundary wrapper
export const SentryErrorBoundary = Sentry.withErrorBoundary;

// Set user context when user logs in
export const setSentryUser = (user: {
  id: string;
  email?: string;
  username?: string;
}) => {
  Sentry.setUser({
    id: user.id,
    email: user.email,
    username: user.username,
  });
};

// Clear user context when user logs out
export const clearSentryUser = () => {
  Sentry.setUser(null);
};

// Capture custom events
export const captureEvent = (event: string, data?: Record<string, any>) => {
  Sentry.addBreadcrumb({
    message: event,
    data,
    level: 'info',
  });
};

// Capture performance metrics
export const capturePerformance = (name: string, duration: number) => {
  Sentry.addBreadcrumb({
    message: `Performance: ${name}`,
    data: { duration },
    level: 'info',
  });
};

// Manual error capture
export const captureError = (error: Error, context?: Record<string, any>) => {
  Sentry.withScope((scope) => {
    if (context) {
      scope.setContext('custom', context);
    }
    Sentry.captureException(error);
  });
};
