import { defineStore } from 'pinia'
import api from '@/plugins/axios'
import jwt_decode from '@/utils/jwt-decode'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    idToken: localStorage.getItem('idToken') || null,
    refreshToken: localStorage.getItem('refreshToken') || null,
    userColor: localStorage.getItem('userColor') || null,
    username: localStorage.getItem('username') || null,
    userProfile: JSON.parse(localStorage.getItem('userProfile') || 'null'),
    tokenExpiry: localStorage.getItem('tokenExpiry') || null,
  }),

  getters: {
    isAuthenticated() {
      return !!this.token
    },
    
    isTokenExpired() {
      if (!this.tokenExpiry) return true
      return new Date().getTime() > parseInt(this.tokenExpiry)
    },
    
    userEmail() {
      return this.userProfile?.email || this.username
    },
    
    displayName() {
      return this.userProfile?.name || this.userProfile?.email || this.username
    }
  },

  actions: {
    async login(authData) {
      const { token, id_token, refresh_token, expires_in } = authData
      
      // Decode the ID token to get user information
      let userProfile = null
      if (id_token) {
        try {
          userProfile = jwt_decode(id_token)
        } catch (error) {
          console.error('Failed to decode ID token', error)
        }
      }
      
      // Calculate token expiration
      const expiryTime = new Date().getTime() + expires_in * 1000
      
      // Set state
      this.token = token
      this.idToken = id_token
      this.refreshToken = refresh_token
      this.userColor = userProfile?.preferred_username?.[0]?.toLowerCase() || 'u'
      this.username = userProfile?.email || ''
      this.userProfile = userProfile
      this.tokenExpiry = expiryTime.toString()
      
      // Store in localStorage
      localStorage.setItem('token', token)
      localStorage.setItem('idToken', id_token || '')
      localStorage.setItem('refreshToken', refresh_token || '')
      localStorage.setItem('userColor', this.userColor)
      localStorage.setItem('username', this.username)
      localStorage.setItem('userProfile', JSON.stringify(userProfile))
      localStorage.setItem('tokenExpiry', expiryTime.toString())
      
      return userProfile
    },

    async loginWithDex() {
      window.location.href = '/api/auth/login'
    },
    
    async refreshAccessToken() {
      if (!this.refreshToken) {
        console.error('No refresh token available')
        this.logout()
        return false
      }
      
      try {
        const response = await api.post('/auth/refresh', {
          refresh_token: this.refreshToken
        })
        
        if (response.data && response.data.access_token) {
          this.login({
            token: response.data.access_token,
            id_token: response.data.id_token,
            refresh_token: response.data.refresh_token || this.refreshToken,
            expires_in: response.data.expires_in
          })
          return true
        }
      } catch (error) {
        console.error('Failed to refresh token', error)
        this.logout()
      }
      
      return false
    },

    async logout() {
      this.token = null
      this.idToken = null
      this.refreshToken = null
      this.userColor = null
      this.username = null
      this.userProfile = null
      this.tokenExpiry = null
      
      localStorage.removeItem('token')
      localStorage.removeItem('idToken')
      localStorage.removeItem('refreshToken')
      localStorage.removeItem('userColor')
      localStorage.removeItem('username')
      localStorage.removeItem('userProfile')
      localStorage.removeItem('tokenExpiry')
    },
  },
})
