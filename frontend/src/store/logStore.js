import { defineStore } from 'pinia';
import { ref } from 'vue';

const MAX_ENTRIES = 100;

export const useLogStore = defineStore('logs', () => {
  // Load persisted logs from localStorage if available
  const storedLogs = localStorage.getItem('logEntries');
  const logEntries = ref(
    storedLogs ? JSON.parse(storedLogs) : [
      { id: 1, message: "Dummy log: Initialized application", timestamp: new Date().toLocaleTimeString() }
    ]
  );

  const persistLogs = () => {
    localStorage.setItem('logEntries', JSON.stringify(logEntries.value));
  };

  const addLogEntry = (message) => {
    const newEntry = {
      id: Date.now(),
      message,
      timestamp: new Date().toLocaleTimeString()
    };
    logEntries.value.unshift(newEntry);
    // Retain only the most recent MAX_ENTRIES logs
    if (logEntries.value.length > MAX_ENTRIES) {
      logEntries.value = logEntries.value.slice(0, MAX_ENTRIES);
    }
    persistLogs();
  };

  return { logEntries, addLogEntry };
});
