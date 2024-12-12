import { defineStore } from 'pinia'
import api from '@/plugins/axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null,
    userColor: null,
    username: null,
  }),

  actions: {
    async login(token, color, username) {
      this.token = token
      this.userColor = color
      this.username = username
      localStorage.setItem('token', token)
    },

    async logout() {
      this.token = null
      this.userColor = null
      this.username = null
      localStorage.removeItem('token')
    },

    isAuthenticated() {
      return !!this.token
    },
  },
})
