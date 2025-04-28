<template>
  <button class="copilot-fab" @click="showModal = true" aria-label="Open Copilot smart assistant">
    🤖
  </button>
  <div v-if="showModal" class="copilot-modal" role="dialog" aria-modal="true" aria-label="Copilot Smart Assistant">
    <div class="modal-content">
      <h2>Copilot Smart Assistant</h2>
      <form @submit.prevent="onSubmit">
        <input v-model="input" type="text" placeholder="Ask or command..." aria-label="Copilot input" autofocus />
        <button type="submit">Send</button>
        <button type="button" @click="showModal = false">Close</button>
      </form>
      <div v-if="response" class="copilot-response">
        <strong>Copilot:</strong> {{ response }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const showModal = ref(false)
const input = ref('')
const response = ref('')

const onSubmit = async () => {
  // Placeholder: In future, send input.value to CopilotKit API and set response.value
  response.value = `You said: "${input.value}" (AI integration coming soon!)`
  input.value = ''
}
</script>

<style scoped>
.copilot-fab {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  font-size: 2rem;
  box-shadow: var(--shadow-lg);
  border: none;
  cursor: pointer;
  z-index: 2001;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.copilot-fab:hover {
  background: var(--color-primary-hover);
}
.copilot-modal {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  z-index: 2002;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-content {
  background: var(--color-surface);
  color: var(--color-text);
  padding: 2rem;
  border-radius: var(--radius-md);
  min-width: 320px;
  box-shadow: var(--shadow-lg);
}
.copilot-response {
  margin-top: 1rem;
  background: var(--color-surface-light);
  padding: 1rem;
  border-radius: var(--radius-sm);
}
</style>
