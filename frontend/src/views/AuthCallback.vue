<template>
  <div class="auth-callback">
    <div v-if="loading" class="auth-loading">
      <div class="spinner"></div>
      <p>Authenticating, please wait...</p>
    </div>
    <div v-if="error" class="auth-error">
      <p>{{ error }}</p>
      <button @click="redirectToLogin" class="btn btn-primary">Try Again</button>
    </div>
  </div>
</template>

<script>
import { useAuthStore } from '@/store/authStore';
import { useRouter } from 'vue-router';

export default {
  name: 'AuthCallback',
  data() {
    return {
      loading: true,
      error: null
    };
  },
  created() {
    this.processAuthCallback();
  },
  methods: {
    processAuthCallback() {
      const query = new URLSearchParams(window.location.search);
      const token = query.get('token');
      const idToken = query.get('id_token');
      const refreshToken = query.get('refresh_token');
      const expiresIn = query.get('expires_in');
      
      console.log("Auth callback received: ", {
        hasToken: !!token,
        hasIdToken: !!idToken,
        hasRefreshToken: !!refreshToken,
        expiresIn
      });
      
      const authStore = useAuthStore();
      const router = useRouter();
      
      if (token && idToken) {
        try {
          console.log("Processing successful authentication");
          authStore.login({
            token,
            id_token: idToken,
            refresh_token: refreshToken,
            expires_in: parseInt(expiresIn || '86400')
          });
          
          // Redirect to home page
          setTimeout(() => {
            this.loading = false;
            console.log("Redirecting to home page after successful auth");
            router.push('/');
          }, 1000);
        } catch (error) {
          console.error('Failed to process auth callback', error);
          this.loading = false;
          this.error = 'Authentication failed. Please try again.';
        }
      } else {
        console.error('Invalid auth callback: Missing token data', { 
          search: window.location.search,
          query: Object.fromEntries(query.entries())
        });
        this.loading = false;
        this.error = 'Invalid authentication response. Missing token data.';
      }
    },
    
    redirectToLogin() {
      const authStore = useAuthStore();
      authStore.loginWithDex();
    }
  }
};
</script>

<style scoped>
.auth-callback {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  text-align: center;
  padding: 20px;
}

.auth-loading, .auth-error {
  max-width: 400px;
  padding: 20px;
  border-radius: 8px;
  background-color: #f8f9fa;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #3498db;
  border-radius: 50%;
  margin: 0 auto 20px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.btn {
  margin-top: 15px;
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.btn:hover {
  background-color: #45a049;
}
</style>
