import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

const baseURL = process.env.NODE_ENV === "development" ? "http://localhost:8090/api" : "/api"
console.log("baseURL: " + baseURL)
console.log("process.env.NODE_ENV: " + process.env.NODE_ENV)
const api = axios.create({   
  baseURL,
  // Add timeout to prevent hanging requests
  timeout: 15000, 
  // Retry on network errors
  retry: 3,
  retryDelay: 1000
})

api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    if (authStore.username) {
      config.headers['X-User-Email'] = authStore.username
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  response => response,
  error => {
    const { config, response } = error;
    
    // Handle network errors that might occur during deployment/redeployment
    if (!response && error.message.includes('Network Error')) {
      console.error('Network error detected. Server might be redeploying.', error.message);
      
      // Implement retry logic for network errors
      const retryConfig = config;
      if (!retryConfig || !retryConfig.retry) {
        return Promise.reject(error);
      }
      
      // Set the retry count
      retryConfig._retryCount = retryConfig._retryCount || 0;
      
      // Check if we've maxed out the total number of retries
      if (retryConfig._retryCount >= retryConfig.retry) {
        console.error(`All ${retryConfig.retry} retry attempts failed.`);
        
        // Show user-friendly message
        if (confirm('Connection to server lost. Would you like to reload the application?')) {
          window.location.reload();
        }
        
        return Promise.reject(error);
      }
      
      // Increase the retry count
      retryConfig._retryCount += 1;
      console.log(`Retry attempt ${retryConfig._retryCount}/${retryConfig.retry}`);
      
      // Create a new promise to handle retry
      const delayRetry = new Promise(resolve => {
        setTimeout(() => {
          console.log('Retrying request...');
          resolve();
        }, retryConfig.retryDelay || 1000);
      });
      
      // Return the promise with the retry
      return delayRetry.then(() => api(retryConfig));
    }
    
    // Handle specific HTTP error statuses
    if (response) {
      // Handle auth errors
      if (response.status === 401) {
        console.warn('Authentication error. Redirecting to login.');
        const authStore = useAuthStore();
        authStore.logout();
        window.location.href = '/login';
      }
      
      // Handle not found errors
      else if (response.status === 404) {
        console.warn('Resource not found:', config.url);
      }
      
      // Handle server errors
      else if (response.status >= 500) {
        console.error('Server error. The application might be updating.', response.data);
        
        // Detect version mismatch or deployment issues
        if (config.url.includes('/version')) {
          console.error('Version endpoint error. Likely deployment in progress.');
        }
      }
      else {
        console.error('API Error:', error.message);
      }
    } else {
      console.error('Unhandled API error:', error.message);
    }
    
    return Promise.reject(error);
  }
)

export default api
