<template>
  <Layout>
    <div class="task-records-view">
      <div class="max-w-7xl mx-auto">
        <!-- Header -->
        <div class="mb-8">
          <a-button type="link" class="mb-4 flex items-center" @click="router.back()">
            <template #icon><LeftOutlined /></template>
            返回任务列表
          </a-button>

          <a-card v-if="currentTask" class="md3-card">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <h1 class="text-3xl font-bold text-gradient mb-2">
                  {{ currentTask.name || '未命名任务' }}
                </h1>
                <div class="flex items-center gap-4 text-sm text-on-surface-variant">
                  <span class="flex items-center">
                    <NumberOutlined class="mr-1" />
                    接龙 ID: {{ getThreadId(currentTask) }}
                  </span>
                  <a-tag :color="currentTask.is_active ? 'success' : 'default'">
                    {{ currentTask.is_active ? '启用中' : '已禁用' }}
                  </a-tag>
                </div>
              </div>
              <a-button type="primary" :loading="checkInLoading" @click="handleManualCheckIn">
                {{ checkInLoading ? '打卡中...' : '立即打卡' }}
              </a-button>
            </div>
          </a-card>
        </div>

        <!-- Stats Summary -->
        <a-row :gutter="[16, 16]" class="mb-6">
          <a-col :xs="12" :sm="8" :md="4">
            <a-card class="md3-card animate-slide-up">
              <p class="text-sm text-on-surface-variant mb-1">总打卡次数</p>
              <p class="text-2xl font-bold text-on-surface">{{ recordStats.total }}</p>
            </a-card>
          </a-col>
          <a-col :xs="12" :sm="8" :md="4">
            <a-card class="md3-card animate-slide-up" style="animation-delay: 0.05s">
              <p class="text-sm text-on-surface-variant mb-1">成功次数</p>
              <p class="text-2xl font-bold text-green-600 dark:text-green-400">
                {{ recordStats.success }}
              </p>
            </a-card>
          </a-col>
          <a-col :xs="12" :sm="8" :md="4">
            <a-card class="md3-card animate-slide-up" style="animation-delay: 0.1s">
              <p class="text-sm text-on-surface-variant mb-1">时间范围外</p>
              <p class="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {{ recordStats.outOfTime }}
              </p>
            </a-card>
          </a-col>
          <a-col :xs="12" :sm="8" :md="4">
            <a-card class="md3-card animate-slide-up" style="animation-delay: 0.15s">
              <p class="text-sm text-on-surface-variant mb-1">失败次数</p>
              <p class="text-2xl font-bold text-red-600 dark:text-red-400">
                {{ recordStats.failure }}
              </p>
            </a-card>
          </a-col>
          <a-col :xs="12" :sm="8" :md="4">
            <a-card class="md3-card animate-slide-up" style="animation-delay: 0.2s">
              <p class="text-sm text-on-surface-variant mb-1">异常次数</p>
              <p class="text-2xl font-bold text-orange-600 dark:text-orange-400">
                {{ recordStats.unknown }}
              </p>
            </a-card>
          </a-col>
          <a-col :xs="12" :sm="8" :md="4">
            <a-card class="md3-card animate-slide-up" style="animation-delay: 0.25s">
              <p class="text-sm text-on-surface-variant mb-1">成功率</p>
              <p class="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {{ recordStats.successRate }}%
              </p>
            </a-card>
          </a-col>
        </a-row>

        <!-- Filters -->
        <a-card class="md3-card mb-6">
          <a-space wrap :size="[16, 16]">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-on-surface">状态筛选:</span>
              <a-radio-group
                v-model:value="filterStatus"
                button-style="solid"
                size="small"
                @change="handleFilterChange"
              >
                <a-radio-button value="">全部</a-radio-button>
                <a-radio-button value="success">成功</a-radio-button>
                <a-radio-button value="out_of_time">时间范围外</a-radio-button>
                <a-radio-button value="failure">失败</a-radio-button>
                <a-radio-button value="unknown">异常</a-radio-button>
              </a-radio-group>
            </div>

            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-on-surface">触发方式:</span>
              <a-radio-group
                v-model:value="filterTrigger"
                button-style="solid"
                size="small"
                @change="handleFilterChange"
              >
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
        </a-card>

        <!-- Records List -->
        <div v-if="loading" class="space-y-4">
          <a-card v-for="i in 5" :key="i">
            <a-skeleton :active="true" :paragraph="{ rows: 3 }" />
          </a-card>
        </div>

        <a-card
          v-else-if="records.length === 0"
          class="md3-card text-center"
          style="padding: 48px 20px"
        >
          <FileTextOutlined class="text-8xl text-on-surface-variant opacity-30 mb-4" />
          <h3 class="text-xl font-semibold text-on-surface mb-2">暂无打卡记录</h3>
          <p class="text-on-surface-variant">当前筛选条件下没有找到任何打卡记录</p>
        </a-card>

        <div v-else class="space-y-4">
          <a-card
            v-for="record in records"
            :key="record.id"
            class="md3-card hover:shadow-xl transition-all animate-slide-up"
          >
            <div class="flex items-start justify-between mb-4">
              <div class="flex-1">
                <div class="flex items-center gap-3 mb-2 flex-wrap">
                  <h3 class="text-lg font-semibold text-on-surface">打卡记录 #{{ record.id }}</h3>
                  <a-tag v-if="record.status === 'success'" color="success">✅ 打卡成功</a-tag>
                  <a-tag v-else-if="record.status === 'out_of_time'" color="default"
                    >🕐 时间范围外</a-tag
                  >
                  <a-tag v-else-if="record.status === 'unknown'" color="warning">❗ 打卡异常</a-tag>
                  <a-tag v-else color="error">❌ 打卡失败</a-tag>
                  <a-tag :color="record.trigger_type === 'scheduled' ? 'blue' : 'orange'">
                    {{ record.trigger_type === 'scheduled' ? '自动触发' : '手动触发' }}
                  </a-tag>
                </div>
                <div class="flex items-center text-sm text-on-surface-variant">
                  <ClockCircleOutlined class="mr-1" />
                  {{ formatDateTime(record.check_in_time) }}
                </div>
              </div>
            </div>

            <!-- Record Details -->
            <div
              class="bg-surface-container-high dark:bg-surface-container rounded-lg p-4 space-y-2"
            >
              <div v-if="record.response_text" class="flex items-start">
                <span class="text-sm font-medium text-on-surface-variant w-20">响应:</span>
                <span class="text-sm text-on-surface flex-1">{{ record.response_text }}</span>
              </div>

              <div v-if="record.error_message" class="flex items-start">
                <span class="text-sm font-medium text-error w-20">错误:</span>
                <span class="text-sm text-error flex-1">{{ record.error_message }}</span>
              </div>
            </div>
          </a-card>
        </div>

        <!-- Pagination -->
        <div v-if="!loading && records.length > 0" class="mt-6 flex justify-center">
          <a-pagination
            v-model:current="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            :page-size-options="['10', '20', '50', '100']"
            show-size-changer
            show-quick-jumper
            :show-total="total => `共 ${total} 条记录`"
            @change="handlePageChange"
            @show-size-change="handleSizeChange"
          />
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  LeftOutlined,
  NumberOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';
