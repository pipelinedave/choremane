<template>
  <header>
    <div class="header-content">
      <h1>CHOREMANE</h1>
      <div class="header-buttons">
        <button @click="toggleAddMode" class="add-button">+</button>
        <button class="install-button">Install App</button>
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
</script>

<style scoped>
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  /* Add padding or margins as needed */
}

.header-buttons > button {
  margin-left: 0.5rem;
}

.version-banner {
  background-color: #222;
  color: #eee;
  padding: 0.5rem;
  margin-top: 1rem;
  text-align: center;
}

.version-banner a {
  color: #9dd9ff;
  margin: 0 0.5rem;
  text-decoration: none;
}
.version-banner a:hover {
  text-decoration: underline;
}

.add-button,
.install-button {
  background-color: #333333;
  color: white;
  border: none;
  padding: 0.5rem;
  border-radius: 50%;
  font-size: 1rem;
  cursor: pointer;
}

.add-button:hover,
.install-button:hover {
  background-color: #555555;
}
</style>
