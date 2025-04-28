<template>
  <form @submit.prevent="onSubmit" class="add-chore-form">
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

    <div class="form-group">
      <label>
        <input type="checkbox" v-model="chore.is_private" />
        Private (only visible to me)
      </label>
    </div>

    <div class="form-actions">
      <button type="submit" class="submit-btn">Add Chore</button>
      <button type="button" class="cancel-btn" @click="onCancel">Cancel</button>
    </div>
  </form>
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
.add-chore-form {
  background: #202020;
  padding: 1.5rem;
  border-radius: 10px;
  color: #fff;
  margin-bottom: 1.5rem;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.4);
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.5rem;
  border-radius: 5px;
  border: 1px solid #444;
  background: #333;
  color: #fff;
}

.form-actions {
  display: flex;
  justify-content: space-between;
}

.submit-btn,
.cancel-btn {
  padding: 0.5rem 1rem;
  border-radius: 5px;
  border: none;
  cursor: pointer;
}

.submit-btn {
  background-color: #27ae60;
  color: white;
  font-weight: bold;
}

.submit-btn:hover {
  background-color: #2ecc71;
}

.cancel-btn {
  background-color: #e74c3c;
  color: white;
  font-weight: bold;
}

.cancel-btn:hover {
  background-color: #ff6f61;
}
</style>
