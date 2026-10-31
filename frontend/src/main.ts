import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { createPinia } from 'pinia'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
const vuetify = createVuetify()

const app = createApp(App)

app.config.performance = import.meta.env.DEV

app.use(createPinia())
app.use(vuetify)

app.mount('#app')