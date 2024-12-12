<template>
  <div class="login">
    <h2>Welcome to Your Task Manager</h2>
    <button @click="loginWithDex">Login with Google or GitHub</button>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/store/authStore'
import { computed } from 'vue'

const authStore = useAuthStore()
const isAuthenticated = computed(() => authStore.isAuthenticated)

const loginWithDex = () => {
  // Redirect to DeX login page
  window.location.href = `https://your-dex-url/auth?client_id=your-client-id&redirect_uri=your-redirect-url`
}

// Check if user is authenticated upon loading
if (isAuthenticated.value) {
  // User is logged in; redirect to main task view
  window.location.href = '/chores'
}
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
