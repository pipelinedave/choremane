import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useLogStore = defineStore('logs', () => {
  const logEntries = ref([
    { id: 1, message: "Dummy log: Initialized application", timestamp: new Date().toLocaleTimeString() }
  ]);

  const addLogEntry = (message) => {
    const newEntry = {
      id: Date.now(),
      message,
      timestamp: new Date().toLocaleTimeString()
    };
    logEntries.value.unshift(newEntry);
  };

  return { logEntries, addLogEntry };
});
