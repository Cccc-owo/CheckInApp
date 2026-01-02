<template>
  <Layout>
    <div class="admin-records-container">
      <a-card>
        <template #title>
          <div class="card-header">
            <div>
              <UnorderedListOutlined />
              <span>所有打卡记录</span>
            </div>
            <a-button type="primary" @click="handleRefresh">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </div>
        </template>

        <!-- Desktop table -->
        <a-table
          v-if="!isMobile"
          :dataSource="checkInStore.allRecords"
          :columns="columns"
          :loading="checkInStore.loading"
          :pagination="false"
          :row-key="record => record.id"
          :scroll="{ x: 'max-content' }"
          bordered
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'check_in_time'">
              {{ formatDateTime(record.check_in_time) }}
            </template>
            <template v-else-if="column.key === 'status'">
              <a-tag v-if="record.status === 'success'" color="success">✅ 打卡成功</a-tag>
              <a-tag v-else-if="record.status === 'out_of_time'" color="default">🕐 时间范围外</a-tag>
              <a-tag v-else-if="record.status === 'unknown'" color="warning">❗ 打卡异常</a-tag>
              <a-tag v-else color="error">❌ 打卡失败</a-tag>
            </template>
            <template v-else-if="column.key === 'trigger_type'">
              <a-tag v-if="record.trigger_type === 'manual'" color="blue">手动</a-tag>
              <a-tag v-else-if="record.trigger_type === 'scheduled'" color="cyan">定时</a-tag>
              <a-tag v-else-if="record.trigger_type === 'admin'" color="orange">管理员</a-tag>
              <a-tag v-else>{{ record.trigger_type }}</a-tag>
            </template>
          </template>
        </a-table>

        <!-- Mobile card view -->
        <a-space v-else direction="vertical" :size="16" style="width: 100%">
          <a-card v-for="record in checkInStore.allRecords" :key="record.id" size="small" :loading="checkInStore.loading">
            <a-descriptions :column="1" size="small" bordered>
              <a-descriptions-item label="ID">{{ record.id }}</a-descriptions-item>
              <a-descriptions-item label="用户ID">{{ record.user_id }}</a-descriptions-item>
              <a-descriptions-item label="用户邮箱">{{ record.user_email || '-' }}</a-descriptions-item>
              <a-descriptions-item label="任务名称">{{ record.task_name || '-' }}</a-descriptions-item>
              <a-descriptions-item label="接龙ID">{{ record.thread_id || '-' }}</a-descriptions-item>
              <a-descriptions-item label="打卡时间">{{ formatDateTime(record.check_in_time) }}</a-descriptions-item>
              <a-descriptions-item label="状态">
                <a-tag v-if="record.status === 'success'" color="success">✅ 打卡成功</a-tag>
                <a-tag v-else-if="record.status === 'out_of_time'" color="default">🕐 时间范围外</a-tag>
                <a-tag v-else-if="record.status === 'unknown'" color="warning">❗ 打卡异常</a-tag>
                <a-tag v-else color="error">❌ 打卡失败</a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="触发方式">
                <a-tag v-if="record.trigger_type === 'manual'" color="blue">手动</a-tag>
                <a-tag v-else-if="record.trigger_type === 'scheduled'" color="cyan">定时</a-tag>
                <a-tag v-else-if="record.trigger_type === 'admin'" color="orange">管理员</a-tag>
                <a-tag v-else>{{ record.trigger_type }}</a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="消息">{{ record.response_text || '-' }}</a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-space>

        <!-- Empty state -->
        <a-empty v-if="!checkInStore.loading && checkInStore.allRecords.length === 0" description="暂无打卡记录" />

        <!-- Pagination -->
        <div class="pagination-container" v-if="checkInStore.total > 0">
          <a-pagination
            v-model:current="checkInStore.currentPage"
            v-model:pageSize="checkInStore.pageSize"
            :total="checkInStore.total"
            :pageSizeOptions="['10', '20', '50', '100']"
            show-size-changer
            show-quick-jumper
            :show-total="total => `共 ${total} 条记录`"
            @change="handlePageChange"
            @showSizeChange="handleSizeChange"
          />
        </div>
      </a-card>
    </div>
  </Layout>
</template>

<script setup>
import { onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { UnorderedListOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import Layout from '@/components/Layout.vue'
import { useCheckInStore } from '@/stores/checkIn'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { formatDateTime } from '@/utils/helpers'

const checkInStore = useCheckInStore()
const { isMobile } = useBreakpoint()

// Table columns configuration
const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: '用户ID', dataIndex: 'user_id', key: 'user_id', width: 100 },
  { title: '用户邮箱', dataIndex: 'user_email', key: 'user_email', width: 180, ellipsis: true },
  { title: '任务名称', dataIndex: 'task_name', key: 'task_name', width: 150, ellipsis: true },
  { title: '接龙ID', dataIndex: 'thread_id', key: 'thread_id', width: 150, ellipsis: true },
  { title: '打卡时间', dataIndex: 'check_in_time', key: 'check_in_time', width: 180 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 120 },
  { title: '触发方式', dataIndex: 'trigger_type', key: 'trigger_type', width: 120 },
  { title: '消息', dataIndex: 'response_text', key: 'response_text', ellipsis: true },
]

const handleRefresh = async () => {
  try {
    await checkInStore.fetchAllRecords()
    message.success('刷新成功')
  } catch (error) {
    message.error(error.message || '刷新失败')
  }
}

const handlePageChange = () => {
  checkInStore.fetchAllRecords()
}

const handleSizeChange = () => {
  checkInStore.currentPage = 1
  checkInStore.fetchAllRecords()
}

onMounted(() => {
  checkInStore.fetchAllRecords()
})
</script>

<style scoped>
.admin-records-container {
  max-width: 1600px;
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

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
