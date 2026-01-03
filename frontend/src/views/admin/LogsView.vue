<template>
  <Layout>
    <div class="admin-logs-container">
      <a-card>
        <template #title>
          <div class="card-header">
            <div>
              <FileTextOutlined />
              <span>系统日志</span>
            </div>
            <a-button type="primary" @click="handleRefresh">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </div>
        </template>

        <a-alert
          message="日志查看"
          description="显示最新的系统日志信息（默认显示最近 200 行）"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 20px"
        />

        <div v-if="adminStore.loading" class="loading-container">
          <a-skeleton :active="true" :paragraph="{ rows: 10 }" />
        </div>

        <div v-else class="logs-content">
          <a-textarea
            v-model:value="logContent"
            :rows="25"
            :readonly="true"
            placeholder="暂无日志内容"
            class="log-textarea"
          />

          <div class="log-info">
            <span>共 {{ logLines }} 行</span>
            <span>最后更新: {{ lastUpdate }}</span>
          </div>
        </div>
      </a-card>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { FileTextOutlined, ReloadOutlined } from '@ant-design/icons-vue';
import Layout from '@/components/Layout.vue';
import { useAdminStore } from '@/stores/admin';
import { formatDateTime } from '@/utils/helpers';

const adminStore = useAdminStore();

const logContent = ref('');
const lastUpdate = ref('');

const logLines = computed(() => {
  if (!logContent.value) return 0;
  const content =
    typeof logContent.value === 'string' ? logContent.value : String(logContent.value);
  return content.split('\n').length;
});

const handleRefresh = async () => {
  try {
    const data = await adminStore.fetchLogs({ lines: 200 });
    if (data.logs) {
      // 确保是字符串
      logContent.value = typeof data.logs === 'string' ? data.logs : String(data.logs);
      lastUpdate.value = formatDateTime(new Date());
      message.success({ content: '刷新成功', duration: 2 });
    } else {
      logContent.value = '无日志内容';
    }
  } catch (error) {
    message.error({ content: error.message || '刷新失败', duration: 4 });
  }
};

onMounted(() => {
  handleRefresh();
});
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

.log-textarea :deep(textarea) {
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre;
  overflow-x: auto;
  word-break: normal;
  overflow-wrap: normal;
}
</style>
