import { defineStore } from 'pinia';
import api from '@/plugins/axios';
import { useAuthStore } from './authStore';

export const useChoreStore = defineStore('chores', {
  state: () => ({
    chores: [],
    logs: [], // Store logs for display
  }),

  actions: {
    async fetchChores() {
      try {
        const response = await api.get('/chores');
        this.chores = response.data;
      } catch (error) {
        console.error('Error fetching chores:', error);
      }
    },

    async fetchLogs() {
      try {
        const response = await api.get('/logs');
        this.logs = response.data;
      } catch (error) {
        console.error('Error fetching logs:', error);
      }
    },

    async addChore(chore) {
      try {
        const response = await api.post('/chores', chore);
        this.fetchChores();
        this.fetchLogs(); // Refresh logs
        console.log(response.data.message);
      } catch (error) {
        console.error('Error adding chore:', error);
      }
    },

    async archiveChore(choreId) {
      try {
        const response = await api.put(`/chores/${choreId}/archive`);
        this.fetchChores();
        this.fetchLogs(); // Refresh logs
        console.log(response.data.message);
      } catch (error) {
        console.error('Error archiving chore:', error);
      }
    },

    async markChoreDone(choreId) {
      const authStore = useAuthStore();
      try {
        const response = await api.put(`/chores/${choreId}/done`, {
          done_by: authStore.username || "anonymous", // Fallback to "anonymous"
        });
        this.fetchChores();
        this.fetchLogs(); // Refresh logs
        console.log(response.data.message);
      } catch (error) {
        console.error('Error marking chore as done:', error);
      }
    },

    async updateChore(chore) {
      try {
        const response = await api.put(`/chores/${chore.id}`, chore);
        this.fetchChores();
        this.fetchLogs(); // Refresh logs
        console.log(response.data.message);
      } catch (error) {
        console.error('Error updating chore:', error);
      }
    },

    async undoLastAction(logId) {
      try {
        const response = await api.post('/undo', { log_id: logId });
        this.fetchChores();
        this.fetchLogs(); // Refresh logs
        console.log(response.data.message);
      } catch (error) {
        console.error('Error undoing last action:', error);
      }
    },
  },

  getters: {
    sortedByUrgency: (state) => {
      return state.chores.sort(
        (a, b) => new Date(a.due_date) - new Date(b.due_date)
      );
    },
    recentLogs: (state) => state.logs.slice().reverse(), // Show logs in reverse order
  },
});
