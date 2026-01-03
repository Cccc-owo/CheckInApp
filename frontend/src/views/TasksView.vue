<template>
  <Layout>
    <div class="tasks-view">
      <div class="max-w-7xl mx-auto">
        <!-- Header Section -->
        <div class="mb-8">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h1 class="text-4xl font-bold text-gradient mb-2">任务管理</h1>
              <p class="text-on-surface-variant">管理您的自动打卡任务</p>
            </div>
            <a-button
              type="primary"
              size="large"
              @click="showCreateDialog = true"
              class="shadow-md3-3"
            >
              <template #icon>
                <PlusOutlined />
              </template>
              创建任务
            </a-button>
          </div>

          <!-- Stats Cards -->
          <a-row :gutter="[16, 16]" class="mb-6">
            <a-col :xs="24" :sm="8" :md="8">
              <a-card class="md3-card animate-slide-up">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm text-on-surface-variant mb-1">总任务数</p>
                    <p class="text-3xl font-bold text-primary">{{ taskStore.taskStats.total }}</p>
                  </div>
                  <div class="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-md3 flex items-center justify-center">
                    <FileTextOutlined class="text-2xl text-primary" />
                  </div>
                </div>
              </a-card>
            </a-col>

            <a-col :xs="24" :sm="8" :md="8">
              <a-card class="md3-card animate-slide-up" style="animation-delay: 0.1s">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm text-on-surface-variant mb-1">启用中</p>
                    <p class="text-3xl font-bold text-green-600 dark:text-green-400">{{ taskStore.taskStats.active }}</p>
                  </div>
                  <div class="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-md3 flex items-center justify-center">
                    <CheckCircleOutlined class="text-2xl text-green-600 dark:text-green-400" />
                  </div>
                </div>
              </a-card>
            </a-col>

            <a-col :xs="24" :sm="8" :md="8">
              <a-card class="md3-card animate-slide-up" style="animation-delay: 0.2s">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm text-on-surface-variant mb-1">已禁用</p>
                    <p class="text-3xl font-bold text-on-surface-variant">{{ taskStore.taskStats.inactive }}</p>
                  </div>
                  <div class="w-12 h-12 bg-surface-container-high rounded-md3 flex items-center justify-center">
                    <StopOutlined class="text-2xl text-on-surface-variant" />
                  </div>
                </div>
              </a-card>
            </a-col>
          </a-row>
        </div>

        <!-- Tasks List -->
        <div v-if="loading">
          <a-row :gutter="[16, 16]">
            <a-col :xs="24" :sm="12" :lg="8" v-for="i in 6" :key="i">
              <a-card>
                <a-skeleton :active="true" :paragraph="{ rows: 4 }" />
              </a-card>
            </a-col>
          </a-row>
        </div>

        <a-card v-else-if="taskStore.tasks.length === 0" class="md3-card text-center" style="padding: 48px 20px;">
          <FileTextOutlined class="text-8xl text-on-surface-variant opacity-30 mb-4" />
          <h3 class="text-xl font-semibold text-on-surface mb-2">暂无任务</h3>
          <p class="text-on-surface-variant mb-6">点击右上角的"创建任务"按钮开始添加您的第一个打卡任务</p>
          <a-button type="primary" @click="showCreateDialog = true">
            创建第一个任务
          </a-button>
        </a-card>

        <a-row v-else :gutter="[16, 16]">
          <a-col
            :xs="24" :sm="12" :lg="8"
            v-for="task in taskStore.tasks"
            :key="task.id"
          >
            <a-card
              class="md3-card hover:scale-105 transform transition-all cursor-pointer animate-slide-up"
              @click="viewTask(task)"
            >
              <!-- Task Header -->
              <div class="flex items-start justify-between mb-4">
                <div class="flex-1">
                  <h3 class="text-lg font-semibold text-on-surface mb-1">{{ task.name || '未命名任务' }}</h3>
                  <a-divider style="margin: 8px 0;" />
                  <p class="text-sm text-on-surface-variant">任务 ID: {{ task.id }}</p>
                </div>
                <a-tag :color="task.is_active ? 'success' : 'default'">
                  {{ task.is_active ? '启用' : '禁用' }}
                </a-tag>
              </div>

              <!-- Task Details -->
              <div class="space-y-2 mb-4">
                <div class="flex items-center text-sm text-on-surface-variant">
                  <TagOutlined class="mr-2" />
                  接龙ID: {{ getThreadId(task) }}
                </div>
                <div class="flex items-center text-sm text-on-surface-variant">
                  <ClockCircleOutlined class="mr-2" />
                  最后打卡: {{ task.last_check_in_time ? formatDateTime(task.last_check_in_time) : '未打卡' }}
                </div>
                <div class="flex items-center text-sm">
                  <CheckCircleOutlined class="mr-2 text-on-surface-variant" />
                  <span v-if="task.last_check_in_status" :class="{
                    'text-green-600 dark:text-green-400 font-medium': task.last_check_in_status === 'success',
                    'text-blue-600 dark:text-blue-400 font-medium': task.last_check_in_status === 'out_of_time',
                    'text-red-600 dark:text-red-400 font-medium': task.last_check_in_status === 'failure',
                    'text-yellow-600 dark:text-yellow-400 font-medium': task.last_check_in_status === 'unknown'
                  }">
                    {{
                      task.last_check_in_status === 'success' ? '✅ 打卡成功' :
                      task.last_check_in_status === 'out_of_time' ? '🕐 时间范围外' :
                      task.last_check_in_status === 'failure' ? '❌ 打卡失败' :
                      '❗ 打卡异常'
                    }}
                  </span>
                  <span v-else class="text-on-surface-variant">暂无打卡记录</span>
                </div>
              </div>

              <!-- Task Actions -->
              <div class="flex gap-2 pt-4 border-t border-outline-variant">
                <a-button
                  type="primary"
                  size="small"
                  :loading="checkInLoading[task.id]"
                  @click.stop="handleCheckIn(task.id)"
                  class="flex-1"
                >
                  {{ checkInLoading[task.id] ? '打卡中...' : '立即打卡' }}
                </a-button>
                <a-button
                  size="small"
                  @click.stop="toggleTaskStatus(task)"
                  class="flex-1"
                >
                  {{ task.is_active ? '禁用' : '启用' }}
                </a-button>
                <a-button
                  type="primary"
                  size="small"
                  ghost
                  @click.stop="editTask(task)"
                  class="icon-button"
                >
                  <template #icon><EditOutlined /></template>
                </a-button>
                <a-button
                  danger
                  size="small"
                  @click.stop="deleteTask(task)"
                  class="icon-button"
                >
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </div>
            </a-card>
          </a-col>
        </a-row>
      </div>
    </div>

    <!-- Create/Edit Task Dialog -->
    <a-modal
      v-model:open="showCreateDialog"
      :title="editingTask ? '编辑任务' : '从模板创建任务'"
      :width="isMobile ? '100%' : 700"
      :style="isMobile ? { top: 0, maxWidth: '100vw' } : {}"
      :maskClosable="false"
    >
      <!-- 只显示从模板创建 -->
      <div v-if="!editingTask">
        <div v-if="loadingTemplates" class="text-center py-8">
          <a-spin size="large" />
          <p class="text-on-surface-variant mt-2">加载模板中...</p>
        </div>

        <div v-else-if="activeTemplates.length === 0" class="text-center py-8">
          <p class="text-on-surface-variant">暂无可用模板</p>
          <p class="text-sm text-on-surface-variant opacity-70 mt-2">请联系管理员创建模板</p>
        </div>

        <div v-else>
          <!-- Template Selection -->
          <a-form-item label="选择模板" v-if="!selectedTemplate">
            <div class="grid grid-cols-1 gap-3">
              <div
                v-for="template in activeTemplates"
                :key="template.id"
                @click="selectTemplate(template)"
                class="border border-outline-variant rounded-lg p-4 cursor-pointer hover:border-primary hover:bg-primary-container/10 transition-all"
              >
                <h4 class="font-semibold text-on-surface mb-1">{{ template.name }}</h4>
                <p class="text-sm text-on-surface-variant">{{ template.description || '无描述' }}</p>
              </div>
            </div>
          </a-form-item>

          <!-- Template Form -->
          <a-form v-if="selectedTemplate" :model="templateTaskForm" ref="templateFormRef" layout="vertical">
            <div class="mb-4 p-3 bg-blue-50 rounded-lg flex items-center justify-between">
              <div class="flex items-center">
                <FileTextOutlined class="text-blue-600 mr-2" />
                <span class="text-sm font-medium text-blue-900">使用模板：{{ selectedTemplate.name }}</span>
              </div>
              <a-button size="small" type="link" @click="selectedTemplate = null">更换模板</a-button>
            </div>

            <a-form-item label="任务名称" name="task_name">
              <a-input v-model:value="templateTaskForm.task_name" placeholder="可选，留空则自动生成" />
            </a-form-item>

            <a-form-item label="接龙 ID" name="thread_id" required>
              <a-input v-model:value="templateTaskForm.thread_id" placeholder="请输入接龙项目 ID" />
            </a-form-item>

            <a-divider orientation="left">填写字段信息</a-divider>

            <!-- Dynamic Fields -->
            <div v-for="(fieldConfig, key) in visibleFields" :key="key">
              <a-form-item
                :label="fieldConfig.display_name"
                :required="fieldConfig.required"
              >
                <!-- Text Input -->
                <a-input
                  v-if="fieldConfig.field_type === 'text'"
                  v-model:value="templateTaskForm.field_values[key]"
                  :placeholder="fieldConfig.placeholder || `请输入${fieldConfig.display_name}`"
                />

                <!-- Textarea -->
                <a-textarea
                  v-else-if="fieldConfig.field_type === 'textarea'"
                  v-model:value="templateTaskForm.field_values[key]"
                  :rows="3"
                  :placeholder="fieldConfig.placeholder || `请输入${fieldConfig.display_name}`"
                />

                <!-- Number Input -->
                <a-input-number
                  v-else-if="fieldConfig.field_type === 'number'"
                  v-model:value="templateTaskForm.field_values[key]"
                  :placeholder="fieldConfig.placeholder || `请输入${fieldConfig.display_name}`"
                  style="width: 100%"
                />

                <!-- Select -->
                <a-select
                  v-else-if="fieldConfig.field_type === 'select'"
                  v-model:value="templateTaskForm.field_values[key]"
                  :placeholder="fieldConfig.placeholder || `请选择${fieldConfig.display_name}`"
                  style="width: 100%"
                >
                  <a-select-option
                    v-for="option in fieldConfig.options"
                    :key="option.value"
                    :value="option.value"
                  >
                    {{ option.label }}
                  </a-select-option>
                </a-select>

                <span v-if="fieldConfig.default_value" class="text-xs text-on-surface-variant mt-1">
                  默认值: {{ fieldConfig.default_value }}
                </span>
              </a-form-item>
            </div>
          </a-form>
        </div>
      </div>

      <!-- Edit Mode Form - 简化版，只显示任务名称和启用状态 -->
      <a-form v-if="editingTask" :model="taskForm" :rules="taskRules" ref="taskFormRef" layout="vertical">
        <a-form-item label="任务名称" name="name">
          <a-input v-model:value="taskForm.name" placeholder="请输入任务名称（例如：公司打卡）" />
        </a-form-item>

        <a-form-item label="启用状态">
          <a-switch v-model:checked="taskForm.is_active" />
          <span class="ml-2 text-sm text-on-surface-variant">
            {{ taskForm.is_active ? '启用自动打卡' : '禁用自动打卡（仍可手动打卡）' }}
          </span>
        </a-form-item>

        <!-- 新增：Crontab 编辑器 -->
        <a-form-item label="打卡时间表">
          <CrontabEditor v-model="taskForm.cron_expression" />
        </a-form-item>

        <a-divider orientation="left">任务 Payload 配置（只读）</a-divider>

        <div class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-on-surface-variant">完整的打卡请求配置</span>
            <a-button
              size="small"
              type="primary"
              ghost
              @click="copyPayload"
            >
              <template #icon><CopyOutlined /></template>
              复制
            </a-button>
          </div>
          <a-textarea
            v-model:value="formattedPayload"
            :rows="12"
            readonly
            class="font-mono text-xs"
            style="resize: vertical; min-height: 200px; max-height: 400px;"
          />
          <p class="text-xs text-on-surface-variant mt-1">
            💡 此配置由模板自动生成，如需修改请删除任务后从模板重新创建
          </p>
        </div>
      </a-form>

      <template #footer>
        <div class="flex gap-3 justify-end">
          <a-button @click="showCreateDialog = false">取消</a-button>
          <a-button type="primary" :loading="submitting" @click="handleSubmit">
            {{ submitting ? '提交中...' : (editingTask ? '保存修改' : '创建任务') }}
          </a-button>
        </div>
      </template>
    </a-modal>
  </Layout>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import {
  PlusOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  StopOutlined,
  TagOutlined,
  ClockCircleOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
} from '@ant-design/icons-vue'
import Layout from '@/components/Layout.vue'
import CrontabEditor from '@/components/CrontabEditor.vue'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { useTaskStore } from '@/stores/task'
import { useTemplateStore } from '@/stores/template'
import { copyToClipboard, formatDateTime } from '@/utils/helpers'
import { usePollStatus } from '@/composables/usePollStatus'

