import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '@/plugins/axios';

const MAX_ENTRIES = 100;

const normalizeDetails = (rawDetails) => {
  if (!rawDetails) return {};
  if (typeof rawDetails === 'string') {
    try {
      return JSON.parse(rawDetails);
    } catch (error) {
      console.warn('Unable to parse log action_details string, returning raw value');
      return { raw: rawDetails };
    }
  }
  return rawDetails;
};

const getChoreLabel = (details, entry) => {
  if (details?.name) return details.name;
  if (details?.previous_state?.name) return details.previous_state.name;
  // For undo entries, try to get the original chore name from nested details
  if (details?.action_type && details?.undone) {
    // This is an undo entry - return null to hide it
    return null;
  }
  if (entry?.chore_id) return null; // Will be filtered out
  return null;
};

const getActionDescription = (action, details, entry) => {
  switch (action) {
    case 'marked_done':
      return 'marked done';
    case 'created':
      return 'created';
    case 'updated':
      return 'updated';
    case 'archived':
      return 'archived';
    case 'unarchived':
      return 'restored';
    case 'undo':
      return null; // Hide undo entries
    case 'import':
      return `imported (${details?.imported_chores?.length || 0} chores)`;
    case 'export':
      return `exported (${details?.chore_count || 0} chores)`;
    default:
      return action || 'activity';
  }
};

const normalizeEntry = (entry) => {
  const details = normalizeDetails(entry?.action_details || entry?.details);
  const action = entry?.action_type || details?.action_type || null;
  const timestamp = entry?.done_at || new Date().toISOString();
  const choreName = getChoreLabel(details, entry);
  const actionDescription = getActionDescription(action, details, entry);
  const user = entry?.done_by || null;

  return {
    id: entry?.id || `local-${Date.now()}`,
    action,
    choreName,
    actionDescription,
    user,
    timestamp,
    raw: entry,
    // Hide undo entries and entries without chore names
    isHidden: action === 'undo' || (!choreName && action !== 'import' && action !== 'export'),
  };
};


export const useLogStore = defineStore('logs', () => {
  const logEntries = ref([]);
  const loading = ref(false);
  const error = ref(null);

  const fetchLogs = async () => {
    loading.value = true;
    error.value = null;
    try {
      const { data } = await api.get('/logs');
      logEntries.value = (data || []).map(normalizeEntry).slice(0, MAX_ENTRIES);
    } catch (err) {
      console.error('Error fetching logs from server:', err);
      error.value = 'Unable to load activity logs right now.';
    } finally {
      loading.value = false;
    }
  };

  const addLocalLogEntry = (message, action = null) => {
    const newEntry = {
      id: `local-${Date.now()}`,
      action,
      message,
      timestamp: new Date().toISOString(),
    };
    logEntries.value.unshift(newEntry);
    if (logEntries.value.length > MAX_ENTRIES) {
      logEntries.value = logEntries.value.slice(0, MAX_ENTRIES);
    }
  };

  return { logEntries, loading, error, fetchLogs, addLocalLogEntry };
});
