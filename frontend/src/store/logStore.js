import { defineStore } from 'pinia';
import { ref } from 'vue';

const MAX_ENTRIES = 100;

export const useLogStore = defineStore('logs', () => {
  // Load persisted logs from localStorage if available
  const logEntries = ref([]);
  
  // Try to load logs, but don't break if the format is incompatible
  try {
    const storedLogs = localStorage.getItem('logEntries');
    if (storedLogs) {
      const parsedLogs = JSON.parse(storedLogs);
      // Validate that it's an array
      if (Array.isArray(parsedLogs)) {
        logEntries.value = parsedLogs;
      } else {
        throw new Error('Stored logs are not in array format');
      }
    } else {
      // Initialize with default log
      logEntries.value = [
        { id: 1, message: "Initialized application", timestamp: new Date().toLocaleTimeString() }
      ];
    }
  } catch (error) {
    console.error('Error loading logs from storage:', error);
    // Reset to default state
    logEntries.value = [
      { id: 1, message: "Initialized application", timestamp: new Date().toLocaleTimeString() }
    ];
  }

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
