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
