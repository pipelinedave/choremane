<template>
  <div ref="overlayRef" :class="['log-overlay', { expanded }]" :style="{ transform: `translateY(${translateY}px)` }"
    role="region" aria-label="Activity Log Overlay" @touchmove.stop @wheel.stop>
    <!-- Handle (hidden when expanded) -->
    <div v-show="!expanded" class="handle" ref="handleRef" @click="toggleExpand" tabindex="0" role="button"
      aria-label="Expand or collapse log overlay">
      <div class="handle-bar"></div>
      <div class="handle-content" v-if="latestEntry">
        <div class="entry-display">
          <span class="chore-pill" v-if="latestEntry.choreName">{{ latestEntry.choreName }}</span>
          <span class="action-text">{{ latestEntry.actionDescription }}</span>
          <span class="user-text" v-if="latestEntry.user">by {{ latestEntry.user }}</span>
        </div>
        <div class="handle-right">
          <span class="time-ago">{{ latestEntry.timeAgo }}</span>
          <button class="revert-btn" @click.stop="handleRevert(latestEntry)" :disabled="latestEntry.isLocal"
            :aria-label="getRevertLabel(latestEntry)" :title="getRevertLabel(latestEntry)">
            <i :class="getRevertIcon(latestEntry)"></i>
          </button>
        </div>
      </div>
      <div class="handle-content empty" v-else>
        No recent activity
      </div>
    </div>

    <!-- Expanded Header (only when expanded) -->
    <div v-show="expanded" class="expanded-header" @click="toggleExpand">
      <div class="handle-bar"></div>
      <h3>Activity Log</h3>
    </div>

    <!-- Expanded Content -->
    <div class="log-content" v-show="expanded">
      <div class="log-list" ref="logListRef">
        <div v-for="entry in visibleEntries" :key="entry.id" class="log-entry">
          <div class="entry-info">
            <div class="entry-display">
              <span class="chore-pill" v-if="entry.choreName">{{ entry.choreName }}</span>
              <span class="action-text">{{ entry.actionDescription }}</span>
              <span class="user-text" v-if="entry.user">by {{ entry.user }}</span>
            </div>
            <span class="entry-time">{{ entry.timeAgo }}</span>
          </div>
          <button class="revert-btn" @click.stop="handleRevert(entry)" :disabled="entry.isLocal"
            :aria-label="getRevertLabel(entry)" :title="getRevertLabel(entry)">
            <i :class="getRevertIcon(entry)"></i>
          </button>
        </div>
        <div v-if="logStore.loading" class="loading-indicator">
          <div class="loading-spinner"></div>
          <span>Loading...</span>
        </div>
        <div v-if="visibleEntries.length === 0 && !logStore.loading" class="empty-state">
          No activity recorded yet
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useLogStore } from '@/store/logStore';
import { useChoreStore } from '@/store/choreStore';
import api from '@/plugins/axios';

const logStore = useLogStore();
const choreStore = useChoreStore();

const expanded = ref(false);
const translateY = ref(0);
const overlayRef = ref(null);
const handleRef = ref(null);
const logListRef = ref(null);

// Touch/drag state
let startY = 0;
let startTranslateY = 0;
let isDragging = false;

const formatTimeAgo = (timestamp) => {
  if (!timestamp) return '';
  const now = new Date();
  const then = new Date(timestamp);
  const diffMs = now - then;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  return `${diffDay}d ago`;
};

// Filter out hidden entries and format for display
const visibleEntries = computed(() => {
  return logStore.logEntries
    .filter(entry => !entry.isHidden)
    .map(entry => ({
      id: entry.id,
      actionType: entry.action,
      choreName: entry.choreName,
      actionDescription: entry.actionDescription,
      user: entry.user,
      timeAgo: formatTimeAgo(entry.timestamp),
      timestamp: entry.timestamp,
      isLocal: String(entry.id).startsWith('local-'),
    }));
});

const latestEntry = computed(() => visibleEntries.value[0] || null);

const getRevertLabel = (entry) => {
  if (entry.actionType === 'created') return 'Archive';
  return 'Undo';
};

const getRevertIcon = (entry) => {
  if (entry.actionType === 'created') return 'fas fa-archive';
  return 'fas fa-undo';
};

const toggleExpand = () => {
  if (!isDragging) {
    expanded.value = !expanded.value;
    translateY.value = 0;
  }
};

const handleRevert = async (entry) => {
  if (entry.isLocal) return;
  try {
    await api.post('/undo', { log_id: entry.id });
    await choreStore.fetchChores();
    await choreStore.fetchChoreCounts();
    await logStore.fetchLogs();
  } catch (e) {
    console.error('Failed to revert action:', e);
  }
};

// Touch handlers for dragging
const onTouchStart = (e) => {
  const target = e.target;
  // Only allow drag from handle area
  if (!handleRef.value?.contains(target) && !overlayRef.value?.querySelector('.expanded-header')?.contains(target)) return;
  startY = e.touches[0].clientY;
  startTranslateY = translateY.value;
  isDragging = false;
};

const onTouchMove = (e) => {
  if (startY === 0) return;
  const currentY = e.touches[0].clientY;
  const diff = currentY - startY;
  if (Math.abs(diff) > 10) {
    isDragging = true;
    translateY.value = startTranslateY + diff;
  }
};