const router = useRouter()
const taskStore = useTaskStore()
const templateStore = useTemplateStore()
const { isMobile } = useBreakpoint()

// 使用轮询 composable
const { startPolling } = usePollStatus({
  interval: 2000,
  maxRetries: 15,
  backoff: false
})

const loading = ref(false)
const showCreateDialog = ref(false)
const submitting = ref(false)
const editingTask = ref(null)
const taskFormRef = ref(null)
const templateFormRef = ref(null)
const checkInLoading = ref({})

// Template mode
const createMode = ref('template') // 'template' or 'manual'
const loadingTemplates = ref(false)
const activeTemplates = ref([])
const selectedTemplate = ref(null)
const templatePreview = ref(null) // 存储从 preview 接口获取的合并后配置

// Manual create form
const taskForm = reactive({
  name: '',
  thread_id: '',
  is_active: true,
  payload_config: '',
  cron_expression: '0 20 * * *', // 新增：Crontab 表达式，默认每天 20:00
})

// Template create form
const templateTaskForm = reactive({
  task_name: '',
  thread_id: '',
  field_values: {}
})

const taskRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  thread_id: [{ required: true, message: '请输入接龙 ID', trigger: 'blur' }],
}

// Compute visible fields from selected template (using merged config)
const visibleFields = computed(() => {
  if (!templatePreview.value) return {}

  // 使用合并后的完整字段配置（包含从父模板继承的字段）
  const fieldConfig = templatePreview.value.field_config
  const visible = {}

  // 递归函数：提取所有可见的普通字段
  const extractVisibleFields = (config, parentPath = '') => {
    for (const [key, value] of Object.entries(config)) {
      const currentPath = parentPath ? `${parentPath}.${key}` : key

      // 判断是否为字段配置对象（包含 display_name）
      if (value && typeof value === 'object' && 'display_name' in value) {
        // 这是一个普通字段配置
        if (!value.hidden) {
          visible[currentPath] = value
        }
      }
      // 判断是否为数组字段
      else if (Array.isArray(value)) {
        // 数组字段：遍历每个元素
        if (value.length > 0) {
          const firstElement = value[0]
          // 如果数组元素是字段配置对象，直接提取
          if (firstElement && typeof firstElement === 'object' && 'display_name' in firstElement) {
            if (!firstElement.hidden) {
              visible[`${currentPath}[0]`] = firstElement
            }
          }
          // 如果数组元素是对象（但不是字段配置），递归处理
          else if (firstElement && typeof firstElement === 'object') {
            extractVisibleFields(firstElement, `${currentPath}[0]`)
          }
        }
      }
      // 判断是否为对象字段（不包含 display_name 的对象）
      else if (value && typeof value === 'object' && !('display_name' in value)) {
        // 递归处理对象字段
        extractVisibleFields(value, currentPath)
      }
    }
  }

  extractVisibleFields(fieldConfig)

  return visible
})

