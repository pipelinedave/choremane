<template>
  <div class="notification-settings-modal" role="dialog" aria-modal="true" aria-label="Notification Settings">
    <div class="modal-content">
      <h2 id="notif-title">Notification Settings</h2>
      <label>
        <input type="checkbox" v-model="enabled" @change="onToggleNotifications" aria-checked="enabled" aria-label="Enable push notifications" />
        Enable Push Notifications
      </label>
      <div v-if="enabled" class="times-section">
        <label v-for="(time, idx) in times" :key="idx">
          Notification Time:
          <input type="time" v-model="times[idx]" aria-label="Notification time" />
          <button type="button" @click="removeTime(idx)" aria-label="Remove notification time">Remove</button>
        </label>
        <button type="button" @click="addTime" aria-label="Add notification time">Add Time</button>
      </div>
      <div class="actions">
        <button @click="$emit('close')" aria-label="Close notification settings">Close</button>
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
.notification-settings-modal {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.modal-content {
  background: var(--color-surface);
  color: var(--color-text);
  padding: 2rem;
  border-radius: var(--radius-md);
  min-width: 280px;
  width: 100%;
  max-width: 500px;
  box-shadow: var(--shadow-lg);
}

.actions {
  margin-top: 1.5rem;
  text-align: right;
}

.times-section label {
  display: flex;
  align-items: center;
  gap: 0.5em;
  margin-bottom: 0.5em;
  flex-wrap: wrap;
}

@media (max-width: 576px) {
  .modal-content {
    padding: 1rem;
  }
  
  .times-section label {
    flex-direction: column;
    align-items: flex-start;
    margin-bottom: 1em;
  }
  
  .times-section button,
  .actions button {
    width: 100%;
    margin-top: 0.5em;
    padding: 0.75em;
  }
}
</style>
