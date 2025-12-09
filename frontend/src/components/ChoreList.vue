<template>
  <div class="chore-list" ref="choreListContainer">
    <PerformanceBar :score="choreStore.householdHealth" />

    <div class="filter-row" :class="{ 'has-filter': filter !== 'all' }">
      <!-- Clear Filters Button (fixed on left) -->
      <transition name="fade">
        <button v-if="filter !== 'all'" class="pill clear-filter-fixed" @click="clearFilters"
          aria-label="Clear filters">
          <i class="fas fa-times"></i>
        </button>
      </transition>

      <div class="filter-pills" ref="pillsContainer">
        <button v-for="pill in pillsWithCounts" :key="pill.value" ref="pillRefs"
          :class="['pill', { active: filter === pill.value }]" :style="{ 'background-color': pill.color }"
          @click="selectFilter(pill.value)" :aria-label="pill.label">
          <span class="pill-count">{{ pill.count }}</span>
          {{ pill.label }}
        </button>
      </div>
    </div>

    <!-- Transition group for chore cards -->
    <transition-group name="list" tag="div" class="chore-cards">
      <ChoreCard v-for="(chore, index) in filteredChores" :key="chore.id" :chore="chore" @markAsDone="markAsDone"
        @archiveChore="archiveChore" @updateChore="updateChore" />
    </transition-group>

    <!-- Loading indicator that shows when loading more chores -->
    <div :class="(isLoading || choreStore.loading) ? 'loading-indicator' : 'loading-indicator-hidden'"
      aria-hidden="!isLoading && !choreStore.loading">
      <div v-if="isLoading || choreStore.loading" class="loading-spinner"></div>
      <span v-if="isLoading || choreStore.loading">Loading chores...</span>
    </div>

    <!-- Element for intersection observer to detect when user scrolls to bottom -->
    <div ref="loadMoreTrigger" class="load-more-trigger"></div>

    <!-- Empty States -->
    <EmptyState v-if="filteredChores.length === 0 && searchQuery" type="search" title="No matching chores found"
      message="Try adjusting your search terms or clear the search to see all chores." buttonText="Clear Search"
      buttonIcon="fas fa-times" @action="clearSearch" />

    <EmptyState v-else-if="filteredChores.length === 0 && filter !== 'all'" type="filtered"
      title="No chores match your filter"
      message="Try selecting a different filter or clear all filters to see all your chores." buttonText="Clear Filters"
      buttonIcon="fas fa-filter" @action="clearFilters" />

    <EmptyState v-else-if="choreStore.sortedByUrgency.length === 0" type="chores" title="No chores yet"
      message="Add your first chore to get started managing your tasks." buttonText="Add New Chore"
      buttonIcon="fas fa-plus" @action="addNewChore" />

    <!-- Scroll to top button -->
    <button v-show="showScrollToTop" class="scroll-to-top-button" @click="scrollToTop" aria-label="Scroll to top">
      <i class="fas fa-arrow-up"></i>
    </button>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, nextTick, onUnmounted } from 'vue';
import { useChoreStore } from '@/store/choreStore';
import { bucketChores } from '@/utils/choreBuckets';
import ChoreCard from './ChoreCard.vue';
import EmptyState from './EmptyState.vue';
import PerformanceBar from './PerformanceBar.vue';

const choreStore = useChoreStore();
const choreListContainer = ref(null);
const loadMoreTrigger = ref(null);
const currentPage = ref(1);
const showScrollToTop = ref(false);
const observer = ref(null);
const isLoading = ref(false); // Track loading state locally
const loadingTimeout = ref(null); // For debouncing

// Reactive states
const filter = ref('all');
const searchQuery = ref('');
const pillsContainer = ref(null);
const pillRefs = ref([]);
const pills = [
  // 'All' removed as per new design
  { label: 'Overdue', value: 'overdue', color: 'var(--color-overdue)' },
  { label: 'Today', value: 'today', color: 'var(--color-due-today)' },
  { label: 'Tomorrow', value: 'tomorrow', color: 'var(--color-due-soon)' },
  { label: 'This Week', value: 'thisWeek', color: 'var(--color-due-7-days)' },
  { label: 'Later', value: 'upcoming', color: 'var(--color-due-far-future)' },
];
// Keep filters and counts in sync by deriving both from the same bucketed set
const bucketedChores = computed(() => bucketChores(choreStore.sortedByUrgency));

