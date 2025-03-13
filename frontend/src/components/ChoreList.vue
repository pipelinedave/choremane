<template>
  <div class="chore-list">
    <!-- Animation for refreshing the list -->
    <transition-group name="list" tag="div" class="chore-cards">
      <ChoreCard
        v-for="chore in sortedChores"
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
import { computed, onMounted } from 'vue';
import { useChoreStore } from '@/store/choreStore';
import ChoreCard from './ChoreCard.vue';

const choreStore = useChoreStore();

onMounted(() => {
  choreStore.fetchChores();
});

const sortedChores = computed(() => choreStore.sortedByUrgency);

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
  grid-template-columns: 1fr; /* changed to a single column layout */
  padding: var(--space-xxs);
}

/* Transition Group Animations */
.list-enter-active, .list-leave-active {
  transition: all 0.3s ease;
}
.list-enter-from, .list-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
