<template>
  <div class="chore-list">
    <div class="filter-pills">
      <button
        v-for="pill in pillsWithCounts"
        :key="pill.value"
        :class="['pill', { active: filter === pill.value }]"
        :style="{ 'background-color': pill.color }"
        @click="filter = pill.value"
        :aria-label="pill.label"
      >
        <span class="pill-count">{{ pill.count }}</span>
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

    <!-- Add EmptyState components for different empty cases -->
    <EmptyState 
      v-if="filteredChores.length === 0 && searchQuery" 
      type="search" 
      title="No matching chores found" 
      message="Try adjusting your search terms or clear the search to see all chores."
      buttonText="Clear Search"
      buttonIcon="fas fa-times"
      @action="clearSearch"
    />
    
    <EmptyState 
      v-else-if="filteredChores.length === 0 && filter !== 'all'" 
      type="filtered" 
      title="No chores match your filter" 
      message="Try selecting a different filter or clear all filters to see all your chores."
      buttonText="Clear Filters"
      buttonIcon="fas fa-filter"
      @action="clearFilters"
    />
    
    <EmptyState 
      v-else-if="choreStore.sortedByUrgency.length === 0" 
      type="chores" 
      title="No chores yet" 
      message="Add your first chore to get started managing your tasks."
      buttonText="Add New Chore" 
      buttonIcon="fas fa-plus"
      @action="addNewChore"
    />
    
    <div v-else class="chore-cards">
      <!-- Existing code with the chore cards -->
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useChoreStore } from '@/store/choreStore';
import ChoreCard from './ChoreCard.vue';
import EmptyState from './EmptyState.vue';

const choreStore = useChoreStore();

onMounted(() => {
  choreStore.fetchChores();
});

const filter = ref('all');
const searchQuery = ref('');
const pills = [
  { label: 'All', value: 'all', color: '#3d3d3d' }, // Darker than surface-light
  { label: 'Overdue', value: 'overdue', color: 'var(--color-overdue)' },
  { label: 'Due Today', value: 'today', color: 'var(--color-due-today)' },
  { label: 'Due Tomorrow', value: 'tomorrow', color: 'var(--color-due-soon)' },
  { label: 'Due This Week', value: 'thisWeek', color: 'var(--color-due-7-days)' },
  { label: 'Later', value: 'upcoming', color: '#4db6ac' }, // Using the due-far-future teal color
];

const filteredChores = computed(() => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  
  const nextWeek = new Date(today);
  nextWeek.setDate(today.getDate() + 7);
  
  // Apply non-archived filter to all views except if handled by ArchivedChores component
  const nonArchivedChores = choreStore.sortedByUrgency.filter(c => !c.archived);
  
  if (filter.value === 'all') return nonArchivedChores;
  if (filter.value === 'overdue') return nonArchivedChores.filter(c => new Date(c.due_date) < today);
  if (filter.value === 'today') return nonArchivedChores.filter(c => new Date(c.due_date).toDateString() === today.toDateString());
  if (filter.value === 'tomorrow') {
    return nonArchivedChores.filter(c => new Date(c.due_date).toDateString() === tomorrow.toDateString());
  }
  if (filter.value === 'thisWeek') {
    return nonArchivedChores.filter(c => {
      const dueDate = new Date(c.due_date);
      // Exclude today and tomorrow, but include the rest of the week
      return dueDate > tomorrow && dueDate <= nextWeek;
    });
  }
  if (filter.value === 'upcoming') {
    return nonArchivedChores.filter(c => {
      const dueDate = new Date(c.due_date);
      // Only show chores due after next week
      return dueDate > nextWeek;
    });
  }
  return nonArchivedChores;
});

const pillsWithCounts = computed(() => {
  return pills.map(pill => {
    let count = 0;
    let color = pill.color;
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    const nextWeek = new Date(today);
    nextWeek.setDate(today.getDate() + 7);
    
    // Non-archived chores
    const nonArchivedChores = choreStore.sortedByUrgency.filter(c => !c.archived);
    
    if (pill.value === 'all') {
      count = nonArchivedChores.length;
    } else if (pill.value === 'overdue') {
      count = nonArchivedChores.filter(c => new Date(c.due_date) < today).length;
    } else if (pill.value === 'today') {
      count = nonArchivedChores.filter(c => new Date(c.due_date).toDateString() === today.toDateString()).length;
    } else if (pill.value === 'tomorrow') {
      count = nonArchivedChores.filter(c => new Date(c.due_date).toDateString() === tomorrow.toDateString()).length;
    } else if (pill.value === 'thisWeek') {
      count = nonArchivedChores.filter(c => {
        const dueDate = new Date(c.due_date);
        // Exclude today and tomorrow, but include the rest of the week
        return dueDate > tomorrow && dueDate <= nextWeek;
      }).length;
    } else if (pill.value === 'upcoming') {
      count = nonArchivedChores.filter(c => {
        const dueDate = new Date(c.due_date);
        // Only count chores due after next week
        return dueDate > nextWeek;
      }).length;
    }
    
    return {
      ...pill,
      count,
      color: pill.color
    };
  });
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
    await choreStore.updateChore(updatedChore.id, updatedChore);
  } catch (error) {
    console.error('Failed to update chore:', error);
  }
};

// Add methods for the empty state actions
const clearSearch = () => {
  searchQuery.value = '';
};

const clearFilters = () => {
  filter.value = 'all';
};

const addNewChore = () => {
  // Emit an event to add a new chore
  const event = new CustomEvent('showAddChoreForm');
  window.dispatchEvent(event);
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
  justify-content: center; /* Always centered regardless of screen size */
  width: 100%; /* Take full width of parent */
}

.pill {
  position: relative;
  background: var(--color-surface-light);
  color: var(--color-text);
  border: none;
  border-radius: 999px;
  padding: 0.4em 1.2em 0.4em 2.2em;
  font-size: 0.95em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
  margin-bottom: 0.3rem;
  color: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
}

.pill .pill-count {
  position: absolute;
  left: 0.5em;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.25);
  color: white;
  font-size: 0.8em;
  font-weight: 600;
  border-radius: 50%;
  width: 1.6em;
  height: 1.6em;
  min-width: 1.6em;
}

.pill:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

@media (max-width: 576px) {
  .filter-pills {
    justify-content: center; /* Keep centered on small screens too */
    padding-bottom: 0.5rem;
    overflow-x: auto;
    scrollbar-width: thin;
    -webkit-overflow-scrolling: touch;
  }
  
  .pill {
    font-size: 0.85em;
    padding: 0.3em 0.9em 0.3em 2em;
    white-space: nowrap;
  }
  
  .pill .pill-count {
    font-size: 0.75em;
    width: 1.5em;
    height: 1.5em;
  }
}

.pill.active {
  /* Override background with custom background from the pill when active, but add white text */
  color: #fff !important;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

.pill.active .pill-count {
  background: rgba(255, 255, 255, 0.25);
  color: rgba(0, 0, 0, 0.8);
}
</style>