// Formatted payload for display in edit mode
const formattedPayload = computed(() => {
  if (!taskForm.payload_config) return '{}'

  try {
    const payload = JSON.parse(taskForm.payload_config)
    return JSON.stringify(payload, null, 2)
  } catch (e) {
    return taskForm.payload_config
  }
})

// Copy payload to clipboard
const copyPayload = async () => {
  const success = await copyToClipboard(formattedPayload.value)
  if (success) {
    message.success('Payload 已复制到剪贴板')
  } else {
    message.error('复制失败')
  }
}

// Initialize field values with defaults when template is selected
watch(selectedTemplate, async (newTemplate) => {
  if (!newTemplate) {
    templatePreview.value = null
    return
  }

  // 获取模板的合并后配置（包含父模板的字段）
  try {
    templatePreview.value = await templateStore.previewTemplate(newTemplate.id)
  } catch (error) {
    message.error('获取模板配置失败')
    templatePreview.value = null
    return
  }

  const fieldConfig = templatePreview.value.field_config
  const fieldValues = {}

  // 递归函数：提取所有字段的默认值
  const extractDefaultValues = (config, parentPath = '') => {
    for (const [key, value] of Object.entries(config)) {
      const currentPath = parentPath ? `${parentPath}.${key}` : key

      // 判断是否为字段配置对象（包含 display_name）
      if (value && typeof value === 'object' && 'display_name' in value) {
        fieldValues[currentPath] = value.default_value || ''
      }
      // 判断是否为数组字段
      else if (Array.isArray(value)) {
        // 数组字段：处理第一个元素的默认值
        if (value.length > 0) {
          const firstElement = value[0]
          // 如果数组元素是字段配置对象，直接提取默认值
          if (firstElement && typeof firstElement === 'object' && 'display_name' in firstElement) {
            fieldValues[`${currentPath}[0]`] = firstElement.default_value || ''
          }
          // 如果数组元素是对象（但不是字段配置），递归处理
          else if (firstElement && typeof firstElement === 'object') {
            extractDefaultValues(firstElement, `${currentPath}[0]`)
          }
        }
      }
      // 判断是否为对象字段（不包含 display_name 的对象）
      else if (value && typeof value === 'object' && !('display_name' in value)) {
        // 递归处理对象字段
        extractDefaultValues(value, currentPath)
      }
    }
  }

  extractDefaultValues(fieldConfig)

  templateTaskForm.field_values = fieldValues
})