const onTouchEnd = () => {
  if (isDragging) {
    if (translateY.value < -50) {
      expanded.value = true;
    } else if (translateY.value > 50) {
      expanded.value = false;
    }
  }
  translateY.value = 0;
  startY = 0;
  setTimeout(() => { isDragging = false; }, 50);
};

onMounted(() => {
  logStore.fetchLogs();
  document.addEventListener('touchstart', onTouchStart, { passive: true });
  document.addEventListener('touchmove', onTouchMove, { passive: true });
  document.addEventListener('touchend', onTouchEnd);
});

onUnmounted(() => {
  document.removeEventListener('touchstart', onTouchStart);
  document.removeEventListener('touchmove', onTouchMove);
  document.removeEventListener('touchend', onTouchEnd);
});
</script>

<style scoped>
.log-overlay {
  position: fixed;
  bottom: 0;
  left: var(--spacing-md, 16px);
  right: var(--spacing-md, 16px);
  max-width: 1200px;
  margin: 0 auto;
  background: var(--color-background, #f5f0e8);
  background-image:
    radial-gradient(120% 160% at 10% 90%, rgba(253, 232, 213, 0.5) 0%, rgba(253, 232, 213, 0) 45%),
    radial-gradient(90% 120% at 90% 80%, rgba(189, 233, 221, 0.5) 0%, rgba(189, 233, 221, 0) 52%);
  color: var(--color-text, #2d3b38);
  box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.15);
  border-top-left-radius: var(--radius-lg, 20px);
  border-top-right-radius: var(--radius-lg, 20px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-bottom: none;
  transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1),
    max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1000;
  max-height: 80px;
  overflow: hidden;
}

.log-overlay.expanded {
  max-height: 70vh;
  overflow: hidden;
}

.handle,
.expanded-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 16px 8px;
  cursor: pointer;
  user-select: none;
}

.expanded-header {
  border-bottom: 1px solid var(--color-surface-lighter, rgba(0, 0, 0, 0.08));
  padding-bottom: 12px;
}

.expanded-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text, #2d3b38);
}

.handle-bar {
  width: 40px;
  height: 4px;
  background: var(--color-surface-lighter, rgba(0, 0, 0, 0.15));
  border-radius: 2px;
  margin-bottom: 8px;
}

.handle-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 12px;
}

.handle-content.empty {
  justify-content: center;
  color: var(--color-text-muted, #6b7c78);
  font-size: 0.9rem;
}

.handle-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.entry-display {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
}

.chore-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  background: var(--color-primary, #2ecc71);
  color: white;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  white-space: nowrap;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.action-text {
  font-size: 0.85rem;
  color: var(--color-text, #2d3b38);
}

.user-text {
  font-size: 0.8rem;
  color: var(--color-text-muted, #6b7c78);
}

.time-ago {
  color: var(--color-text-muted, #6b7c78);
  font-size: 0.75rem;
  flex-shrink: 0;
}

.log-content {
  padding: 0 16px 16px;
  max-height: calc(70vh - 60px);
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: var(--color-surface-lighter, rgba(0, 0, 0, 0.1)) transparent;
}

.log-content::-webkit-scrollbar {
  width: 6px;
}

.log-content::-webkit-scrollbar-track {
  background: transparent;
}

.log-content::-webkit-scrollbar-thumb {
  background-color: var(--color-surface-lighter, rgba(0, 0, 0, 0.15));
  border-radius: 20px;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.log-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-surface-lighter, rgba(0, 0, 0, 0.08));
  gap: 12px;
}

.log-entry:last-child {
  border-bottom: none;
}

.entry-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.entry-time {
  color: var(--color-text-muted, #6b7c78);
  font-size: 0.75rem;
}

.revert-btn {
  width: 40px;
  height: 40px;
  min-width: 40px;
  border-radius: var(--radius-md, 12px);
  border: 1px solid var(--color-surface-lighter, rgba(0, 0, 0, 0.1));
  background: var(--color-surface-light, rgba(255, 255, 255, 0.6));
  color: var(--color-text, #2d3b38);
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm, 0 1px 3px rgba(0, 0, 0, 0.1));
}

.revert-btn:hover:not(:disabled) {
  background: var(--color-surface, #fff);
  box-shadow: var(--shadow-md, 0 4px 6px rgba(0, 0, 0, 0.1));
  transform: translateY(-2px);
  color: var(--color-primary, #2ecc71);
}

.revert-btn:active:not(:disabled) {
  transform: scale(0.95);
  background: var(--color-primary, #2ecc71);
  color: white;
}

.revert-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background: var(--color-surface-lighter, rgba(0, 0, 0, 0.05));
}

.loading-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1rem 0;
  color: var(--color-text-muted, #6b7c78);
  font-size: 0.9rem;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  margin-bottom: 0.5rem;
  border: 3px solid var(--color-surface-lighter, rgba(0, 0, 0, 0.1));
  border-radius: 50%;
  border-top-color: var(--color-primary, #2ecc71);
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  text-align: center;
  padding: 2rem 1rem;
  color: var(--color-text-muted, #6b7c78);
}
</style>
