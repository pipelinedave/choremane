﻿<template>
  <header>
    <div class="header-content">
      <h1>CHOREMANE</h1>
      <div class="header-buttons">
        <button @click="toggleAddMode" class="add-button">+</button>
        <button
          v-if="showInstallButton"
          @click="installPWA"
          class="install-button"
        >
          Install App
        </button>
        <button @click="toggleBanner">About</button>
      </div>
    </div>
    <AddChoreForm v-if="addMode" @addChore="handleAddChore" @cancel="toggleAddMode" />
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
}

.header-buttons {
  display: flex;
  gap: var(--space-sm);
}

.header-buttons button {
  composes: btn from global;
  min-width: 36px;
  min-height: 36px;
  padding: var(--space-xs);
  background: var(--color-surface-light);
  color: var(--color-text);
  border-radius: 50%;
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
}

.version-banner a {
  color: var(--color-primary);
  margin: 0 var(--space-xs);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.version-banner a:hover {
  color: var(--color-primary-hover);
}
</style>
