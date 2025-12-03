<template>
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
    ref="cardRef"
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
            {{ chore.interval_days }}
          </span>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import Hammer from 'hammerjs';
import { useChoreStore } from '@/store/choreStore';
import { useAuthStore } from '@/store/authStore';

const props = defineProps(['chore', 'isArchivedView']);
const emit = defineEmits(['markAsDone', 'updateChore', 'archiveChore']);

const choreStore = useChoreStore();
const authStore = useAuthStore();

const editMode = ref(false);
const editableChore = ref({ ...props.chore });
let hammer = null;
let isRevealingAction = false;
const cardRef = ref(null);
let scrollHandler = null;
let returnTimer = null;
let initialY = 0; // Track initial Y position for detecting vertical scrolls
let isScrolling = false; // Flag to determine if user is scrolling
const MIN_SWIPE_DISTANCE = 40; // Minimum distance in pixels before triggering swipe action
const SCROLL_DETECTION_THRESHOLD = 15; // Pixel threshold to detect vertical scrolling
const RETURN_ANIMATION_MS = 480;
const MAX_RETURN_DISTANCE = 140;
const MAX_RETURN_TILT = 8;

watch(
  () => choreStore.editingChoreId,
  (currentId, previousId) => {
    const nowEditingThis = currentId === props.chore.id;
    const wasEditingThis = previousId === props.chore.id;

    if (nowEditingThis) {
      editableChore.value = { ...props.chore };
      editMode.value = true;
    } else if (wasEditingThis) {
      editMode.value = false;
      editableChore.value = { ...props.chore };
    }
  }
);

watch(
  () => props.chore,
  (latestChore) => {
    if (choreStore.editingChoreId !== props.chore.id) {
      editableChore.value = { ...latestChore };
    }
  },
  { deep: true }
);

const isEditModeActive = () => choreStore.editingChoreId === props.chore.id || editMode.value;

const handleDblClick = () => {
  if (choreStore.isDoneToday(props.chore) || props.isArchivedView) return;
  enterEditMode();
};

const enterEditMode = () => {
  if (choreStore.isDoneToday(props.chore) || props.isArchivedView) return;
  if (choreStore.editingChoreId === props.chore.id) return;
  choreStore.setEditingChore(props.chore.id);
};

const markDone = () => {
  if (choreStore.isDoneToday(props.chore) || props.isArchivedView) {
    console.log('Chore already done today or is in archived view');
    return;
  }
  emit('markAsDone', props.chore.id);
};

const resetSwipeState = (card) => {
  if (returnTimer) {
    clearTimeout(returnTimer);
    returnTimer = null;
  }
  // Reset all swipe-related classes
  card.classList.remove('swipe-left', 'swipe-right', 'swipe-reveal-left', 'swipe-reveal-right', 'swiping', 'returning');
  // Reset inline style transform
  card.style.transform = '';
  card.style.removeProperty('--swipe-current-tilt');
  card.style.removeProperty('--swipe-return-distance');
  card.style.removeProperty('--swipe-return-tilt');
  isRevealingAction = false;
  isScrolling = false;
};

const applySwipeTransform = (card, deltaX) => {
  const clampedDistance = Math.max(-MAX_RETURN_DISTANCE, Math.min(MAX_RETURN_DISTANCE, deltaX));
  const tilt = Math.max(-MAX_RETURN_TILT, Math.min(MAX_RETURN_TILT, clampedDistance / 14));
  card.style.setProperty('--swipe-current-tilt', `${tilt}deg`);
  card.style.transform = `translateX(${clampedDistance}px) rotate(${tilt}deg)`;
  return { clampedDistance, tilt };
};

const animateReturn = (card, deltaX) => {
  const { clampedDistance, tilt } = applySwipeTransform(card, deltaX);
  card.style.setProperty('--swipe-return-distance', `${clampedDistance}px`);
  card.style.setProperty('--swipe-return-tilt', `${tilt}deg`);
  card.classList.add('returning');

  returnTimer = setTimeout(() => {
    card.classList.remove('returning');
    resetSwipeState(card);
  }, RETURN_ANIMATION_MS);
};

