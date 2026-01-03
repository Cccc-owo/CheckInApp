<template>
  <Layout>
    <div class="admin-stats-container">
      <a-row :gutter="20">
        <a-col :span="24">
          <a-card>
            <template #title>
              <div class="card-header">
                <BarChartOutlined />
                <span>系统统计信息</span>
                <a-button type="primary" @click="handleRefresh">
                  <template #icon><ReloadOutlined /></template>
                  刷新
                </a-button>
              </div>
            </template>

            <div v-if="adminStore.loading" class="loading-container">
              <a-skeleton :active="true" :paragraph="{ rows: 5 }" />
            </div>

            <div v-else-if="adminStore.stats" class="stats-content">
              <a-row :gutter="[20, 20]">
                <a-col :xs="24" :sm="12" :md="6">
                  <a-statistic title="总用户数" :value="adminStore.totalUsers">
                    <template #prefix>
                      <UserOutlined />
                    </template>
                  </a-statistic>
                </a-col>
                <a-col :xs="24" :sm="12" :md="6">
                  <a-statistic
                    title="已审批用户数"
                    :value="adminStore.activeUsers"
                    :value-style="{ color: '#52c41a' }"
                  >
                    <template #prefix>
                      <CheckOutlined />
                    </template>
                  </a-statistic>
                </a-col>
                <a-col :xs="24" :sm="12" :md="6">
                  <a-statistic title="总打卡次数" :value="adminStore.totalRecords">
                    <template #prefix>
                      <UnorderedListOutlined />
                    </template>
                  </a-statistic>
                </a-col>
                <a-col :xs="24" :sm="12" :md="6">
                  <a-statistic
                    title="今日打卡"
                    :value="adminStore.todayRecords"
                    :value-style="{ color: '#1890ff' }"
                  >
                    <template #prefix>
                      <CalendarOutlined />
                    </template>
                  </a-statistic>
                </a-col>
              </a-row>

              <a-divider />

              <a-descriptions title="详细信息" :column="{ xs: 1, sm: 1, md: 2 }" bordered>
                <a-descriptions-item label="管理员数量">
                  {{ adminStore.stats?.users?.admin || 0 }}
                </a-descriptions-item>
                <a-descriptions-item label="普通用户数量">
                  {{ adminStore.stats?.users?.regular || 0 }}
                </a-descriptions-item>
                <a-descriptions-item label="今日成功打卡">
                  <a-tag color="success">{{
                    adminStore.stats?.check_in_records?.today_success || 0
                  }}</a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="今日失败打卡">
                  <a-tag color="error">{{
                    adminStore.stats?.check_in_records?.today_failure || 0
                  }}</a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="今日时间范围外">
                  <a-tag color="default">{{
                    adminStore.stats?.check_in_records?.today_out_of_time || 0
                  }}</a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="今日异常打卡">
                  <a-tag color="warning">{{
                    adminStore.stats?.check_in_records?.today_unknown || 0
                  }}</a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="总成功率" :span="2">
                  <a-progress
                    :percent="calculateSuccessRate()"
                    :stroke-color="getProgressColor(calculateSuccessRate())"
                  />
                </a-descriptions-item>
              </a-descriptions>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>
  </Layout>
</template>

<script setup>
import { onMounted } from 'vue';
import { message } from 'ant-design-vue';
import {
  BarChartOutlined,
  ReloadOutlined,
  UserOutlined,
  CheckOutlined,
  UnorderedListOutlined,
  CalendarOutlined,
} from '@ant-design/icons-vue';
import Layout from '@/components/Layout.vue';
import { useAdminStore } from '@/stores/admin';

const adminStore = useAdminStore();

const getProgressColor = percentage => {
  if (percentage >= 90) return '#52c41a';
  if (percentage >= 70) return '#faad14';
  return '#ff4d4f';
};

const calculateSuccessRate = () => {
  const total = adminStore.stats?.check_in_records?.total || 0;
  const todaySuccess = adminStore.stats?.check_in_records?.today_success || 0;

  if (total === 0) return 0;

  // Calculate success rate based on all records (not just today)
  // We need to get success count from backend or calculate differently
  // For now, use today's success rate as approximation
  const todayTotal = adminStore.stats?.check_in_records?.today || 0;
  if (todayTotal === 0) return 0;

  return Math.round((todaySuccess / todayTotal) * 100);
};

const handleRefresh = async () => {
  try {
    await adminStore.fetchStats();
    message.success('刷新成功');
  } catch (error) {
    message.error(error.message || '刷新失败');
  }
};

onMounted(() => {
  adminStore.fetchStats();
});
</script>

<style scoped>
.admin-stats-container {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.card-header :deep(.ant-btn) {
  margin-left: auto;
}

.loading-container {
  padding: 20px;
}

.stats-content {
  padding: 20px 0;
}
</style>