// Load templates
const loadTemplates = async () => {
  loadingTemplates.value = true
  try {
    activeTemplates.value = await templateStore.fetchActiveTemplates()
  } catch (error) {
    message.error(error.message || '加载模板失败')
  } finally {
    loadingTemplates.value = false
  }
}

// Select template
const selectTemplate = (template) => {
  selectedTemplate.value = template
}

// Handle mode change
const handleModeChange = (mode) => {
  selectedTemplate.value = null
  templateTaskForm.task_name = ''
  templateTaskForm.thread_id = ''
  templateTaskForm.field_values = {}
}

// 从 payload_config 中提取 ThreadId
const getThreadId = (task) => {
  if (!task.payload_config) return '未知'

  try {
    const payload = JSON.parse(task.payload_config)
    return payload.ThreadId || '未知'
  } catch (e) {
    console.error('解析 payload_config 失败:', e)
    return '未知'
  }
}

// 加载任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    await taskStore.fetchMyTasks()
  } catch (error) {
    message.error(error.message || '加载任务列表失败')
  } finally {
    loading.value = false
  }
}

// 查看任务详情
const viewTask = (task) => {
  router.push(`/tasks/${task.id}/records`)
}

// 编辑任务
const editTask = (task) => {
  editingTask.value = task

  // 从 payload_config 中提取 thread_id
  let threadId = ''
  try {
    const payload = JSON.parse(task.payload_config || '{}')
    threadId = payload.ThreadId || ''
  } catch (e) {
    console.error('解析 payload_config 失败:', e)
  }

  Object.assign(taskForm, {
    name: task.name,
    thread_id: threadId,
    is_active: task.is_active,
    payload_config: task.payload_config || '{}',
    cron_expression: task.cron_expression || '0 20 * * *',
  })
  showCreateDialog.value = true
}

