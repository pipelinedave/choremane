import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

const baseURL = process.env.NODE_ENV === "development" ? "http://localhost:8090/api" : "/api"
console.log("baseURL: " + baseURL)
console.log("process.env.NODE_ENV: " + process.env.NODE_ENV)
const api = axios.create({ baseURL })

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

async function testConnection() {
  try {
    const response = await api.get('/status')
    console.log('Connection successful:', response.data)
  } catch (error) {
    console.error('Error connecting to backend:', error)
    const errorBanner = document.createElement('div')
    errorBanner.textContent = 'The backend service is currently unavailable'
    Object.assign(errorBanner.style, {
      position: 'fixed',
      top: '0',
      left: '0',
      width: '100%',
      backgroundColor: 'red',
      color: 'white',
      textAlign: 'center',
      padding: '1em',
      zIndex: '9999'
    })
    document.body.appendChild(errorBanner)
  }
}

testConnection()

export default api