onMounted(() => {
  const card = cardRef.value;

  // Skip initializing Hammer.js for archived chores view
  if (props.isArchivedView) {
    return;
  }
  
  // Initialize Hammer.js with horizontal swipes while preserving vertical scrolling
  hammer = new Hammer(card, { touchAction: 'pan-y' });
  hammer.get('pan').set({ direction: Hammer.DIRECTION_HORIZONTAL, threshold: 5 });
  
  // Pan start - capture initial position and reset state
  hammer.on('panstart', (event) => {
    if (choreStore.isDoneToday(props.chore) || isEditModeActive()) return;
    
    // Cancel any return animation before starting a fresh gesture
    resetSwipeState(card);
    
    // Store initial Y position to detect scrolling direction
    initialY = event.center.y;
    isScrolling = false;
    card.classList.add('swiping');
  });
  
  // Handle panning to left (for edit)
  hammer.on('panleft', (event) => {
    if (choreStore.isDoneToday(props.chore) || isEditModeActive()) return;
    
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
      applySwipeTransform(card, translateX);
      
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
    if (choreStore.isDoneToday(props.chore) || isEditModeActive()) return;
    
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
      applySwipeTransform(card, translateX);
      
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
    if (choreStore.isDoneToday(props.chore) || isEditModeActive()) return;
    
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
      animateReturn(card, event.deltaX);
    }
  });
  
  // Add a handler for regular touch events to reset swipe state
  // when the user starts scrolling
  scrollHandler = () => {
    if (!isEditModeActive() && card && isRevealingAction) {
      resetSwipeState(card);
    }
  };

  document.addEventListener('scroll', scrollHandler, { passive: true });
});

onBeforeUnmount(() => {
  if (hammer) {
    hammer.destroy();
    hammer = null;
  }

  if (scrollHandler) {
    document.removeEventListener('scroll', scrollHandler);
  }

  if (returnTimer) {
    clearTimeout(returnTimer);
    returnTimer = null;
  }
});

const saveChore = async () => {
  try {
    const choreData = {
      ...props.chore,    // Preserve existing values
      ...editableChore.value,  // Merge edited values
      due_date: new Date(editableChore.value.due_date).toISOString(), // Ensure date format
      interval_days: editableChore.value.interval_days, // Ensure interval_days is updated
      is_private: editableChore.value.is_private,
      // Persist which user owns this chore when it is private, otherwise clear it.
      owner_email: editableChore.value.is_private
        ? editableChore.value.owner_email || authStore.userEmail || authStore.username || null
        : null
    };
    console.log("Saving Chore Data:", choreData);
    await choreStore.updateChore(props.chore.id, choreData);
    emit('updateChore', choreData);
    choreStore.clearEditingChore();
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
  if (choreStore.editingChoreId === props.chore.id) {
    choreStore.clearEditingChore();
  }
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
  padding: var(--space-sm) var(--space-lg);
  border-radius: 24px;
  margin-bottom: var(--space-xxs);
  box-shadow: var(--shadow-md);
  transition: transform var(--transition-normal), box-shadow var(--transition-normal), filter var(--transition-normal);
  touch-action: pan-y;
  -ms-touch-action: pan-y;
  color: var(--color-text);
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  will-change: transform, filter;
}

.chore-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  filter: saturate(1.02);
}

/* Swipe Action Containers */
.swipe-action {
  position: absolute;
  top: 0;
  height: 100%;
  width: 88px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s var(--motion-soft);
  box-shadow: 0 0 20px rgba(31, 45, 44, 0.15);
  z-index: 2;
}

.edit-action {
  right: 0;
  background: linear-gradient(135deg, #fde8d9, #f6c7ae);
  transform: translateX(100%);
}

.done-action {
  left: 0;
  background: linear-gradient(135deg, #d5f1e5, #9edfc7);
  transform: translateX(-100%);
}

/* Swipe Action Buttons */
.done-button, .edit-button {
  border: none;
  background: transparent;
  color: #0f1b1a;
  font-size: 1.5rem;
  cursor: pointer;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Reveal states */
.chore-card.swipe-reveal-left .edit-action {
  transform: translateX(0);
}

.chore-card.swipe-reveal-right .done-action {
  transform: translateX(0);
}

/* Animation states */
.chore-card.swipe-left {
  transform: translateX(-100px);
  opacity: 0.9;
  transition: transform 0.32s var(--motion-emphasized), opacity 0.32s var(--motion-emphasized);
}

.chore-card.swipe-right {
  transform: translateX(100px);
  opacity: 0.9;
  transition: transform 0.32s var(--motion-emphasized), opacity 0.32s var(--motion-emphasized);
}

.chore-card.swiping {
  transition: none;
  box-shadow: var(--shadow-lg);
  filter: saturate(1.05);
}

.chore-card.returning {
  animation: return-snap var(--swipe-return-duration) var(--motion-rubber), return-glow 380ms ease;
}

.chore-card.returning::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 50% 50%, var(--swipe-return-highlight) 0%, transparent 55%);
  opacity: 0.12;
  pointer-events: none;
  mix-blend-mode: screen;
  animation: return-highlight var(--swipe-return-duration) ease;
}

.chore-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-sm);
  min-height: 2.6rem;
  flex-wrap: wrap;
  z-index: 1;
}

.chore-title {
  font-weight: 700;
  font-size: clamp(0.95rem, 1.5vw, 1.05rem);
  letter-spacing: 0.01em;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: normal;
  word-break: break-word;
}

