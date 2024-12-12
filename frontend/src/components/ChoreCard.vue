<template>
  <div
    class="chore-card"
    :class="choreClass(chore)"
    :id="`chore-card-${chore.id}`"
    @dblclick="editMode = true"
  >
    <transition name="fade">
      <div v-if="editMode" class="chore-edit">
        <input v-model="editableChore.name" placeholder="Name" />
        <input v-model="editableChore.due_date" type="date" />
        <input v-model="editableChore.interval_days" type="number" />
        <button @click="saveChore" class="save-btn">Save</button>
        <button @click="archiveChore" class="archive-btn">Archive</button>
        <button @click="cancelEditMode" class="cancel-btn">Cancel</button>
      </div>
      <div v-else>
        <div class="chore-header">{{ chore.name }}</div>
        <div class="chore-body">
          <div class="info-box left">
            <span>📅</span> {{ friendlyDueDate(chore.due_date) }}
          </div>
          <div class="info-box right">
            <span>⏳</span> {{ friendlyInterval(chore.interval_days) }}
          </div>
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

  // Add swipe gesture handlers with animations
  hammer.on('swiperight', () => {
    // Add swiping animation
    card.classList.add('swipe-right');
    setTimeout(() => {
      emit('markAsDone', props.chore.id);
    }, 300); // Duration of the animation
  });
  hammer.on('swipeleft', () => {
    // Optional: Add a subtle animation or visual feedback
    card.classList.add('enter-edit-mode');
    setTimeout(() => {
      editMode.value = true;
      card.classList.remove('enter-edit-mode');
    }, 300);
  });


  // Cleanup on component unmount
  onBeforeUnmount(() => {
    hammer.destroy();
  });
});

const saveChore = async () => {
  console.log('Saving chore:', editableChore.value);
  try {
    await choreStore.updateChore(editableChore.value);
    emit('updateChore', editableChore.value);
    editMode.value = false;
  } catch (error) {
    console.error('Error saving chore:', error);
  }
};

const archiveChore = async () => {
  console.log('Archiving chore:', props.chore.id);
  try {
    await choreStore.archiveChore(props.chore.id);
    emit('archiveChore', props.chore.id);
    console.log('Chore archived successfully.');
  } catch (error) {
    console.error('Error archiving chore:', error);
  }
};

const cancelEditMode = () => {
  editableChore.value = { ...props.chore }; // Reset fields
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
  if (diffDays <= 7) return 'due-week';
  return 'due-month';
};

const friendlyDueDate = (due_date) => {
  const today = new Date();
  const dueDate = new Date(due_date);
  const diffDays = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));

  if (diffDays < 0) return `Overdue by ${Math.abs(diffDays)} days`;
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Tomorrow';
  if (diffDays <= 7) return `In ${diffDays} days`;
  return `In ${diffDays} days`;
};

const friendlyInterval = (interval) => {
  if (interval === 1) return 'Every day';
  return `Every ${interval} days`;
};
</script>

<style scoped>
.chore-card {
  background: #202020;
  padding: 1rem;
  border-radius: 10px;
  margin-bottom: 1rem;
  color: #fff;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
  position: relative;
  overflow: hidden;
  transition: transform 0.3s ease-in-out, opacity 0.3s ease-in-out;
}

/* Swiping Animations */
.chore-card.swipe-right {
  transform: translateX(100%);
  opacity: 0;
}

.chore-card.swipe-left {
  transform: translateX(-100%);
  opacity: 0;
}

.chore-card.enter-edit-mode {
  /* Example: Briefly change background color */
  animation: highlight 0.3s forwards;
}

@keyframes highlight {
  0% {
    background-color: inherit;
  }
  50% {
    background-color: rgba(255, 255, 255, 0.2);
  }
  100% {
    background-color: inherit;
  }
}
/* Chore Header Styling */
.chore-header {
  font-weight: bold;
  font-size: 1.5rem;
  background: rgba(100, 100, 100, 0.6);
  padding: 0.5rem;
  border-radius: 5px;
  margin-bottom: 0.5rem;
}

/* Chore Body Styling */
.chore-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Info Boxes Styling */
.info-box {
  background: rgba(100, 100, 100, 0.6);
  padding: 0.3rem 0.5rem;
  border-radius: 5px;
  display: flex;
  align-items: center;
}

/* Left and Right Alignment */
.info-box.left {
  justify-content: flex-start;
}

.info-box.right {
  justify-content: flex-end;
}

/* Chore Card Color Classes */
.chore-card.overdue {
  background-color: #8e44ad; /* Purple for overdue */
}

.chore-card.due-today {
  background-color: #e74c3c; /* Red for due today */
}

.chore-card.due-tomorrow {
  background-color: #f1c40f; /* Yellow for due tomorrow */
}

.chore-card.due-week {
  background-color: #27ae60; /* Green for due within 7 days */
}

.chore-card.due-month {
  background-color: #2980b9; /* Blue for due within 30 days */
}

.chore-card.archived {
  background-color: #7f8c8d; /* Gray for archived */
}

/* Fade Transition */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