// 删除任务
const deleteTask = (task) => {
  Modal.confirm({
    title: '删除确认',
    content: `确定要删除任务"${task.name || task.id}"吗？此操作不可恢复。`,
    okText: '确定删除',
    cancelText: '取消',
    okType: 'danger',
    onOk: async () => {
      try {
        await taskStore.deleteTask(task.id)
        message.success('任务删除成功')
        await fetchTasks()
      } catch (error) {
        message.error(error.message || '删除任务失败')
      }
    },
  })
}

// 切换任务状态
const toggleTaskStatus = async (task) => {
  try {
    await taskStore.toggleTask(task.id)
    message.success(task.is_active ? '任务已禁用' : '任务已启用')
  } catch (error) {
    message.error(error.message || '切换任务状态失败')
  }
}

// 手动打卡 (异步轮询方式)
const handleCheckIn = async (taskId) => {
  checkInLoading.value[taskId] = true

  try {
    // 调用异步打卡接口，立即返回 record_id
    const result = await taskStore.checkInTask(taskId)

    // 获取 record_id
    const recordId = result.record_id
    if (!recordId) {
      message.error('打卡请求失败:未获取到记录ID')
      checkInLoading.value[taskId] = false
      return
    }

    // 如果初始状态就是失败,显示错误并刷新任务列表
    if (result.status === 'failure') {
      message.error(result.message || '打卡失败')
      checkInLoading.value[taskId] = false
      await fetchTasks()
      return
    }

    // 显示提示消息
    message.info('打卡任务已启动，正在后台处理...')

    // 使用轮询 composable 检查打卡状态
    startPolling(
      async () => {
        const status = await taskStore.getCheckInRecordStatus(recordId)
        return {
          completed: status.status !== 'pending',
          success: status.status === 'success',
          data: status
        }
      },
      {
        onSuccess: async () => {
          checkInLoading.value[taskId] = false
          message.success('打卡成功！')
          await fetchTasks()
        },
        onFailure: async (statusData) => {
          checkInLoading.value[taskId] = false
          const errorMsg = statusData.error_message || statusData.response_text || '打卡失败'
          message.error(errorMsg)
          await fetchTasks()
        },
        onTimeout: () => {
          checkInLoading.value[taskId] = false
          message.warning('打卡处理时间较长，请稍后查看打卡记录')
        }
      }
    )

  } catch (error) {
    console.error('启动打卡失败:', error)
    checkInLoading.value[taskId] = false
    message.error(error.message || '启动打卡任务失败')
  }
}

