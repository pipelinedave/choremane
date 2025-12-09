<!-- Automatic version checker component -->
<template>
  <div v-if="showUpdateNotice" class="update-notice">
    <div class="update-message">
      <div class="update-info">
        <i class="fas fa-sync-alt update-icon"></i>
        <span>{{ updateMessage }}</span>
      </div>
      <div class="update-actions">
        <button @click="handlePrimaryAction" class="update-button">{{ primaryButtonText }}</button>
        <button v-if="showDismissButton" @click="dismissUpdate" class="dismiss-button">Later</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { fetchVersionInfo } from '@/utils/version';

const showUpdateNotice = ref(false);
const checkInterval = ref(null);
const currentVersion = ref(null);
const noticeType = ref('update'); // 'update' or 'dataMigration'
const updateMessage = ref('Update available');
const primaryButtonText = ref('Update');
const showDismissButton = ref(true);

// Storage keys for version tracking
const VERSION_STORAGE_KEY = 'choremane_current_version';
const DISMISS_UNTIL_NEXT_VERSION_KEY = 'choremane_dismissed_update';

// Check for app updates
const checkForUpdates = async () => {
  try {
    // Check if we're in development mode
    const isDevelopment = window.location.hostname === 'localhost' || 
                         window.location.hostname === '127.0.0.1' ||
                         window.location.hostname.includes('.local');
    
    // Skip update checks in development mode to prevent refresh loops
    if (isDevelopment) {
      console.log('Skipping version check in development mode');
      return;
    }
    
    // Check if we recently reloaded the page (within last 30 seconds)
    const lastRefresh = parseInt(sessionStorage.getItem('last_page_refresh') || '0');
    const now = Date.now();
    // If lastRefresh is 0, it means the sessionStorage key is not set yet - set it now
    if (lastRefresh === 0) {
      sessionStorage.setItem('last_page_refresh', now.toString());
      console.log('Setting initial page refresh timestamp');
      return; // Skip this check until next interval
    }
    
    const recentlyRefreshed = (now - lastRefresh) < 30000; // 30 seconds
    
    if (recentlyRefreshed) {
      console.log('Page was recently refreshed, skipping update check');
      return;
    }
    
    // Get current version info from server
    const newVersion = await fetchVersionInfo();
    
    // Get stored version info from localStorage
    let storedVersionInfo = null;
    try {
      const storedData = localStorage.getItem(VERSION_STORAGE_KEY);
      if (storedData) {
        storedVersionInfo = JSON.parse(storedData);
      }
    } catch (error) {
      console.error('Error parsing stored version info:', error);
    }
    
    // Initialize currentVersion if this is the first check
    if (!currentVersion.value) {
      currentVersion.value = storedVersionInfo || newVersion;
      
      // Store current version if not already stored
      if (!storedVersionInfo) {
        localStorage.setItem(VERSION_STORAGE_KEY, JSON.stringify(newVersion));
      }
      return;
    }
    
    // Check if version has changed
    const versionChanged = !storedVersionInfo || 
      newVersion.version_tag !== storedVersionInfo.version_tag ||
      newVersion.backend_image !== storedVersionInfo.backend_image ||
      newVersion.frontend_image !== storedVersionInfo.frontend_image;
    
    if (versionChanged) {
      console.log('New version detected:', newVersion);
      console.log('Previous version:', storedVersionInfo || 'none');
      
      // Check if user has dismissed this specific version already
      let isDismissed = false;
      try {
        const dismissedVersionStr = localStorage.getItem(DISMISS_UNTIL_NEXT_VERSION_KEY);
        if (dismissedVersionStr) {
          const dismissedVersion = JSON.parse(dismissedVersionStr);
          
          // Compare the actual objects
          isDismissed = dismissedVersion.version_tag === newVersion.version_tag &&
                        dismissedVersion.backend_image === newVersion.backend_image &&
                        dismissedVersion.frontend_image === newVersion.frontend_image;
                        
          console.log('Dismissed version check:', isDismissed, dismissedVersion);
        }
      } catch (error) {
        console.error('Error checking dismissed version:', error);
      }
      
      // Update stored version, even if we don't show the notification
      localStorage.setItem(VERSION_STORAGE_KEY, JSON.stringify(newVersion));
      
      if (!isDismissed) {
        showUpdateNotice.value = true;
      }
    }
  } catch (error) {
    console.error('Error checking for updates:', error);
  }
};