// Watch for scroll events to show/hide scroll to top button
const handleScroll = () => {
  if (choreListContainer.value) {
    showScrollToTop.value = window.scrollY > 300;
  }
};

const selectFilter = (value) => {
  filter.value = value;
  scrollToActivePill(value);
};

const scrollToActivePill = (value) => {
  nextTick(() => {
    if (!pillRefs.value || pillRefs.value.length === 0) return;

    const index = pills.findIndex(p => p.value === value);
    if (index !== -1 && pillRefs.value[index]) {
      pillRefs.value[index].scrollIntoView({
        behavior: 'smooth',
        inline: 'start',
        block: 'nearest'
      });
    }
  });
};

// Scroll back to top function
const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  });
};

// Initial data loading
onMounted(async () => {
  // Initial fetch
  await choreStore.fetchChores(1);

  // Set up intersection observer for infinite scrolling
  setupIntersectionObserver();

  // Add scroll event listener for scroll-to-top button
  window.addEventListener('scroll', handleScroll);
});

onUnmounted(() => {
  // Clean up event listeners and observers
  window.removeEventListener('scroll', handleScroll);
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
      if (entry.isIntersecting && choreStore.hasMoreChores && !isLoading.value) {
        loadMoreChores();
      }
    }, {
      root: null, // Use viewport as root
      rootMargin: '150px', // Increased margin to load more before reaching the end
      threshold: 0.1 // Trigger when at least 10% of the element is visible
    });

    // Start observing the trigger element
    observer.value.observe(loadMoreTrigger.value);
  }
};

// Function to load more chores for infinite scrolling
const loadMoreChores = async () => {
  // Prevent multiple concurrent loading requests
  if (isLoading.value || !choreStore.hasMoreChores) return;

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
      await choreStore.fetchChores(currentPage.value);

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

const filteredChores = computed(() => {
  const buckets = bucketedChores.value.buckets;
  return buckets[filter.value] || buckets.all;
});

const pillsWithCounts = computed(() => {
  const counts = choreStore.totalCounts;
  return pills.map(pill => ({
    ...pill,
    count: counts[pill.value] || 0,
    color: pill.color
  }));
});

const markAsDone = async (choreId) => {
  try {
    await choreStore.markChoreDone(choreId);
  } catch (error) {
    console.error(`Failed to mark chore ${choreId} as done:`, error);
  }
};

const archiveChore = async (choreId) => {
  try {
    await choreStore.archiveChore(choreId);
  } catch (error) {
    console.error(`Failed to archive chore ${choreId}:`, error);
  }
};

const updateChore = async (updatedChore) => {
  try {
    await choreStore.updateChore(updatedChore.id, updatedChore);
  } catch (error) {
    console.error('Failed to update chore:', error);
  }
};

// Add methods for the empty state actions
const clearSearch = () => {
  searchQuery.value = '';
};

const clearFilters = () => {
  filter.value = 'all';
  // Scroll container back to start
  if (pillsContainer.value) {
    pillsContainer.value.scrollTo({
      left: 0,
      behavior: 'smooth'
    });
  }
};

const addNewChore = () => {
  // Emit an event to add a new chore
  const event = new CustomEvent('showAddChoreForm');
  window.dispatchEvent(event);
};
</script>

<style scoped>
.chore-list {
  padding: var(--space-md);
  max-width: 880px;
  margin: 0 auto 120px;
  color: var(--color-text);
  position: relative;
}

.filter-row {
  display: flex;
  align-items: center;
  margin: 0 -20px var(--space-md);
  /* Negative margin to stretch full width on mobile */
  position: relative;
}

.clear-filter-fixed {
  margin-left: 1.25rem;
  /* Match side padding */
  margin-right: 0.75rem;
  /* Gap between button and list */
  padding: 0;
  width: 2.6em;
  /* Slightly larger to be an easier target */
  height: 2.6em;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  color: var(--color-text-muted);
  flex-shrink: 0;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
  z-index: 2;
  backdrop-filter: blur(12px);
}

.clear-filter-fixed:hover {
  background: #fff;
  color: var(--color-error);
  border-color: var(--color-error);
  transform: scale(1.05);
  box-shadow: var(--shadow-md);
}

.clear-filter-fixed i {
  font-size: 1.1em;
}

.filter-pills {
  display: flex;
  overflow-x: auto;
  white-space: nowrap;
  scrollbar-width: none;
  /* Firefox */
  -ms-overflow-style: none;
  /* IE 10+ */
  -webkit-overflow-scrolling: touch;
  flex: 1;
  padding-right: 1.25rem;
  /* End padding */
  padding-left: 1.25rem;
  /* Default start padding */
  padding-top: 0.5rem;
  /* Space for shadow */
  padding-bottom: 0.5rem;
  align-items: center;
  gap: 0.75rem;
  transition: padding-left 0.3s ease;
}

/* Adjust padding when filter is active (X button present) */
.filter-row.has-filter .filter-pills {
  padding-left: 0;
}

/* Hide scrollbar for Chrome/Safari/Opera */
.filter-pills::-webkit-scrollbar {
  display: none;
}

.pill {
  position: relative;
  background: rgba(255, 255, 255, 0.9);
  color: var(--color-text);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 999px;
  padding: 0.5em 1.4em 0.5em 2.4em;
  font-size: 0.95em;
  font-weight: 600;
  cursor: pointer;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast), filter var(--transition-fast), background-color 0.2s;
  outline: none;
  box-shadow: var(--shadow-sm);
  display: flex;
  align-items: center;
  backdrop-filter: blur(12px);
  flex-shrink: 0;
}

