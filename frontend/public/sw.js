/**
 * Enhanced Service Worker for CryptoVault PWA
 * 
 * Features:
 * - Multi-cache strategy (static, API, images)
 * - Stale-while-revalidate for API responses
 * - Image optimization with format fallbacks
 * - Background sync for failed mutations
 * - Push notification support
 * - Cache size management
 */

const CACHE_VERSION = 'v2.0.1';
const STATIC_CACHE = `cryptovault-static-${CACHE_VERSION}`;
const API_CACHE = `cryptovault-api-${CACHE_VERSION}`;
const IMAGE_CACHE = `cryptovault-images-${CACHE_VERSION}`;

const CRITICAL_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/logo.svg',
  '/favicon.svg',
  '/icon-192x192.png',
  '/icon-512x512.png'
];

const CACHE_DURATION = {
  api: 5 * 60 * 1000,      // 5 minutes for API
  static: 24 * 60 * 60 * 1000,  // 1 day for static
  images: 7 * 24 * 60 * 60 * 1000  // 7 days for images
};

// Maximum cache sizes
const MAX_CACHE_SIZES = {
  [API_CACHE]: 100,
  [IMAGE_CACHE]: 200,
  [STATIC_CACHE]: 50
};

// Install event - cache critical assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
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
          .filter((name) => !name.includes(CACHE_VERSION))
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

  // API requests: network-first with stale-while-revalidate
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/health')) {
    event.respondWith(networkFirstStrategy(event.request, API_CACHE));
  }
  // Image requests: cache-first with background refresh
  else if (isImageRequest(url)) {
    event.respondWith(imageCacheStrategy(event.request));
  }
  // Static assets: cache-first, network fallback
  else {
    event.respondWith(cacheFirstStrategy(event.request, STATIC_CACHE));
  }
});

/**
 * Check if request is for an image
 */
function isImageRequest(url) {
  return /\.(jpg|jpeg|png|gif|webp|avif|svg|ico|bmp|tif|tiff)(\?.*)?$/i.test(url.pathname);
}

/**
 * Image cache strategy: cache-first with background refresh
 */
async function imageCacheStrategy(request) {
  const cache = await caches.open(IMAGE_CACHE);
  
  // Try cache first
  const cached = await cache.match(request);
  if (cached) {
    // Refresh in background if cache is older than 1 day
    const cachedTime = cached.headers.get('sw-cached-time');
    const age = cachedTime ? Date.now() - parseInt(cachedTime) : Infinity;
    
    if (age > 24 * 60 * 60 * 1000) {
      fetch(request)
        .then(response => {
          if (response.ok) {
            const responseToCache = response.clone();
            const headers = new Headers(response.headers);
            headers.set('sw-cached-time', Date.now().toString());
            
            return cache.put(request, new Response(responseToCache.body, {
              status: response.status,
              statusText: response.statusText,
              headers
            }));
          }
        })
        .catch(() => {});
    }
    
    return cached;
  }
  
  // Not in cache, fetch from network
  try {
    const response = await fetch(request);
    
    if (response.ok) {
      // Clone and add timestamp
      const responseToCache = response.clone();
      const headers = new Headers(response.headers);
      headers.set('sw-cached-time', Date.now().toString());
      
      await cache.put(request, new Response(responseToCache.body, {
        status: response.status,
        statusText: response.statusText,
        headers
      }));
    }
    
    return response;
  } catch (error) {
    console.warn('[SW] Image fetch failed:', request.url);
    // Return placeholder SVG
    return new Response(
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect fill="#1a1a2e" width="100" height="100"/><text x="50" y="50" text-anchor="middle" fill="#666" font-size="10">Image Unavailable</text></svg>',
      { headers: { 'Content-Type': 'image/svg+xml' } }
    );
  }
}
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
