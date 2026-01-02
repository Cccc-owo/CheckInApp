<template>
  <Layout>
    <div class="task-records-view">
      <div class="max-w-7xl mx-auto">
        <!-- Header -->
        <div class="mb-8">
          <a-button
            @click="router.back()"
            type="link"
            class="mb-4 flex items-center"
          >
            <template #icon><LeftOutlined /></template>
            返回任务列表
          </a-button>

          <div v-if="currentTask" class="fluent-card p-6">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <h1 class="text-3xl font-bold text-gradient mb-2">{{ currentTask.name || '未命名任务' }}</h1>
                <div class="flex items-center gap-4 text-sm text-gray-600">
                  <span class="flex items-center">
                    <NumberOutlined class="mr-1" />
                    接龙 ID: {{ getThreadId(currentTask) }}
                  </span>
                  <a-tag :color="currentTask.is_active ? 'success' : 'default'">
                    {{ currentTask.is_active ? '启用中' : '已禁用' }}
                  </a-tag>
                </div>
              </div>
              <a-button
                type="primary"
                :loading="checkInLoading"
                @click="handleManualCheckIn"
              >
                {{ checkInLoading ? '打卡中...' : '立即打卡' }}
              </a-button>
            </div>
          </div>
        </div>

        <!-- Stats Summary -->
        <a-row :gutter="[16, 16]" class="mb-6">
          <a-col :xs="12" :sm="8" :md="4">
            <div class="fluent-card p-5 animate-slide-up">
              <p class="text-sm text-gray-600 mb-1">总打卡次数</p>
              <p class="text-2xl font-bold text-gray-800">{{ recordStats.total }}</p>
            </div>
          </a-col>
          <a-col :xs="12" :sm="8" :md="4">
            <div class="fluent-card p-5 animate-slide-up" style="animation-delay: 0.05s">
              <p class="text-sm text-gray-600 mb-1">成功次数</p>
              <p class="text-2xl font-bold text-green-600">{{ recordStats.success }}</p>
            </div>
          </a-col>
          <a-col :xs="12" :sm="8" :md="4">
            <div class="fluent-card p-5 animate-slide-up" style="animation-delay: 0.1s">
              <p class="text-sm text-gray-600 mb-1">时间范围外</p>
              <p class="text-2xl font-bold text-blue-600">{{ recordStats.outOfTime }}</p>
            </div>
          </a-col>
          <a-col :xs="12" :sm="8" :md="4">
            <div class="fluent-card p-5 animate-slide-up" style="animation-delay: 0.15s">
              <p class="text-sm text-gray-600 mb-1">失败次数</p>
              <p class="text-2xl font-bold text-red-600">{{ recordStats.failure }}</p>
            </div>
          </a-col>
          <a-col :xs="12" :sm="8" :md="4">
            <div class="fluent-card p-5 animate-slide-up" style="animation-delay: 0.2s">
              <p class="text-sm text-gray-600 mb-1">异常次数</p>
              <p class="text-2xl font-bold text-orange-600">{{ recordStats.unknown }}</p>
            </div>
          </a-col>
          <a-col :xs="12" :sm="8" :md="4">
            <div class="fluent-card p-5 animate-slide-up" style="animation-delay: 0.25s">
              <p class="text-sm text-gray-600 mb-1">成功率</p>
              <p class="text-2xl font-bold text-purple-600">{{ recordStats.successRate }}%</p>
            </div>
          </a-col>
        </a-row>

        <!-- Filters -->
        <div class="fluent-card p-4 mb-6">
          <a-space wrap :size="[16, 16]">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-gray-700">状态筛选:</span>
              <a-radio-group v-model:value="filterStatus" button-style="solid" size="small" @change="handleFilterChange">
                <a-radio-button value="">全部</a-radio-button>
                <a-radio-button value="success">成功</a-radio-button>
                <a-radio-button value="out_of_time">时间范围外</a-radio-button>
                <a-radio-button value="failure">失败</a-radio-button>
                <a-radio-button value="unknown">异常</a-radio-button>
              </a-radio-group>
            </div>

            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-gray-700">触发方式:</span>
              <a-radio-group v-model:value="filterTrigger" button-style="solid" size="small" @change="handleFilterChange">
                <a-radio-button value="">全部</a-radio-button>
                <a-radio-button value="scheduler">自动</a-radio-button>
                <a-radio-button value="manual">手动</a-radio-button>
              </a-radio-group>
            </div>

            <a-button size="small" @click="fetchRecords">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </a-space>
        </div>

        <!-- Records List -->
        <div v-if="loading" class="space-y-4">
          <a-card v-for="i in 5" :key="i">
            <a-skeleton :active="true" :paragraph="{ rows: 3 }" />
          </a-card>
        </div>

        <div v-else-if="records.length === 0" class="fluent-card p-12 text-center">
          <FileTextOutlined class="text-8xl text-gray-300 mb-4" />
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
                <div class="flex items-center gap-3 mb-2 flex-wrap">
                  <h3 class="text-lg font-semibold text-gray-800">
                    打卡记录 #{{ record.id }}
                  </h3>
                  <a-tag
                    v-if="record.status === 'success'"
                    color="success"
                  >✅ 打卡成功</a-tag>
                  <a-tag
                    v-else-if="record.status === 'out_of_time'"
                    color="default"
                  >🕐 时间范围外</a-tag>
                  <a-tag
                    v-else-if="record.status === 'unknown'"
                    color="warning"
                  >❗ 打卡异常</a-tag>
                  <a-tag
                    v-else
                    color="error"
                  >❌ 打卡失败</a-tag>
                  <a-tag :color="record.trigger_type === 'scheduled' ? 'blue' : 'orange'">
                    {{ record.trigger_type === 'scheduled' ? '自动触发' : '手动触发' }}
                  </a-tag>
                </div>
                <div class="flex items-center text-sm text-gray-600">
                  <ClockCircleOutlined class="mr-1" />
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
          <a-pagination
            v-model:current="currentPage"
            v-model:pageSize="pageSize"
            :total="total"
            :pageSizeOptions="['10', '20', '50', '100']"
            show-size-changer
            show-quick-jumper
            :show-total="total => `共 ${total} 条记录`"
            @change="handlePageChange"
            @showSizeChange="handleSizeChange"
          />
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  LeftOutlined,
  NumberOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue'
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

// 从 payload_config 中提取 ThreadId
const getThreadId = (task) => {
  if (!task || !task.payload_config) return '未知'

  try {
    const payload = JSON.parse(task.payload_config)
    return payload.ThreadId || '未知'
  } catch (e) {
    console.error('解析 payload_config 失败:', e)
    return '未知'
  }
}

// 获取任务详情
const fetchTaskDetail = async () => {
  try {
    currentTask.value = await taskStore.fetchTask(taskId.value)
  } catch (error) {
    message.error(error.message || '获取任务详情失败')
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
    message.error(error.message || '获取打卡记录失败')
  } finally {
    loading.value = false
  }
}

// 手动打卡
const handleManualCheckIn = async () => {
  checkInLoading.value = true

  // 显示持久化通知
  const hide = message.loading('正在打卡中，请稍候... 您可以继续浏览其他页面', 0)

  try {
    const result = await taskStore.checkInTask(taskId.value)
    hide()

    if (result.success) {
      message.success('打卡成功')
      // 刷新记录列表
      await fetchRecords()
    } else {
      message.warning(result.message || '打卡失败')
    }
  } catch (error) {
    hide()
    message.error(error.message || '打卡失败')
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
