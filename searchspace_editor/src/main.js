import { createApp } from 'vue'
import './style.css'
import '@vue-flow/core/dist/style.css'
import App from './App.vue'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import { createPinia } from 'pinia'

import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { faUndo, faRedo, faEraser } from '@fortawesome/free-solid-svg-icons'

library.add(faUndo, faRedo, faEraser)

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

app.component('font-awesome-icon', FontAwesomeIcon)
app.mount('#app')

