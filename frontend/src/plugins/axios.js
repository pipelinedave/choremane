import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

const baseURL = process.env.NODE_ENV === "development" ? "http://localhost:8090/api" : "/api"
console.log("baseURL: " + baseURL)
console.log("process.env.NODE_ENV: " + process.env.NODE_ENV)
const api = axios.create({   baseURL })

api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 404) {
      console.warn('Resource not found:', error.config.url)
    } else {
      console.error('API Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export default api
