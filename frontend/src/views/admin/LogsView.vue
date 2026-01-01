<template>
  <Layout>
    <div class="admin-logs-container">
      <el-card>
        <template #header>
          <div class="card-header">
            <div>
              <el-icon><Document /></el-icon>
              <span>系统日志</span>
            </div>
            <el-button type="primary" :icon="Refresh" @click="handleRefresh">
              刷新
            </el-button>
          </div>
        </template>

        <el-alert
          title="日志查看"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 20px"
        >
          <p>显示最新的系统日志信息（默认显示最近 200 行）</p>
        </el-alert>

        <div v-if="adminStore.loading" class="loading-container">
          <el-skeleton :rows="10" animated />
        </div>

        <div v-else class="logs-content">
          <el-input
            v-model="logContent"
            type="textarea"
            :rows="25"
            readonly
            placeholder="暂无日志内容"
          />

          <div class="log-info">
            <span>共 {{ logLines }} 行</span>
            <span>最后更新: {{ lastUpdate }}</span>
          </div>
        </div>
      </el-card>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Refresh } from '@element-plus/icons-vue'
import Layout from '@/components/Layout.vue'
import { useAdminStore } from '@/stores/admin'
import { formatDateTime } from '@/utils/helpers'

const adminStore = useAdminStore()

const logContent = ref('')
const lastUpdate = ref('')

const logLines = computed(() => {
  if (!logContent.value) return 0
  const content = typeof logContent.value === 'string' ? logContent.value : String(logContent.value)
  return content.split('\n').length
})

const handleRefresh = async () => {
  try {
    const data = await adminStore.fetchLogs({ lines: 200 })
    if (data.logs) {
      // 确保是字符串
      logContent.value = typeof data.logs === 'string' ? data.logs : String(data.logs)
      lastUpdate.value = formatDateTime(new Date())
      ElMessage.success('刷新成功')
    } else {
      logContent.value = '无日志内容'
    }
  } catch (error) {
    ElMessage.error(error.message || '刷新失败')
  }
}

onMounted(() => {
  handleRefresh()
})
</script>

<style scoped>
.admin-logs-container {
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header > div {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.loading-container {
  padding: 20px;
}

.logs-content {
  font-family: 'Courier New', Courier, monospace;
}

.log-info {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}

:deep(.el-textarea__inner) {
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre;
  overflow-x: auto;
  word-break: normal;
  overflow-wrap: normal;
}
</style>
