import { createApp } from 'vue'
import App from './App.vue'
import { useAuth } from './app/auth'
import { initTheme } from './app/theme'
import './style.css'

initTheme()

const auth = useAuth()

if (auth.state.token && !auth.state.initialized) {
  void auth.refreshCurrentUser().catch(() => undefined)
}

createApp(App).mount('#app')