import Layout from '@/components/Layout.vue';
import { useTaskStore } from '@/stores/task';
import { formatDateTime } from '@/utils/helpers';
import { usePolling } from '@/composables/usePolling';

const route = useRoute();
const router = useRouter();
const taskStore = useTaskStore();
const { startPolling } = usePolling();

const taskId = computed(() => parseInt(route.params.taskId));
const currentTask = ref(null);
const records = ref([]);
const loading = ref(false);
const checkInLoading = ref(false);

// Pagination
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);

// Filters
const filterStatus = ref('');
const filterTrigger = ref('');

// Stats
const recordStats = computed(() => {
  const success = records.value.filter(r => r.status === 'success').length;
  const outOfTime = records.value.filter(r => r.status === 'out_of_time').length;
  const failure = records.value.filter(r => r.status === 'failure').length;
  const unknown = records.value.filter(r => r.status === 'unknown').length;
  const totalRecords = records.value.length;
  const successRate = totalRecords > 0 ? Math.round((success / totalRecords) * 100) : 0;

  return {
    total: totalRecords,
    success,
    outOfTime,
    failure,
    unknown,
    successRate,
  };
});

// 从 payload_config 中提取 ThreadId
const getThreadId = task => {
  if (!task || !task.payload_config) return '未知';

  try {
    const payload = JSON.parse(task.payload_config);
    return payload.ThreadId || '未知';
  } catch (e) {
    console.error('解析 payload_config 失败:', e);
    return '未知';
  }
};

