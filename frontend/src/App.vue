<template>
  <a-config-provider :theme="antdTheme" :locale="zhCN">
    <router-view />
  </a-config-provider>
</template>

<script setup>
import { onMounted } from 'vue'
import { ConfigProvider as AConfigProvider } from 'ant-design-vue'
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import { useAuthStore } from '@/stores/auth'
import antdTheme from './antd-theme'

const authStore = useAuthStore()

// 应用启动时验证 Token
onMounted(async () => {
  if (authStore.isAuthenticated) {
    try {
      await authStore.fetchCurrentUser()
    } catch (error) {
      console.error('验证用户信息失败:', error)
      // Token 可能已过期，清除认证状态
      authStore.clearAuth()
    }
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  overflow-x: hidden;
}

#app {
  width: 100%;
  height: 100%;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
