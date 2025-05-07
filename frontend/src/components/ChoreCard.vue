<template>
  <div
    class="chore-card"
    :class="[
      choreClass(chore),
      {
        'edit-mode': editMode,
        'done-today': choreStore.isDoneToday(chore),
        'private-chore': chore.is_private
      }
    ]"
    :id="`chore-card-${chore.id}`"
    @dblclick="handleDblClick"
    role="listitem"
    tabindex="0"
    :aria-label="chore.is_private ? `Private chore: ${chore.name}` : `Chore: ${chore.name}`"
  >
  <transition name="fade">
      <div v-if="editMode" class="chore-edit">
        <form @submit.prevent="saveChore" class="edit-chore-form">
          <div class="form-header">
            <h3>Edit Chore</h3>
          </div>
          
          <div class="form-body">
            <div class="form-group">
              <label for="chore-name">Name</label>
              <input id="chore-name" v-model="editableChore.name" type="text" placeholder="Chore Name" required />
            </div>

            <div class="form-group">
              <label for="chore-due-date">Due Date</label>
              <input id="chore-due-date" v-model="editableChore.due_date" type="date" required />
            </div>

            <div class="form-group">
              <label for="chore-interval">Interval (days)</label>
              <input id="chore-interval" v-model="editableChore.interval_days" type="number" required />
            </div>

            <div class="form-group custom-checkbox-wrapper">
              <input type="checkbox" id="chore-private" v-model="editableChore.is_private" />
              <label for="chore-private">
                <span class="checkbox-icon">
                  <i v-if="editableChore.is_private" class="fas fa-check"></i>
                </span>
                <span class="checkbox-text">Private (only visible to me)</span>
              </label>
            </div>
          </div>

          <div class="form-footer">
            <button type="button" class="archive-button" @click="archiveChore">
              <i class="fas fa-archive"></i> Archive
            </button>
            <div class="action-buttons">
              <button type="button" class="cancel-button" @click="cancelEditMode">
                <i class="fas fa-times"></i> Cancel
              </button>
              <button type="submit" class="save-button">
                <i class="fas fa-save"></i> Save
              </button>
            </div>
          </div>
        </form>
      </div>
      <div v-else class="chore-content">
        <span class="chore-title">
          <span v-if="chore.is_private" title="Private chore" aria-label="Private chore" role="img">🔒</span>
          {{ chore.name }}
        </span>
        <div class="chore-right">
          <span
            :class="{'chore-overdue': isOverdue(chore.due_date), 'chore-due': !isOverdue(chore.due_date)}"
            class="chore-due"
          >
            {{ friendlyDueDate(chore.due_date) }}
          </span>
          <span class="chore-interval">
            ⏳ {{ chore.interval_days }}
          </span>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import Hammer from 'hammerjs';
import { useChoreStore } from '@/store/choreStore';

const props = defineProps(['chore']);
const emit = defineEmits(['markAsDone', 'updateChore', 'archiveChore']);

const choreStore = useChoreStore();

const editMode = ref(false);
const editableChore = ref({ ...props.chore });

const handleDblClick = () => {
  if (choreStore.isDoneToday(props.chore)) return;
  editMode.value = true;
};

onMounted(() => {
  const card = document.getElementById(`chore-card-${props.chore.id}`);
  const hammer = new Hammer(card);

  hammer.on('swiperight', () => {
    if (choreStore.isDoneToday(props.chore)) {
      console.log('Chore already done today');
      return;
    }
    card.classList.add('swipe-right');
    setTimeout(() => {
      emit('markAsDone', props.chore.id);
    }, 300);
  });

  hammer.on('swipeleft', () => {
    card.classList.add('enter-edit-mode');
    setTimeout(() => {
      editMode.value = true;
      card.classList.remove('enter-edit-mode');
    }, 300);
  });

  onBeforeUnmount(() => {
    hammer.destroy();
  });
});

const saveChore = async () => {
  try {
    const choreData = {
      ...props.chore,    // Preserve existing values
      ...editableChore.value,  // Merge edited values
      due_date: new Date(editableChore.value.due_date).toISOString(), // Ensure date format
      interval_days: editableChore.value.interval_days, // Ensure interval_days is updated
      is_private: editableChore.value.is_private,
      owner_email: editableChore.value.is_private ? editableChore.value.owner_email : null
    };
    console.log("Saving Chore Data:", choreData);
    await choreStore.updateChore(choreData);
    emit('updateChore', choreData);
    editMode.value = false;
  } catch (error) {
    console.error('Error saving chore:', error);
  }
};

