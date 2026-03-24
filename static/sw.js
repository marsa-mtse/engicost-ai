/**
 * EngiCost AI - Service Worker v7
 * Strategy: Cache-First for static assets, Network-First for dynamic requests.
 * Falls back to offline page if navigation request fails.
 */

const CACHE_NAME = 'engicost-v7';
const STATIC_CACHE = 'engicost-static-v7';
const OFFLINE_URL = './offline.html';

// Core static assets to cache immediately on install
const STATIC_ASSETS = [
  './',
  './offline.html',
  './static/manifest.json',
];

// Optional assets - cached individually, failures won't block install
const OPTIONAL_ASSETS = [
  './assets/logo.png',
  './assets/icon-192.png',
  './assets/icon-512.png',
  './static/stlite.css',
];

// Large assets - cached with lower priority (background)
const LARGE_ASSETS = [
  './static/stlite.js',
];

// ── INSTALL ─────────────────────────────────────────────────────────────────
self.addEventListener('install', (event) => {
  console.log('[SW v7] Installing...');
  self.skipWaiting(); // Activate immediately
  event.waitUntil(
    caches.open(STATIC_CACHE).then(async (cache) => {
      // Cache core assets (must succeed)
      try {
        await cache.addAll(STATIC_ASSETS);
        console.log('[SW] Core assets cached.');
      } catch (err) {
        console.warn('[SW] Core cache partial failure:', err);
      }

      // Cache optional assets (failures are non-fatal)
      await Promise.all(
        OPTIONAL_ASSETS.map(url =>
          cache.add(url).catch(err =>
            console.warn(`[SW] Optional asset failed: ${url}`, err)
          )
        )
      );

      // Cache large assets in background without blocking install
      Promise.all(
        LARGE_ASSETS.map(url =>
          cache.add(url).catch(err =>
            console.warn(`[SW] Large asset cache failed: ${url}`, err)
          )
        )
      ).then(() => console.log('[SW] Large assets cached successfully.'));
    })
  );
});

// ── ACTIVATE ─────────────────────────────────────────────────────────────────
self.addEventListener('activate', (event) => {
  console.log('[SW v7] Activating — clearing old caches...');
  event.waitUntil(
    Promise.all([
      clients.claim(), // Take control of all pages immediately
      caches.keys().then((keys) =>
        Promise.all(
          keys
            .filter(key => key !== STATIC_CACHE && key !== CACHE_NAME)
            .map(key => {
              console.log('[SW] Deleting old cache:', key);
              return caches.delete(key);
            })
        )
      )
    ])
  );
});

// ── FETCH ─────────────────────────────────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and cross-origin requests (except Pollinations API for renders)
  if (request.method !== 'GET') {
    return;
  }

  // Skip cross-origin requests (let them go through normally)
  if (!url.origin.includes(self.location.origin)) {
    return;
  }

  // For navigation requests (HTML pages): Network-First, fallback to offline page
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then(response => {
          // Cache a fresh copy of the page
          const cloned = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, cloned));
          return response;
        })
        .catch(() =>
          caches.match(request).then(cached =>
            cached || caches.match(OFFLINE_URL)
          )
        )
    );
    return;
  }

  // For static assets: Cache-First, fallback to network, cache result
  event.respondWith(
    caches.match(request).then(cached => {
      if (cached) return cached;
      return fetch(request).then(response => {
        if (response && response.status === 200 && response.type === 'basic') {
          const cloned = response.clone();
          caches.open(STATIC_CACHE).then(cache => cache.put(request, cloned));
        }
        return response;
      }).catch(() => {
        console.warn('[SW] Fetch failed for:', request.url);
        return null;
      });
    })
  );
});

// ── BACKGROUND SYNC (for offline actions) ────────────────────────────────────
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-data') {
    console.log('[SW] Background sync triggered.');
  }
});

// ── PUSH NOTIFICATIONS ────────────────────────────────────────────────────────
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    self.registration.showNotification(data.title || 'EngiCost AI', {
      body: data.body || 'إشعار جديد من المنصة',
      icon: './assets/icon-192.png',
      badge: './assets/icon-192.png',
    });
  }
});
