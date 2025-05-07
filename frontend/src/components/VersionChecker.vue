// Automatic version checker component
<template>
  <div v-if="showUpdateNotice" class="update-notice">
    <div class="update-message">
      <span>A new version is available!</span>
      <div class="update-actions">
        <button @click="reloadApp" class="update-button">Update Now</button>
        <button @click="dismissUpdate" class="dismiss-button">Later</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import axios from '@/plugins/axios';

const showUpdateNotice = ref(false);
const checkInterval = ref(null);
const currentVersion = ref(null);

// Check for app updates
const checkForUpdates = async () => {
  try {
    // Get current version info from server
    const response = await axios.get('/version');
    const newVersion = response.data;
    
    // If this is our first check, just store the version
    if (!currentVersion.value) {
      currentVersion.value = newVersion;
      return;
    }
    
    // Check if version has changed
    if (newVersion.version_tag !== currentVersion.value.version_tag ||
        newVersion.backend_image !== currentVersion.value.backend_image ||
        newVersion.frontend_image !== currentVersion.value.frontend_image) {
      
      console.log('New version detected:', newVersion);
      showUpdateNotice.value = true;
    }
  } catch (error) {
    console.error('Error checking for updates:', error);
  }
};

// Reload the app to apply updates
const reloadApp = () => {
  // Clear caches before reloading
  if ('caches' in window) {
    caches.keys().then(cacheNames => {
      cacheNames.forEach(cacheName => {
        caches.delete(cacheName);
      });
    });
  }
  
  // Force reload from server, not from cache
  window.location.reload(true);
};

// Dismiss the update notice
const dismissUpdate = () => {
  showUpdateNotice.value = false;
};

onMounted(() => {
  // Initial check
  checkForUpdates();
  
  // Set up periodic checks (every 5 minutes)
  checkInterval.value = setInterval(checkForUpdates, 5 * 60 * 1000);
  
  // Listen for service worker update events
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', (event) => {
      if (event.data.type === 'reload') {
        showUpdateNotice.value = true;
      }
    });
  }
});

onUnmounted(() => {
  // Clean up interval on component unmount
  if (checkInterval.value) {
    clearInterval(checkInterval.value);
  }
});
</script>

<style scoped>
.update-notice {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
  background-color: var(--color-primary);
  color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  padding: 0;
  overflow: hidden;
  width: 300px;
  animation: slide-in 0.3s ease-out;
}

@keyframes slide-in {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.update-message {
  padding: 12px 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.update-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

button {
  padding: 6px 12px;
  border-radius: 4px;
  border: none;
  font-weight: 500;
  cursor: pointer;
}

.update-button {
  background-color: white;
  color: var(--color-primary);
}

.dismiss-button {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}
</style>
