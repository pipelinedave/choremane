<template>
  <div class="modal-overlay" role="dialog" aria-modal="true" aria-label="Add New Chore" @click.self="onCancel">
    <div class="modal-content">
      <div class="modal-header">
        <h2>Add New Chore</h2>
      </div>
      <div class="modal-body">
        <form @submit.prevent="onSubmit" id="add-chore-form">
          <div class="form-group">
            <label for="chore-name">Name</label>
            <input id="chore-name" v-model="chore.name" type="text" placeholder="Chore Name" required />
          </div>

          <div class="form-group">
            <label for="chore-due-date">Due Date</label>
            <input id="chore-due-date" v-model="chore.due_date" type="date" required />
          </div>

          <div class="form-group">
            <label for="chore-interval">Interval (days)</label>
            <input id="chore-interval" v-model="chore.interval_days" type="number" required />
          </div>

          <div class="form-group custom-checkbox-wrapper">
            <input type="checkbox" id="chore-private" v-model="chore.is_private" />
            <label for="chore-private">
              <span class="checkbox-icon">
                <i v-if="chore.is_private" class="fas fa-check"></i>
              </span>
              <span class="checkbox-text">Private (only visible to me)</span>
            </label>
          </div>
        </form>
      </div>
      <div class="modal-footer">
        <button type="submit" form="add-chore-form" class="submit-button">
          <i class="fas fa-plus"></i> Add Chore
        </button>
        <button type="button" class="cancel-button" @click="onCancel">
          <i class="fas fa-times"></i> Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from '@/store/authStore';

// Helper function to format today's date as YYYY-MM-DD
const getTodayDate = () => {
  const today = new Date();
  return today.toISOString().split('T')[0];
};

const authStore = useAuthStore();

const chore = ref({
  name: '',
  due_date: getTodayDate(), // Default to today's date
  interval_days: 3,
  done: false, // Default value
  done_by: null, // Default value
  archived: false, // Default value
  is_private: false, // New field
});

const emit = defineEmits(['addChore', 'cancel']);

const onSubmit = () => {
  console.log('Submitting new chore:', chore.value);
  // Attach owner_email if private
  const choreData = { ...chore.value };
  if (choreData.is_private) {
    choreData.owner_email = authStore.username;
  } else {
    choreData.owner_email = null;
  }
  emit('addChore', choreData);
  // Reset chore to default values
  chore.value = {
    name: '',
    due_date: getTodayDate(), // Reset to today's date
    interval_days: 3,
    done: false,
    done_by: null,
    archived: false,
    is_private: false,
  };
};

const onCancel = () => {
  console.log('Canceling chore creation');
  emit('cancel');
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  backdrop-filter: blur(2px);
}

.modal-content {
  background: var(--color-surface);
  color: var(--color-text);
  border-radius: var(--radius-md);
  min-width: 280px;
  width: 100%;
  max-width: 500px;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  background: var(--color-surface-light);
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--color-surface-lighter);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.close-button {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0.25rem;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color var(--transition-fast), color var(--transition-fast);
}

.close-button:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--color-text);
  transform: none;
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid var(--color-surface-lighter);
  gap: 0.75rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--color-text);
}

.form-group input {
  width: 100%;
  padding: 0.625rem;
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

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.checkbox-wrapper input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--color-primary);
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

.submit-button {
  background: var(--color-primary);
  color: white;
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-sm);
  border: none;
  cursor: pointer;
  font-weight: 600;
  min-width: 120px;
}

.submit-button:hover {
  background: var(--color-primary-hover);
  transform: none;
}

.cancel-button {
  background: var(--color-surface-light);
  color: var(--color-text);
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-sm);
  border: none;
  cursor: pointer;
  font-weight: 600;
  min-width: 120px;
}

.cancel-button:hover {
  background: var(--color-surface-lighter);
  transform: none;
}

@media (max-width: 576px) {
  .modal-content {
    max-width: 95%;
  }
  
  .modal-header, .modal-body, .modal-footer {
    padding: 1rem;
  }
  
  .modal-footer {
    flex-direction: column-reverse;
  }
  
  .submit-button, .cancel-button {
    width: 100%;
  }
}
</style>
