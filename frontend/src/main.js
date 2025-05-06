// frontend/src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import './assets/shared.css'
import '@fortawesome/fontawesome-free/css/all.min.css'
import { useChoreStore } from '@/store/choreStore'

function getNotificationSettings() {
  try {
    return JSON.parse(localStorage.getItem('notificationSettings')) || { enabled: false, times: [] };
  } catch {
    return { enabled: false, times: [] };
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
app.mount('#app')

setupChoreNotificationScheduler();

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then(registration => {
        console.log('ServiceWorker registration successful')
      })
      .catch(error => {
        console.error('ServiceWorker registration failed:', error)
      })
  })
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
