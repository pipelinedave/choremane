import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/components/Login.vue'
import ChoreList from '@/components/ChoreList.vue'

const routes = [
  {
    path: '/',
    name: 'ChoreList',
    component: ChoreList,
    meta: { title: "Chores" },
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
  next();
});

export default router
