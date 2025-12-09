import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

const baseURL = import.meta.env.DEV ? "http://localhost:8090/api" : "/api"
console.log("baseURL: " + baseURL)
console.log("import.meta.env.MODE: " + import.meta.env.MODE)
const api = axios.create({
  baseURL,
  // Add timeout to prevent hanging requests
  timeout: 15000,
  // Retry on network errors
  retry: 3,
  retryDelay: 1000
})

// Flag to prevent multiple refresh token requests
let isRefreshing = false;
// Store pending requests that should be retried after token refresh
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`;
    }
    if (authStore.userEmail) {
      config.headers['X-User-Email'] = authStore.userEmail;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  response => response,
  async error => {
    const { config, response } = error;
    const authStore = useAuthStore();

    // Skip if retry is undefined or this is a refresh token request
    if (!config || config.url.includes('/auth/refresh') || config._retry) {
      return Promise.reject(error);
    }

    // Handle 401 Unauthorized errors - token might be expired
    if (response && response.status === 401) {
      // Check if token refresh is needed and possible
      if (authStore.isTokenExpired && authStore.refreshToken) {
        // If already refreshing, queue this request
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          })
            .then(token => {
              config.headers.Authorization = `Bearer ${token}`;
              return api(config);
            })
            .catch(err => {
              return Promise.reject(err);
            });
        }

        config._retry = true;
        isRefreshing = true;

        return authStore.refreshAccessToken()
          .then(success => {
            if (success) {
              processQueue(null, authStore.token);
              config.headers.Authorization = `Bearer ${authStore.token}`;
              return api(config);
            } else {
              processQueue(new Error('Failed to refresh token'));
              authStore.logout();
              window.location.href = '/login';
              return Promise.reject(error);
            }
          })
          .catch(refreshError => {
            processQueue(refreshError);
            authStore.logout();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          })
          .finally(() => {
            isRefreshing = false;
          });
      } else {
        // No refresh token or other 401 error - redirect to login
        console.warn('Authentication error. Redirecting to login.');
        authStore.logout();
        window.location.href = '/login';
      }
    }

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
      // Handle not found errors
      if (response.status === 404) {
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
    }

    return Promise.reject(error);
  }
);

export default api;