const archiveChore = async () => {
  try {
    await choreStore.archiveChore(props.chore.id);
    emit('archiveChore', props.chore.id);
  } catch (error) {
    console.error('Error archiving chore:', error);
  }
};

const cancelEditMode = () => {
  editableChore.value = { ...props.chore };
  editMode.value = false;
};

const choreClass = (chore) => {
  const today = new Date().setUTCHours(0, 0, 0, 0);
  const dueDate = new Date(chore.due_date).setUTCHours(0, 0, 0, 0);
  const diffDays = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));

  if (chore.archived) return 'archived';
  if (diffDays < 0) return 'overdue';
  if (diffDays === 0) return 'due-today';
  if (diffDays === 1) return 'due-tomorrow';
  if (diffDays <= 2) return 'due-2-days';
  if (diffDays <= 3) return 'due-3-days';
  if (diffDays <= 7) return 'due-7-days';
  if (diffDays <= 14) return 'due-14-days';
  if (diffDays <= 30) return 'due-30-days';
  return 'due-far-future';
};

const isOverdue = (due_date) => {
  const today = new Date().setUTCHours(0, 0, 0, 0);
  const dueDate = new Date(due_date).setUTCHours(0, 0, 0, 0);
  return dueDate < today;
};

const friendlyDueDate = (due_date) => {
  const today = new Date();
  const dueDate = new Date(due_date);
  const diffDays = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));

  if (diffDays < 0) return `Overdue by ${Math.abs(diffDays)} days`;
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Tomorrow';
  if (diffDays <= 2) return `In ${diffDays} days`;
  if (diffDays <= 7) return `In ${diffDays} days`;
  if (diffDays <= 14) return `In ${diffDays} days`;
  if (diffDays <= 30) return `In ${diffDays} days`;
  return `In ${diffDays} days`;
};
</script>

<style scoped>
.chore-card {
  display: flex;
  flex-direction: column;
  padding: var(--space-xs) var(--space-md); /* Reduced vertical padding */
  border-radius: var(--radius-md);
  margin-bottom: var(--space-xxs); /* Reduced from xs to xxs */
  box-shadow: var(--shadow-md);
  transition: all var(--transition-normal);
  color: rgba(255, 255, 255, 0.95); /* Base text color for all cards */
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.2); /* Subtle text shadow for better contrast */
}

.chore-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-sm);
  min-height: 2.5rem;
  flex-wrap: wrap;
}

.chore-title {
  font-weight: 600;
  font-size: clamp(0.85rem, 1.5vw, 1rem);
  letter-spacing: 0.02em;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: normal; /* Allow wrapping */
  word-break: break-word; /* Prevent overflow on small screens */
}

.chore-right {
  display: flex;
  gap: var(--space-xs);
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}

@media (max-width: 576px) {
  .chore-content {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-xs);
  }
  
  .chore-title {
    font-size: 0.95rem;
    width: 100%;
    margin-bottom: var(--space-xxs);
  }
  
  .chore-right {
    width: 100%;
    justify-content: space-between;
  }
  
  .chore-card {
    padding: var(--space-xs) var(--space-sm);
  }
  
  .form-header, .form-body, .form-footer {
    padding: 0.75rem;
  }
  
  .form-footer {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .action-buttons {
    width: 100%;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .save-button, .cancel-button, .archive-button {
    width: 100%;
    padding: 0.5rem;
  }
}

.chore-due {
  font-size: 0.8rem; /* Smaller font size */
  padding: 0.1em 0.4em; /* Reduced padding */
  border-radius: var(--radius-sm);
  background: rgba(0, 0, 0, 0.2);
  line-height: 1.4;
}

.chore-interval {
  font-size: 0.8rem; /* Smaller font size */
  opacity: 0.9;
  background: rgba(0, 0, 0, 0.15);
  padding: 0.1em 0.4em; /* Reduced padding */
  border-radius: var(--radius-sm);
  line-height: 1.4;
}

.chore-overdue {
  font-weight: 700;
  color: #fff;
  background: rgba(255, 0, 0, 0.2);
}

.edit-chore-form {
  background: var(--color-surface);
  padding: 0;
  border-radius: var(--radius-md);
  margin: var(--space-xs) 0;
  box-shadow: var(--shadow-lg);
  width: 100%;
  overflow: hidden;
}

.form-header {
  background: var(--color-surface-light);
  padding: 0.75rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--color-surface-lighter);
}

