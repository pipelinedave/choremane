<template>
  <div class="modal-overlay" role="dialog" aria-modal="true" aria-label="Notification Settings" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h2 id="notif-title">Notification Settings</h2>
        <button class="close-button" @click="$emit('close')" aria-label="Close dialog">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="modal-body">
        <div class="checkbox-wrapper">
          <input type="checkbox" id="enable-notif" v-model="enabled" @change="onToggleNotifications" aria-checked="enabled" aria-label="Enable push notifications" />
          <label for="enable-notif">Enable Push Notifications</label>
        </div>
        
        <div v-if="enabled" class="times-section">
          <div v-for="(time, idx) in times" :key="idx" class="time-input-group">
            <label>Notification Time:</label>
            <div class="time-controls">
              <input type="time" v-model="times[idx]" aria-label="Notification time" />
              <button type="button" class="danger-button" @click="removeTime(idx)" aria-label="Remove notification time">
                <i class="fas fa-trash-alt"></i>
              </button>
            </div>
          </div>
          <button type="button" class="action-button add-time-button" @click="addTime" aria-label="Add notification time">
            <i class="fas fa-plus"></i> Add Time
          </button>
        </div>
      </div>
      <div class="modal-footer">
        <button class="save-button" @click="$emit('close')" aria-label="Save notification settings">Save & Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';

const NOTIF_KEY = 'notificationSettings';
const enabled = ref(false);
const times = ref(["09:00"]);

onMounted(() => {
  const saved = localStorage.getItem(NOTIF_KEY);
  if (saved) {
    const parsed = JSON.parse(saved);
    enabled.value = parsed.enabled;
    times.value = parsed.times || ["09:00"];
  }
});

watch([enabled, times], () => {
  localStorage.setItem(NOTIF_KEY, JSON.stringify({ enabled: enabled.value, times: times.value }));
});

const addTime = () => {
  times.value.push("12:00");
};
const removeTime = (idx) => {
  times.value.splice(idx, 1);
};

const onToggleNotifications = async () => {
  if (enabled.value && 'Notification' in window) {
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      enabled.value = false;
      alert('Notification permission denied.');
    }
  }
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  backdrop-filter: blur(2px);
}

.modal-content {
  background: var(--color-surface);
  color: var(--color-text);
  border-radius: var(--radius-md);
  min-width: 280px;
  width: 100%;
  max-width: 500px;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  background: var(--color-surface-light);
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--color-surface-lighter);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.close-button {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0.25rem;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color var(--transition-fast), color var(--transition-fast);
}

.close-button:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--color-text);
  transform: none;
}

.modal-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.modal-footer {
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid var(--color-surface-lighter);
  gap: 0.75rem;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.checkbox-wrapper input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--color-primary);
}

.times-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 0.5rem;
}

.time-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background: var(--color-surface-light);
  padding: 0.75rem;
  border-radius: var(--radius-sm);
}

.time-controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.time-controls input[type="time"] {
  flex: 1;
  padding: 0.5rem;
}

.action-button {
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  background: var(--color-surface-light);
  color: var(--color-text);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: background-color var(--transition-fast);
}

.action-button:hover {
  background: var(--color-surface-lighter);
  transform: none;
}

.danger-button {
  background: var(--color-danger);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  padding: 0.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color var(--transition-fast);
}

.danger-button:hover {
  background: var(--color-danger-hover);
  transform: none;
}

.add-time-button {
  background: var(--color-primary);
  color: white;
}

.add-time-button:hover {
  background: var(--color-primary-hover);
}

.primary-button {
  background: var(--color-surface-light);
  color: var(--color-text);
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-sm);
  border: none;
  cursor: pointer;
  font-weight: 600;
}

.primary-button:hover {
  background: var(--color-surface-lighter);
  transform: none;
}

.save-button {
  background: var(--color-primary);
  color: white;
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-sm);
  border: none;
  cursor: pointer;
  font-weight: 600;
}

.save-button:hover {
  background: var(--color-primary-hover);
  transform: none;
}

@media (max-width: 576px) {
  .modal-content {
    max-width: 95%;
  }
  
  .modal-header, .modal-body, .modal-footer {
    padding: 1rem;
  }
  
  .time-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .action-button, .primary-button, .danger-button {
    width: 100%;
  }
}
</style>
