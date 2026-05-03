import { createApp } from 'vue'
import App from './App.vue'
import { useAuth } from './app/auth'
import './style.css'

const auth = useAuth()

if (auth.state.token && !auth.state.initialized) {
  void auth.refreshCurrentUser().catch(() => undefined)
}

createApp(App).mount('#app')