.form-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.close-edit-button {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 1rem;
  padding: 0.25rem;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color var(--transition-fast), color var(--transition-fast);
}

.close-edit-button:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--color-text);
  transform: none;
}

.form-body {
  padding: 1rem;
}

.form-footer {
  padding: 0.75rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--color-surface-lighter);
}

.action-buttons {
  display: flex;
  gap: var(--space-xs);
}

.form-group {
  margin-bottom: var(--space-sm);
}

.form-group input {
  width: 100%;
  padding: 0.5rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-surface-lighter);
  background: var(--color-surface-light);
  color: var(--color-text);
  box-sizing: border-box;
  transition: border-color var(--transition-fast);
}

.form-group input:focus {
  border-color: var(--color-primary);
  outline: none;
}

.custom-checkbox-wrapper {
  display: flex;
  margin-bottom: 1rem;
}

.custom-checkbox-wrapper input[type="checkbox"] {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.custom-checkbox-wrapper label {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
  font-weight: 500;
}

.checkbox-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  background: var(--color-surface-light);
  border: 2px solid var(--color-primary);
  border-radius: var(--radius-sm);
  margin-right: 0.75rem;
  color: white;
  transition: background-color var(--transition-fast);
}

.custom-checkbox-wrapper input[type="checkbox"]:checked + label .checkbox-icon {
  background: var(--color-primary);
}

.custom-checkbox-wrapper input[type="checkbox"]:focus + label .checkbox-icon {
  box-shadow: 0 0 0 2px rgba(46, 204, 113, 0.3);
}

.checkbox-text {
  color: var(--color-text);
  transition: color var(--transition-fast);
}

.custom-checkbox-wrapper:hover .checkbox-text {
  color: var(--color-primary);
}

.save-button {
  background: var(--color-primary);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-sm);
  border: none;
  cursor: pointer;
  font-weight: 600;
}

.save-button:hover {
  background: var(--color-primary-hover);
  transform: none;
}

.cancel-button {
  background: var(--color-surface-light);
  color: var(--color-text);
  padding: 0.5rem 1rem;
  border-radius: var(--radius-sm);
  border: none;
  cursor: pointer;
  font-weight: 600;
}

.cancel-button:hover {
  background: var(--color-surface-lighter);
  transform: none;
}

.archive-button {
  background: var(--color-warning);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-sm);
  border: none;
  cursor: pointer;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.archive-button:hover {
  background: var(--color-warning-hover);
  transform: none;
}

/* Status Colors */
.chore-card.overdue { background-color: var(--color-overdue); }
.chore-card.due-today { background-color: var(--color-due-today); }
.chore-card.due-tomorrow { background-color: var(--color-due-soon); }
.chore-card.due-2-days { background-color: var(--color-due-2-days); }
.chore-card.due-3-days { background-color: var(--color-due-3-days); }
.chore-card.due-7-days { background-color: var(--color-due-7-days); }
.chore-card.due-14-days { background-color: var(--color-due-14-days); }
.chore-card.due-30-days { background-color: var(--color-due-30-days); }
.chore-card.due-far-future { background-color: var(--color-due-far-future); }
.chore-card.archived { background-color: var(--color-archived); }

/* Add done today state */
.chore-card.done-today {
  position: relative;
  opacity: 0.6;
  filter: grayscale(40%);
  pointer-events: none;
}

.chore-card.done-today .chore-content {
  text-decoration: line-through;
  text-decoration-color: rgba(255, 255, 255, 0.6);
}

.chore-card.done-today::after {
  content: "✓ Done today";
  position: absolute;
  top: 50%;
  right: var(--space-md);
  transform: translateY(-50%);
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.9);
  background: rgba(0, 0, 0, 0.2);
  padding: 0.2em 0.6em;
  border-radius: var(--radius-sm);
  pointer-events: none;
}

/* Add private chore state */
.chore-card.private-chore {
  border-left: 4px solid #ffb300;
  background: linear-gradient(90deg, #232323 90%, #ffb30022 100%);
}
</style>
