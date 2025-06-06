﻿<template>
  <div
    class="chore-card"
    :class="[
      choreClass(chore),
      {
        'edit-mode': editMode,
        'done-today': choreStore.isDoneToday(chore),
        'private-chore': chore.is_private,
        'archived-view': isArchivedView
      }
    ]"
    :id="`chore-card-${chore.id}`"
    @dblclick="handleDblClick"
    role="listitem"
    tabindex="0"
    :aria-label="chore.is_private ? `Private chore: ${chore.name}` : `Chore: ${chore.name}`"
  >
    <!-- Left swipe action (Edit) -->
    <div class="swipe-action edit-action">
      <button class="edit-button" @click="enterEditMode">
        <i class="fas fa-edit"></i>
      </button>
    </div>
    
    <!-- Right swipe action (Mark as done) -->
    <div class="swipe-action done-action">
      <button class="done-button" @click="markDone">
        <i class="fas fa-check"></i>
      </button>
    </div>
    
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
            <button v-if="!isArchivedView" type="button" class="archive-button" @click="archiveChore">
              <i class="fas" :class="chore.archived ? 'fa-undo' : 'fa-archive'"></i> {{ chore.archived ? 'Unarchive' : 'Archive' }}
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

const props = defineProps(['chore', 'isArchivedView']);
const emit = defineEmits(['markAsDone', 'updateChore', 'archiveChore']);

const choreStore = useChoreStore();

const editMode = ref(false);
const editableChore = ref({ ...props.chore });
let hammer = null;
let isRevealingAction = false;
let initialY = 0; // Track initial Y position for detecting vertical scrolls
let isScrolling = false; // Flag to determine if user is scrolling
const MIN_SWIPE_DISTANCE = 40; // Minimum distance in pixels before triggering swipe action
const SCROLL_DETECTION_THRESHOLD = 15; // Pixel threshold to detect vertical scrolling

const handleDblClick = () => {
  if (choreStore.isDoneToday(props.chore) || props.isArchivedView) return;
  editMode.value = true;
};

const enterEditMode = () => {
  if (choreStore.isDoneToday(props.chore) || props.isArchivedView) return;
  editMode.value = true;
};

const markDone = () => {
  if (choreStore.isDoneToday(props.chore) || props.isArchivedView) {
    console.log('Chore already done today or is in archived view');
    return;
  }
  emit('markAsDone', props.chore.id);
};

const resetSwipeState = (card) => {
  // Reset all swipe-related classes
  card.classList.remove('swipe-left', 'swipe-right', 'swipe-reveal-left', 'swipe-reveal-right', 'swiping', 'returning');
  // Reset inline style transform
  card.style.transform = '';
  isRevealingAction = false;
  isScrolling = false;
};

