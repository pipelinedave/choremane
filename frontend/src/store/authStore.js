import { defineStore } from 'pinia'
import api from '@/plugins/axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    userColor: localStorage.getItem('userColor') || null,
    username: localStorage.getItem('username') || null,
  }),

  actions: {
    async login(token, color, username) {
      this.token = token
      this.userColor = color
      this.username = username
      localStorage.setItem('token', token)
      localStorage.setItem('userColor', color)
      localStorage.setItem('username', username)
    },

    async logout() {
      this.token = null
      this.userColor = null
      this.username = null
      localStorage.removeItem('token')
      localStorage.removeItem('userColor')
      localStorage.removeItem('username')
    },

    isAuthenticated() {
      return !!this.token
    },
  },
})
