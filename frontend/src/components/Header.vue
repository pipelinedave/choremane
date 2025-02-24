<template>
  <header>
    <button @click="toggleBanner">About</button>
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
</script>

<style scoped>
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
</style>
