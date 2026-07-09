import { createApp } from 'vue'
import './style.css'
import '@vue-flow/core/dist/style.css'
import App from './App.vue'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import { createPinia } from 'pinia'


const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.mount('#app')

