import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { createPinia } from 'pinia'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import { briseTheme } from './shared/config/vuetify.theme'
const vuetify = createVuetify({
  theme: {
    defaultTheme: 'light',
    themes: { light: briseTheme }
  }
})

const app = createApp(App)

app.config.performance = import.meta.env.DEV

app.use(createPinia())
app.use(vuetify)

app.mount('#app')