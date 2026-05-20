import { createRouter, createWebHistory } from 'vue-router'
import App from '../App.vue'
import DownloadPopup from '../features/download-popup/ui/DownloadPopup.vue'
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'start',
      component: App.vue
    },
    {
      path: '/',
      name: 'download',
      component: DownloadPopup.vue
    }
  ],
})

export default router
