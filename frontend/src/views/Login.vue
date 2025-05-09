<template>
  <div class="login-page">
    <div class="login-container">
      <h1>Welcome to Choremane</h1>
      <p>Your smart chore management application</p>
      
      <button @click="login" class="login-button">
        <span class="button-icon">
          <i class="fas fa-sign-in-alt"></i>
        </span>
        <span class="button-text">Sign in with Google</span>
      </button>
      
      <div class="login-info">
        <p>A secure login using Dex authentication</p>
      </div>
    </div>
  </div>
</template>

<script>
import { useAuthStore } from '@/store/authStore';

export default {
  name: 'LoginPage',
  setup() {
    const authStore = useAuthStore();
    
    return {
      login() {
        authStore.loginWithDex();
      }
    };
  }
};
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background-color: #f5f5f5;
}

.login-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
  text-align: center;
}

h1 {
  color: #333;
  margin-bottom: 10px;
  font-size: 24px;
}

p {
  color: #666;
  margin-bottom: 30px;
}

.login-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 12px 20px;
  background-color: #4285F4;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.login-button:hover {
  background-color: #3367D6;
}

.button-icon {
  margin-right: 10px;
}

.login-info {
  margin-top: 30px;
  font-size: 14px;
  color: #777;
}
</style>
