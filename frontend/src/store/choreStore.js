import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '@/plugins/axios';
import { useLogStore } from '@/store/logStore';

export const useChoreStore = defineStore('chores', () => {
  const chores = ref([]);
  const archivedChores = ref([]); // Separate ref for archived chores
  const loading = ref(false);
  const error = ref(null);
  // Add pagination states
  const pageSize = ref(10); // Number of items per page
  const hasMoreChores = ref(true); // Whether there are more chores to load
  const hasMoreArchivedChores = ref(true); // Whether there are more archived chores to load
  // Add total chore counts for each category
  const choreCounts = ref({
    all: 0,
    overdue: 0,
    today: 0,
    tomorrow: 0,
    thisWeek: 0,
    upcoming: 0
  });
  // Flag to track if counts are being fetched
  const fetchingCounts = ref(false);
  const editingChoreId = ref(null);

  const normalizeToLocalDate = (dateValue) => {
    const parsed = new Date(dateValue);
    return new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate());
  };

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

    return today.getTime() === dueDate.getTime();
  };

  const sortedByUrgency = computed(() => {
    return [...chores.value].map(chore => ({
      ...chore,
      disabled: isChoreDisabledToday(chore)
    })).sort((a, b) => {
      const dateA = normalizeToLocalDate(a.due_date);
      const dateB = normalizeToLocalDate(b.due_date);
      return dateA - dateB;
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
      return dateA - dateB;
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

  const fetchChores = async (page = 1) => {
    if (page === 1) {
      // Reset for first page load
      chores.value = [];
      hasMoreChores.value = true;
      
      // Fetch the total counts when resetting the page
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

  const fetchChoreCounts = async () => {
    fetchingCounts.value = true;
    try {
      const response = await api.get('/chores/count');
      choreCounts.value = response.data;
    } catch (err) {
      console.error('Failed to fetch chore counts:', err);
      // In case of error, fallback to calculating counts from loaded chores
      updateLocalChoreCounts();
    } finally {
      fetchingCounts.value = false;
    }
  };
  
  // Calculate counts from loaded chores (as a fallback if API fails)
  const updateLocalChoreCounts = () => {
    const today = normalizeToLocalDate(new Date());

    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const nextWeek = new Date(today);
    nextWeek.setDate(today.getDate() + 7);
    
    // Non-archived chores
    const nonArchivedChores = chores.value.filter(c => !c.archived);
    
    choreCounts.value.all = nonArchivedChores.length;
    choreCounts.value.overdue = nonArchivedChores.filter(c => normalizeToLocalDate(c.due_date) < today).length;
    choreCounts.value.today = nonArchivedChores.filter(c => normalizeToLocalDate(c.due_date).toDateString() === today.toDateString()).length;
    choreCounts.value.tomorrow = nonArchivedChores.filter(c => normalizeToLocalDate(c.due_date).toDateString() === tomorrow.toDateString()).length;
    choreCounts.value.thisWeek = nonArchivedChores.filter(c => {
      const dueDate = normalizeToLocalDate(c.due_date);
      return dueDate > tomorrow && dueDate <= nextWeek;
    }).length;
    choreCounts.value.upcoming = nonArchivedChores.filter(c => {
      const dueDate = normalizeToLocalDate(c.due_date);
      return dueDate > nextWeek;
    }).length;
  };

  const markChoreDone = async (choreId) => {
    const chore = chores.value.find(c => c.id === choreId);
    error.value = null;
    try {
      const response = await api.put(`/chores/${choreId}/done`, {
        done_by: 'user' // TODO: Get actual user from auth store
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
      const logStore = useLogStore();
      logStore.addLogEntry(`${chore.name} marked as done`);
      
      // Refresh chore counts after marking a chore as done
      fetchChoreCounts();
      
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

  const undoChore = (choreId) => {
    const chore = chores.value.find(c => c.id === choreId);
    if (chore) {
      chore.done = false;
      const logStore = useLogStore();
      logStore.addLogEntry(`${chore.name} undone`);
      
      // Refresh counts when undoing a chore
      fetchChoreCounts();
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
      
      // Refresh counts when adding a new chore
      fetchChoreCounts();
      
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
      
      // Refresh counts after updating a chore since due dates may have changed
      fetchChoreCounts();
      
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
          archivedChores.value.push({...chores.value[index], archived: true}); // Add to archived chores
        }
        chores.value.splice(index, 1); // Remove from active chores
      }
      
      // Refresh counts after archiving a chore
      fetchChoreCounts();
      
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
      
      // Refresh counts after unarchiving a chore
      fetchChoreCounts();
      
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
    fetchChoreCounts,
    fetchingCounts,
    editingChoreId,
    setEditingChore,
    clearEditingChore
  };
});
