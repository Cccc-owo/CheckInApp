<template>
  <div class="layout-container">
    <Navbar />
    <div class="main-content">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import Navbar from './Navbar.vue'
import { useTokenMonitor } from '@/composables/useTokenMonitor'

// 启动全局 Token 监控
const { startMonitoring } = useTokenMonitor()

onMounted(() => {
  startMonitoring()
})
</script>

<style scoped>
.layout-container {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
}

.dark .layout-container {
  background: linear-gradient(135deg, #1a1a1a 0%, #0f0f0f 100%);
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
</style>
