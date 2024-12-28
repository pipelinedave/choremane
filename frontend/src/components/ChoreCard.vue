<template>
  <div
    class="chore-card"
    :class="[choreClass(chore), { 'edit-mode': editMode }]"
    :id="`chore-card-${chore.id}`"
    @dblclick="editMode = true"
  >
  <transition name="fade">
      <div v-if="editMode" class="chore-edit">
        <form @submit.prevent="saveChore" class="edit-chore-form">
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

          <div class="form-actions">
            <button type="submit" class="submit-btn">Save</button>
            <button type="button" class="cancel-btn" @click="cancelEditMode">Cancel</button>
            <button type="button" class="archive-btn" @click="archiveChore">Archive</button>
          </div>
        </form>
      </div>
      <div v-else class="chore-content">
        <span class="chore-title">{{ chore.name }}</span>
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

onMounted(() => {
  const card = document.getElementById(`chore-card-${props.chore.id}`);
  const hammer = new Hammer(card);

  hammer.on('swiperight', () => {
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
    await choreStore.updateChore(editableChore.value);
    emit('updateChore', editableChore.value);
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
  justify-content: center;
  align-items: stretch;
  padding: 0.6rem 1rem;
  border-radius: 8px;
  margin-bottom: 0.6rem;
  color: #333333;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
  position: relative;
  transition: height 0.3s ease;
}

.chore-card.edit-mode {
  height: auto;
}

.chore-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.chore-title {
  font-weight: bold;
  font-size: clamp(0.9rem, 2vw, 1.2rem);
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chore-right {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 0.5rem;
}

.chore-title,
.chore-due,
.chore-interval {
  background: #ffffff80;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.9rem;
}

.chore-card.edit-mode {
  height: auto;
}

.edit-chore-form {
  background: #202020;
  padding: 1.5rem;
  border-radius: 10px;
  color: #fff;
  margin: 1.5rem auto; /* Ensures equal margin and padding on all sides */
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

.form-group input {
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
.cancel-btn,
.archive-btn {
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

.archive-btn {
  background-color: #f1c40f;
  color: #333;
  font-weight: bold;
}

.archive-btn:hover {
  background-color: #f39c12;
}

/* Colors Adjusted for Granularity */
.chore-card.overdue {
  background-color: #ff5252;
}

.chore-card.due-today {
  background-color: #ff7043;
}

.chore-card.due-tomorrow {
  background-color: #ffa726;
}

.chore-card.due-2-days {
  background-color: #ffee58;
}

.chore-card.due-3-days {
  background-color: #aed581;
}

.chore-card.due-7-days {
  background-color: #81c784;
}

.chore-card.due-14-days {
  background-color: #4caf50;
}

.chore-card.due-30-days {
  background-color: #42a5f5;
}

.chore-card.due-far-future {
  background-color: #7986cb;
}
</style>
