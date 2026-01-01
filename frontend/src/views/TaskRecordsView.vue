<template>
  <Layout>
    <div class="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 p-6">
      <div class="max-w-7xl mx-auto">
        <!-- Header -->
        <div class="mb-8 animate-fade-in">
          <button
            @click="router.back()"
            class="mb-4 flex items-center text-gray-600 hover:text-gray-900 transition-colors"
          >
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            返回任务列表
          </button>

          <div v-if="currentTask" class="fluent-card p-6">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <h1 class="text-3xl font-bold text-gradient mb-2">{{ currentTask.name || '未命名任务' }}</h1>
                <div class="flex items-center gap-4 text-sm text-gray-600">
                  <span class="flex items-center">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                    </svg>
                    接龙 ID: {{ currentTask.thread_id }}
                  </span>
                  <span :class="currentTask.is_active ? 'status-success' : 'status-info'">
                    {{ currentTask.is_active ? '启用中' : '已禁用' }}
                  </span>
                </div>
              </div>
              <button
                @click="handleManualCheckIn"
                :disabled="checkInLoading"
                class="md3-button-filled"
              >
                {{ checkInLoading ? '打卡中...' : '立即打卡' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Stats Summary -->
        <div class="grid grid-cols-1 md:grid-cols-6 gap-4 mb-6">
          <div class="fluent-card p-5 animate-slide-up">
            <p class="text-sm text-gray-600 mb-1">总打卡次数</p>
            <p class="text-2xl font-bold text-gray-800">{{ recordStats.total }}</p>
          </div>
          <div class="fluent-card p-5 animate-slide-up" style="animation-delay: 0.05s">
            <p class="text-sm text-gray-600 mb-1">成功次数</p>
            <p class="text-2xl font-bold text-green-600">{{ recordStats.success }}</p>
          </div>
          <div class="fluent-card p-5 animate-slide-up" style="animation-delay: 0.1s">
            <p class="text-sm text-gray-600 mb-1">时间范围外</p>
            <p class="text-2xl font-bold text-blue-600">{{ recordStats.outOfTime }}</p>
          </div>
          <div class="fluent-card p-5 animate-slide-up" style="animation-delay: 0.15s">
            <p class="text-sm text-gray-600 mb-1">失败次数</p>
            <p class="text-2xl font-bold text-red-600">{{ recordStats.failure }}</p>
          </div>
          <div class="fluent-card p-5 animate-slide-up" style="animation-delay: 0.2s">
            <p class="text-sm text-gray-600 mb-1">异常次数</p>
            <p class="text-2xl font-bold text-orange-600">{{ recordStats.unknown }}</p>
          </div>
          <div class="fluent-card p-5 animate-slide-up" style="animation-delay: 0.25s">
            <p class="text-sm text-gray-600 mb-1">成功率</p>
            <p class="text-2xl font-bold text-purple-600">{{ recordStats.successRate }}%</p>
          </div>
        </div>

        <!-- Filters -->
        <div class="fluent-card p-4 mb-6">
          <div class="flex flex-wrap items-center gap-4">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-gray-700">状态筛选:</span>
              <el-radio-group v-model="filterStatus" size="small" @change="handleFilterChange">
                <el-radio-button label="">全部</el-radio-button>
                <el-radio-button label="success">成功</el-radio-button>
                <el-radio-button label="out_of_time">时间范围外</el-radio-button>
                <el-radio-button label="failure">失败</el-radio-button>
                <el-radio-button label="unknown">异常</el-radio-button>
              </el-radio-group>
            </div>

            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-gray-700">触发方式:</span>
              <el-radio-group v-model="filterTrigger" size="small" @change="handleFilterChange">
                <el-radio-button label="">全部</el-radio-button>
                <el-radio-button label="scheduler">自动</el-radio-button>
                <el-radio-button label="manual">手动</el-radio-button>
              </el-radio-group>
            </div>

            <div class="flex-1"></div>

            <el-button size="small" @click="fetchRecords">
              <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              刷新
            </el-button>
          </div>
        </div>

        <!-- Records List -->
        <div v-if="loading" class="space-y-4">
          <div v-for="i in 5" :key="i" class="fluent-card p-6">
            <div class="skeleton h-6 w-1/4 mb-3"></div>
            <div class="skeleton h-4 w-full mb-2"></div>
            <div class="skeleton h-4 w-3/4"></div>
          </div>
        </div>

        <div v-else-if="records.length === 0" class="fluent-card p-12 text-center">
          <svg class="w-20 h-20 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 class="text-xl font-semibold text-gray-700 mb-2">暂无打卡记录</h3>
          <p class="text-gray-500">当前筛选条件下没有找到任何打卡记录</p>
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="record in records"
            :key="record.id"
            class="fluent-card p-6 hover:shadow-xl transition-all animate-slide-up"
          >
            <div class="flex items-start justify-between mb-4">
              <div class="flex-1">
                <div class="flex items-center gap-3 mb-2">
                  <h3 class="text-lg font-semibold text-gray-800">
                    打卡记录 #{{ record.id }}
                  </h3>
                  <span
                    v-if="record.status === 'success'"
                    class="status-success"
                  >✅ 打卡成功</span>
                  <span
                    v-else-if="record.status === 'out_of_time'"
                    class="status-info"
                  >🕐 时间范围外</span>
                  <span
                    v-else-if="record.status === 'unknown'"
                    class="status-warning"
                  >❗ 打卡异常</span>
                  <span
                    v-else
                    class="status-error"
                  >❌ 打卡失败</span>
                  <span :class="record.trigger_type === 'scheduler' ? 'status-info' : 'status-warning'">
                    {{ record.trigger_type === 'scheduler' ? '自动触发' : '手动触发' }}
                  </span>
                </div>
                <div class="flex items-center text-sm text-gray-600">
                  <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {{ formatDateTime(record.check_in_time) }}
                </div>
              </div>
            </div>

            <!-- Record Details -->
            <div class="bg-gray-50 rounded-lg p-4 space-y-2">
              <div v-if="record.response_text" class="flex items-start">
                <span class="text-sm font-medium text-gray-700 w-20">响应:</span>
                <span class="text-sm text-gray-900 flex-1">{{ record.response_text }}</span>
              </div>

              <div v-if="record.error_message" class="flex items-start">
                <span class="text-sm font-medium text-red-700 w-20">错误:</span>
                <span class="text-sm text-red-600 flex-1">{{ record.error_message }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="!loading && records.length > 0" class="mt-6 flex justify-center">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import Layout from '@/components/Layout.vue'
import { useTaskStore } from '@/stores/task'
import { formatDateTime } from '@/utils/helpers'

const route = useRoute()
const router = useRouter()
const taskStore = useTaskStore()

const taskId = computed(() => parseInt(route.params.taskId))
const currentTask = ref(null)
const records = ref([])
const loading = ref(false)
const checkInLoading = ref(false)

// Pagination
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// Filters
const filterStatus = ref('')
const filterTrigger = ref('')

// Stats
const recordStats = computed(() => {
  const success = records.value.filter(r => r.status === 'success').length
  const outOfTime = records.value.filter(r => r.status === 'out_of_time').length
  const failure = records.value.filter(r => r.status === 'failure').length
  const unknown = records.value.filter(r => r.status === 'unknown').length
  const totalRecords = records.value.length
  const successRate = totalRecords > 0 ? Math.round((success / totalRecords) * 100) : 0

  return {
    total: totalRecords,
    success,
    outOfTime,
    failure,
    unknown,
    successRate,
  }
})

// 获取任务详情
const fetchTaskDetail = async () => {
  try {
    currentTask.value = await taskStore.fetchTask(taskId.value)
  } catch (error) {
    ElMessage.error(error.message || '获取任务详情失败')
    router.push('/tasks')
  }
}

// 获取打卡记录
const fetchRecords = async () => {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    }

    if (filterStatus.value) {
      params.status = filterStatus.value
    }

    if (filterTrigger.value) {
      params.trigger_type = filterTrigger.value
    }

    const response = await taskStore.fetchTaskRecords(taskId.value, params)

    // API 可能返回数组或对象
    if (Array.isArray(response)) {
      records.value = response
      total.value = response.length
    } else if (response.items) {
      records.value = response.items
      total.value = response.total || response.items.length
    } else {
      records.value = []
      total.value = 0
    }
  } catch (error) {
    ElMessage.error(error.message || '获取打卡记录失败')
  } finally {
    loading.value = false
  }
}

// 手动打卡
const handleManualCheckIn = async () => {
  checkInLoading.value = true

  // 显示持久化通知
  const loadingMessage = ElMessage({
    message: '正在打卡中，请稍候... 您可以继续浏览其他页面',
    type: 'info',
    duration: 0,
    showClose: false
  })

  try {
    const result = await taskStore.checkInTask(taskId.value)
    loadingMessage.close()

    if (result.success) {
      ElMessage.success('打卡成功')
      // 刷新记录列表
      await fetchRecords()
    } else {
      ElMessage.warning(result.message || '打卡失败')
    }
  } catch (error) {
    loadingMessage.close()
    ElMessage.error(error.message || '打卡失败')
  } finally {
    checkInLoading.value = false
  }
}

// 筛选变化
const handleFilterChange = () => {
  currentPage.value = 1
  fetchRecords()
}

// 分页变化
const handlePageChange = () => {
  fetchRecords()
}

const handleSizeChange = () => {
  currentPage.value = 1
  fetchRecords()
}

// 格式化响应数据
const formatResponse = (data) => {
  if (!data) return '-'
  if (typeof data === 'string') {
    try {
      const parsed = JSON.parse(data)
      return JSON.stringify(parsed, null, 2).substring(0, 200) + (data.length > 200 ? '...' : '')
    } catch {
      return data.substring(0, 200) + (data.length > 200 ? '...' : '')
    }
  }
  return JSON.stringify(data, null, 2).substring(0, 200)
}

onMounted(async () => {
  await fetchTaskDetail()
  await fetchRecords()
})
</script>

<style scoped>
/* Additional component-specific styles if needed */
</style>
