<template>
  <div class="login">
    <h2>Welcome to Your Task Manager</h2>
    <button @click="loginWithDex">Login with Google or GitHub</button>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/store/authStore'
import { computed, onMounted } from 'vue'

const authStore = useAuthStore()
const isAuthenticated = computed(() => authStore.isAuthenticated)

const loginWithDex = () => {
  // Redirect to DeX login page
  window.location.href = `https://your-dex-url/auth?client_id=your-client-id&redirect_uri=${encodeURIComponent(window.location.origin + '/?callback=1')}`
}

onMounted(() => {
  // Handle OAuth2 callback
  const params = new URLSearchParams(window.location.search)
  if (params.has('callback')) {
    // Example: token, color, username returned in URL fragment or query
    // In real Dex setup, you may need to exchange code for token via backend
    const token = params.get('token')
    const color = params.get('color')
    const username = params.get('username')
    if (token && username) {
      authStore.login(token, color, username)
      window.location.replace('/')
    }
  } else if (authStore.isAuthenticated()) {
    window.location.replace('/')
  }
})
</script>

<style scoped>
/* Basic styling for login */
.login {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
}
</style>
