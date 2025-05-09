import { createRouter, createWebHistory } from 'vue-router'
import ChoreList from '@/components/ChoreList.vue'
import Login from '@/views/Login.vue'
import AuthCallback from '@/views/AuthCallback.vue'
import { useAuthStore } from '@/store/authStore'

const routes = [
  {
    path: '/',
    name: 'ChoreList',
    component: ChoreList,
    meta: { 
      title: "Chores",
      requiresAuth: true 
    },
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { title: "Login" }
  },
  {
    path: '/auth-callback',
    name: 'AuthCallback',
    component: AuthCallback,
    meta: { title: "Authentication" }
  },
  {
    path: '/:catchAll(.*)',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || "CHOREMANE";
  
  const authStore = useAuthStore();
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  
  if (requiresAuth && !authStore.isAuthenticated) {
    next('/login');
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/');
  } else {
    next();
  }
});

export default router