.chore-right {
  display: flex;
  gap: 0.4rem;
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
    font-size: 1rem;
    width: 100%;
    margin-bottom: var(--space-xxs);
  }
  
  .chore-right {
    width: 100%;
    justify-content: space-between;
  }
  
  .chore-card {
    padding: var(--space-sm) var(--space-md);
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
  font-size: 0.85rem;
  padding: 0.2em 0.65em;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.65);
  line-height: 1.4;
  color: var(--color-text);
  box-shadow: var(--shadow-sm);
}

.chore-interval {
  font-size: 0.85rem;
  font-weight: 700;
  background: rgba(0, 0, 0, 0.06);
  padding: 0.2em 0.8em;
  border-radius: 12px;
  line-height: 1.4;
  color: var(--color-text);
  border: 1px solid rgba(0, 0, 0, 0.06);
  min-width: 38px;
  text-align: center;
}

.chore-overdue {
  font-weight: 800;
  color: #8d1f1f;
  background: rgba(255, 162, 150, 0.3);
}

.edit-chore-form {
  background: var(--color-surface);
  padding: 0;
  border-radius: var(--radius-lg);
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
  background: rgba(0, 0, 0, 0.06);
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
  box-shadow: 0 0 0 2px rgba(47, 111, 111, 0.2);
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
  color: #fdfbf7;
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
  color: #3b2b1a;
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
.chore-card.overdue { background: linear-gradient(135deg, #fde4e0, #f7b4ae); }
.chore-card.due-today { background: linear-gradient(135deg, #fde8d9, #f6c7ae); }
.chore-card.due-tomorrow { background: linear-gradient(135deg, #f8efdc, #f2ddba); }
.chore-card.due-2-days { background: linear-gradient(135deg, #f6f2e4, #eee7c9); }
.chore-card.due-3-days { background: linear-gradient(135deg, #eef3e9, #e2e6d2); }
.chore-card.due-7-days { background: linear-gradient(135deg, #e8f4ec, #d3ead8); }
.chore-card.due-14-days { background: linear-gradient(135deg, #e5f4ef, #c6e7dc); }
.chore-card.due-30-days { background: linear-gradient(135deg, #def2ed, #b7e1d7); }
.chore-card.due-far-future { background: linear-gradient(135deg, #d5f1ed, #a4dcd3); }
.chore-card.archived { background: linear-gradient(135deg, #eef0f3, #d6d8dc); }

/* Add done today state */
.chore-card.done-today {
  position: relative;
  opacity: 0.72;
  filter: saturate(0.85);
  pointer-events: none;
}

.chore-card.done-today .chore-content {
  text-decoration: line-through;
  text-decoration-color: rgba(31, 45, 44, 0.45);
}

.chore-card.done-today::after {
  content: "✓ Done today";
  position: absolute;
  top: 50%;
  right: var(--space-md);
  transform: translateY(-50%);
  font-size: 0.82rem;
  color: var(--color-text);
  background: rgba(255, 255, 255, 0.75);
  padding: 0.25em 0.65em;
  border-radius: 14px;
  pointer-events: none;
  border: 1px solid rgba(0, 0, 0, 0.06);
}

/* Add private chore state */
.chore-card.private-chore {
  border-left: 4px solid #e1b85f;
  background: linear-gradient(90deg, rgba(255, 230, 180, 0.45), transparent 60%);
}

/* Visual hint for mobile swipe */
@media (max-width: 767px) {
  .chore-card {
    --swipe-return-duration: 520ms;
  }

  .chore-card.swiping {
    filter: saturate(1.08);
  }
}

@keyframes return-snap {
  0% {
    transform: translateX(var(--swipe-return-distance, 0px)) rotate(var(--swipe-return-tilt, 0deg));
  }
  60% {
    transform: translateX(0) rotate(0deg);
  }
  78% {
    transform: translateX(calc(var(--swipe-return-distance, 0px) * -0.16));
  }
  92% {
    transform: translateX(calc(var(--swipe-return-distance, 0px) * 0.08));
  }
  100% {
    transform: translateX(0) rotate(0deg);
  }
}

@keyframes return-glow {
  0% {
    box-shadow: var(--shadow-lg);
    filter: saturate(1.08);
  }
  100% {
    box-shadow: var(--shadow-md);
    filter: saturate(1);
  }
}

@keyframes return-highlight {
  0% {
    opacity: 0.18;
    transform: scale(1);
  }
  70% {
    opacity: 0.06;
    transform: scale(1.05);
  }
  100% {
    opacity: 0;
    transform: scale(1.12);
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
  50% { transform: scale(1.08); }
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
  pointer-events: none;
  overflow: hidden;
  margin-bottom: 0;
}

.chore-card.archived-view::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(214, 216, 220, 0.4);
  z-index: 10;
}
</style>
