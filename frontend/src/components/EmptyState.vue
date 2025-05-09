<template>
  <div class="empty-state">
    <div class="illustration-container" :class="type">
      <EmptyChores v-if="type === 'chores'" />
      <EmptyArchived v-else-if="type === 'archived'" />
      <EmptySearch v-else-if="type === 'search'" />
      <EmptyFiltered v-else-if="type === 'filtered'" />
    </div>
    <h3 class="empty-title">{{ title }}</h3>
    <p class="empty-message">{{ message }}</p>
    <button v-if="buttonText" class="action-button" @click="$emit('action')">
      <i :class="buttonIcon" v-if="buttonIcon"></i> {{ buttonText }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import EmptyChores from './illustrations/EmptyChores.vue';
import EmptyArchived from './illustrations/EmptyArchived.vue';
import EmptySearch from './illustrations/EmptySearch.vue';
import EmptyFiltered from './illustrations/EmptyFiltered.vue';

const props = defineProps({
  type: {
    type: String,
    required: true,
    validator: (value) => ['chores', 'archived', 'search', 'filtered'].includes(value)
  },
  title: {
    type: String,
    required: true
  },
  message: {
    type: String,
    required: true
  },
  buttonText: {
    type: String,
    default: ''
  },
  buttonIcon: {
    type: String,
    default: ''
  }
});

defineEmits(['action']);
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  margin: 2rem auto;
  max-width: 400px;
}

.illustration-container {
  width: 200px;
  height: 200px;
  margin-bottom: 1.5rem;
}

.empty-title {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
  color: var(--color-text);
}

.empty-message {
  color: var(--color-text-secondary);
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.action-button {
  background-color: var(--color-primary);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background-color 0.2s;
}

.action-button:hover {
  background-color: var(--color-primary-dark);
}

/* Animation for the illustrations */
.illustration-container svg {
  animation: fadeIn 0.6s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
