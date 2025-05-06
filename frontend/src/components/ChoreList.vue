<template>
  <div class="chore-list">
    <div class="filter-pills">
      <button
        v-for="pill in pills"
        :key="pill.value"
        :class="['pill', { active: filter === pill.value }]"
        @click="filter = pill.value"
        :aria-label="pill.label"
      >
        {{ pill.label }}
      </button>
    </div>
    <transition-group name="list" tag="div" class="chore-cards">
      <ChoreCard
        v-for="chore in filteredChores"
        :key="chore.id"
        :chore="chore"
        @markAsDone="markAsDone"
        @archiveChore="archiveChore"
        @updateChore="updateChore"
      />
    </transition-group>

    <!-- Activity Log is hidden for now -->
    <!--
    <div class="log-section">
      <h2>Activity Log</h2>
      <ul>
        <li v-for="log in recentLogs" :key="log.id">
          <strong>{{ log.action_type }}</strong>: {{ log.action_details || 'No details available' }}
        </li>
      </ul>
    </div>
    -->
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useChoreStore } from '@/store/choreStore';
import ChoreCard from './ChoreCard.vue';

const choreStore = useChoreStore();

onMounted(() => {
  choreStore.fetchChores();
});

const filter = ref('all');
const pills = [
  { label: 'All', value: 'all' },
  { label: 'Overdue', value: 'overdue' },
  { label: 'Due Today', value: 'today' },
  { label: 'Upcoming', value: 'upcoming' },
  { label: 'Archived', value: 'archived' },
];

const filteredChores = computed(() => {
  if (filter.value === 'all') return choreStore.sortedByUrgency;
  if (filter.value === 'overdue') return choreStore.sortedByUrgency.filter(c => new Date(c.due_date) < new Date().setHours(0,0,0,0) && !c.archived);
  if (filter.value === 'today') return choreStore.sortedByUrgency.filter(c => new Date(c.due_date).toDateString() === new Date().toDateString() && !c.archived);
  if (filter.value === 'upcoming') return choreStore.sortedByUrgency.filter(c => new Date(c.due_date) > new Date().setHours(0,0,0,0) && !c.archived);
  if (filter.value === 'archived') return choreStore.sortedByUrgency.filter(c => c.archived);
  return choreStore.sortedByUrgency;
});

const markAsDone = async (choreId) => {
  try {
    await choreStore.markChoreDone(choreId);
  } catch (error) {
    console.error(`Failed to mark chore ${choreId} as done:`, error);
  }
};

const archiveChore = async (choreId) => {
  try {
    await choreStore.archiveChore(choreId);
  } catch (error) {
    console.error(`Failed to archive chore ${choreId}:`, error);
  }
};

const updateChore = async (updatedChore) => {
  try {
    await choreStore.updateChore(updatedChore);
  } catch (error) {
    console.error('Failed to update chore:', error);
  }
};
</script>

<style scoped>
.chore-list {
  padding: var(--space-xs); /* Reduced padding */
  background-color: #121212;
  max-width: 1200px;
  margin: 0 auto;
  color: rgba(255, 255, 255, 0.95);
}

/* Enhance text styling for headers */
h2 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
}

.log-section {
  margin-top: 2rem;
  background: #1a1a1a;
  padding: 1rem;
  border-radius: 10px;
}

.log-section h2 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.log-section ul {
  list-style: none;
  padding: 0;
}

.log-section li {
  padding: 0.5rem 0.8rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 0.9rem;
  line-height: 1.4;
}

.log-section li strong {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  margin-right: 0.5em;
}

.chore-cards {
  display: grid;
  gap: var(--space-xxs);
  grid-template-columns: 1fr; /* Base is single column */
  padding: var(--space-xxs);
}

@media (min-width: 768px) {
  .chore-cards {
    grid-template-columns: repeat(2, 1fr); /* Two columns on tablets */
    gap: var(--space-xs);
  }
}

@media (min-width: 1200px) {
  .chore-cards {
    grid-template-columns: repeat(3, 1fr); /* Three columns on larger screens */
    gap: var(--space-sm);
  }
}

/* Transition Group Animations */
.list-enter-active, .list-leave-active {
  transition: all 0.3s ease;
}
.list-enter-from, .list-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.filter-pills {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  justify-content: center;
}

.pill {
  background: var(--color-surface-light);
  color: var(--color-text);
  border: none;
  border-radius: 999px;
  padding: 0.4em 1.2em;
  font-size: 0.95em;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  outline: none;
  margin-bottom: 0.3rem;
}

@media (max-width: 576px) {
  .filter-pills {
    justify-content: flex-start;
    overflow-x: auto;
    padding-bottom: 0.5rem;
    scrollbar-width: thin;
    -webkit-overflow-scrolling: touch;
  }
  
  .pill {
    font-size: 0.85em;
    padding: 0.3em 0.9em;
    white-space: nowrap;
  }
}
.pill.active, .pill:focus {
  background: var(--color-primary);
  color: #fff;
}
</style>
