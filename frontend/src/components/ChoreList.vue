<template>
  <div class="chore-list" ref="choreListContainer">
    <div class="filter-pills">
      <button
        v-for="pill in pillsWithCounts"
        :key="pill.value"
        :class="['pill', { active: filter === pill.value }]"
        :style="{ 'background-color': pill.color }"
        @click="filter = pill.value"
        :aria-label="pill.label"
      >
        <span class="pill-count">{{ pill.count }}</span>
        {{ pill.label }}
      </button>
    </div>
    
    <!-- Transition group for chore cards -->
    <transition-group name="list" tag="div" class="chore-cards">
      <ChoreCard
        v-for="(chore, index) in filteredChores"
        :key="`chore-${chore.id}-${index}`"
        :chore="chore"
        @markAsDone="markAsDone"
        @archiveChore="archiveChore"
        @updateChore="updateChore"
      />
    </transition-group>

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

    <!-- Empty States -->
    <EmptyState 
      v-if="filteredChores.length === 0 && searchQuery" 
      type="search" 
      title="No matching chores found" 
      message="Try adjusting your search terms or clear the search to see all chores."
      buttonText="Clear Search"
      buttonIcon="fas fa-times"
      @action="clearSearch"
    />
    
    <EmptyState 
      v-else-if="filteredChores.length === 0 && filter !== 'all'" 
      type="filtered" 
      title="No chores match your filter" 
      message="Try selecting a different filter or clear all filters to see all your chores."
      buttonText="Clear Filters"
      buttonIcon="fas fa-filter"
      @action="clearFilters"
    />
    
    <EmptyState 
      v-else-if="choreStore.sortedByUrgency.length === 0" 
      type="chores" 
      title="No chores yet" 
      message="Add your first chore to get started managing your tasks."
      buttonText="Add New Chore" 
      buttonIcon="fas fa-plus"
      @action="addNewChore"
    />
    
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
</template>

<script setup>
import { computed, onMounted, ref, nextTick, onUnmounted } from 'vue';
import { useChoreStore } from '@/store/choreStore';
import { bucketChores } from '@/utils/choreBuckets';
import ChoreCard from './ChoreCard.vue';
import EmptyState from './EmptyState.vue';

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
const pills = [
  { label: 'All', value: 'all', color: '#3d3d3d' }, // Darker than surface-light
  { label: 'Overdue', value: 'overdue', color: 'var(--color-overdue)' },
  { label: 'Due Today', value: 'today', color: 'var(--color-due-today)' },
  { label: 'Due Tomorrow', value: 'tomorrow', color: 'var(--color-due-soon)' },
  { label: 'Due This Week', value: 'thisWeek', color: 'var(--color-due-7-days)' },
  { label: 'Later', value: 'upcoming', color: '#4db6ac' }, // Using the due-far-future teal color
];
// Keep filters and counts in sync by deriving both from the same bucketed set
const bucketedChores = computed(() => bucketChores(choreStore.sortedByUrgency));

// Watch for scroll events to show/hide scroll to top button
const handleScroll = () => {
  if (choreListContainer.value) {
    showScrollToTop.value = window.scrollY > 300;
  }
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
  const counts = bucketedChores.value.counts;
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
};

const addNewChore = () => {
  // Emit an event to add a new chore
  const event = new CustomEvent('showAddChoreForm');
  window.dispatchEvent(event);
};
</script>

<style scoped>
.chore-list {
  padding: var(--space-xs); /* Reduced padding */
  background-color: #121212;
  max-width: 1200px;
  margin: 0 auto;
  color: rgba(255, 255, 255, 0.95);
  position: relative; /* Needed for absolute positioning of scroll-to-top button */
  min-height: 80vh; /* Ensure we have space even when few chores */
}

/* Enhance text styling for headers */
h2 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
}

.log-section {
  margin-top: 2rem;
  background: #1a1a1a;
  padding: 1rem;
  border-radius: 10px;
}

.log-section h2 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.log-section ul {
  list-style: none;
  padding: 0;
}

.log-section li {
  padding: 0.5rem 0.8rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 0.9rem;
  line-height: 1.4;
}

.log-section li strong {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  margin-right: 0.5em;
}

.chore-cards {
  display: grid;
  gap: var(--space-xxs);
  grid-template-columns: 1fr; /* Base is single column */
  padding: var(--space-xxs);
}

@media (min-width: 768px) {
  .chore-cards {
    grid-template-columns: repeat(2, 1fr); /* Two columns on tablets */
    gap: var(--space-xs);
  }
}

@media (min-width: 1200px) {
  .chore-cards {
    grid-template-columns: repeat(3, 1fr); /* Three columns on larger screens */
    gap: var(--space-sm);
  }
}

/* Transition Group Animations */
.list-enter-active, .list-leave-active {
  transition: all 0.3s ease;
}
.list-enter-from, .list-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.filter-pills {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  justify-content: center; /* Always centered regardless of screen size */
  width: 100%; /* Take full width of parent */
}

.pill {
  position: relative;
  background: var(--color-surface-light);
  color: var(--color-text);
  border: none;
  border-radius: 999px;
  padding: 0.4em 1.2em 0.4em 2.2em;
  font-size: 0.95em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
  margin-bottom: 0.3rem;
  color: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
}

.pill .pill-count {
  position: absolute;
  left: 0.5em;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.25);
  color: white;
  font-size: 0.8em;
  font-weight: 600;
  border-radius: 50%;
  width: 1.6em;
  height: 1.6em;
  min-width: 1.6em;
}

.pill:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

@media (max-width: 576px) {
  .filter-pills {
    justify-content: center; /* Keep centered on small screens too */
    padding-bottom: 0.5rem;
    overflow-x: auto;
    scrollbar-width: thin;
    -webkit-overflow-scrolling: touch;
  }
  
  .pill {
    font-size: 0.85em;
    padding: 0.3em 0.9em 0.3em 2em;
    white-space: nowrap;
  }
  
  .pill .pill-count {
    font-size: 0.75em;
    width: 1.5em;
    height: 1.5em;
  }
}

.pill.active {
  /* Override background with custom background from the pill when active, but add white text */
  color: #fff !important;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

.pill.active .pill-count {
  background: rgba(255, 255, 255, 0.25);
  color: rgba(0, 0, 0, 0.8);
}

/* Add styling for scroll to top button */
.scroll-to-top-button {
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background-color: rgba(74, 85, 104, 0.9);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 9999; /* Very high z-index to ensure it's above all content */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  transition: background-color 0.2s, transform 0.2s;
}

.scroll-to-top-button:hover {
  background-color: rgba(74, 85, 104, 1);
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
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  height: 90px; /* Increased fixed height to prevent layout shifts */
  margin-bottom: 20px; /* Increased margin for more space */
  opacity: 1;
  transition: opacity 0.4s ease, visibility 0.4s ease; /* Smoother transition */
  visibility: visible;
}

/* Hidden state that maintains layout */
.loading-indicator-hidden {
  height: 90px; /* Same height as visible state */
  visibility: hidden;
  opacity: 0;
  margin-bottom: 20px; /* Same margin as visible state */
  transition: opacity 0.4s ease, visibility 0.4s ease; /* Smoother transition */
}

.loading-spinner {
  width: 30px;
  height: 30px;
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
