/**
 * Service Worker for CryptoVault
 * Handles caching, offline support, and background sync
 */

const CACHE_NAME = 'cryptovault-v1';
const API_CACHE_NAME = 'cryptovault-api-v1';
const CRITICAL_ASSETS = [
  '/',
  '/index.html',
  '/logo.svg',
  '/favicon.svg'
];

const CACHE_DURATION = {
  api: 5 * 60 * 1000, // 5 minutes for API
  static: 24 * 60 * 60 * 1000, // 1 day for static
};

// Install event - cache critical assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Caching critical assets:', CRITICAL_ASSETS);
      return cache.addAll(CRITICAL_ASSETS);
    }).catch((error) => {
      console.error('[SW] Cache install failed:', error);
    })
  );
  
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');
  
  event.waitUntil(
    caches.keys().then((names) => {
      return Promise.all(
        names
          .filter((name) => name !== CACHE_NAME && name !== API_CACHE_NAME)
          .map((name) => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    })
  );
  
  self.clients.claim();
});

// Fetch event - network-first for API, cache-first for static
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }
  
  // Skip external APIs and non-origin requests
  if (url.origin !== self.location.origin) {
    return;
  }

  // API requests: network-first, cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstStrategy(event.request, API_CACHE_NAME));
  }
  // Static assets: cache-first, network fallback
  else {
    event.respondWith(cacheFirstStrategy(event.request, CACHE_NAME));
  }
});

/**
 * Network-first strategy: Try network, fallback to cache
 */
async function networkFirstStrategy(request, cacheName) {
  try {
    const response = await fetch(request);
    
    // Cache successful responses
    if (response && response.status === 200) {
      const cacheResponse = response.clone();
      const cache = await caches.open(cacheName);
      cache.put(request, cacheResponse);
    }
    
    return response;
  } catch (error) {
    console.warn('[SW] Network request failed, checking cache:', error);
    
    // Return cached response if available
    const cached = await caches.match(request);
    if (cached) {
      console.log('[SW] Returning cached response');
      return cached;
    }
    
    // Return offline response
    return new Response(
      JSON.stringify({
        error: 'Offline',
        message: 'You are offline. Please check your connection.',
        cached: false
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

/**
 * Cache-first strategy: Check cache first, then network
 */
async function cacheFirstStrategy(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) {
    // Update cache in background (stale-while-revalidate)
    fetch(request)
      .then((response) => {
        if (response && response.status === 200) {
          const cache = caches.open(cacheName);
          cache.then((c) => c.put(request, response));
        }
      })
      .catch(() => { /* Ignore network errors */ });
    
    return cached;
  }

  try {
    const response = await fetch(request);
    if (response && response.status === 200) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.warn('[SW] Failed to fetch:', request.url, error);
    return new Response('Resource not available offline', { status: 503 });
  }
}

// Message handler for cache management
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.keys().then((names) => {
      names.forEach((name) => caches.delete(name));
      console.log('[SW] Cache cleared');
    });
  }
});

// Background sync for mutations (offline mutations)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-mutations') {
    event.waitUntil(syncPendingMutations());
  }
});

async function syncPendingMutations() {
  try {
    // This would require storing pending mutations in IndexedDB
    // Implementation depends on your mutation strategy
    console.log('[SW] Syncing pending mutations...');
  } catch (error) {
    console.error('[SW] Sync failed:', error);
  }
}

console.log('[SW] Service Worker script loaded');
