<template>
  <header>
    <div class="header-content">
      <h1>CHOREMANE</h1>
      <div class="header-buttons">
        <button @click="toggleAddMode" class="add-button" aria-label="Add new chore">+</button>
        <button
          v-if="showInstallButton"
          @click="installPWA"
          class="install-button"
          aria-label="Install app"
        >
          Install App
        </button>
        <button @click="toggleBanner" aria-label="About">About</button>
        <button @click="toggleNotifications" aria-label="Notification settings">Notifications</button>
        <button @click="toggleImportExport" aria-label="Import or export data">Import/Export</button>
      </div>
    </div>
    <AddChoreForm v-if="addMode" @addChore="handleAddChore" @cancel="toggleAddMode" />
    <NotificationSettings v-if="showNotifications" @close="toggleNotifications" />
    <ImportExport v-if="showImportExport" @close="toggleImportExport" />
    <div v-if="showBanner && versionInfo" class="version-banner">
      <a :href="versionTagLink" target="_blank" rel="noopener noreferrer">
        {{ versionInfo.version_tag }} github ref
      </a>
      |
      <a :href="backendImageLink" target="_blank" rel="noopener noreferrer">
        {{ versionInfo.backend_image }} backend image
      </a>
      |
      <a :href="frontendImageLink" target="_blank" rel="noopener noreferrer">
        {{ versionInfo.frontend_image }} frontend image
      </a>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from '@/plugins/axios'
import AddChoreForm from '@/components/AddChoreForm.vue'
import NotificationSettings from '@/components/NotificationSettings.vue'
import ImportExport from '@/components/ImportExport.vue'

const showBanner = ref(false)
const versionInfo = ref(null)

const toggleBanner = () => {
  showBanner.value = !showBanner.value
}

onMounted(async () => {
  try {
    const response = await axios.get('/version')
    versionInfo.value = response.data
  } catch (error) {
    console.error('Failed to fetch version info:', error)
  }
})

const versionTagLink = computed(() => {
  if (!versionInfo.value) return '#'
  const tag = versionInfo.value.version_tag
  return tag.startsWith('v')
    ? `https://github.com/pipelinedave/choremane/releases/tag/${tag}`
    : `https://github.com/pipelinedave/choremane/tree/${tag}`
})

const backendImageLink = computed(() => {
  if (!versionInfo.value) return '#'
  const backendRef = (versionInfo.value.backend_image.split(':')[1] || 'latest')
  return `https://hub.docker.com/r/pipelinedave/choremane-backend/tags?name=${backendRef}`
})

const frontendImageLink = computed(() => {
  if (!versionInfo.value) return '#'
  const frontendRef = (versionInfo.value.frontend_image.split(':')[1] || 'latest')
  return `https://hub.docker.com/r/pipelinedave/choremane-frontend/tags?name=${frontendRef}`
})

const addMode = ref(false)
const toggleAddMode = () => {
  addMode.value = !addMode.value
}

const emit = defineEmits(['addChore'])
const handleAddChore = (newChore) => {
  emit('addChore', newChore)
  addMode.value = false
}

const deferredPrompt = ref(null)
const showInstallButton = ref(false)

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault()
  deferredPrompt.value = e
  showInstallButton.value = true
})

window.addEventListener('appinstalled', () => {
  deferredPrompt.value = null
  showInstallButton.value = false
})

const installPWA = async () => {
  if (!deferredPrompt.value) return

  deferredPrompt.value.prompt()
  const { outcome } = await deferredPrompt.value.userChoice

  if (outcome === 'accepted') {
    deferredPrompt.value = null
    showInstallButton.value = false
  }
}

const showNotifications = ref(false)
const toggleNotifications = () => {
  showNotifications.value = !showNotifications.value
}

const showImportExport = ref(false)
const toggleImportExport = () => {
  showImportExport.value = !showImportExport.value
}
</script>

<style scoped>
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
  flex-wrap: wrap;
}

.header-buttons {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-top: var(--space-xs);
}

.header-buttons button {
  composes: btn from global;
  min-width: 36px;
  min-height: 36px;
  padding: var(--space-xs);
  background: var(--color-surface-light);
  color: var(--color-text);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;
}

@media (max-width: 576px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-buttons {
    margin-top: var(--space-md);
    width: 100%;
    justify-content: space-between;
  }
  
  .header-buttons button:not(.add-button) {
    font-size: 0.8rem;
    white-space: nowrap;
    border-radius: var(--radius-sm);
    padding: var(--space-xs) var(--space-sm);
    min-width: unset;
    width: auto;
    flex: 1;
    margin: 0 0.1rem;
  }
}

.header-buttons button:hover {
  background: var(--color-surface-lighter);
}

.version-banner {
  background: var(--color-surface);
  color: var(--color-text-muted);
  padding: var(--space-sm);
  border-radius: var(--radius-sm);
  margin-top: var(--space-sm);
  overflow-x: auto;
  white-space: nowrap;
  scrollbar-width: thin;
  -webkit-overflow-scrolling: touch;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-xs);
}

.version-banner a {
  color: var(--color-primary);
  margin: 0 var(--space-xs);
  text-decoration: none;
  transition: color var(--transition-fast);
}

@media (max-width: 576px) {
  .version-banner {
    padding: var(--space-xs);
    flex-direction: column;
    align-items: center;
  }
  
  .version-banner a {
    display: block;
    margin: var(--space-xxs) 0;
  }
}

.version-banner a:hover {
  color: var(--color-primary-hover);
}

.link-button {
  padding: 8px 16px;
  background-color: #4299e1;
  color: white;
  border: none;
  border-radius: 4px;
  text-decoration: none;
  font-size: 14px;
  transition: background-color 0.2s;
}

.link-button:hover {
  background-color: #3182ce;
}
</style>
