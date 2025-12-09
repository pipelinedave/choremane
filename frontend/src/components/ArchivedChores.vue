<template>
  <div class="archived-chores-modal">
    <div class="modal-overlay" role="dialog" aria-modal="true" aria-label="Archived Chores"
      @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Archived Chores</h2>
        </div>
        <div class="modal-body" ref="modalBody">
          <!-- Replace the no-archived div with EmptyState -->
          <EmptyState v-if="archivedChores.length === 0" type="archived" title="No archived chores"
            message="Archived chores will appear here once you archive them from your active chores list." />
          <div v-else class="chore-cards-archived">
            <div v-for="(chore, index) in archivedChores" :key="chore.id" class="archived-chore-container">
              <ChoreCard :chore="chore" :isArchivedView="true" @markAsDone="markAsDone" @updateChore="updateChore"
                @archiveChore="unarchiveChore" />
              <button class="unarchive-button" @click="unarchiveChore(chore.id)" aria-label="Unarchive chore"
                title="Unarchive chore">
                <i class="fas fa-undo"></i>
              </button>
            </div>
          </div>
          <!-- Loading indicator that shows when loading more chores -->
          <div :class="(isLoading || choreStore.loading) ? 'loading-indicator' : 'loading-indicator-hidden'"
            aria-hidden="!isLoading && !choreStore.loading">
            <div v-if="isLoading || choreStore.loading" class="loading-spinner"></div>
            <span v-if="isLoading || choreStore.loading">Loading chores...</span>
          </div>
          <!-- Element for intersection observer to detect when user scrolls to bottom -->
          <div ref="loadMoreTrigger" class="load-more-trigger"></div>
          <!-- Scroll to top button -->
          <button v-show="showScrollToTop" class="scroll-to-top-button" @click="scrollToTop" aria-label="Scroll to top">
            <i class="fas fa-arrow-up"></i>
          </button>
        </div>
        <div class="modal-footer">
          <button type="button" class="neutral-button" @click="$emit('close')"
            aria-label="Close archived chores dialog">
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, nextTick } from 'vue';
import { useChoreStore } from '@/store/choreStore';
import ChoreCard from './ChoreCard.vue';
import EmptyState from './EmptyState.vue';

defineEmits(['close']);

const choreStore = useChoreStore();
const modalBody = ref(null);
const loadMoreTrigger = ref(null);
const currentPage = ref(1);
const showScrollToTop = ref(false);
const observer = ref(null);
const isLoading = ref(false); // Track loading state locally
const loadingTimeout = ref(null); // For debouncing

// Get only archived chores
const archivedChores = computed(() => {
  return choreStore.sortedArchivedChores;
});

// Computed property for loading state from store
const loading = computed(() => choreStore.loading);

// Watch for scroll events to show/hide scroll to top button
const handleScroll = () => {
  if (modalBody.value) {
    showScrollToTop.value = modalBody.value.scrollTop > 300;
  }
};

// Scroll back to top function
const scrollToTop = () => {
  if (modalBody.value) {
    modalBody.value.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }
};

// Initial data loading
onMounted(async () => {
  // Initial fetch of archived chores
  await choreStore.fetchArchivedChores(1);

  // Set up intersection observer for infinite scrolling
  setupIntersectionObserver();

  // Add scroll event listener for scroll-to-top button
  if (modalBody.value) {
    modalBody.value.addEventListener('scroll', handleScroll);
  }
});

onUnmounted(() => {
  // Clean up event listeners and observers
  if (modalBody.value) {
    modalBody.value.removeEventListener('scroll', handleScroll);
  }
  if (observer.value) {
    observer.value.disconnect();
  }
  // Clear any pending timeouts
  if (loadingTimeout.value) {
    clearTimeout(loadingTimeout.value);
  }
});

// Setup intersection observer for infinite scrolling
const setupIntersectionObserver = () => {
  // Check if IntersectionObserver is available
  if ('IntersectionObserver' in window && loadMoreTrigger.value) {
    // Disconnect existing observer if any
    if (observer.value) {
      observer.value.disconnect();
    }

    // Create a new observer
    observer.value = new IntersectionObserver((entries) => {
      const entry = entries[0];
      // Load more when the trigger element is visible and we have more to load
      if (entry.isIntersecting && choreStore.hasMoreArchivedChores && !isLoading.value) {
        loadMoreArchivedChores();
      }
    }, {
      root: modalBody.value, // Use modal body as root
      rootMargin: '150px', // Increased margin to load more before reaching the end
      threshold: 0.1 // Trigger when at least 10% of the element is visible
    });

    // Start observing the trigger element
    observer.value.observe(loadMoreTrigger.value);
  }
};

