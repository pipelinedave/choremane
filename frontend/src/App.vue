<template>
  <div id="app">
    <ErrorBoundary>
      <Header @addChore="handleAddChore" />
      <!-- Removed duplicate ChoreList component -->
      <router-view></router-view>
      <Log />
      <CopilotButton />
      <VersionChecker />
    </ErrorBoundary>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from '@/plugins/axios'
import Header from '@/components/Header.vue'
import ChoreList from '@/components/ChoreList.vue'
import { useChoreStore } from '@/store/choreStore'
import Log from '@/components/Log.vue'
import CopilotButton from '@/components/CopilotButton.vue'
import ErrorBoundary from '@/components/ErrorBoundary.vue'
import VersionChecker from '@/components/VersionChecker.vue'

const versionInfo = ref(null)
const choreStore = useChoreStore()
const isVersionMismatch = ref(false)

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
        
        // Show user a message about clearing storage
        const confirmReset = confirm(
          'A new version of the application has been detected. ' +
          'To prevent errors, would you like to clear application data? ' +
          '(Your login information will be preserved)'
        );
        
        if (confirmReset) {
          await resetLocalStorage();
          // Reload the page to ensure a clean state
          window.location.reload();
        }
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
  try {
    const response = await axios.get('/version')
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
    await choreStore.addChore(newChore)
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
