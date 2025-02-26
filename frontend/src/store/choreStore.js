import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '@/plugins/axios';

export const useChoreStore = defineStore('chores', () => {
  const chores = ref([]);
  const loading = ref(false);
  const error = ref(null);

  const sortedByUrgency = computed(() => {
    return [...chores.value].sort((a, b) => {
      if (a.archived && !b.archived) return 1;
      if (!a.archived && b.archived) return -1;

      const dateA = new Date(a.due_date);
      const dateB = new Date(b.due_date);
      return dateA - dateB;
    });
  });

  const isDoneToday = (chore) => {
    if (!chore?.last_done) return false;
    const today = new Date().setHours(0, 0, 0, 0);
    const doneDate = new Date(chore.last_done).setHours(0, 0, 0, 0);
    return today === doneDate;
  };

  const fetchChores = async () => {
    loading.value = true;
    error.value = null;
    try {
      const response = await api.get('/chores');
      chores.value = response.data;
    } catch (err) {
      error.value = 'Failed to fetch chores. Please try again later.';
      console.error('Failed to fetch chores:', err);
    } finally {
      loading.value = false;
    }
  };

  const markChoreDone = async (choreId) => {
    const chore = chores.value.find(c => c.id === choreId);
    if (isDoneToday(chore)) {
      console.log('Chore already done today');
      return null;
    }

    try {
      const response = await api.put(`/chores/${choreId}/done`, {
        done_by: 'user' // TODO: Get actual user from auth store
      });

      const index = chores.value.findIndex(c => c.id === choreId);
      if (index !== -1) {
        chores.value[index] = {
          ...chores.value[index],
          done: true,
          due_date: response.data.new_due_date,
          last_done: new Date().toISOString()
        };
      }
      return response.data;
    } catch (error) {
      console.error('Failed to mark chore as done:', error);
      throw error;
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

  const updateChore = async (updatedChore) => {
    try {
      const response = await api.put(`/chores/${updatedChore.id}`, updatedChore);
      const index = chores.value.findIndex(c => c.id === updatedChore.id);
      if (index !== -1) {
        chores.value[index] = response.data;
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
    isDoneToday,
    fetchChores,
    addChore,
    updateChore,
    archiveChore,
    markChoreDone,
  };
});
