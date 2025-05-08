<template>
  <div class="archived-chores-modal">
    <div class="modal-overlay" role="dialog" aria-modal="true" aria-label="Archived Chores" @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Archived Chores</h2>
        </div>
        <div class="modal-body">
          <div v-if="archivedChores.length === 0" class="no-archived">
            <p>No archived chores found.</p>
          </div>
          <div v-else class="chore-cards-archived">
            <div v-for="chore in archivedChores" :key="chore.id" class="archived-chore-container">
              <ChoreCard
                :chore="chore"
                :isArchivedView="true"
                @markAsDone="markAsDone"
                @updateChore="updateChore"
                @archiveChore="unarchiveChore"
              />
              <button 
                class="unarchive-button" 
                @click="unarchiveChore(chore.id)" 
                aria-label="Unarchive chore"
                title="Unarchive chore"
              >
                <i class="fas fa-undo"></i>
              </button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="neutral-button" @click="$emit('close')">
            <i class="fas fa-check"></i> Done
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useChoreStore } from '@/store/choreStore';
import ChoreCard from './ChoreCard.vue';

defineEmits(['close']);

const choreStore = useChoreStore();

// Get only archived chores
const archivedChores = computed(() => {
  return choreStore.sortedArchivedChores;
});

const markAsDone = async (choreId) => {
  try {
    await choreStore.markChoreDone(choreId);
  } catch (error) {
    console.error(`Failed to mark chore ${choreId} as done:`, error);
  }
};

const updateChore = async (updatedChore) => {
  try {
    await choreStore.updateChore(updatedChore.id, updatedChore);
  } catch (error) {
    console.error('Failed to update chore:', error);
  }
};

// Unarchive the chore using the store's dedicated method
const unarchiveChore = async (choreId) => {
  try {
    await choreStore.unarchiveChore(choreId);
  } catch (error) {
    console.error(`Failed to unarchive chore ${choreId}:`, error);
  }
};
</script>

<style scoped>
.archived-chores-modal {
  font-family: 'Roboto', sans-serif;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  background-color: #1e1e1e;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  color: rgba(255, 255, 255, 0.95);
}

.modal-header {
  padding: 1rem;
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 500;
}

.close-button {
  background: none;
  border: none;
  color: #999;
  font-size: 1.2rem;
  cursor: pointer;
}

.close-button:hover {
  color: #fff;
}

.modal-body {
  padding: 1rem;
  overflow-y: auto;
  flex-grow: 1;
  max-height: 60vh; /* Limit height to prevent oversized modal */
}

.no-archived {
  text-align: center;
  padding: 2rem;
  color: #777;
}

.chore-cards-archived {
  display: flex;
  flex-direction: column;
  gap: 0.5rem; /* Reduced gap between items */
}

.archived-chore-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  position: relative;
  margin-bottom: 0.75rem;
}

.archived-chore-container :deep(.chore-card) {
  width: calc(100% - 40px);
  margin-bottom: 0;
}

.unarchive-button {
  background-color: #4a5568;
  color: white;
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  min-width: 36px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s, transform 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* Add animation for the unarchive button */
@keyframes pulse-button {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.unarchive-button:active {
  animation: pulse-button 0.3s;
  background-color: #4CAF50; /* Change color during animation */
}

.unarchive-button:hover {
  background-color: #647182;
  transform: scale(1.05);
}

.unarchive-button i {
  font-size: 0.9rem;
}

.modal-footer {
  padding: 1rem;
  border-top: 1px solid #333;
  display: flex;
  justify-content: flex-end;
}

.neutral-button {
  padding: 0.5rem 1rem;
  background-color: #4d4d4d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background-color 0.2s;
}

.neutral-button:hover {
  background-color: #5a5a5a;
}
</style>
