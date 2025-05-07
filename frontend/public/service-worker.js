// Extract version from URL query parameter if available
self.CACHE_VERSION = new URL(self.location).searchParams.get('v') || Date.now();

// Use a dynamic cache name with app version to ensure it changes on each deployment
const CACHE_NAME = 'choremane-cache-' + self.CACHE_VERSION;

self.addEventListener('install', (event) => {
  self.skipWaiting(); // force waiting SW to become active
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll([
        '/',
        '/index.html',
        '/manifest.json'
      ]);
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});

self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          // Delete any cache that doesn't match our current cache name
          if (!cacheWhitelist.includes(cacheName)) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
    .then(() => {
      console.log('Service worker activated with cache:', CACHE_NAME);
      return self.clients.claim();
    })
    .then(() => self.clients.matchAll({ type: 'window' }))
    .then(clients => {
      // Notify clients about the update
      clients.forEach(client => {
        client.postMessage({ 
          type: 'reload',
          version: self.CACHE_VERSION
        });
      });
    })
  );
});
