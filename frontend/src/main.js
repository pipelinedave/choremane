// frontend/src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import './assets/shared.css'
import '@fortawesome/fontawesome-free/css/all.min.css'
import { useChoreStore } from '@/store/choreStore'
import axios from '@/plugins/axios'

// Add version check to handle data migrations on app updates
const APP_VERSION = '1.0.0'; // Update this when making breaking changes to storage
const STORAGE_VERSION_KEY = 'choremane_storage_version';

// Checks if local storage version matches current app version and performs migration if needed
async function verifyStorageVersion() {
  const storedVersion = localStorage.getItem(STORAGE_VERSION_KEY);
  
  if (storedVersion !== APP_VERSION) {
    console.log(`Storage version mismatch: ${storedVersion} vs ${APP_VERSION}`);
    
    try {
      // Fetch version info from backend to confirm redeployment
      const versionResponse = await axios.get('/version');
      console.log('Backend version info:', versionResponse.data);
      
      // Perform migration based on version changes
      await migrateStorage(storedVersion, APP_VERSION);
      
      // Update stored version
      localStorage.setItem(STORAGE_VERSION_KEY, APP_VERSION);
    } catch (error) {
      console.error('Error during version check:', error);
    }
  }
}

// Handle data migrations between versions
async function migrateStorage(fromVersion, toVersion) {
  console.log(`Migrating storage from ${fromVersion || 'initial'} to ${toVersion}`);
  
  // If this is a fresh install (no version)
  if (!fromVersion) {
    // No migration needed, just initialize
    return;
  }
  
  // Add specific migrations based on version changes
  // For example:
  // if (fromVersion === '0.9.0' && toVersion === '1.0.0') {
  //   migrateFrom0_9To1_0();
  // }
  
  // For now, we'll implement a simple reset of problematic stores
  // This is safer than keeping potentially incompatible data
  resetProblematicStores();
}

// Reset stores that might cause issues after redeployment
function resetProblematicStores() {
  // Keep user authentication if possible
  const token = localStorage.getItem('token');
  const userColor = localStorage.getItem('userColor');
  const username = localStorage.getItem('username');
  
  // Reset log entries which might have incompatible structure
  localStorage.removeItem('logEntries');
  
  // Restore authentication data if it existed
  if (token) localStorage.setItem('token', token);
  if (userColor) localStorage.setItem('userColor', userColor);
  if (username) localStorage.setItem('username', username);
}

function getNotificationSettings() {
  try {
    const settings = JSON.parse(localStorage.getItem('notificationSettings'));
    if (!settings) return { enabled: false, times: [] };
    
    // Ensure times is always an array
    if (!settings.times || !Array.isArray(settings.times)) {
      settings.times = [];
    }
    
    // Validate structure of notification settings
    if (typeof settings.enabled !== 'boolean') {
      settings.enabled = false;
    }
    
    // Make sure time strings are in proper format (HH:MM)
    settings.times = settings.times.filter(time => {
      return typeof time === 'string' && /^([01]\d|2[0-3]):([0-5]\d)$/.test(time);
    });
    
    // Update storage with validated settings to fix any inconsistencies
    localStorage.setItem('notificationSettings', JSON.stringify(settings));
    
    return settings;
  } catch (error) {
    console.error('Error parsing notification settings:', error);
    // Reset to default state
    const defaultSettings = { enabled: false, times: [] };
    localStorage.setItem('notificationSettings', JSON.stringify(defaultSettings));
    return defaultSettings;
  }
}

function shouldNotifyNow(times) {
  const now = new Date();
  const nowStr = now.toTimeString().slice(0,5); // 'HH:MM'
  return times.includes(nowStr);
}

function showChoreNotifications(chores) {
  const dueChores = chores.filter(c => {
    const dueDate = new Date(c.due_date);
    const today = new Date();
    today.setHours(0,0,0,0);
    dueDate.setHours(0,0,0,0);
    return dueDate <= today && !c.done && !c.archived;
  });
  if (dueChores.length > 0) {
    const body = dueChores.map(c => c.name).join(', ');
    new Notification('Chores Due', { body });
  }
}

// Prevent duplicate notifications per day
let lastNotifiedDate = null;

function setupChoreNotificationScheduler() {
  if (!('Notification' in window)) return;
  setInterval(async () => {
    const settings = getNotificationSettings();
    if (!settings.enabled || !settings.times.length) return;
    if (Notification.permission !== 'granted') return;
    const now = new Date();
    const todayStr = now.toISOString().slice(0,10);
    if (lastNotifiedDate === todayStr) return;
    if (shouldNotifyNow(settings.times)) {
      const choreStore = useChoreStore();
      await choreStore.fetchChores();
      showChoreNotifications(choreStore.chores);
      lastNotifiedDate = todayStr;
    }
  }, 60000); // check every minute
}

const app = createApp(App)
app.use(router)
app.use(createPinia())

// Verify storage version before mounting the app
verifyStorageVersion().then(() => {
  app.mount('#app')
  setupChoreNotificationScheduler();
}).catch(error => {
  console.error('Failed to verify storage version:', error);
  // Mount app anyway, but there might be issues
  app.mount('#app')
  setupChoreNotificationScheduler();
});

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    // Pass the APP_VERSION to the service worker to ensure cache busting on updates
    const swUrl = `/service-worker.js?v=${APP_VERSION}`;
    navigator.serviceWorker.register(swUrl)
      .then(registration => {
        console.log('ServiceWorker registration successful')
        
        // Add update checking
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New service worker is installed but waiting to activate
              console.log('New version available! Reload to update.');
              
              // Optionally show a notification to the user
              if (confirm('A new version of Choremane is available. Reload to update?')) {
                window.location.reload();
              }
            }
          });
        });
      })
      .catch(error => {
        console.error('ServiceWorker registration failed:', error)
      })
  })
  
  // Listen for service worker messages
  navigator.serviceWorker.addEventListener('message', (event) => {
    if (event.data.type === 'reload') {
      console.log('Service worker requested reload');
      window.location.reload();
    }
  });
}

// Add meta theme-color for PWA (using CSS variable for consistency)
const metaThemeColor = document.createElement('meta')
metaThemeColor.name = 'theme-color'
metaThemeColor.content = getComputedStyle(document.documentElement).getPropertyValue('--color-background').trim() // dynamically use CSS variable
document.head.appendChild(metaThemeColor)

let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  // Prevent the mini-infobar from appearing on mobile
  e.preventDefault();
  // Stash the event so it can be triggered later.
  deferredPrompt = e;
  // Update UI notify the user they can install the PWA
  const installButton = document.getElementById('install-button');
  if (installButton) {
    installButton.style.display = 'block';
    installButton.addEventListener('click', () => {
      // Show the install prompt
      deferredPrompt.prompt();
      // Wait for the user to respond to the prompt
      deferredPrompt.userChoice.then((choiceResult) => {
        if (choiceResult.outcome === 'accepted') {
          console.log('User accepted the install prompt');
        } else {
          console.log('User dismissed the install prompt');
        }
        deferredPrompt = null;
      });
    });
  }
});

window.addEventListener('appinstalled', () => {
  console.log('PWA was installed');
});

// Verify storage version on startup
verifyStorageVersion();
