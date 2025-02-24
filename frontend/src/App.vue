<template>
  <div id="app">
    <Header @addChore="handleAddChore" />
    <router-view></router-view>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from '@/plugins/axios'
import Header from '@/components/Header.vue'
import { useChoreStore } from '@/store/choreStore'

const versionInfo = ref(null)
const choreStore = useChoreStore()

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
  font-family: Arial, sans-serif;
  color: #333;
  padding: 1rem;
}

.version-banner {
  background-color: #222;
  color: #eee;
  padding: 0.5rem;
  margin-bottom: 1rem;
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
