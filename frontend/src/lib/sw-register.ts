/**
 * Service Worker Registration and Management
 * Handles SW registration, updates, and user notifications
 */

interface UpdateInfo {
  newWorker: ServiceWorker;
  registration: ServiceWorkerRegistration;
}

class ServiceWorkerManager {
  private registration: ServiceWorkerRegistration | null = null;
  private updateCheckInterval: NodeJS.Timeout | null = null;
  private updateCallback: ((info: UpdateInfo) => void) | null = null;

  /**
   * Register service worker
   */
  async register(swPath = '/sw.js'): Promise<boolean> {
    if (!('serviceWorker' in navigator)) {
      console.warn('⚠️ Service Workers not supported in this browser');
      return false;
    }

    try {
      console.log('📝 Registering service worker...');
      this.registration = await navigator.serviceWorker.register(swPath, {
        scope: '/',
      });

      console.log('✅ Service Worker registered successfully');

      // Listen for updates
      this.listenForUpdates();

      // Check for updates every hour
      this.startPeriodicUpdates(60 * 60 * 1000);

      // Notify user if there's an update waiting
      this.handleControllerChange();

      return true;
    } catch (error) {
      console.error('❌ Service Worker registration failed:', error);
      return false;
    }
  }

  /**
   * Listen for service worker updates
   */
  private listenForUpdates(): void {
    if (!this.registration) return;

    this.registration.addEventListener('updatefound', () => {
      const newWorker = this.registration!.installing;

      if (!newWorker) return;

      console.log('🔄 New service worker found');

      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          // New version available - notify user
          console.log('📦 New service worker ready to activate');

          if (this.updateCallback) {
            this.updateCallback({
              newWorker,
              registration: this.registration!,
            });
          }

          // Emit event for other parts of app
          window.dispatchEvent(
            new CustomEvent('sw:update-available', {
              detail: { newWorker, registration: this.registration },
            })
          );
        }
      });
    });
  }

  /**
   * Handle service worker controller change
   */
  private handleControllerChange(): void {
    let refreshing = false;

    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (refreshing) return;

      refreshing = true;
      console.log('🔄 Service worker controller changed, reloading...');

      // Reload page to use new service worker
      window.location.reload();
    });
  }

  /**
   * Check for updates periodically
   */
  private startPeriodicUpdates(interval: number): void {
    this.updateCheckInterval = setInterval(() => {
      if (this.registration) {
        console.log('🔍 Checking for service worker updates...');
        this.registration
          .update()
          .catch((error) => console.error('Failed to check for updates:', error));
      }
    }, interval);
  }

  /**
   * Stop periodic updates
   */
  stopPeriodicUpdates(): void {
    if (this.updateCheckInterval) {
      clearInterval(this.updateCheckInterval);
      this.updateCheckInterval = null;
    }
  }

  /**
   * Skip waiting and activate new service worker
   */
  async skipWaiting(): Promise<void> {
    if (!this.registration?.waiting) {
      console.warn('No waiting service worker found');
      return;
    }

    console.log('⏭️ Telling service worker to skip waiting...');
    this.registration.waiting.postMessage({ type: 'SKIP_WAITING' });
  }

  /**
   * Clear all caches
   */
  async clearCache(): Promise<void> {
    if (!this.registration?.active) {
      console.warn('No active service worker found');
      return;
    }

    console.log('🗑️ Clearing service worker caches...');
    this.registration.active.postMessage({ type: 'CLEAR_CACHE' });

    // Also clear browser caches
    if ('caches' in window) {
      const cacheNames = await caches.keys();
      await Promise.all(cacheNames.map((name) => caches.delete(name)));
      console.log('✅ All caches cleared');
    }
  }

  /**
   * Unregister service worker
   */
  async unregister(): Promise<void> {
    if (!this.registration) return;

    try {
      const success = await this.registration.unregister();
      if (success) {
        console.log('✅ Service Worker unregistered');
        this.registration = null;
      } else {
        console.warn('Failed to unregister Service Worker');
      }
    } catch (error) {
      console.error('❌ Error unregistering Service Worker:', error);
    }
  }

  /**
   * Set callback for when update is available
   */
  onUpdateAvailable(callback: (info: UpdateInfo) => void): void {
    this.updateCallback = callback;
  }

  /**
   * Get current registration
   */
  getRegistration(): ServiceWorkerRegistration | null {
    return this.registration;
  }

  /**
   * Check if service worker is active
   */
  isActive(): boolean {
    return this.registration?.active !== undefined;
  }
}

// Singleton instance
let manager: ServiceWorkerManager | null = null;

/**
 * Get or create the service worker manager
 */
export function getSWManager(): ServiceWorkerManager {
  if (!manager) {
    manager = new ServiceWorkerManager();
  }
  return manager;
}

/**
 * Register service worker (convenience function)
 */
export async function registerServiceWorker(
  onUpdateAvailable?: (info: UpdateInfo) => void
): Promise<boolean> {
  const manager = getSWManager();

  if (onUpdateAvailable) {
    manager.onUpdateAvailable(onUpdateAvailable);
  }

  return manager.register();
}

/**
 * React hook for service worker
 */
import { useEffect, useState } from 'react';

export function useServiceWorker() {
  const [isActive, setIsActive] = useState(false);
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null);

  useEffect(() => {
    const manager = getSWManager();

    // Check if already registered
    setIsActive(manager.isActive());

    // Register if not already registered
    if (!manager.getRegistration()) {
      manager.onUpdateAvailable((info) => {
        setUpdateAvailable(true);
        setUpdateInfo(info);
        console.log('🎉 Service Worker update available');
      });

      manager.register();
    }

    // Listen for updates
    const handleUpdate = (event: Event) => {
      const customEvent = event as CustomEvent;
      setUpdateAvailable(true);
      setUpdateInfo(customEvent.detail);
    };

    window.addEventListener('sw:update-available', handleUpdate);

    return () => {
      window.removeEventListener('sw:update-available', handleUpdate);
    };
  }, []);

  const skipWaiting = async () => {
    const manager = getSWManager();
    await manager.skipWaiting();
  };

  const clearCache = async () => {
    const manager = getSWManager();
    await manager.clearCache();
    setUpdateAvailable(false);
  };

  return {
    isActive,
    updateAvailable,
    updateInfo,
    skipWaiting,
    clearCache,
  };
}

/**
 * Global update listener - shows prompt to user
 */
export function initSWUpdateHandler(): void {
  const manager = getSWManager();

  manager.onUpdateAvailable((info) => {
    console.log('🔔 New version available!');

    // You can show a toast notification here
    // For example, with react-hot-toast or your notification system
    window.dispatchEvent(
      new CustomEvent('app:update-available', {
        detail: { info },
      })
    );
  });

  registerServiceWorker().catch(console.error);
}
