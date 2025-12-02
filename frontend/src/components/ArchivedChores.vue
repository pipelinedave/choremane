<template>
  <div class="archived-chores-modal">
    <div class="modal-overlay" role="dialog" aria-modal="true" aria-label="Archived Chores" @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Archived Chores</h2>
        </div>
        <div class="modal-body" ref="modalBody">
          <!-- Replace the no-archived div with EmptyState -->
          <EmptyState 
            v-if="archivedChores.length === 0" 
            type="archived" 
            title="No archived chores" 
            message="Archived chores will appear here once you archive them from your active chores list."
          />
          <div v-else class="chore-cards-archived">
            <div v-for="(chore, index) in archivedChores" :key="`archived-chore-${chore.id}-${index}`" class="archived-chore-container">
              <ChoreCard
                :chore="chore"
                :isArchivedView="true"
                @markAsDone="markAsDone"
                @updateChore="updateChore"
                @archiveChore="unarchiveChore"
              />
              <button 
                class="unarchive-button" 
                @click="unarchiveChore(chore.id)" 
                aria-label="Unarchive chore"
                title="Unarchive chore"
              >
                <i class="fas fa-undo"></i>
              </button>
            </div>
          </div>
          <!-- Loading indicator that shows when loading more chores -->
          <div 
            :class="(isLoading || choreStore.loading) ? 'loading-indicator' : 'loading-indicator-hidden'"
            aria-hidden="!isLoading && !choreStore.loading"
          >
            <div v-if="isLoading || choreStore.loading" class="loading-spinner"></div>
            <span v-if="isLoading || choreStore.loading">Loading chores...</span>
          </div>
          <!-- Element for intersection observer to detect when user scrolls to bottom -->
          <div ref="loadMoreTrigger" class="load-more-trigger"></div>
          <!-- Scroll to top button -->
          <button 
            v-show="showScrollToTop" 
            class="scroll-to-top-button" 
            @click="scrollToTop"
            aria-label="Scroll to top"
          >
            <i class="fas fa-arrow-up"></i>
          </button>
        </div>
        <div class="modal-footer">
          <button
            type="button"
            class="neutral-button"
            @click="$emit('close')"
            aria-label="Close archived chores dialog"
          >
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
  font-family: 'Roboto', sans-serif;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  background-color: #1e1e1e;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  color: rgba(255, 255, 255, 0.95);
}

.modal-header {
  padding: 1rem;
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 500;
}

.close-button {
  background: none;
  border: none;
  color: #999;
  font-size: 1.2rem;
  cursor: pointer;
}

.close-button:hover {
  color: #fff;
}

.modal-body {
  padding: 1rem;
  overflow-y: auto;
  flex-grow: 1;
  max-height: 60vh; /* Limit height to prevent oversized modal */
  position: relative; /* For positioning the scroll-to-top button */
}

.no-archived {
  text-align: center;
  padding: 2rem;
  color: #777;
}

.chore-cards-archived {
  display: flex;
  flex-direction: column;
  gap: 0.5rem; /* Reduced gap between items */
}

.archived-chore-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  position: relative;
  margin-bottom: 0.75rem;
}

.archived-chore-container :deep(.chore-card) {
  width: calc(100% - 40px);
  margin-bottom: 0;
}

.unarchive-button {
  background-color: #4a5568;
  color: white;
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  min-width: 36px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s, transform 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* Add animation for the unarchive button */
@keyframes pulse-button {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.unarchive-button:active {
  animation: pulse-button 0.3s;
  background-color: #4CAF50; /* Change color during animation */
}

.unarchive-button:hover {
  background-color: #647182;
  transform: scale(1.05);
}

.unarchive-button i {
  font-size: 0.9rem;
}

.modal-footer {
  padding: 1rem;
  border-top: 1px solid #333;
  display: flex;
  justify-content: flex-end;
}

.neutral-button {
  padding: 0.5rem 1rem;
  background-color: #4d4d4d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background-color 0.2s;
}

.neutral-button:hover {
  background-color: #5a5a5a;
}

/* Add styling for scroll to top button */
.scroll-to-top-button {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: rgba(74, 85, 104, 0.8);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 1000; /* Higher z-index to ensure it's above all content */
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  transition: background-color 0.2s, transform 0.2s;
}

.scroll-to-top-button:hover {
  background-color: rgba(74, 85, 104, 1);
  transform: translateY(-2px);
}

.scroll-to-top-button i {
  font-size: 1rem;
}

/* Add styling for infinite scroll loading indicator */
.loading-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1rem 0;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  height: 80px; /* Fixed height to prevent layout shifts */
  margin-bottom: 20px; /* Increased margin for more space */
  opacity: 1;
  transition: opacity 0.4s ease, visibility 0.4s ease; /* Smoother transition */
  visibility: visible;
}

/* Hidden state that maintains layout */
.loading-indicator-hidden {
  height: 80px; /* Same height as visible state */
  visibility: hidden;
  opacity: 0;
  margin-bottom: 20px; /* Same margin as visible state */
  transition: opacity 0.4s ease, visibility 0.4s ease; /* Smoother transition */
}

.loading-spinner {
  width: 24px;
  height: 24px;
  margin-bottom: 0.5rem;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
  flex-shrink: 0; /* Prevent spinner from shrinking */
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.load-more-trigger {
  height: 100px; /* Increase height to create more buffer room */
  margin-top: 20px;
  margin-bottom: 20px;
  visibility: hidden; /* Hide it but keep it in the layout */
  width: 100%; /* Ensure it takes full width */
  display: block;
  position: relative;
}
</style>
