﻿import { defineStore } from 'pinia';
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
      const response = await api.get('/chores');
      chores.value = response.data.map(chore => ({
        ...chore,
        disabled: isChoreDisabledToday(chore)
      }));
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
      const logStore = useLogStore();
      logStore.addLogEntry(`${chore.name} marked as done`);
      return response.data;
    } catch (error) {
      console.error('Failed to mark chore as done:', error);
      throw error;
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

  const updateChore = async (updatedChore) => {
    try {
      const response = await api.put(`/chores/${updatedChore.id}`, updatedChore);
      console.log("Updated Chore Response:", response.data);  // Log API response
      const index = chores.value.findIndex(c => c.id === updatedChore.id);
      if (index !== -1) {
        chores.value[index] = {
          ...chores.value[index],  // Preserve existing values
          ...response.data,        // Update only returned fields
          interval_days: updatedChore.interval_days, // Ensure interval_days is updated
          due_date: updatedChore.due_date // Ensure due_date is updated
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
    undoChore,
  };
});
