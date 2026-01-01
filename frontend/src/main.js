import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import {
  User,
  Key,
  Calendar,
  Refresh,
  Document,
  List,
  Plus,
  UserFilled,
  DataAnalysis,
  Loading,
  SuccessFilled,
  WarningFilled,
  CircleCloseFilled
} from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)
const pinia = createPinia()

// 按需注册 Element Plus 图标（仅注册使用的13个）
const icons = {
  User,
  Key,
  Calendar,
  Refresh,
  Document,
  List,
  Plus,
  UserFilled,
  DataAnalysis,
  Loading,
  SuccessFilled,
  WarningFilled,
  CircleCloseFilled
}

for (const [key, component] of Object.entries(icons)) {
  app.component(key, component)
}

app.use(pinia)
app.use(router)
app.use(ElementPlus, { locale: zhCn })

app.mount('#app')
