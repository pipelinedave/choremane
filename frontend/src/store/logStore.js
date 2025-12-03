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

const choreLabel = (details, entry) => {
  if (details?.name) return details.name;
  if (details?.previous_state?.name) return details.previous_state.name;
  if (entry?.chore_id) return `Chore #${entry.chore_id}`;
  return 'Chore';
};

const buildMessage = (action, details, entry) => {
  const label = choreLabel(details, entry);
  switch (action) {
    case 'marked_done':
      return `${label} marked done${entry?.done_by ? ` by ${entry.done_by}` : ''}`;
    case 'created':
      return `Created ${label}`;
    case 'updated':
      return `Updated ${label}`;
    case 'archived':
      return `Archived ${label}`;
    case 'unarchived':
      return `Unarchived ${label}`;
    case 'undo':
      return `Undid ${details?.action_type || 'previous action'}`;
    case 'import':
      return `Imported data (${details?.imported_chores?.length || 0} chores, ${details?.imported_logs || 0} logs)`;
    case 'export':
      return `Exported data (${details?.chore_count || 0} chores, ${details?.log_count || 0} logs)`;
    default:
      return `${label}: ${action || 'Activity recorded'}`;
  }
};

const normalizeEntry = (entry) => {
  const details = normalizeDetails(entry?.action_details || entry?.details);
  const action = entry?.action_type || details?.action_type || null;
  const timestamp = entry?.done_at || new Date().toISOString();
  return {
    id: entry?.id || `local-${Date.now()}`,
    action,
    message: buildMessage(action, details, entry),
    timestamp,
    raw: entry,
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