onMounted(() => {
  const card = document.getElementById(`chore-card-${props.chore.id}`);
  
  // Skip initializing Hammer.js for archived chores view
  if (props.isArchivedView) {
    return;
  }
  
  // Initialize Hammer.js with vertical recognition to detect scrolling
  hammer = new Hammer(card);
  hammer.get('pan').set({ direction: Hammer.DIRECTION_ALL, threshold: 5 });
  
  // Pan start - capture initial position and reset state
  hammer.on('panstart', (event) => {
    if (choreStore.isDoneToday(props.chore) || editMode.value) return;
    
    // Store initial Y position to detect scrolling direction
    initialY = event.center.y;
    isScrolling = false;
    card.classList.add('swiping');
  });
  
  // Handle panning to left (for edit)
  hammer.on('panleft', (event) => {
    if (choreStore.isDoneToday(props.chore) || editMode.value) return;
    
    // Check if user is scrolling vertically
    const verticalDistance = Math.abs(event.center.y - initialY);
    if (verticalDistance > SCROLL_DETECTION_THRESHOLD) {
      isScrolling = true;
      resetSwipeState(card);
      return;
    }
    
    // If not scrolling, handle horizontal swipe
    if (!isScrolling) {
      // Apply a transform effect to the card during panning
      const translateX = Math.min(0, event.deltaX);
      card.style.transform = `translateX(${translateX}px)`;
      
      // Only reveal action if swipe distance exceeds minimum threshold
      if (Math.abs(event.deltaX) >= MIN_SWIPE_DISTANCE) {
        card.classList.add('swipe-reveal-left');
        isRevealingAction = true;
      } else {
        card.classList.remove('swipe-reveal-left');
        isRevealingAction = false;
      }
    }
  });
  
  // Handle panning to right (for done)
  hammer.on('panright', (event) => {
    if (choreStore.isDoneToday(props.chore) || editMode.value) return;
    
    // Check if user is scrolling vertically
    const verticalDistance = Math.abs(event.center.y - initialY);
    if (verticalDistance > SCROLL_DETECTION_THRESHOLD) {
      isScrolling = true;
      resetSwipeState(card);
      return;
    }
    
    // If not scrolling, handle horizontal swipe
    if (!isScrolling) {
      // Apply a transform effect to the card during panning
      const translateX = Math.max(0, event.deltaX);
      card.style.transform = `translateX(${translateX}px)`;
      
      // Only reveal action if swipe distance exceeds minimum threshold
      if (Math.abs(event.deltaX) >= MIN_SWIPE_DISTANCE) {
        card.classList.add('swipe-reveal-right');
        isRevealingAction = true;
      } else {
        card.classList.remove('swipe-reveal-right');
        isRevealingAction = false;
      }
    }
  });
  
  // Handle end of panning gesture
  hammer.on('panend', (event) => {
    if (choreStore.isDoneToday(props.chore) || editMode.value) return;
    
    card.classList.remove('swiping');
    
    // If detected as a scroll, abort swipe action
    if (isScrolling) {
      resetSwipeState(card);
      return;
    }
    
    // Only trigger action if swipe was deliberate (exceeds threshold)
    const swipeDistance = Math.abs(event.deltaX);
    
    if (isRevealingAction && swipeDistance >= MIN_SWIPE_DISTANCE) {
      if (card.classList.contains('swipe-reveal-left')) {
        // For left swipe (Edit)
        card.classList.add('swipe-left');
        setTimeout(() => {
          enterEditMode();
          resetSwipeState(card);
        }, 300);
      } else if (card.classList.contains('swipe-reveal-right')) {
        // For right swipe (Done)
        card.classList.add('swipe-right');
        setTimeout(() => {
          markDone();
          resetSwipeState(card);
        }, 300);
      }
    } else {
      // For short swipes, return to original position with animation
      card.classList.add('returning');
      setTimeout(() => {
        card.classList.remove('returning');
        resetSwipeState(card);
      }, 300);
    }
  });
  
  // Add a handler for regular touch events to reset swipe state
  // when the user starts scrolling
  document.addEventListener('scroll', () => {
    if (!editMode.value && card && isRevealingAction) {
      resetSwipeState(card);
    }
  }, { passive: true });

  onBeforeUnmount(() => {
    if (hammer) {
      hammer.destroy();
      hammer = null;
    }
    document.removeEventListener('scroll', () => {});
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
    await choreStore.updateChore(props.chore.id, choreData);
    emit('updateChore', choreData);
    editMode.value = false;
  } catch (error) {
    console.error('Error saving chore:', error);
  }
};

const archiveChore = async () => {
  try {
    if (props.chore.archived) {
      // If already archived, then unarchive
      const updatedChore = { ...props.chore, archived: false };
      await choreStore.updateChore(props.chore.id, updatedChore);
    } else {
      // If not archived, then archive
      await choreStore.archiveChore(props.chore.id);
    }
    emit('archiveChore', props.chore.id);
  } catch (error) {
    console.error('Error updating archive status:', error);
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
  position: relative;
  overflow: hidden; /* Important for hiding the swipe actions */
}

/* Swipe Action Containers */
.swipe-action {
  position: absolute;
  top: 0;
  height: 100%;
  width: 80px; /* Increased width for better visibility */
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.3); /* Add shadow for depth */
  z-index: 2; /* Ensure actions appear above card content */
}

.edit-action {
  right: 0;
  background-color: #FF9800; /* Brighter orange for edit */
  transform: translateX(100%); /* Hidden by default */
}

.done-action {
  left: 0;
  background-color: #4CAF50; /* Brighter green for done */
  transform: translateX(-100%); /* Hidden by default */
}

/* Swipe Action Buttons */
.done-button, .edit-button {
  border: none;
  background: transparent;
  color: white;
  font-size: 1.75rem; /* Larger icons */
  cursor: pointer;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4); /* Add text shadow for better contrast */
}

/* Reveal states */
.chore-card.swipe-reveal-left .edit-action {
  transform: translateX(0); /* Show edit action */
}

.chore-card.swipe-reveal-right .done-action {
  transform: translateX(0); /* Show done action */
}

/* Add text labels to buttons */
.done-button::after, .edit-button::after {
  position: absolute;
  font-size: 0.75rem;
  font-weight: bold;
  margin-top: 3.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.done-button::after {
  content: "Done";
}

.edit-button::after {
  content: "Edit";
}

/* Animation states */
.chore-card.swipe-left {
  transform: translateX(-100px);
  opacity: 0.9;
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.chore-card.swipe-right {
  transform: translateX(100px);
  opacity: 0.9;
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.chore-card.swiping {
  transition: transform 0.1s;
}

.chore-card.returning {
  transition: transform 0.3s ease-out;
}

.chore-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-sm);
  min-height: 2.5rem;
  flex-wrap: wrap;
  z-index: 1; /* Ensure content is above the swipe actions */
}

/* Rest of the original styles */
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

/* Visual hint for swipable cards - refined */
@media (min-width: 768px) {
  .chore-card:not(.done-today)::before,
  .chore-card:not(.done-today)::after {
    content: '';
    position: absolute;
    top: 0;
    bottom: 0;
    width: 8px;
    background-color: rgba(255, 255, 255, 0.15);
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease, background-color 0.3s ease;
  }
  
  .chore-card:not(.done-today)::before {
    left: 0;
    border-radius: var(--radius-md) 0 0 var(--radius-md);
    background-image: linear-gradient(to right, transparent, #4CAF50);
  }
  
  .chore-card:not(.done-today):hover::before {
    opacity: 1;
  }
  
  .chore-card:not(.done-today)::after {
    right: 0;
    border-radius: 0 var(--radius-md) var(--radius-md) 0;
    background-image: linear-gradient(to left, transparent, #FF9800);
  }
  
  .chore-card:not(.done-today):hover::after {
    opacity: 1;
  }
  
  /* Add swipe hint icon on hover */
  .chore-card:not(.done-today):hover::before {
    content: '⟸'; /* Left arrow for done action */
    display: flex;
    align-items: center;
    justify-content: center;
    color: rgba(255, 255, 255, 0.7);
    font-size: 1.2rem;
    width: 24px;
  }
  
  .chore-card:not(.done-today):hover::after {
    content: '⟹'; /* Right arrow for edit action */
    display: flex;
    align-items: center;
    justify-content: center;
    color: rgba(255, 255, 255, 0.7);
    font-size: 1.2rem;
    width: 24px;
  }
}

/* Visual hint for mobile swipe */
@media (max-width: 767px) {
  .chore-card:not(.done-today):not(.edit-mode):active::before {
    content: '⟺';
    position: absolute;
    top: 50%;
    right: 10px;
    transform: translateY(-50%);
    color: rgba(255, 255, 255, 0.6);
    font-size: 1.2rem;
    background-color: rgba(0, 0, 0, 0.2);
    border-radius: 50%;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: fadeIn 0.3s forwards;
    pointer-events: none;
    z-index: 10;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  
  /* Make the returning animation more pronounced */
  .chore-card.returning {
    transition: transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }
  
  /* Add resistance effect to swiping */
  .chore-card.swiping {
    transition: transform 0.1s cubic-bezier(0.1, 0.7, 0.7, 1);
  }
}

/* Animation for swipe actions */
@keyframes ripple {
  0% { 
    box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.3);
    opacity: 1;
  }
  100% { 
    box-shadow: 0 0 0 20px rgba(255, 255, 255, 0);
    opacity: 0;
  }
}

.chore-card.swipe-reveal-left .edit-action::before,
.chore-card.swipe-reveal-right .done-action::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  transform: translate(-50%, -50%);
  animation: ripple 1s infinite;
}

/* Add pulsing animation for action buttons */
@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.chore-card.swipe-reveal-left .edit-button i,
.chore-card.swipe-reveal-right .done-button i {
  animation: pulse 0.75s infinite;
}

/* Fade transition for edit mode */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* Archived view styles */
.chore-card.archived-view {
  opacity: 0.85;
  position: relative;
  pointer-events: none; /* Disable interactions */
  overflow: hidden; /* Ensure the overlay stays contained */
  margin-bottom: 0; /* Remove the default margin when in archived view */
}

.chore-card.archived-view::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(60, 60, 60, 0.2);
  z-index: 10;
}
</style>
