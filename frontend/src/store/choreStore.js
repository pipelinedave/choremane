import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '@/plugins/axios';
import { useLogStore } from '@/store/logStore';
import { useAuthStore } from '@/store/authStore';
import { bucketChores, normalizeToLocalDate } from '@/utils/choreBuckets';

export const useChoreStore = defineStore('chores', () => {
  const chores = ref([]);
  const archivedChores = ref([]); // Separate ref for archived chores
  const loading = ref(false);
  const error = ref(null);
  // Add pagination states
  const pageSize = ref(10); // Number of items per page
  const hasMoreChores = ref(true); // Whether there are more chores to load
  const hasMoreArchivedChores = ref(true); // Whether there are more archived chores to load


  // New state for total counts from server
  const totalCounts = ref({
    all: 0,
    overdue: 0,
    today: 0,
    tomorrow: 0,
    thisWeek: 0,
    upcoming: 0
  });

  // Calculate local bucket counts for fallback/optimistic updates if needed
  // But primarily we will use totalCounts from server
  const choreCounts = computed(() => bucketChores(chores.value).counts);
  const editingChoreId = ref(null);

  const householdHealth = computed(() => {
    if (chores.value.length === 0) return 100;

    let totalScore = 0;
    let activeChoreCount = 0;
    const now = new Date();
    // Normalize now to midnight for day-level granularity if desired, 
    // but for progress bars, real-time "now" might differ slightly. 
    // Let's stick to real-time for 'freshness' feel or normalize for stability.
    // Given the prompt "how due chores are", using real timestamps is fine.

    chores.value.forEach(chore => {
      // Skip undefined intervals or chores that shouldn't affect score (optional: maybe skip paused/archived which are already filtered out of 'chores' usually)
      if (!chore.interval_days || chore.interval_days <= 0) {
        return;
      }

      activeChoreCount++;

      const dueDate = new Date(chore.due_date);
      const intervalMs = chore.interval_days * 24 * 60 * 60 * 1000;

      // Calculate time difference
      // Positive diff = Overdue by diff ms
      // Negative diff = Due in diff ms (future)
      const diffMs = now.getTime() - dueDate.getTime();

      let score = 100;

      if (diffMs > 0) {
        // OVERDUE
        // Calculate overdue ratio: how many intervals has it been overdue?
        const overdueRatio = diffMs / intervalMs;
        // Decay from 80 to 0.
        // If 1 full interval overdue (ratio 1.0), score becomes 0.
        // Formula: 80 - (overdueRatio * 80)
        score = Math.max(0, 80 - (overdueRatio * 80));
      } else {
        // NOT OVERDUE (Fresh to Standard)
        // diffMs is negative. 
        // Time elapsed since "start" (roughly) = intervalMs + diffMs (since diffMs is negative remainder)
        // Actually simpler: 
        // Fraction elapsed =  1 - (Time Until Due / Interval)
        const timeUntilDue = -diffMs;
        const fractionElapsed = 1 - (timeUntilDue / intervalMs);

        // Clamp fraction for safety (e.g. if due date is way in future due to edit)
        const safeFraction = Math.max(0, Math.min(1, fractionElapsed));

        if (safeFraction <= 0.5) {
          // Fresh Zone
          score = 100;
        } else {
          // Standard Zone (0.5 to 1.0) -> Decays 100 to 80
          // Mapping: 0.5 -> 100, 1.0 -> 80
          // Slope = (80 - 100) / (1.0 - 0.5) = -20 / 0.5 = -40
          score = 100 + ((safeFraction - 0.5) * -40);
        }
      }

      totalScore += score;
    });

    return activeChoreCount === 0 ? 100 : Math.round(totalScore / activeChoreCount);
  });

  const setEditingChore = (choreId) => {
    editingChoreId.value = choreId;
  };

  const clearEditingChore = () => {
    editingChoreId.value = null;
  };

  const isChoreDisabledToday = (chore) => {
    if (!chore?.due_date || !chore?.interval) return false;

    const today = normalizeToLocalDate(new Date());
    const dueDate = normalizeToLocalDate(chore.due_date);

    if (!today || !dueDate) return false;

    return today.getTime() === dueDate.getTime();
  };

  const sortedByUrgency = computed(() => {
    return [...chores.value].map(chore => ({
      ...chore,
      disabled: isChoreDisabledToday(chore)
    })).sort((a, b) => {
      const dateA = normalizeToLocalDate(a.due_date);
      const dateB = normalizeToLocalDate(b.due_date);
      return (dateA?.getTime() ?? Infinity) - (dateB?.getTime() ?? Infinity);
    });
  });

  // Get all archived chores sorted by due date
  const sortedArchivedChores = computed(() => {
    return [...archivedChores.value].map(chore => ({
      ...chore,
      disabled: isChoreDisabledToday(chore)
    })).sort((a, b) => {
      const dateA = normalizeToLocalDate(a.due_date);
      const dateB = normalizeToLocalDate(b.due_date);
      return (dateA?.getTime() ?? Infinity) - (dateB?.getTime() ?? Infinity);
    });
  });

  const isDoneToday = (chore) => {
    if (!chore?.last_done) return false;

    // Convert both dates to local midnight for accurate comparison
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const lastDone = new Date(chore.last_done);
    lastDone.setHours(0, 0, 0, 0);

    return today.getTime() === lastDone.getTime();
  };

  const fetchChoreCounts = async () => {
    try {
      const response = await api.get('/chores/count');
      totalCounts.value = response.data;
    } catch (err) {
      console.error('Failed to fetch chore counts:', err);
      // Don't set global error state here to avoid disrupting main UI if just counts fail
    }
  };

  const fetchChores = async (page = 1) => {
    if (page === 1) {
      // Reset for first page load
      chores.value = [];
      hasMoreChores.value = true;
      // Also fetch counts on initial load
      fetchChoreCounts();
    }

    if (!hasMoreChores.value && page > 1) return;

    loading.value = true;
    error.value = null;
    try {
      // Fetch active chores with pagination
      const response = await api.get('/chores', {
        params: {
          page,
          limit: pageSize.value
        }
      });

      const newChores = response.data.map(chore => ({
        ...chore,
        disabled: isChoreDisabledToday(chore)
      }));

      // Append new chores to existing ones for infinite scrolling
      if (page === 1) {
        chores.value = newChores;
      } else {
        // Filter out any duplicates before appending
        const existingIds = new Set(chores.value.map(c => c.id));
        const uniqueNewChores = newChores.filter(chore => !existingIds.has(chore.id));
        chores.value = [...chores.value, ...uniqueNewChores];
      }

      // Check if there are more chores to load
      if (newChores.length < pageSize.value) {
        hasMoreChores.value = false;
      }

    } catch (err) {
      error.value = 'Failed to fetch chores. Please try again later.';
      console.error('Failed to fetch chores:', err);
    } finally {
      loading.value = false;
    }
  };

  const fetchArchivedChores = async (page = 1) => {
    if (page === 1) {
      // Reset for first page load
      archivedChores.value = [];
      hasMoreArchivedChores.value = true;
    }

    if (!hasMoreArchivedChores.value && page > 1) return;

    loading.value = true;
    error.value = null;
    try {
      // Fetch archived chores with pagination
      const archivedResponse = await api.get('/chores/archived', {
        params: {
          page,
          limit: pageSize.value
        }
      });

      const newArchivedChores = archivedResponse.data.map(chore => ({
        ...chore,
        disabled: isChoreDisabledToday(chore)
      }));

      // Append new archived chores to existing ones for infinite scrolling
      if (page === 1) {
        archivedChores.value = newArchivedChores;
      } else {
        // Filter out any duplicates before appending
        const existingIds = new Set(archivedChores.value.map(c => c.id));
        const uniqueNewArchivedChores = newArchivedChores.filter(chore => !existingIds.has(chore.id));
        archivedChores.value = [...archivedChores.value, ...uniqueNewArchivedChores];
      }

      // Check if there are more archived chores to load
      if (newArchivedChores.length < pageSize.value) {
        hasMoreArchivedChores.value = false;
      }

    } catch (err) {
      error.value = 'Failed to fetch archived chores. Please try again later.';
      console.error('Failed to fetch archived chores:', err);
    } finally {
      loading.value = false;
    }
  };

  const markChoreDone = async (choreId) => {
    const authStore = useAuthStore();
    const logStore = useLogStore();
    const chore = chores.value.find(c => c.id === choreId);
    error.value = null;
    try {
      const response = await api.put(`/chores/${choreId}/done`, {
        done_by: authStore.userEmail || 'user'
      });
      const serverLastDone = response.data?.last_done || new Date().toISOString();

      const index = chores.value.findIndex(c => c.id === choreId);
      if (index !== -1) {
        chores.value[index] = {
          ...chores.value[index],
          done: true,
          due_date: response.data.new_due_date,
          last_done: serverLastDone,
          done_by: response.data?.done_by ?? chores.value[index].done_by
        };
      }
      await logStore.fetchLogs();
      fetchChoreCounts(); // Refresh counts

      return response.data;
    } catch (err) {
      if (err.response?.status === 409) {
        const detail = err.response.data?.detail;
        error.value = detail?.message || 'Chore already completed today';
        if (chore && detail?.last_done) {
          chore.last_done = detail.last_done;
        }
        return null;
      }
      error.value = 'Failed to mark chore as done. Please try again.';
      console.error('Failed to mark chore as done:', err);
      throw err;
    }
  };

  const undoChore = async (choreId) => {
    const logStore = useLogStore();
    const chore = chores.value.find(c => c.id === choreId);
    if (chore) {
      chore.done = false;
      await logStore.fetchLogs();
      logStore.addLocalLogEntry(`${chore.name} undone`, 'undo');
      fetchChoreCounts(); // Refresh counts
    }
  };

  const addChore = async (newChore) => {
    try {
      const response = await api.post('/chores', newChore);
      // Create complete chore object since backend only returns id
      const createdChore = {
        ...newChore,
        id: response.data.id,
        done: false,
        done_by: null,
        archived: false
      };
      chores.value.push(createdChore);
      const logStore = useLogStore();
      await logStore.fetchLogs();
      fetchChoreCounts(); // Refresh counts

      return createdChore;
    } catch (error) {
      console.error('Failed to add chore:', error);
      throw error;
    }
  };

  const updateChore = async (choreId, updatedChore) => {
    try {
      const payload = {
        ...updatedChore,
        id: choreId
      };
      const response = await api.put(`/chores/${choreId}`, payload);
      console.log("Updated Chore Response:", response.data);  // Log API response
      const index = chores.value.findIndex(c => c.id === choreId);
      if (index !== -1) {
        chores.value[index] = {
          ...chores.value[index],  // Preserve existing values
          ...response.data,        // Update only returned fields
          interval_days: updatedChore.interval_days, // Ensure interval_days is updated
          due_date: updatedChore.due_date // Ensure due_date is updated
        };
        chores.value = [...chores.value];  // Force reactivity update
      }

      const logStore = useLogStore();
      await logStore.fetchLogs();
      fetchChoreCounts(); // Refresh counts

      return response.data;
    } catch (error) {
      console.error('Failed to update chore:', error);
      throw error;
    }
  };

  const archiveChore = async (choreId) => {
    try {
      const response = await api.put(`/chores/${choreId}/archive`);
      const index = chores.value.findIndex(c => c.id === choreId);
      if (index !== -1) {
        // Check if this chore already exists in archived chores to avoid duplicates
        const existsInArchived = archivedChores.value.some(c => c.id === choreId);
        if (!existsInArchived) {
          archivedChores.value.push({ ...chores.value[index], archived: true }); // Add to archived chores
        }
        chores.value.splice(index, 1); // Remove from active chores
      }

      const logStore = useLogStore();
      await logStore.fetchLogs();
      fetchChoreCounts(); // Refresh counts

      return response.data;
    } catch (error) {
      console.error('Failed to archive chore:', error);
      throw error;
    }
  };

  // Add unarchive chore method
  const unarchiveChore = async (choreId) => {
    try {
      // Call the unarchive endpoint
      const response = await api.put(`/chores/${choreId}/unarchive`);

      // Update local state by moving from archived to active
      const index = archivedChores.value.findIndex(c => c.id === choreId);
      if (index !== -1) {
        // Remove from archived chores
        const unarchived = { ...archivedChores.value[index], archived: false };
        archivedChores.value.splice(index, 1);

        // Check if this chore already exists in active chores to avoid duplicates
        const existsInActive = chores.value.some(c => c.id === choreId);
        if (!existsInActive) {
          // Add to active chores
          chores.value.push(unarchived);
        }
      }

      const logStore = useLogStore();
      await logStore.fetchLogs();
      fetchChoreCounts(); // Refresh counts

      return response.data;
    } catch (error) {
      console.error('Failed to unarchive chore:', error);
      throw error;
    }
  };

  return {
    chores,
    archivedChores,
    loading,
    error,
    sortedByUrgency,
    sortedArchivedChores,
    isDoneToday,
    fetchChores,
    fetchArchivedChores,
    hasMoreChores,
    hasMoreArchivedChores,
    pageSize,
    addChore,
    updateChore,
    archiveChore,
    unarchiveChore,
    markChoreDone,
    undoChore,
    choreCounts,
    householdHealth,
    totalCounts, // Export new state
    fetchChoreCounts, // Export new method
    editingChoreId,
    setEditingChore,
    clearEditingChore
  };
});
