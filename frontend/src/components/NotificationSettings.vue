﻿<template>
  <div class="modal-overlay" role="dialog" aria-modal="true" aria-label="Notification Settings" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h2 id="notif-title">Notification Settings</h2>
      </div>
      <div class="modal-body">
        <div class="custom-checkbox-wrapper">
          <input type="checkbox" id="enable-notif" v-model="enabled" @change="onToggleNotifications" aria-checked="enabled" aria-label="Enable push notifications" />
          <label for="enable-notif">
            <span class="checkbox-icon">
              <i v-if="enabled" class="fas fa-check"></i>
            </span>
            <span class="checkbox-text">Enable Push Notifications</span>
          </label>
        </div>
        
        <div v-if="enabled" class="times-section">
          <div v-for="(time, idx) in times" :key="idx" class="time-input-group">
            <label>Notification Time:</label>
            <div class="time-controls">
              <input type="time" v-model="times[idx]" aria-label="Notification time" />
              <button 
                v-if="times.length > 1" 
                type="button" 
                class="danger-button" 
                @click="removeTime(idx)" 
                aria-label="Remove notification time"
              >
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
        <button class="cancel-button" @click="cancelChanges" aria-label="Cancel changes">
          <i class="fas fa-times"></i> Cancel
        </button>
        <button class="save-button" @click="saveChanges" aria-label="Save notification settings">
          <i class="fas fa-save"></i> Save
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';

const NOTIF_KEY = 'notificationSettings';
const enabled = ref(false);
const times = ref(["09:00"]);
const initialSettings = ref({ enabled: false, times: ["09:00"] });

const emit = defineEmits(['close']);

onMounted(() => {
  loadSettings();
});

function loadSettings() {
  const saved = localStorage.getItem(NOTIF_KEY);
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      enabled.value = parsed.enabled;
      // Ensure times is always an array, even if it was somehow saved incorrectly
      times.value = Array.isArray(parsed.times) && parsed.times.length > 0 
        ? parsed.times 
        : ["09:00"];
      
      // Store initial settings for cancellation
      initialSettings.value = { 
        enabled: enabled.value, 
        times: [...times.value] 
      };
    } catch (e) {
      console.error("Error loading notification settings:", e);
      resetToDefaults();
    }
  } else {
    resetToDefaults();
  }
}

function resetToDefaults() {
  enabled.value = false;
  times.value = ["09:00"];
  initialSettings.value = { enabled: false, times: ["09:00"] };
}

function saveSettings() {
  try {
    localStorage.setItem(NOTIF_KEY, JSON.stringify({ 
      enabled: enabled.value, 
      times: times.value 
    }));
    // Update initial settings after saving
    initialSettings.value = { 
      enabled: enabled.value, 
      times: [...times.value] 
    };
    return true;
  } catch (e) {
    console.error("Error saving notification settings:", e);
    return false;
  }
}

const addTime = () => {
  times.value.push("12:00");
};

const removeTime = (idx) => {
  // Only remove if we have more than one time to prevent having zero times
  if (times.value.length > 1) {
    times.value.splice(idx, 1);
  }
};

const saveChanges = () => {
  const success = saveSettings();
  if (success) {
    emit('close');
  } else {
    alert('Failed to save notification settings. Please try again.');
  }
};

const cancelChanges = () => {
  // Restore the initial settings
  enabled.value = initialSettings.value.enabled;
  times.value = [...initialSettings.value.times];
  emit('close');
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

.cancel-button {
  background: var(--color-surface-light);
  color: var(--color-text);
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-sm);
  border: none;
  cursor: pointer;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.cancel-button:hover {
  background: var(--color-surface-lighter);
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
