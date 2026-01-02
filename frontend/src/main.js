import { createApp } from 'vue'
import { createPinia } from 'pinia'

// Ant Design Vue
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import { ConfigProvider } from 'ant-design-vue'
import antdTheme from './antd-theme'

import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Ant Design Vue with custom theme
app.use(Antd)

// Configure Ant Design globally
app.config.globalProperties.$antdConfig = {
  theme: antdTheme,
  locale: zhCN,
}

app.mount('#app')
