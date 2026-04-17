import { createRouter, createWebHistory } from 'vue-router'
import App from '@/App.vue'
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'start',
      component: App.vue
    }
  ],
})

export default router
