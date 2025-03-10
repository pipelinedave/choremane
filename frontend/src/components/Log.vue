<template>
  <div :class="['log-overlay', { expanded }]">
    <div class="handle" @click="toggleExpand">
      <!-- Drag handle indicator -->
      <div class="handle-bar"></div>
    </div>
    <div class="log-content">
      <div v-if="!expanded">
        <strong>Latest:</strong> {{ latestLog }}
      </div>
      <div v-else>
        <div v-for="entry in logEntries" :key="entry.id" class="log-entry">
          <small>{{ entry.timestamp }}</small>
          <div>{{ entry.message }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useLogStore } from '@/store/logStore';

const expanded = ref(false);
const logStore = useLogStore();

const toggleExpand = () => {
  expanded.value = !expanded.value;
};

const logEntries = computed(() => logStore.logEntries);
const latestLog = computed(() => (logStore.logEntries[0] ? logStore.logEntries[0].message : 'No actions yet'));
</script>

<style scoped>
.log-overlay {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #333;
  color: #fff;
  box-shadow: 0 -4px 8px rgba(0,0,0,0.1);
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
  transition: transform 0.3s ease-in-out;
  transform: translateY(calc(100% - 56px));
  z-index: 1000;
  padding: 8px 16px 16px;
}
.log-overlay.expanded {
  transform: translateY(0);
  max-height: 50vh;
  overflow-y: auto;
}
.handle {
  width: 100%;
  display: flex;
  justify-content: center;
  cursor: pointer;
}
.handle-bar {
  width: 40px;
  height: 4px;
  background: #ccc;
  border-radius: 2px;
  margin-bottom: 8px;
}
.log-entry {
  border-bottom: 1px solid #eee;
  padding: 8px 0;
}
</style>
