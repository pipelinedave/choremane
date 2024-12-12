<template>
  <div class="chore-list">
    <header class="header">
      <h1>CHOREMANE  :[]]</h1>
      <div class="header-buttons">
        <button @click="toggleAddMode" class="add-button">+</button>
        <!-- Undo button is hidden for now -->
        <!-- <button @click="undoLastAction" class="undo-button">↶</button> -->
      </div>
    </header>

    <AddChoreForm v-if="addMode" @addChore="addChore" @cancel="toggleAddMode" />

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
import { ref, computed, onMounted } from 'vue';
import { useChoreStore } from '@/store/choreStore';
import ChoreCard from '@/components/ChoreCard.vue';
import AddChoreForm from '@/components/AddChoreForm.vue';

const choreStore = useChoreStore();

onMounted(() => {
  console.log('Fetching chores on mount...');
  choreStore.fetchChores();
  // No need to fetch logs if we're not displaying them
  // choreStore.fetchLogs();
});

const addMode = ref(false);

const toggleAddMode = () => {
  addMode.value = !addMode.value;
  console.log('Toggled add mode:', addMode.value);
};

const sortedChores = computed(() => {
  console.log('Recomputing sorted chores...');
  return choreStore.sortedByUrgency;
});

const addChore = async (newChore) => {
  console.log('Adding new chore:', newChore);
  try {
    await choreStore.addChore(newChore);
    console.log('Successfully added chore.');
  } catch (error) {
    console.error('Failed to add chore:', error);
  }
};

const markAsDone = async (choreId) => {
  console.log(`Marking chore as done: ID ${choreId}`);
  try {
    await choreStore.markChoreDone(choreId);
    console.log(`Successfully marked chore ${choreId} as done.`);
  } catch (error) {
    console.error(`Failed to mark chore ${choreId} as done:`, error);
  }
};

const archiveChore = async (choreId) => {
  console.log(`Archiving chore: ID ${choreId}`);
  try {
    await choreStore.archiveChore(choreId);
    console.log(`Successfully archived chore ${choreId}.`);
  } catch (error) {
    console.error(`Failed to archive chore ${choreId}:`, error);
  }
};

const updateChore = async (updatedChore) => {
  console.log('Updating chore:', updatedChore);
  try {
    await choreStore.updateChore(updatedChore);
    console.log('Successfully updated chore.');
  } catch (error) {
    console.error('Failed to update chore:', error);
  }
};
</script>

<style scoped>
.chore-list {
  padding: 1rem;
  background-color: #121212;
  max-width: 1200px;
  margin: 0 auto;
  color: #e0e0e0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.header-buttons {
  display: flex;
  gap: 0.5rem;
}

.add-button,
.undo-button {
  background-color: #333333;
  color: white;
  border: none;
  padding: 0.5rem;
  border-radius: 50%;
  font-size: 1rem;
  cursor: pointer;
}

.add-button:hover,
.undo-button:hover {
  background-color: #555555;
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
  padding: 0.5rem 0;
  border-bottom: 1px solid #444;
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
