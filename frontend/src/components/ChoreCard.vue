<template>
  <div
    class="chore-card"
    :class="[choreClass(chore), { 'edit-mode': editMode }]"
    :id="`chore-card-${chore.id}`"
    @dblclick="editMode = true"
  >
    <transition name="fade">
      <div v-if="editMode" class="chore-edit">
        <input v-model="editableChore.name" class="edit-input" placeholder="Chore Name" />
        <input v-model="editableChore.due_date" class="edit-input" type="date" />
        <input v-model="editableChore.interval_days" class="edit-input" type="number" placeholder="Interval (days)" />
        <div class="edit-actions">
          <button @click="saveChore" class="save-btn">Save</button>
          <button @click="archiveChore" class="archive-btn">Archive</button>
          <button @click="cancelEditMode" class="cancel-btn">Cancel</button>
        </div>
      </div>
      <div v-else class="chore-content">
        <span class="chore-title">{{ chore.name }}</span>
        <span class="chore-interval">Every {{ chore.interval_days }} days</span>
        <span
          :class="{'chore-overdue': isOverdue(chore.due_date), 'chore-due': !isOverdue(chore.due_date)}"
          class="chore-due"
        >
          {{ friendlyDueDate(chore.due_date) }}
        </span>
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
  flex: 1;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chore-title,
.chore-interval,
.chore-due {
  background: #ffffff80;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.9rem;
  margin-left: 0.5rem;
}

.chore-edit {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  width: 100%;
  background-color: #f9f9f9;
  padding: 1rem;
  border-radius: 8px;
}

.edit-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
}

.edit-actions {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
}

.save-btn {
  background-color: #4caf50;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.archive-btn {
  background-color: #f44336;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.cancel-btn {
  background-color: #9e9e9e;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
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