// Function to load more archived chores for infinite scrolling
const loadMoreArchivedChores = async () => {
  // Prevent multiple concurrent loading requests
  if (isLoading.value || !choreStore.hasMoreArchivedChores) return;

  // Set local loading state to prevent multiple triggers
  isLoading.value = true;

  // Clear any existing timeout
  if (loadingTimeout.value) {
    clearTimeout(loadingTimeout.value);
  }

  // Debounce the loading operation with a 400ms delay to prevent rapid re-triggering
  loadingTimeout.value = setTimeout(async () => {
    try {
      currentPage.value++;
      await choreStore.fetchArchivedChores(currentPage.value);

      // Re-setup observer after content changes
      nextTick(() => {
        setupIntersectionObserver();
      });
    } finally {
      // Reset loading state after a longer cooldown period to prevent too frequent loading
      setTimeout(() => {
        isLoading.value = false;
        loadingTimeout.value = null;
      }, 700); // Longer cooldown to prevent rapid re-triggering
    }
  }, 400); // Slightly longer debounce for smoother experience
};

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
  font-family: 'Space Grotesk', 'Manrope', sans-serif;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(31, 45, 44, 0.4);
  /* Darkened surface color for overlay */
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease-out;
  overscroll-behavior: contain;
  overflow: auto;
}

.modal-content {
  width: 90%;
  max-width: 600px;
  max-height: 85vh;
  background: var(--color-background);
  /* Use app background */
  background-image:
    radial-gradient(120% 160% at 10% 10%, rgba(253, 232, 213, 0.5) 0%, rgba(253, 232, 213, 0) 45%),
    radial-gradient(90% 120% at 90% 20%, rgba(189, 233, 221, 0.5) 0%, rgba(189, 233, 221, 0) 52%);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  color: var(--color-text);
  border: 1px solid rgba(255, 255, 255, 0.6);
  animation: slideUp 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}

.modal-header {
  padding: 1.5rem 1.5rem 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--color-surface-lighter);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
}

.close-button {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-button:hover {
  background-color: var(--color-surface-lighter);
  color: var(--color-text);
}

.modal-body {
  padding: 1rem 1.5rem;
  overflow-y: auto;
  flex-grow: 1;
  position: relative;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  /* Custom Scrollbar for the modal */
  scrollbar-width: thin;
  scrollbar-color: var(--color-surface-lighter) transparent;
}

.modal-body::-webkit-scrollbar {
  width: 6px;
}

.modal-body::-webkit-scrollbar-track {
  background: transparent;
}

.modal-body::-webkit-scrollbar-thumb {
  background-color: var(--color-surface-lighter);
  border-radius: 20px;
}

.no-archived {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--color-text-muted);
}

.chore-cards-archived {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.archived-chore-container {
  display: flex;
  align-items: stretch;
  gap: var(--space-xs);
  position: relative;
  margin-bottom: var(--space-xs);
}

.archived-chore-container :deep(.chore-card) {
  flex: 1;
  width: auto;
  /* Let flex handle width */
  margin-bottom: 0;
}

.unarchive-button {
  background-color: var(--color-surface-light);
  color: var(--color-text);
  border: 1px solid var(--color-surface-lighter);
  border-radius: var(--radius-md);
  /* Match card radius roughly but for small button */
  width: 48px;
  min-width: 48px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm);
  margin-top: 2px;
  /* Slight alignment fix if needed */
}

/* Add animation for the unarchive button */
@keyframes pulse-button {
  0% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.1);
  }

  100% {
    transform: scale(1);
  }
}

.unarchive-button:active {
  animation: pulse-button 0.3s;
  background-color: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.unarchive-button:hover {
  background-color: var(--color-surface);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  color: var(--color-primary);
}

.unarchive-button i {
  font-size: 1rem;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-surface-lighter);
  display: flex;
  justify-content: flex-end;
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  border-bottom-left-radius: var(--radius-lg);
  border-bottom-right-radius: var(--radius-lg);
}

.neutral-button {
  padding: 0.6rem 1.2rem;
  background-color: var(--color-surface-light);
  color: var(--color-text);
  border: 1px solid var(--color-surface-lighter);
  border-radius: var(--radius-md);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  transition: all 0.2s;
  box-shadow: var(--shadow-sm);
}

.neutral-button:hover {
  background-color: var(--color-surface);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

/* Scroll to top button */
.scroll-to-top-button {
  position: sticky;
  bottom: 20px;
  left: 100%;
  /* Align to right */
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--color-primary);
  color: #fff;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  box-shadow: var(--shadow-md);
  transition: all 0.2s;
  opacity: 0.9;
}

.scroll-to-top-button:hover {
  background-color: var(--color-primary-hover);
  transform: translateY(-2px);
  opacity: 1;
}

.scroll-to-top-button i {
  font-size: 1rem;
}

/* Loading indicator */
.loading-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1rem 0;
  color: var(--color-text-muted);
  font-size: 0.9rem;
  height: 80px;
  margin-bottom: 20px;
  opacity: 1;
  transition: opacity 0.4s ease, visibility 0.4s ease;
  visibility: visible;
}

.loading-indicator-hidden {
  height: 80px;
  visibility: hidden;
  opacity: 0;
  margin-bottom: 20px;
  transition: opacity 0.4s ease, visibility 0.4s ease;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  margin-bottom: 0.5rem;
  border: 3px solid var(--color-surface-lighter);
  border-radius: 50%;
  border-top-color: var(--color-primary);
  animation: spin 1s ease-in-out infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.load-more-trigger {
  height: 60px;
  margin-top: 10px;
  margin-bottom: 10px;
  visibility: hidden;
  width: 100%;
  display: block;
}
</style>
