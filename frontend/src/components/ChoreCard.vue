<template>
  <div class="chore-card-wrapper">
    <!-- Swipe Background Layer (Gmail Style) -->
    <div 
      class="swipe-background"
      :style="backgroundStyle"
    >
      <div class="action-icon icon-left" :style="leftIconStyle">
        <i class="fas fa-check"></i>
      </div>
      <div class="action-icon icon-right" :style="rightIconStyle">
        <i class="fas fa-edit"></i>
      </div>
    </div>

    <!-- Sliding Surface -->
    <div
      class="chore-card"
      :style="{ transform: isSwiping || isReturning ? `translateX(${swipeOffset}px)` : '' }"
      :class="[
        choreClass(chore),
        {
          'edit-mode': editMode,
          'done-today': choreStore.isDoneToday(chore),
          'private-chore': chore.is_private,
          'archived-view': isArchivedView,
          'swiping': isSwiping,
          'returning': isReturning
        }
      ]"
      :id="`chore-card-${chore.id}`"
      ref="cardRef"
      @dblclick="handleDblClick"
      @pointerdown="handlePointerDown"
      @pointermove="handlePointerMove"
      @pointerup="handlePointerUp"
      @pointercancel="handlePointerCancel"
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
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue';
import { useChoreStore } from '@/store/choreStore';
import { useAuthStore } from '@/store/authStore';

const props = defineProps(['chore', 'isArchivedView']);
const emit = defineEmits(['markAsDone', 'updateChore', 'archiveChore']);

const choreStore = useChoreStore();
const authStore = useAuthStore();

const editMode = ref(false);
const editableChore = ref({ ...props.chore });
const cardRef = ref(null);

// Swipe constants
const MIN_SWIPE_DISTANCE = 40;
const SWIPE_THRESHOLD = 80;
const MAX_RETURN_TILT = 8;
const MAX_RETURN_DISTANCE = 140;
const RETURN_ANIMATION_MS = 480;

// Swipe State
const isSwiping = ref(false);
const isReturning = ref(false);
const swipeOffset = ref(0);

// Visual Computeds
const swipeThresholdPct = computed(() => Math.min(1, Math.abs(swipeOffset.value) / SWIPE_THRESHOLD));

const leftIconStyle = computed(() => {
  // Left Icon (Done/Check) - Visible when dragging Right (offset > 0)
  if (swipeOffset.value <= 0) return { opacity: 0, transform: 'scale(0.8)' };
  const scale = 0.8 + (swipeThresholdPct.value * 0.4); // 0.8 -> 1.2
  return {
    opacity: Math.min(1, swipeThresholdPct.value * 1.5), // Fade in faster
    transform: `scale(${scale})`
  };
});

const rightIconStyle = computed(() => {
  // Right Icon (Edit/Pencil) - Visible when dragging Left (offset < 0)
  if (swipeOffset.value >= 0) return { opacity: 0, transform: 'scale(0.8)' };
  const scale = 0.8 + (swipeThresholdPct.value * 0.4);
  return {
    opacity: Math.min(1, swipeThresholdPct.value * 1.5),
    transform: `scale(${scale})`
  };
});

const backgroundStyle = computed(() => {
  if (swipeOffset.value === 0) return {};
  // Use theme variables for colors
  const colorDone = 'var(--color-primary)';   // Teal for Done
  const colorEdit = 'var(--color-warning)';   // Amber for Edit
  
  return {
    backgroundColor: swipeOffset.value > 0 ? colorDone : colorEdit
  };
});

// Pointer tracking
let startX = 0;
let startY = 0;
let currentX = 0;
let isGestureActive = false;
let isScrollLocked = false;
let isSwipeLocked = false;

const isEditModeActive = () => choreStore.editingChoreId === props.chore.id || editMode.value;

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

/* --- Pointer Event Handlers for Swipe --- */

const handlePointerDown = (e) => {
  if (choreStore.isDoneToday(props.chore) || isEditModeActive() || props.isArchivedView) return;
  if (!e.isPrimary) return;

  isGestureActive = true;
  isScrollLocked = false;
  isSwipeLocked = false;
  startX = e.clientX;
  startY = e.clientY;
  currentX = e.clientX;
  isReturning.value = false;
  e.target.setPointerCapture(e.pointerId);
};

