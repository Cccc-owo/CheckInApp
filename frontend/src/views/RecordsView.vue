<template>
  <Layout>
    <div class="records-container">
      <el-card>
        <template #header>
          <div class="card-header">
            <div>
              <el-icon><List /></el-icon>
              <span>我的打卡记录</span>
            </div>
            <el-button type="primary" :icon="Refresh" @click="handleRefresh">
              刷新
            </el-button>
          </div>
        </template>

        <!-- 统计信息 -->
        <div class="stats-container">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-statistic title="总打卡次数" :value="total" />
            </el-col>
            <el-col :span="8">
              <el-statistic
                title="成功次数"
                :value="successCount"
                value-style="color: #67c23a"
              />
            </el-col>
            <el-col :span="8">
              <el-statistic
                title="成功率"
                :value="parseFloat(checkInStore.successRate)"
                suffix="%"
                :precision="2"
              />
            </el-col>
          </el-row>
        </div>

        <el-divider />

        <!-- 记录表格 -->
        <el-table
          :data="checkInStore.myRecords"
          v-loading="checkInStore.loading"
          stripe
          border
        >
          <el-table-column prop="id" label="ID" width="80" />

          <el-table-column prop="check_in_time" label="打卡时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.check_in_time) }}
            </template>
          </el-table-column>

          <el-table-column prop="status" label="状态" width="120">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'success'" type="success">✅ 打卡成功</el-tag>
              <el-tag v-else-if="row.status === 'out_of_time'" type="info">🕐 时间范围外</el-tag>
              <el-tag v-else-if="row.status === 'unknown'" type="warning">❗ 打卡异常</el-tag>
              <el-tag v-else type="danger">❌ 打卡失败</el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="trigger_type" label="触发方式" width="120">
            <template #default="{ row }">
              <el-tag v-if="row.trigger_type === 'manual'" type="primary">手动</el-tag>
              <el-tag v-else-if="row.trigger_type === 'scheduled'" type="info">定时</el-tag>
              <el-tag v-else-if="row.trigger_type === 'admin'" type="warning">管理员</el-tag>
              <el-tag v-else>{{ row.trigger_type }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="response_text" label="消息" min-width="200" show-overflow-tooltip />
        </el-table>

        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="checkInStore.currentPage"
            v-model:page-size="checkInStore.pageSize"
            :total="total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @current-change="handlePageChange"
            @size-change="handleSizeChange"
          />
        </div>
      </el-card>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { List, Refresh } from '@element-plus/icons-vue'
import Layout from '@/components/Layout.vue'
import { useCheckInStore } from '@/stores/checkIn'
import { formatDateTime } from '@/utils/helpers'

const checkInStore = useCheckInStore()

const total = computed(() => checkInStore.total)

const successCount = computed(() => {
  return checkInStore.myRecords.filter((r) => r.status === 'success').length
})

// 刷新数据
const handleRefresh = async () => {
  try {
    await checkInStore.fetchMyRecords()
    ElMessage.success('刷新成功')
  } catch (error) {
    ElMessage.error(error.message || '刷新失败')
  }
}

// 页码改变
const handlePageChange = () => {
  checkInStore.fetchMyRecords()
}

// 每页数量改变
const handleSizeChange = () => {
  checkInStore.currentPage = 1
  checkInStore.fetchMyRecords()
}

onMounted(() => {
  checkInStore.fetchMyRecords()
})
</script>

<style scoped>
.records-container {
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

.stats-container {
  padding: 20px 0;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