.pill .pill-count {
  position: absolute;
  left: 0.55em;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.08);
  color: var(--color-text);
  font-size: 0.8em;
  font-weight: 700;
  border-radius: 50%;
  width: 1.6em;
  height: 1.6em;
  min-width: 1.6em;
  box-shadow: var(--shadow-sm);
}

.pill:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.pill.active {
  color: #0f1b1a !important;
  font-weight: 700;
  box-shadow: var(--shadow-lg);
  filter: brightness(1.05);
}

.pill.active .pill-count {
  background: rgba(255, 255, 255, 0.7);
  color: #102321;
}

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: scale(0.8) translateX(-10px);
  margin-right: 0;
  /* Collapse gap */
}

@media (max-width: 576px) {
  .clear-filter-fixed {
    width: 2.3em;
    height: 2.3em;
  }

  .pill {
    font-size: 0.9em;
    padding: 0.35em 1em 0.35em 2.1em;
  }

  .pill .pill-count {
    font-size: 0.78em;
    width: 1.5em;
    height: 1.5em;
  }
}

.chore-cards {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: 0 var(--space-xxs);
}

/* Transition Group Animations */
.list-enter-active {
  animation: card-rise 320ms var(--motion-soft);
}

.list-leave-active {
  animation: card-fall 260ms var(--motion-emphasized) forwards;
  position: relative;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateY(14px) scale(0.98);
}

.list-move {
  transition: transform 320ms var(--motion-soft);
}

/* Add styling for scroll to top button */
.scroll-to-top-button {
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.78);
  color: var(--color-text);
  border: 1px solid rgba(255, 255, 255, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 9999;
  box-shadow: var(--shadow-lg);
  transition: background-color 0.2s, transform 0.2s;
  backdrop-filter: blur(12px);
}

.scroll-to-top-button:hover {
  background: rgba(255, 255, 255, 0.95);
  transform: translateY(-2px);
}

.scroll-to-top-button i {
  font-size: 1.2rem;
}

/* Add styling for infinite scroll loading indicator */
.loading-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1rem 0;
  color: var(--color-text-muted);
  font-size: 0.9rem;
  height: 90px;
  margin-bottom: 20px;
  opacity: 1;
  transition: opacity 0.4s ease, visibility 0.4s ease;
  visibility: visible;
}

/* Hidden state that maintains layout */
.loading-indicator-hidden {
  height: 90px;
  visibility: hidden;
  opacity: 0;
  margin-bottom: 20px;
  transition: opacity 0.4s ease, visibility 0.4s ease;
}

@keyframes card-rise {
  0% {
    opacity: 0;
    transform: translateY(12px) scale(0.98);
  }

  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes card-fall {
  0% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }

  100% {
    opacity: 0;
    transform: translateY(-10px) scale(0.98);
  }
}

.loading-spinner {
  width: 30px;
  height: 30px;
  margin-bottom: 0.5rem;
  border: 3px solid rgba(0, 0, 0, 0.1);
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

.load-more-trigger {
  height: 100px;
  margin-top: 20px;
  margin-bottom: 20px;
  visibility: hidden;
  width: 100%;
  display: block;
  position: relative;
}
</style>
