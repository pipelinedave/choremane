<template>
  <header>
    <div class="header-content">
      <h1>CHOREMANE</h1>
      <div class="header-buttons">
        <button @click="toggleAddMode" class="add-button" aria-label="Add new chore" title="Add new chore">
          <i class="fas fa-plus"></i>
        </button>
        <button
          v-if="showInstallButton"
          @click="installPWA"
          class="install-button"
          aria-label="Install app"
          title="Install app"
        >
          <i class="fas fa-download"></i>
        </button>
        <button @click="toggleAboutModal" aria-label="About" title="About">
          <i class="fas fa-info-circle"></i>
        </button>
        <button @click="toggleNotifications" aria-label="Notification settings" title="Notifications">
          <i class="fas fa-bell"></i>
        </button>
        <button @click="toggleImportExport" aria-label="Import or export data" title="Import/Export">
          <i class="fas fa-exchange-alt"></i>
        </button>
      </div>
    </div>
    <AddChoreForm v-if="addMode" @addChore="handleAddChore" @cancel="toggleAddMode" />
    <NotificationSettings v-if="showNotifications" @close="toggleNotifications" />
    <ImportExport v-if="showImportExport" @close="toggleImportExport" />
    
    <!-- About Modal Dialog -->
    <div v-if="showAboutModal && versionInfo" class="modal-overlay" @click.self="toggleAboutModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>About ChoreMane</h2>
          <button class="close-button" @click="toggleAboutModal" aria-label="Close dialog">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="about-info">
            <div class="info-item">
              <h3>Version</h3>
              <a :href="versionTagLink" target="_blank" rel="noopener noreferrer" class="version-link">
                <i class="fab fa-github"></i> {{ versionInfo.version_tag }}
              </a>
            </div>
            <div class="info-item">
              <h3>Backend Image</h3>
              <a :href="backendImageLink" target="_blank" rel="noopener noreferrer" class="version-link">
                <i class="fab fa-docker"></i> {{ versionInfo.backend_image }}
              </a>
            </div>
            <div class="info-item">
              <h3>Frontend Image</h3>
              <a :href="frontendImageLink" target="_blank" rel="noopener noreferrer" class="version-link">
                <i class="fab fa-docker"></i> {{ versionInfo.frontend_image }}
              </a>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="primary-button" @click="toggleAboutModal">Close</button>
        </div>
      </div>
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
const showAboutModal = ref(false)
const versionInfo = ref(null)

const toggleBanner = () => {
  showBanner.value = !showBanner.value
}

const toggleAboutModal = () => {
  showAboutModal.value = !showAboutModal.value
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

.header-buttons button:hover {
  background: var(--color-surface-lighter);
}

.header-buttons i {
  font-size: 1rem;
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
    border-radius: var(--radius-sm);
    padding: var(--space-xs);
    min-width: 32px;
    width: auto;
    flex: 1;
    margin: 0 0.1rem;
  }
  
  .header-buttons i {
    font-size: 0.9rem;
  }
}

.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  backdrop-filter: blur(2px);
}

.modal-content {
  background: var(--color-surface);
  color: var(--color-text);
  border-radius: var(--radius-md);
  min-width: 280px;
  width: 100%;
  max-width: 500px;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  background: var(--color-surface-light);
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--color-surface-lighter);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.close-button {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0.25rem;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color var(--transition-fast), color var(--transition-fast);
}

.close-button:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--color-text);
  transform: none;
}

.modal-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.modal-footer {
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid var(--color-surface-lighter);
  gap: 0.75rem;
}

.primary-button {
  background: var(--color-primary);
  color: white;
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-sm);
  border: none;
  cursor: pointer;
  font-weight: 600;
}

.primary-button:hover {
  background: var(--color-primary-hover);
  transform: none;
}

.about-info {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.info-item {
  background: var(--color-surface-light);
  padding: 1rem;
  border-radius: var(--radius-sm);
}

.info-item h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  color: var(--color-text-muted);
}

.version-link {
  color: var(--color-primary);
  text-decoration: none;
  transition: color var(--transition-fast);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.version-link:hover {
  color: var(--color-primary-hover);
  text-decoration: underline;
}

@media (max-width: 576px) {
  .modal-content {
    max-width: 95%;
  }
  
  .modal-header, .modal-body, .modal-footer {
    padding: 1rem;
  }
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
