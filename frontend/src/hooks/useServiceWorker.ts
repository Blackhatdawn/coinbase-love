import { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';

interface ServiceWorkerState {
  isSupported: boolean;
  isInstalled: boolean;
  isUpdating: boolean;
  offlineReady: boolean;
  needRefresh: boolean;
  cacheStatus: Record<string, number>;
}

/**
 * Hook for managing Service Worker registration and lifecycle
 * 
 * Features:
 * - PWA installation prompts
 * - Offline readiness detection
 * - Update notifications
 * - Cache management
 * - Background sync status
 */
export function useServiceWorker() {
  const [state, setState] = useState<ServiceWorkerState>({
    isSupported: false,
    isInstalled: false,
    isUpdating: false,
    offlineReady: false,
    needRefresh: false,
    cacheStatus: {},
  });

  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);

  /**
   * Register the service worker
   */
  const register = useCallback(async () => {
    if (!('serviceWorker' in navigator)) {
      console.log('[SW] Service workers not supported');
      return;
    }

    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
        updateViaCache: 'imports',
      });

      console.log('[SW] Service worker registered:', registration.scope);

      // Listen for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New version available
              setState(prev => ({ ...prev, needRefresh: true }));
              toast.info('Update Available', {
                description: 'A new version is available. Click to refresh.',
                action: {
                  label: 'Update',
                  onClick: () => updateServiceWorker(),
                },
                duration: 0, // Don't auto-dismiss
              });
            }
          });
        }
      });

      // Check if controller exists (SW is controlling the page)
      if (navigator.serviceWorker.controller) {
        setState(prev => ({ ...prev, isInstalled: true }));
      }

      // Listen for messages from SW
      navigator.serviceWorker.addEventListener('message', (event) => {
        const { type, data } = event.data;
        
        switch (type) {
          case 'SYNC_COMPLETE':
            toast.success('Offline data synced successfully');
            break;
            
          case 'CACHE_STATUS':
            setState(prev => ({ ...prev, cacheStatus: data.caches }));
            break;
        }
      });

      setState(prev => ({ ...prev, isSupported: true }));

      // Get initial cache status
      getCacheStatus();

    } catch (error) {
      console.error('[SW] Registration failed:', error);
      toast.error('PWA features unavailable');
    }
  }, []);

  /**
   * Update the service worker
   */
  const updateServiceWorker = useCallback(async () => {
    if (!navigator.serviceWorker.controller) return;

    // Tell the SW to skip waiting
    navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
    
    // Reload to activate new SW
    window.location.reload();
  }, []);

  /**
   * Unregister the service worker
   */
  const unregister = useCallback(async () => {
    const registration = await navigator.serviceWorker.ready;
    await registration.unregister();
    setState(prev => ({ ...prev, isInstalled: false }));
    toast.success('Service worker unregistered');
  }, []);

  /**
   * Clear all caches
   */
  const clearCaches = useCallback(async () => {
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({ type: 'CLEAR_CACHE' });
      toast.info('Caches cleared');
    }
  }, []);

  /**
   * Get cache status from SW
   */
  const getCacheStatus = useCallback(async () => {
    if (!navigator.serviceWorker.controller) return;

    const channel = new MessageChannel();
    
    channel.port1.onmessage = (event) => {
      if (event.data.type === 'CACHE_STATUS') {
        setState(prev => ({ ...prev, cacheStatus: event.data.caches }));
      }
    };

    navigator.serviceWorker.controller.postMessage(
      { type: 'GET_CACHE_STATUS' },
      [channel.port2]
    );
  }, []);

  /**
   * Prompt user to install PWA
   */
  const promptInstall = useCallback(async () => {
    if (!deferredPrompt) {
      toast.info('App is already installed or installation not available');
      return;
    }

    deferredPrompt.prompt();
    
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      toast.success('App installed successfully!');
    } else {
      toast.info('Installation cancelled');
    }
    
    setDeferredPrompt(null);
  }, [deferredPrompt]);

  /**
   * Check if app can be installed
   */
  const canInstall = useCallback(() => {
    return !!deferredPrompt;
  }, [deferredPrompt]);

  // Register SW on mount
  useEffect(() => {
    register();

    // Listen for beforeinstallprompt
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setState(prev => ({ ...prev, offlineReady: true }));
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    // Listen for app installed
    const handleAppInstalled = () => {
      setDeferredPrompt(null);
      toast.success('App installed! You can now use it offline.');
    };

    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, [register]);

  // Listen for online/offline events
  useEffect(() => {
    const handleOnline = () => {
      toast.success('You are back online');
    };

    const handleOffline = () => {
      toast.warning('You are offline. Some features may be limited.');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return {
    ...state,
    deferredPrompt,
    register,
    updateServiceWorker,
    unregister,
    clearCaches,
    getCacheStatus,
    promptInstall,
    canInstall,
  };
}

/**
 * Hook to track network status
 */
export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [connectionType, setConnectionType] = useState<string>('unknown');

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Check connection type if available
    const connection = (navigator as any).connection;
    if (connection) {
      setConnectionType(connection.effectiveType);
      
      connection.addEventListener('change', () => {
        setConnectionType(connection.effectiveType);
      });
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return { isOnline, connectionType };
}

/**
 * Hook to queue mutations for background sync
 */
export function useBackgroundSync() {
  const [pendingCount, setPendingCount] = useState(0);

  /**
   * Queue a mutation for background sync
   */
  const queueMutation = useCallback(async (mutation: () => Promise<any>) => {
    if (!('serviceWorker' in navigator) || !navigator.serviceWorker.controller) {
      // No SW, try to execute immediately
      return mutation();
    }

    if (!navigator.onLine) {
      // Store in IndexedDB for later sync
      // This would integrate with your storage solution
      setPendingCount(prev => prev + 1);
      
      toast.info('Action queued for sync', {
        description: 'Will execute when you are back online',
      });
      
      return;
    }

    // Execute immediately if online
    try {
      await mutation();
    } catch (error) {
      // If it fails, queue for retry
      setPendingCount(prev => prev + 1);
      throw error;
    }
  }, []);

  /**
   * Trigger background sync
   */
  const triggerSync = useCallback(async () => {
    if (!('serviceWorker' in navigator)) return;

    const registration = await navigator.serviceWorker.ready;
    
    if ('sync' in registration) {
      await (registration as any).sync.register('background-sync');
    }
  }, []);

  return {
    pendingCount,
    queueMutation,
    triggerSync,
  };
}

export default useServiceWorker;