// 提交表单
const handleSubmit = async () => {
  submitting.value = true

  try {
    // Edit mode
    if (editingTask.value) {
      if (!taskFormRef.value) return
      await taskFormRef.value.validate()

      await taskStore.updateTask(editingTask.value.id, taskForm)
      message.success('任务更新成功')
    }
    // Create from template
    else if (createMode.value === 'template') {
      if (!selectedTemplate.value) {
        message.warning('请选择一个模板')
        return
      }

      if (!templateTaskForm.thread_id) {
        message.warning('请输入接龙 ID')
        return
      }

      await templateStore.createTaskFromTemplate(
        selectedTemplate.value.id,
        templateTaskForm.thread_id,
        templateTaskForm.field_values,
        templateTaskForm.task_name || null
      )

      message.success('任务创建成功')
    }
    // Create manually
    else {
      if (!taskFormRef.value) return
      await taskFormRef.value.validate()

      await taskStore.createTask(taskForm)
      message.success('任务创建成功')
    }

    showCreateDialog.value = false
    resetForm()
    await fetchTasks()
  } catch (error) {
    message.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  editingTask.value = null
  selectedTemplate.value = null
  createMode.value = 'template'

  Object.assign(taskForm, {
    name: '',
    thread_id: '',
    is_active: true,
    payload_config: '',
  })

  templateTaskForm.task_name = ''
  templateTaskForm.thread_id = ''
  templateTaskForm.field_values = {}

  taskFormRef.value?.resetFields()
}

// Watch dialog open to load templates
watch(showCreateDialog, (isOpen) => {
  if (isOpen && !editingTask.value) {
    loadTemplates()
  }
})

onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.icon-button {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  padding: 4px 8px;
}
</style>
