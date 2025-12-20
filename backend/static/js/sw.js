/**
 * AgTools Mobile Service Worker
 * Provides offline support and caching for the mobile crew interface.
 * v2.6.0 Phase 6.6
 */

const CACHE_NAME = 'agtools-mobile-v1';
const OFFLINE_URL = '/m/offline';

// Files to cache for offline use
const STATIC_ASSETS = [
    '/static/css/mobile.css',
    '/static/js/app.js',
    '/static/manifest.json',
];

// API routes that should work offline with cached data
const CACHEABLE_API_ROUTES = [
    '/m/tasks',
];

// ============================================================================
// INSTALL EVENT
// ============================================================================

self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Caching static assets...');
                // Cache static assets and offline page
                return cache.addAll([
                    ...STATIC_ASSETS,
                    OFFLINE_URL,
                ]);
            })
            .then(() => {
                // Activate immediately
                return self.skipWaiting();
            })
    );
});

// ============================================================================
// ACTIVATE EVENT
// ============================================================================

self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');

    event.waitUntil(
        // Clean up old caches
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name !== CACHE_NAME)
                        .map((name) => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => {
                // Take control of all pages immediately
                return self.clients.claim();
            })
    );
});

// ============================================================================
// FETCH EVENT
// ============================================================================

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Skip non-GET requests (form submissions, etc.)
    if (event.request.method !== 'GET') {
        return;
    }

    // Skip cross-origin requests
    if (url.origin !== location.origin) {
        return;
    }

    // Handle static assets - cache first
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(cacheFirst(event.request));
        return;
    }

    // Handle mobile routes - network first with cache fallback
    if (url.pathname.startsWith('/m/')) {
        event.respondWith(networkFirstWithOffline(event.request));
        return;
    }
});

// ============================================================================
// CACHING STRATEGIES
// ============================================================================

/**
 * Cache-first strategy for static assets.
 * Returns cached version if available, otherwise fetches from network.
 */
async function cacheFirst(request) {
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
        return cachedResponse;
    }

    try {
        const networkResponse = await fetch(request);

        // Cache the response for future use
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.log('[SW] Fetch failed for:', request.url);
        return new Response('Offline', { status: 503 });
    }
}

/**
 * Network-first strategy with offline fallback.
 * Tries network first, falls back to cache, then offline page.
 */
async function networkFirstWithOffline(request) {
    try {
        const networkResponse = await fetch(request);

        // Cache successful HTML responses
        if (networkResponse.ok && request.headers.get('accept')?.includes('text/html')) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.log('[SW] Network request failed, checking cache:', request.url);

        // Try to return cached response
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        // Return offline page for navigation requests
        if (request.mode === 'navigate') {
            const offlineResponse = await caches.match(OFFLINE_URL);
            if (offlineResponse) {
                return offlineResponse;
            }
        }

        return new Response('Offline', { status: 503 });
    }
}

// ============================================================================
// MESSAGE HANDLING
// ============================================================================

self.addEventListener('message', (event) => {
    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data.type === 'CLEAR_CACHE') {
        caches.delete(CACHE_NAME)
            .then(() => {
                console.log('[SW] Cache cleared');
            });
    }
});
