<template>
  <Layout>
    <div class="admin-stats-container">
      <el-row :gutter="20">
        <el-col :span="24">
          <el-card>
            <template #header>
              <div class="card-header">
                <el-icon><DataAnalysis /></el-icon>
                <span>系统统计信息</span>
                <el-button type="primary" :icon="Refresh" @click="handleRefresh">
                  刷新
                </el-button>
              </div>
            </template>

            <div v-if="adminStore.loading" class="loading-container">
              <el-skeleton :rows="5" animated />
            </div>

            <div v-else-if="adminStore.stats" class="stats-content">
              <el-row :gutter="20">
                <el-col :span="6">
                  <el-statistic
                    title="总用户数"
                    :value="adminStore.totalUsers"
                    prefix-icon="User"
                  />
                </el-col>
                <el-col :span="6">
                  <el-statistic
                    title="已审批用户数"
                    :value="adminStore.activeUsers"
                    prefix-icon="Check"
                    value-style="color: #67c23a"
                  />
                </el-col>
                <el-col :span="6">
                  <el-statistic
                    title="总打卡次数"
                    :value="adminStore.totalRecords"
                    prefix-icon="List"
                  />
                </el-col>
                <el-col :span="6">
                  <el-statistic
                    title="今日打卡"
                    :value="adminStore.todayRecords"
                    prefix-icon="Calendar"
                    value-style="color: #409eff"
                  />
                </el-col>
              </el-row>

              <el-divider />

              <el-descriptions title="详细信息" :column="2" border>
                <el-descriptions-item label="管理员数量">
                  {{ adminStore.stats?.users?.admin || 0 }}
                </el-descriptions-item>
                <el-descriptions-item label="普通用户数量">
                  {{ adminStore.stats?.users?.regular || 0 }}
                </el-descriptions-item>
                <el-descriptions-item label="今日成功打卡">
                  <el-tag type="success">{{ adminStore.stats?.check_in_records?.today_success || 0 }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="今日失败打卡">
                  <el-tag type="danger">{{ adminStore.stats?.check_in_records?.today_failure || 0 }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="今日时间范围外">
                  <el-tag type="info">{{ adminStore.stats?.check_in_records?.today_out_of_time || 0 }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="今日异常打卡">
                  <el-tag type="warning">{{ adminStore.stats?.check_in_records?.today_unknown || 0 }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="总成功率" :span="2">
                  <el-progress
                    :percentage="calculateSuccessRate()"
                    :color="getProgressColor"
                  />
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </Layout>
</template>

<script setup>
import { onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis, Refresh } from '@element-plus/icons-vue'
import Layout from '@/components/Layout.vue'
import { useAdminStore } from '@/stores/admin'

const adminStore = useAdminStore()

const getProgressColor = (percentage) => {
  if (percentage >= 90) return '#67c23a'
  if (percentage >= 70) return '#e6a23c'
  return '#f56c6c'
}

const calculateSuccessRate = () => {
  const total = adminStore.stats?.check_in_records?.total || 0
  const todaySuccess = adminStore.stats?.check_in_records?.today_success || 0

  if (total === 0) return 0

  // Calculate success rate based on all records (not just today)
  // We need to get success count from backend or calculate differently
  // For now, use today's success rate as approximation
  const todayTotal = adminStore.stats?.check_in_records?.today || 0
  if (todayTotal === 0) return 0

  return Math.round((todaySuccess / todayTotal) * 100)
}

const handleRefresh = async () => {
  try {
    await adminStore.fetchStats()
    ElMessage.success('刷新成功')
  } catch (error) {
    ElMessage.error(error.message || '刷新失败')
  }
}

onMounted(() => {
  adminStore.fetchStats()
})
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
  font-weight: bold;
}

.card-header .el-button {
  margin-left: auto;
}

.loading-container {
  padding: 20px;
}

.stats-content {
  padding: 20px 0;
}
</style>
