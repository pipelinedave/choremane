// frontend/src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import './assets/shared.css'

const app = createApp(App)
app.use(router)
app.use(createPinia())
app.mount('#app')

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/service-worker.js')
    .then(registration => {
      console.log('ServiceWorker registration successful with scope: ', registration.scope);
    })
    .catch(error => {
      console.log('ServiceWorker registration failed: ', error);
    });
}
