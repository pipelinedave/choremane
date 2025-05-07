// Extract version from URL query parameter if available
// If no version parameter is provided, use a fixed fallback instead of Date.now()
// to prevent triggering unnecessary updates on each refresh
self.CACHE_VERSION = new URL(self.location).searchParams.get('v') || 'base-version';

// Use a dynamic cache name with app version to ensure it changes on deployments only
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
      // Check if we're in a development environment
      const isDevelopment = self.location.hostname === 'localhost' || 
                           self.location.hostname === '127.0.0.1' ||
                           self.location.hostname.includes('.local');
      
      // Only notify clients about the update if this is a new version AND not in development
      const isVersionChange = !self.previousVersion || self.previousVersion !== self.CACHE_VERSION;
      
      if (isVersionChange && !isDevelopment) {
        console.log('Notifying clients about version change from', self.previousVersion, 'to', self.CACHE_VERSION);
        
        // Store this notification in the cache to prevent duplicate notifications
        caches.open('version-notifications').then(cache => {
          // Check if we've already notified for this version recently (within last 5 minutes)
          return cache.match('last-notification').then(response => {
            if (response) {
              return response.json().then(data => {
                const notifiedRecently = (Date.now() - data.timestamp) < 300000; // 5 minutes
                
                if (notifiedRecently && data.version === self.CACHE_VERSION) {
                  console.log('Already notified about this version recently, skipping notification');
                  return;
                }
                
                // Notification is either for a different version or was sent long ago
                sendNotification();
              });
            } else {
              // No recent notification found
              sendNotification();
            }
          });
        });
        
        function sendNotification() {
          // Store this notification timestamp
          caches.open('version-notifications').then(cache => {
            cache.put('last-notification', new Response(JSON.stringify({
              version: self.CACHE_VERSION,
              timestamp: Date.now()
            })));
          });
          
          clients.forEach(client => {
            client.postMessage({ 
              type: 'reload',
              version: self.CACHE_VERSION
            });
          });
        }
      }
      
      // Track the current version to detect future changes
      self.previousVersion = self.CACHE_VERSION;
    })
  );
});
