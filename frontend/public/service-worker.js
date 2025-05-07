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
      
      // Special fix for refresh loop issue: always skip the first activation notification
      // This prevents the page from refreshing in an infinite loop
      if (clients.length > 0) {
        caches.open('version-info').then(cache => {
          cache.match('previous-version').then(response => {
            if (!response) {
              // First activation - store version but don't notify
              cache.put('previous-version', new Response(self.CACHE_VERSION));
              console.log('First service worker activation - storing version without notification');
              return;
            }
            
            // Get the stored version
            response.text().then(previousVersion => {
              // If version changed and not in development, notify
              if (previousVersion !== self.CACHE_VERSION && !isDevelopment) {
                // Check if we recently notified (within 30 seconds)
                caches.open('version-notifications').then(notifCache => {
                  notifCache.match('last-notification').then(notifResponse => {
                    let shouldNotify = true;
                    
                    if (notifResponse) {
                      notifResponse.json().then(data => {
                        const notifiedRecently = (Date.now() - data.timestamp) < 30000; // 30 seconds
                        
                        if (notifiedRecently) {
                          console.log('Already notified recently, skipping to prevent refresh loop');
                          shouldNotify = false;
                        } else {
                          // Only notify about the new version
                          sendNotificationToClients(clients);
                        }
                      });
                    } else {
                      // No recent notification, safe to notify
                      sendNotificationToClients(clients);
                    }
                  });
                });
              } else {
                console.log('Version unchanged or in development, not notifying');
              }
              
              // Always update the stored version
              cache.put('previous-version', new Response(self.CACHE_VERSION));
            });
          });
        });
      }
    })
  );
});

// Helper function to send notifications to clients
function sendNotificationToClients(clients) {
  console.log('Notifying clients about new version:', self.CACHE_VERSION);
  
  // Record notification time to prevent refresh loops
  caches.open('version-notifications').then(cache => {
    cache.put('last-notification', new Response(JSON.stringify({
      version: self.CACHE_VERSION,
      timestamp: Date.now()
    })));
  });
  
  // Notify all clients
  clients.forEach(client => {
    client.postMessage({ 
      type: 'reload',
      version: self.CACHE_VERSION
    });
  });
}