// Reload the app to apply updates
const reloadApp = async () => {
  try {
    // Get the latest version info before reloading
    const latestVersion = await fetchVersionInfo();
    
    // Update stored version to prevent showing notification again after reload
    localStorage.setItem(VERSION_STORAGE_KEY, JSON.stringify(latestVersion));
    
    // Store a flag to indicate we just performed an update
    localStorage.setItem('choremane_just_updated', 'true');
    
    // Remove any dismissed state since we're applying the update
    localStorage.removeItem(DISMISS_UNTIL_NEXT_VERSION_KEY);
  } catch (error) {
    console.error('Error updating version info before reload:', error);
  }
  
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

// Mark the current page load time in session storage
const recordPageLoadTime = () => {
  const now = Date.now();
  sessionStorage.setItem('last_page_refresh', now.toString());
  console.log('Recorded page load time:', new Date(now).toISOString());
};

// Dismiss the update notice until next version
const dismissUpdate = async () => {
  try {
    // Get current version to store as dismissed
    const currentVersion = await fetchVersionInfo();
    
    // Store the complete version object as dismissed
    const dismissedVersionJson = JSON.stringify({
      version_tag: currentVersion.version_tag,
      backend_image: currentVersion.backend_image,
      frontend_image: currentVersion.frontend_image
    });
    
    // Store this version as dismissed
    localStorage.setItem(DISMISS_UNTIL_NEXT_VERSION_KEY, dismissedVersionJson);
    
    // Also update the current version storage to match
    localStorage.setItem(VERSION_STORAGE_KEY, JSON.stringify(currentVersion));
    
    console.log('Dismissed version:', currentVersion);
    
    // Hide notification
    showUpdateNotice.value = false;
  } catch (error) {
    console.error('Error saving dismissed version:', error);
    // Still hide notification even if storing dismissed state fails
    showUpdateNotice.value = false;
  }
};

// Reset local storage but preserve authentication
const resetLocalStorage = async () => {
  // Save authentication data
  const token = localStorage.getItem('token');
  const userColor = localStorage.getItem('userColor');
  const username = localStorage.getItem('username');
  
  // Clear all localStorage except specific items we want to preserve
  const itemsToPreserve = ['choremane_storage_version', 'token', 'userColor', 'username'];
  
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (!itemsToPreserve.includes(key)) {
      localStorage.removeItem(key);
    }
  }
  
  // Restore auth data if it was present
  if (token) localStorage.setItem('token', token);
  if (userColor) localStorage.setItem('userColor', userColor);
  if (username) localStorage.setItem('username', username);
  
  console.log('Local storage has been reset (preserving auth data)');
  
  // Store current version info for future comparisons
  try {
    const currentVersionData = await fetchVersionInfo();
    localStorage.setItem('appVersionInfo', JSON.stringify(currentVersionData));
  } catch (error) {
    console.error('Error updating version info after reset:', error);
  }
};

// Handle the primary action button click
const handlePrimaryAction = async () => {
  if (noticeType.value === 'update') {
    await reloadApp();
  } else if (noticeType.value === 'dataMigration') {
    await resetLocalStorage();
    // Reload the page to ensure a clean state
    window.location.reload(true);
  }
};

onMounted(() => {
  // Record this page load time
  recordPageLoadTime();
  
  // Check if we just did an update (prevents show-on-reload behavior)
  const justUpdated = localStorage.getItem('choremane_just_updated') === 'true';
  if (justUpdated) {
    console.log('Just performed an update, skipping update check');
    localStorage.removeItem('choremane_just_updated');
    // Skip the initial check
  } else {
    // Initial check only if we didn't just update
    checkForUpdates();
  }
  
  // Set up periodic checks (every 15 minutes - increased from 5 to reduce unnecessary checks)
  checkInterval.value = setInterval(checkForUpdates, 15 * 60 * 1000);
  
  // Listen for service worker update events
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', (event) => {
      if (event.data.type === 'reload') {
        // Only show notification if user hasn't dismissed this version
        const dismissedVersion = localStorage.getItem(DISMISS_UNTIL_NEXT_VERSION_KEY);
        if (!dismissedVersion) {
          noticeType.value = 'update';
          updateMessage.value = 'Update available';
          primaryButtonText.value = 'Update';
          showDismissButton.value = true;
          showUpdateNotice.value = true;
        }
      }
    });
  }
  
  // Listen for the custom update event from main.js
  window.addEventListener('choremane:update-available', () => {
    console.log('Update available event received');
    
    // Check if we recently refreshed the page (within last 30 seconds)
    const lastRefresh = parseInt(sessionStorage.getItem('last_page_refresh') || '0');
    const now = Date.now();
    const recentlyRefreshed = (now - lastRefresh) < 30000; // 30 seconds
    
    // Update timestamp immediately to prevent update notification cascades
    sessionStorage.setItem('last_page_refresh', now.toString());
    
    if (recentlyRefreshed) {
      console.log('Page was recently refreshed, ignoring update notification');
      return;
    }
    
    // Check if this notification has already been shown recently
    const lastUpdateNotification = parseInt(sessionStorage.getItem('last_update_notification') || '0');
    const recentlyNotified = (now - lastUpdateNotification) < 60000; // 1 minute
    
    if (recentlyNotified) {
      console.log('Update notification was recently shown, ignoring duplicate');
      return;
    }
    
    // Record this notification timestamp
    sessionStorage.setItem('last_update_notification', now.toString());
    
    // Check if user has not dismissed this version before showing notification
    const dismissedVersion = localStorage.getItem(DISMISS_UNTIL_NEXT_VERSION_KEY);
    if (!dismissedVersion) {
      noticeType.value = 'update';
      updateMessage.value = 'Update available';
      primaryButtonText.value = 'Update';
      showDismissButton.value = true;
      showUpdateNotice.value = true;
    }
  });
  
  // Listen for data migration needed event
  window.addEventListener('choremane:data-migration-needed', (event) => {
    console.log('Data migration event received', event.detail);
    noticeType.value = 'dataMigration';
    updateMessage.value = 'New version detected. Data update required.';
    primaryButtonText.value = 'Update Data';
    showDismissButton.value = false; // No dismiss option for data migration
    showUpdateNotice.value = true;
  });
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
  width: 250px;
  animation: slide-in 0.3s ease-out;
  max-width: calc(100vw - 40px);
}

@keyframes slide-in {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.update-message {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.update-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.update-icon {
  animation: spin 1.5s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.update-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

button {
  padding: 4px 10px;
  border-radius: 4px;
  border: none;
  font-weight: 500;
  cursor: pointer;
  font-size: 0.85rem;
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
