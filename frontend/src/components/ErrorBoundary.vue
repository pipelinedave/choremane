// Provides error recovery for app crashes
<template>
  <div v-if="error" class="error-boundary">
    <div class="error-container">
      <h3>Application Error</h3>
      <p>There was a problem with the application.</p>
      <div class="error-details" v-if="showDetails">
        <pre>{{ errorDetails }}</pre>
      </div>
      <div class="error-actions">
        <button @click="resetError" class="retry-button">Try Again</button>
        <button @click="clearAndReload" class="reset-button">Reset App Data</button>
        <button @click="toggleDetails" class="details-button">
          {{ showDetails ? 'Hide Details' : 'Show Details' }}
        </button>
      </div>
    </div>
  </div>
  <slot v-else></slot>
</template>

<script setup>
import { ref, onErrorCaptured, provide } from 'vue';

const error = ref(null);
const errorDetails = ref('');
const showDetails = ref(false);

// Make error state available to child components
provide('error', error);

// Handle errors from child components
onErrorCaptured((err, instance, info) => {
  console.error('Error captured by boundary:', err);
  console.error('Component:', instance);
  console.error('Info:', info);
  
  error.value = err;
  errorDetails.value = `Error: ${err.message}\nInfo: ${info}\nStack: ${err.stack}`;
  
  // Prevent the error from propagating further
  return false;
});

// Reset the error state to allow the app to render again
const resetError = () => {
  error.value = null;
  errorDetails.value = '';
};

// Clear localStorage and reload the page
const clearAndReload = () => {
  // Preserve authentication data
  const token = localStorage.getItem('token');
  const userColor = localStorage.getItem('userColor');
  const username = localStorage.getItem('username');
  
  // Clear all localStorage
  localStorage.clear();
  
  // Restore essential auth data
  if (token) localStorage.setItem('token', token);
  if (userColor) localStorage.setItem('userColor', userColor);
  if (username) localStorage.setItem('username', username);
  
  // Reload the page
  window.location.reload();
};

// Toggle showing error details
const toggleDetails = () => {
  showDetails.value = !showDetails.value;
};
</script>

<style scoped>
.error-boundary {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.7);
  z-index: 9999;
}

.error-container {
  background-color: var(--color-background);
  border-radius: 8px;
  padding: 20px;
  max-width: 90%;
  width: 500px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

h3 {
  color: #e53935;
  margin-top: 0;
}

.error-details {
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  padding: 10px;
  margin: 10px 0;
  max-height: 200px;
  overflow-y: auto;
}

pre {
  margin: 0;
  white-space: pre-wrap;
  font-size: 12px;
}

.error-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

button {
  padding: 8px 15px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-weight: 500;
}

.retry-button {
  background-color: var(--color-primary);
  color: white;
}

.reset-button {
  background-color: #e53935;
  color: white;
}

.details-button {
  background-color: transparent;
  border: 1px solid #ccc;
}
</style>
