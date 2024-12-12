import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

// Set the base URL for all API calls from an environment variable
const baseURL = (() => {
  if (process.env.NODE_ENV === "development") {
    // Adjust for local dev with port forwarding
    return `http://localhost:8090/api`;
  }
  return "/api"; // Staging/Prod with Traefik reverse proxy
})();

console.log("baseURL:  " + baseURL);
console.log("process.env.NODE_ENV: " + process.env.NODE_ENV);
const api = axios.create({ baseURL });

// Add a request interceptor to include the token if it’s available
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Test API call function
async function testConnection() {
  try {
    const response = await api.get('/status') // Replace '/status' with your actual test endpoint if different
    console.log('Connection successful:', response.data)
  } catch (error) {
    console.error('Error connecting to backend:', error)
  }
}

// Call the test function on load for verification purposes
testConnection()

export default api
