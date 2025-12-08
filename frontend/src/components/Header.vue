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
        <button @click="toggleSettings" aria-label="Menu" title="Menu">
          <i class="fas fa-bars"></i>
        </button>
      </div>
    </div>
    
    <!-- Menu -->
    <div v-if="showSettings" class="settings-menu" ref="settingsMenu">
      <div class="settings-menu-item" @click="toggleArchivedChores">
        <i class="fas fa-archive"></i> Archived Chores
      </div>
      <div class="settings-menu-item" @click="toggleNotifications">
        <i class="fas fa-bell"></i> Notifications
      </div>
      <div class="settings-menu-item" @click="toggleImportExport">
        <i class="fas fa-exchange-alt"></i> Import/Export
      </div>
      <div class="settings-menu-item" @click="goToResetPage">
        <i class="fas fa-wrench"></i> Troubleshooting
      </div>
      <div class="settings-menu-item" @click="toggleAboutModal">
        <i class="fas fa-info-circle"></i> About
      </div>
    </div>
    
    <AddChoreForm v-if="addMode" @addChore="handleAddChore" @cancel="toggleAddMode" />
    <NotificationSettings v-if="showNotifications" @close="toggleNotifications" />
    <ImportExport v-if="showImportExport" @close="toggleImportExport" />
    <ArchivedChores v-if="showArchivedChores" @close="toggleArchivedChores" />
    
    <!-- About Modal Dialog -->
    <div v-if="showAboutModal && versionInfo" class="modal-overlay" role="dialog" aria-modal="true" aria-label="About Choremane" @click.self="toggleAboutModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>About Choremane</h2>
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
          <button class="neutral-button" @click="toggleAboutModal">
            <i class="fas fa-check"></i> Done
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from '@/plugins/axios'
import api from '@/plugins/axios'
import AddChoreForm from '@/components/AddChoreForm.vue'
import NotificationSettings from '@/components/NotificationSettings.vue'
import ImportExport from '@/components/ImportExport.vue'
import ArchivedChores from '@/components/ArchivedChores.vue'

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
    const response = await api.get('version')
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

// Add listener for the custom event to show add chore form
onMounted(() => {
  window.addEventListener('showAddChoreForm:trigger', () => {
    addMode.value = true;
  });
});

// Clean up event listener
onUnmounted(() => {
  window.removeEventListener('showAddChoreForm:trigger', () => {});
});

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
  showSettings.value = false
}

const showArchivedChores = ref(false)
const toggleArchivedChores = () => {
  showArchivedChores.value = !showArchivedChores.value
  showSettings.value = false
}

const showImportExport = ref(false)
const toggleImportExport = () => {
  showImportExport.value = !showImportExport.value
}

const showSettings = ref(false)
const settingsMenu = ref(null)

const closeSettingsOnClickOutside = (event) => {
  if (settingsMenu.value && !settingsMenu.value.contains(event.target) && 
      !event.target.closest('[aria-label="Menu"]')) {
    showSettings.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', closeSettingsOnClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', closeSettingsOnClickOutside)
})

const toggleSettings = (event) => {
  if (event) event.stopPropagation()
  showSettings.value = !showSettings.value
  // Close other popovers if opening settings
  if (showSettings.value) {
    showNotifications.value = false
    showImportExport.value = false
    showArchivedChores.value = false
    showAboutModal.value = false
  }
}

const goToResetPage = () => {
  // Ensure we're using the correct path that matches our ingress configuration
  const resetPath = '/reset.html';
  // Open in a new tab to avoid navigating away from the app
  window.open(window.location.origin + resetPath, '_blank');
  // Close the menu after selecting an option
  showSettings.value = false;
}
</script>

<style scoped>
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-lg);
  background: rgba(255, 255, 255, 0.65);
  border-radius: 28px;
  margin-bottom: var(--space-md);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.7);
}

.header-content h1 {
  letter-spacing: 0.08em;
  font-size: 1.6rem;
  color: var(--color-text);
}

.header-buttons {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: nowrap;
  align-items: center;
}

.header-buttons button {
  min-width: 42px;
  min-height: 42px;
  width: 42px;
  height: 42px;
  padding: var(--space-xs);
  background: rgba(255, 255, 255, 0.85);
  color: var(--color-text);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.8);
  cursor: pointer;
  font-size: 1rem;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast), background-color var(--transition-fast);
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(12px);
}

.header-buttons button:hover {
  background: rgba(255, 255, 255, 0.95);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.header-buttons button:active {
  transform: translateY(0);
}

.header-buttons i {
  font-size: 1rem;
}

/* Settings Menu Styles */
.settings-menu {
  position: absolute;
  top: 60px;
  right: 10px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 18px;
  box-shadow: var(--shadow-lg);
  z-index: 1000;
  overflow: hidden;
  width: 220px;
  animation: menuFadeIn 0.2s ease-out;
  transform-origin: top right;
}

@keyframes menuFadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.settings-menu-item {
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--color-text);
}

.settings-menu-item:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.settings-menu-item:active {
  background-color: rgba(0, 0, 0, 0.06);
}

.settings-menu-item i {
  width: 20px;
  text-align: center;
  font-size: 1rem;
  color: var(--color-text-muted);
}

/* Only apply flex-wrap at a very small screen size */
@media (max-width: 380px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-buttons {
    margin-top: var(--space-md);
    width: 100%;
    justify-content: flex-end;
  }
  
  .header-buttons button {
    margin-left: var(--space-xs);
  }

  .settings-menu {
    right: 0;
    width: 100%;
    max-width: 100%;
    border-radius: 0;
    top: 120px;
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
  border-radius: var(--radius-lg);
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
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.primary-button:hover {
  background: var(--color-primary-hover);
  transform: none;
}

.neutral-button {
  background: var(--color-surface-light);
  color: var(--color-text);
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-sm);
  border: none;
  cursor: pointer;
  font-weight: 600;
}

.neutral-button:hover {
  background: var(--color-surface-lighter);
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
</style>
