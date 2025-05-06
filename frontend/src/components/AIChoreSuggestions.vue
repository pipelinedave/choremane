<template>
  <div class="ai-chore-suggestions">
    <div class="suggestions-header">
      <h2>AI Chore Suggestions</h2>
      <p class="subtitle">Get personalized chore suggestions based on your needs</p>
    </div>

    <div class="input-section">
      <textarea
        v-model="userInput"
        class="suggestion-input"
        placeholder="Describe your situation (e.g., 'I have a small apartment with two cats' or 'I need help organizing weekly household tasks')"
        rows="4"
        @keyup.ctrl.enter="generateSuggestions"
      ></textarea>
      <button 
        @click="generateSuggestions" 
        class="generate-button"
        :disabled="isLoading || !userInput.trim()"
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
</template>

<script setup>
import { ref } from 'vue'
import axios from '@/plugins/axios'

const userInput = ref('')
const suggestions = ref([])
const isLoading = ref(false)
const error = ref(null)

const generateSuggestions = async () => {
  if (!userInput.value.trim() || isLoading.value) return
  
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
          content: userInput.value
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
      // Mark suggestion as added
      suggestion.added = true
    }
  } catch (e) {
    console.error('Error adding chore:', e)
    error.value = 'Failed to add chore. Please try again.'
  }
}
</script>

<style scoped>
.ai-chore-suggestions {
  max-width: 800px;
  margin: 2rem auto;
  padding: 1.5rem;
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.suggestions-header {
  margin-bottom: 1.5rem;
  text-align: center;
}

.suggestions-header h2 {
  margin: 0;
  color: #1a202c;
  font-size: 1.5rem;
}

.subtitle {
  color: #4a5568;
  margin-top: 0.5rem;
}

.input-section {
  margin-bottom: 1.5rem;
}

.suggestion-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  margin-bottom: 1rem;
  font-size: 1rem;
  resize: vertical;
}

.generate-button {
  width: 100%;
  padding: 0.75rem;
  background-color: #4299e1;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.generate-button:hover:not(:disabled) {
  background-color: #3182ce;
}

.generate-button:disabled {
  background-color: #cbd5e0;
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
  background-color: #f7fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  transition: transform 0.2s;
}

.suggestion-item:hover {
  transform: translateY(-1px);
}

.suggestion-item.added {
  opacity: 0.7;
  background-color: #f0fff4;
  border-color: #9ae6b4;
}

.suggestion-content h4 {
  margin: 0;
  color: #2d3748;
  font-size: 1.125rem;
}

.suggestion-content p {
  margin: 0.25rem 0 0;
  color: #718096;
  font-size: 0.875rem;
}

.add-button {
  padding: 0.5rem 1rem;
  background-color: #48bb78;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.add-button:hover:not(:disabled) {
  background-color: #38a169;
}

.add-button:disabled {
  background-color: #9ae6b4;
  cursor: not-allowed;
}

.error-message {
  margin: 1rem 0;
  padding: 0.75rem;
  background-color: #fff5f5;
  border: 1px solid #feb2b2;
  color: #c53030;
  border-radius: 0.375rem;
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
  border: 3px solid #e2e8f0;
  border-top-color: #4299e1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
