<template>
  <div id="app">
    <ErrorBoundary>
      <!-- Only show Header and LogOverlay when authenticated -->
      <template v-if="isAuthenticated">
        <Header @addChore="handleAddChore" />
        <LogOverlay />
      </template>
      <router-view></router-view>
      <VersionChecker />
    </ErrorBoundary>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from '@/plugins/axios'
import api from '@/plugins/axios'
import Header from '@/components/Header.vue'
import ChoreList from '@/components/ChoreList.vue'
import { useChoreStore } from '@/store/choreStore'
// Commented out AI assistant import
// import CopilotButton from '@/components/CopilotButton.vue'
import ErrorBoundary from '@/components/ErrorBoundary.vue'
import VersionChecker from '@/components/VersionChecker.vue'
import LogOverlay from '@/components/LogOverlay.vue'
import { useAuthStore } from '@/store/authStore'

const versionInfo = ref(null)
const choreStore = useChoreStore()
const authStore = useAuthStore()
const isVersionMismatch = ref(false)

// Computed property to check if user is authenticated
const isAuthenticated = computed(() => authStore.isAuthenticated)

// Function to check if localStorage needs to be cleared
async function checkVersionConsistency() {
  try {
    const storedVersionInfo = localStorage.getItem('appVersionInfo');

    if (versionInfo.value && storedVersionInfo) {
      const parsedStoredVersion = JSON.parse(storedVersionInfo);

      // If the backend or frontend image has changed, we may need to reset storage
      if (parsedStoredVersion.backend_image !== versionInfo.value.backend_image ||
        parsedStoredVersion.frontend_image !== versionInfo.value.frontend_image) {

        console.log('Version mismatch detected:', {
          stored: parsedStoredVersion,
          current: versionInfo.value
        });

        isVersionMismatch.value = true;

        // Dispatch custom event instead of showing blocking dialog
        window.dispatchEvent(new CustomEvent('choremane:data-migration-needed', {
          detail: {
            fromVersion: parsedStoredVersion,
            toVersion: versionInfo.value
          }
        }));
      }
    }

    // Store current version info for future comparisons
    if (versionInfo.value) {
      localStorage.setItem('appVersionInfo', JSON.stringify(versionInfo.value));
    }
  } catch (error) {
    console.error('Error checking version consistency:', error);
  }
}

// Reset local storage but preserve authentication
async function resetLocalStorage() {
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
}

onMounted(async () => {
  // Add event listener for the showAddChoreForm event
  window.addEventListener('showAddChoreForm', () => {
    // Trigger the add chore form by calling the header's button action
    handleAddChore();
  });

  // Check if we need to clean up version data to fix persistent notification issues
  const persistentVersionFix = async () => {
    try {
      // Count how many times the app has been loaded with the same version
      const versionLoadCount = localStorage.getItem('version_load_count') || '0';
      const currentCount = parseInt(versionLoadCount, 10) + 1;
      localStorage.setItem('version_load_count', currentCount.toString());

      // If the app has been loaded more than 3 times and we still have a version issue
      if (currentCount > 3 && localStorage.getItem('version_cleanup_performed') !== 'true') {
        // Perform an automatic cleanup
        console.log('Performing automatic version data cleanup after multiple loads');
        const keysToRemove = [
          'choremane_current_version',
          'choremane_dismissed_update',
          'VERSION_STORAGE_KEY',
          'DISMISS_UNTIL_NEXT_VERSION_KEY',
          'appVersionInfo'
        ];

        keysToRemove.forEach(key => {
          localStorage.removeItem(key);
        });

        // Mark this cleanup as performed
        localStorage.setItem('version_cleanup_performed', 'true');
      }
    } catch (error) {
      console.error('Error in persistent version fix:', error);
    }
  };

  await persistentVersionFix();

  // Continue with normal app initialization
  try {
    const response = await api.get('version')
    versionInfo.value = response.data

    // After getting version info, check consistency
    await checkVersionConsistency();
  } catch (error) {
    console.error('Failed to fetch version info:', error)
  }
})

const versionTagLink = computed(() => {
  if (!versionInfo.value) return '#'
  const tag = versionInfo.value.version_tag
  // If it starts with 'v', treat as a release tag, else link to main branch or similar
  if (tag.startsWith('v')) {
    return `https://github.com/pipelinedave/choremane/releases/tag/${tag}`
  } else {
    // Link to main branch if staging
    return `https://github.com/pipelinedave/choremane/tree/${tag}`
  }
})

const backendImageLink = computed(() => {
  if (!versionInfo.value) return '#'
  const backendRef = versionInfo.value.backend_image.split(':')[1] || 'latest'
  return `https://hub.docker.com/r/pipelinedave/choremane-backend/tags?name=${backendRef}`
})

const frontendImageLink = computed(() => {
  if (!versionInfo.value) return '#'
  const frontendRef = versionInfo.value.frontend_image.split(':')[1] || 'latest'
  return `https://hub.docker.com/r/pipelinedave/choremane-frontend/tags?name=${frontendRef}`
})

const handleAddChore = async (newChore) => {
  try {
    // If newChore is provided, add it to the store
    if (newChore) {
      await choreStore.addChore(newChore)
    } else {
      // Otherwise, we just want to show the add chore form
      // Send a custom event to the Header component to show the form
      window.dispatchEvent(new CustomEvent('showAddChoreForm:trigger'));
    }
  } catch (error) {
    console.error('Failed to add chore:', error)
  }
}
</script>

<style scoped>
#app {
  font-family: 'Roboto', Arial, sans-serif;
  color: var(--color-text);
  padding: var(--spacing-md);
}

.version-banner {
  background-color: var(--color-surface);
  color: var(--color-text);
  padding: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  text-align: center;
  border-radius: 4px;
  box-shadow: var(--shadow-sm);
}

.version-banner a {
  color: var(--color-link);
  margin: 0 var(--spacing-sm);
}

.version-banner a:hover {
  text-decoration: underline;
}
</style>

<style>
/* Global styles */
#app {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
  box-sizing: border-box;
}

@media (max-width: 576px) {
  #app {
    padding: 0.5rem;
  }
}
</style>