// 获取任务详情
const fetchTaskDetail = async () => {
  try {
    currentTask.value = await taskStore.fetchTask(taskId.value);
  } catch (error) {
    message.error(error.message || '获取任务详情失败');
    router.push('/tasks');
  }
};

// 获取打卡记录
const fetchRecords = async () => {
  loading.value = true;
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    };

    if (filterStatus.value) {
      params.status = filterStatus.value;
    }

    if (filterTrigger.value) {
      params.trigger_type = filterTrigger.value;
    }

    const response = await taskStore.fetchTaskRecords(taskId.value, params);

    // 后端现在返回 { records, total, skip, limit }
    if (response.records) {
      records.value = response.records;
      total.value = response.total || 0;
    } else if (Array.isArray(response)) {
      // 兼容旧格式
      records.value = response;
      total.value = response.length;
    } else {
      records.value = [];
      total.value = 0;
    }
  } catch (error) {
    message.error(error.message || '获取打卡记录失败');
  } finally {
    loading.value = false;
  }
};

// 手动打卡
const handleManualCheckIn = async () => {
  checkInLoading.value = true;

  try {
    // 调用异步打卡接口，立即返回 record_id
    const result = await taskStore.checkInTask(taskId.value);

    // 获取 record_id
    const recordId = result.record_id;
    if (!recordId) {
      message.error('打卡请求失败：未获取到记录ID');
      checkInLoading.value = false;
      return;
    }

    // 如果初始状态就是失败，显示错误并刷新记录列表
    if (result.status === 'failure') {
      const errorMsg =
        (result.error_message && result.error_message.trim()) ||
        (result.response_text && result.response_text.trim()) ||
        '打卡失败';
      message.error(errorMsg);
      checkInLoading.value = false;
      await fetchRecords();
      return;
    }

    // 显示提示消息
    message.info('打卡任务已启动，正在后台处理...');

    // 使用轮询 composable 检查打卡状态
    startPolling(
      async () => {
        const status = await taskStore.getCheckInRecordStatus(recordId);
        return {
          completed: status.status !== 'pending',
          success: status.status === 'success',
          data: status,
        };
      },
      {
        onSuccess: async () => {
          checkInLoading.value = false;
          message.success('打卡成功！');
          await fetchRecords();
        },
        onFailure: async statusData => {
          checkInLoading.value = false;
          // 优先使用 error_message，如果为空则使用 response_text，都为空则使用默认消息
          const errorMsg =
            (statusData.error_message && statusData.error_message.trim()) ||
            (statusData.response_text && statusData.response_text.trim()) ||
            '打卡失败';
          message.error(errorMsg);
          await fetchRecords();
        },
        onTimeout: () => {
          checkInLoading.value = false;
          message.warning('打卡处理时间较长，请稍后查看打卡记录');
        },
      }
    );
  } catch (error) {
    console.error('启动打卡失败:', error);
    checkInLoading.value = false;
    message.error(error.message || '启动打卡任务失败');
  }
};

// 筛选变化
const handleFilterChange = () => {
  currentPage.value = 1;
  fetchRecords();
};

// 分页变化
const handlePageChange = () => {
  fetchRecords();
};

const handleSizeChange = () => {
  currentPage.value = 1;
  fetchRecords();
};

onMounted(async () => {
  await fetchTaskDetail();
  await fetchRecords();
});
</script>

<style scoped>
/* Additional component-specific styles if needed */
</style>
