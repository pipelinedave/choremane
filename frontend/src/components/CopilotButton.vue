<template>
  <button class="copilot-fab" @click="showModal = true" aria-label="Open AI Chore Assistant">
    🤖
  </button>
  <div v-if="showModal" class="copilot-modal" role="dialog" aria-modal="true" aria-label="AI Chore Assistant">
    <div class="modal-content">
      <div class="modal-header">
        <h2>AI Chore Assistant</h2>
        <button type="button" class="close-button" @click="showModal = false" aria-label="Close">×</button>
      </div>
      
      <div class="input-section">
        <textarea
          v-model="input"
          class="suggestion-input"
          placeholder="Describe your situation (e.g., 'I have a small apartment with two cats' or 'I need help organizing weekly household tasks')"
          rows="4"
          @keyup.ctrl.enter="generateSuggestions"
        ></textarea>
        <button 
          class="generate-button"
          :disabled="isLoading || !input.trim()"
          @click="generateSuggestions"
        >
          {{ isLoading ? 'Generating...' : 'Get Suggestions' }}
        </button>
      </div>

      <div v-if="error" class="error-message">
        {{ error }}
      </div>

      <div v-if="suggestions.length > 0" class="suggestions-list">
        <div v-for="(suggestion, index) in suggestions" 
             :key="index" 
             class="suggestion-item"
             :class="{ 'added': suggestion.added }"
        >
          <div class="suggestion-content">
            <h4>{{ suggestion.name }}</h4>
            <p>Repeat every {{ suggestion.intervalDays }} days</p>
          </div>
          <button 
            @click="addChore(suggestion)"
            class="add-button"
            :disabled="suggestion.added"
          >
            {{ suggestion.added ? 'Added' : 'Add Chore' }}
          </button>
        </div>
      </div>

      <div v-if="isLoading" class="loading">
        <div class="loading-spinner"></div>
        <p>Generating suggestions...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from '@/plugins/axios'

const showModal = ref(false)
const input = ref('')
const suggestions = ref([])
const isLoading = ref(false)
const error = ref(null)

const generateSuggestions = async () => {
  if (!input.value.trim() || isLoading.value) return
  
  error.value = null
  isLoading.value = true
  suggestions.value = []

  try {
    const response = await axios.post('/mcp/generate', {
      messages: [
        {
          role: 'system',
          content: `You are a helpful AI assistant that suggests household chores. When users describe their living situation or needs, respond with a JSON array of chore objects. Each chore should have:
          - name: A descriptive name for the chore
          - intervalDays: How often the chore should be repeated (in days)
          Consider the user's specific situation, common household tasks, seasonal maintenance, and any special requirements mentioned.`
        },
        {
          role: 'user',
          content: input.value
        }
      ]
    })

    // Parse the response and format suggestions
    const suggestedChores = JSON.parse(response.data.content)
    if (Array.isArray(suggestedChores)) {
      suggestions.value = suggestedChores.map(chore => ({
        ...chore,
        added: false
      }))
    }
  } catch (e) {
    console.error('Error generating suggestions:', e)
    error.value = 'Failed to generate suggestions. Please try again.'
  } finally {
    isLoading.value = false
  }
}

const addChore = async (suggestion) => {
  if (suggestion.added) return

  try {
    const response = await axios.post('/api/chores', {
      name: suggestion.name,
      interval_days: suggestion.intervalDays,
      due_date: new Date().toISOString().split('T')[0], // Set due date to today
      is_private: false
    })

    if (response.status === 200) {
      suggestion.added = true
    }
  } catch (e) {
    console.error('Error adding chore:', e)
    error.value = 'Failed to add chore. Please try again.'
  }
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
  padding: 1.5rem;
  border-radius: var(--radius-md);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-text);
  cursor: pointer;
  padding: 0.5rem;
}

.close-button:hover {
  color: var(--color-primary);
}

.input-section {
  margin-bottom: 1.5rem;
}

.suggestion-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  margin-bottom: 1rem;
  font-size: 1rem;
  resize: vertical;
}

.generate-button {
  width: 100%;
  padding: 0.75rem;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.generate-button:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.generate-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.suggestion-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: var(--color-surface-light);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  transition: transform 0.2s;
}

.suggestion-item:hover {
  transform: translateY(-1px);
}

.suggestion-item.added {
  opacity: 0.7;
  background: var(--color-success-light);
  border-color: var(--color-success);
}

.suggestion-content h4 {
  margin: 0;
  font-size: 1.125rem;
}

.suggestion-content p {
  margin: 0.25rem 0 0;
  color: var(--color-text-muted);
  font-size: 0.875rem;
}

.add-button {
  padding: 0.5rem 1rem;
  background: var(--color-success);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.2s;
}

.add-button:hover:not(:disabled) {
  background: var(--color-success-dark);
}

.add-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.error-message {
  margin: 1rem 0;
  padding: 0.75rem;
  background: var(--color-error-light);
  border: 1px solid var(--color-error);
  color: var(--color-error);
  border-radius: var(--radius-sm);
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 2rem 0;
}

.loading-spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
