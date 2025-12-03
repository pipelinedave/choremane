import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '@/plugins/axios';
import { useLogStore } from '@/store/logStore';

export const useChoreStore = defineStore('chores', () => {
  const chores = ref([]);
  const loading = ref(false);
  const error = ref(null);

  const isChoreDisabledToday = (chore) => {
    if (!chore?.due_date || !chore?.interval) return false;

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const dueDate = new Date(chore.due_date);
    dueDate.setHours(0, 0, 0, 0);

    return today.getTime() === dueDate.getTime();
  };

  const sortedByUrgency = computed(() => {
    return [...chores.value].map(chore => ({
      ...chore,
      disabled: isChoreDisabledToday(chore)
    })).sort((a, b) => {
      if (a.archived && !b.archived) return 1;
      if (!a.archived && b.archived) return -1;

      const dateA = new Date(a.due_date);
      const dateB = new Date(b.due_date);
      return dateA - dateB;
    });
  });

  // Get archived chores
  const archivedChores = computed(() => {
    return chores.value.filter(c => c.archived);
  });

  // Get non-archived chores
  const activeChores = computed(() => {
    return chores.value.filter(c => !c.archived);
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

  const fetchChores = async () => {
    loading.value = true;
    error.value = null;
    try {
      // First get the active chores
      const activeResponse = await api.get('/chores');
      const activeChores = activeResponse.data.map(chore => ({
        ...chore,
        disabled: isChoreDisabledToday(chore)
      }));
      
      // Then get archived chores directly from backend
      const archivedResponse = await api.get('/chores/archived');
      const archivedChores = archivedResponse.data.map(chore => ({
        ...chore,
        disabled: isChoreDisabledToday(chore)
      }));
      
      // Combine both sets
      chores.value = [...activeChores, ...archivedChores];
    } catch (err) {
      error.value = 'Failed to fetch chores. Please try again later.';
      console.error('Failed to fetch chores:', err);
    } finally {
      loading.value = false;
    }
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
          last_done: serverLastDone
        };
      }
      const logStore = useLogStore();
      logStore.addLogEntry(`${chore.name} marked as done`);
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
          due_date: updatedChore.due_date, // Ensure due_date is updated
          archived: updatedChore.archived // Ensure archived status is updated
        };
        chores.value = [...chores.value];  // Force reactivity update
      }
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
        chores.value[index] = { ...chores.value[index], archived: true };
        chores.value = [...chores.value];  // Force reactivity update
      }
      return response.data;
    } catch (error) {
      console.error('Failed to archive chore:', error);
      throw error;
    }
  };

  return {
    chores,
    loading,
    error,
    sortedByUrgency,
    archivedChores,  // New computed property
    activeChores,    // New computed property
    isDoneToday,
    fetchChores,
    addChore,
    updateChore,
    archiveChore,
    markChoreDone,
    undoChore,
  };
});
