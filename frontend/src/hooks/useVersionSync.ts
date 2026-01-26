/**
 * Version Sync Hook
 * 
 * Automatically checks frontend-backend version compatibility
 * and handles version mismatches gracefully.
 */

import { useEffect, useState, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';

const APP_VERSION = '1.0.0';

interface VersionInfo {
  version: string;
  api_version: string;
  build_timestamp: string;
  git_commit: string;
  environment: string;
  min_frontend_version: string;
  features: Record<string, boolean>;
}

interface CompatibilityCheck {
  compatible: boolean;
  message: string;
  server_version: string;
  client_version: string;
  upgrade_required: boolean;
}

interface UseVersionSyncResult {
  isCompatible: boolean;
  serverVersion: string | null;
  clientVersion: string;
  features: Record<string, boolean>;
  isLoading: boolean;
  error: string | null;
  checkCompatibility: () => Promise<void>;
}

export function useVersionSync(): UseVersionSyncResult {
  const [isCompatible, setIsCompatible] = useState(true);
  const [serverVersion, setServerVersion] = useState<string | null>(null);
  const [features, setFeatures] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const checkCompatibility = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Get API base URL
      const apiUrl = import.meta.env.VITE_API_BASE_URL || '';
      
      // Check version endpoint
      const response = await fetch(`${apiUrl}/api/version/check?client_version=${APP_VERSION}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Version check failed: ${response.status}`);
      }

      const data: CompatibilityCheck = await response.json();
      
      setServerVersion(data.server_version);
      setIsCompatible(data.compatible);

      if (!data.compatible && data.upgrade_required) {
        toast({
          title: 'Update Required',
          description: 'A new version is available. Please refresh the page.',
          variant: 'destructive',
        });
      }

      // Also fetch features
      try {
        const featuresResponse = await fetch(`${apiUrl}/api/version/features`, {
          credentials: 'include',
        });
        if (featuresResponse.ok) {
          const featuresData = await featuresResponse.json();
          setFeatures(featuresData.features || {});
        }
      } catch {
        // Features fetch is optional
      }

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Version check failed';
      setError(message);
      // Don't block the app on version check failure
      setIsCompatible(true);
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    // Check on mount
    checkCompatibility();

    // Re-check periodically (every 5 minutes)
    const interval = setInterval(checkCompatibility, 5 * 60 * 1000);

    // Re-check on visibility change (user returns to tab)
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        checkCompatibility();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [checkCompatibility]);

  return {
    isCompatible,
    serverVersion,
    clientVersion: APP_VERSION,
    features,
    isLoading,
    error,
    checkCompatibility,
  };
}

/**
 * Check if a specific feature is enabled
 */
export function useFeatureFlag(featureName: string): boolean {
  const { features, isLoading } = useVersionSync();
  
  if (isLoading) {
    // Default to enabled while loading
    return true;
  }
  
  return features[featureName] ?? true;
}