const handlePointerMove = (e) => {
  if (!isGestureActive) return;

  const dx = e.clientX - startX;
  const dy = e.clientY - startY;

  if (isScrollLocked) return;

  if (!isSwipeLocked) {
    const absDx = Math.abs(dx);
    const absDy = Math.abs(dy);
    const DISTANCE_THRESHOLD = 5;

    if (absDx < DISTANCE_THRESHOLD && absDy < DISTANCE_THRESHOLD) return;

    if (absDy > absDx) {
      isScrollLocked = true;
      isGestureActive = false;
      return;
    } else {
      isSwipeLocked = true;
      isSwiping.value = true;
    }
  }

  if (isSwipeLocked) {
    if (e.cancelable) e.preventDefault();
    currentX = e.clientX;
    const rawOffset = currentX - startX;
    // Limit dist? Gmail allows pulling quite far.
    swipeOffset.value = Math.max(-MAX_RETURN_DISTANCE * 1.5, Math.min(MAX_RETURN_DISTANCE * 1.5, rawOffset));
  }
};

const handlePointerUp = (e) => {
  if (!isGestureActive) return;
  endGesture();
  e.target.releasePointerCapture(e.pointerId);
};

const handlePointerCancel = (e) => {
  if (!isGestureActive) return;
  endGesture();
  e.target.releasePointerCapture(e.pointerId);
};

const endGesture = () => {
    isGestureActive = false;
    isSwiping.value = false;
    
    if (isSwipeLocked && Math.abs(swipeOffset.value) > SWIPE_THRESHOLD) {
        if (swipeOffset.value < 0) {
             // Dragged Left -> Edit (Orange)
             triggerEdit(); 
        } else {
             // Dragged Right -> Done (Green)
             triggerDone(); 
        }
    } else {
        animateReturn();
    }
    
    isScrollLocked = false;
    isSwipeLocked = false;
};

const triggerEdit = () => {
    enterEditMode(); // This will clear swipe UI immediately via reactivity usually
    // Force reset to clean up
    swipeOffset.value = 0;
    isReturning.value = false;
};

const triggerDone = () => {
    markDone();
    swipeOffset.value = 0;
    isReturning.value = false;
};

const animateReturn = () => {
    isReturning.value = true;
    swipeOffset.value = 0;
    setTimeout(() => {
        isReturning.value = false;
    }, RETURN_ANIMATION_MS);
};

const resetSwipeState = () => {
    swipeOffset.value = 0;
    isSwiping.value = false;
    isReturning.value = false;
    isGestureActive = false;
    isScrollLocked = false;
    isSwipeLocked = false;
};

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
/* Wrapper for swipe context */
.chore-card-wrapper {
  position: relative;
  /* maintain margins/padding logic of original if any external layout depended on it,
     but here we just need to contain the card */
  margin-bottom: var(--space-xxs);
  border-radius: 24px; /* match card radius */
  overflow: hidden; /* clip the background */
  /* Remove direct interactions that might conflict */
  touch-action: pan-y; 
}

/* The Background Layer (Colors + Icons) */
.swipe-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 24px;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 1.5rem;
  box-sizing: border-box;
  transition: background-color 0.2s ease;
  background-color: transparent; /* Default */
}

/* Icons on the background */
.action-icon {
  color: white; /* Icons always white on colored bg */
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  will-change: transform, opacity;
}

/* The Surface Card */
.chore-card {
  position: relative;
  z-index: 2; /* Sit on top */
  display: flex;
  flex-direction: column;
  padding: var(--space-sm) var(--space-lg);
  border-radius: 24px;
  /* margin-bottom handled by wrapper now */
  box-shadow: var(--shadow-md);
  transition: box-shadow var(--transition-normal), filter var(--transition-normal);
  background: var(--color-surface, #ffffff); /* Ensure background is opaque */
  
  /* Reset touch action here too */
  touch-action: pan-y;
  -ms-touch-action: pan-y;
  color: var(--color-text);
  overflow: hidden;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  will-change: transform;
}

/* Apply transform transition only when returning */
.chore-card.returning {
  transition: transform 0.3s var(--motion-spring);
}
/* When swiping, no transition on transform for 1:1 feel */
.chore-card.swiping {
  transition: none;
  box-shadow: var(--shadow-lg);
}

.chore-card:hover {
  /* Only hover effect if not swiping/returning to avoid jitter */
  /* transform: translateY(-2px); We might want to disable vertical hover shift to avoid conflict? */ 
  box-shadow: var(--shadow-lg);
}
/* Re-add hover transform only if we want it, but maybe safer without for now */


/* Content specific interactions */
.chore-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-sm);
  min-height: 2.6rem;
  flex-wrap: wrap;
  z-index: 1;
  pointer-events: none; /* Let clicks pass to card? No, buttons inside need events */
}
/* Re-enable pointer events for buttons if they exist */
.chore-content * {
  pointer-events: auto;
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
