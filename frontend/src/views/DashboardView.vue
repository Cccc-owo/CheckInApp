<template>
  <Layout>
    <div class="dashboard-container">
      <a-row :gutter="[20, 20]">
        <!-- Token 状态卡片 -->
        <a-col :xs="24" :sm="24" :md="24">
          <a-card class="status-card">
            <template #title>
              <div class="card-header">
                <KeyOutlined />
                <span>Token 状态</span>
              </div>
            </template>

            <div v-if="tokenStatusLoading" class="loading-container">
              <a-skeleton :active="true" :paragraph="{ rows: 3 }" />
            </div>

            <div v-else-if="tokenStatus" class="token-status">
              <a-descriptions :column="{ xs: 1, sm: 1, md: 2 }" bordered>
                <a-descriptions-item label="Token 状态">
                  <a-tag :color="tokenStatus.is_valid ? 'success' : 'error'">
                    {{ tokenStatus.is_valid ? '有效' : '无效' }}
                  </a-tag>
                </a-descriptions-item>

                <a-descriptions-item label="过期时间">
                  {{ formatExpireTime }}
                </a-descriptions-item>

                <a-descriptions-item label="剩余时间">
                  <a-tag v-if="tokenStatus.is_valid" :color="tokenStatus.expiring_soon ? 'warning' : 'success'">
                    {{ formatRemainTime }}
                  </a-tag>
                  <a-tag v-else color="error">已过期</a-tag>
                </a-descriptions-item>

                <a-descriptions-item label="即将过期">
                  <a-tag v-if="!tokenStatus.is_valid" color="error">
                    已过期
                  </a-tag>
                  <a-tag v-else :color="tokenStatus.expiring_soon ? 'warning' : 'success'">
                    {{ tokenStatus.expiring_soon ? '是' : '否' }}
                  </a-tag>
                </a-descriptions-item>
              </a-descriptions>

              <a-alert
                v-if="tokenStatus.expiring_soon"
                message="Token 即将过期"
                description="您的 Token 将在 30 分钟内过期，请在过期后及时刷新 Token！"
                type="warning"
                :closable="false"
                show-icon
                style="margin-top: 15px"
              />
            </div>
          </a-card>
        </a-col>

        <!-- 手动打卡卡片 -->
        <a-col :xs="24" :sm="24" :md="24">
          <a-card>
            <template #title>
              <div class="card-header">
                <CalendarOutlined />
                <span>手动打卡</span>
              </div>
            </template>

            <div class="check-in-container">
              <p class="hint">选择任务并点击下方按钮立即执行打卡操作</p>

              <!-- 任务选择 -->
              <a-select
                v-model:value="selectedTaskId"
                placeholder="请选择要打卡的任务"
                :loading="taskStore.loading"
                style="width: 100%; max-width: 400px; margin-bottom: 20px"
              >
                <a-select-option
                  v-for="task in taskStore.tasks"
                  :key="task.id"
                  :value="task.id"
                >
                  <div style="display: flex; justify-content: space-between; align-items: center">
                    <span>{{ task.name }}</span>
                    <a-tag size="small" :color="task.is_active ? 'success' : 'default'">
                      {{ task.is_active ? '启用' : '禁用' }}
                    </a-tag>
                  </div>
                </a-select-option>
              </a-select>

              <a-button
                type="primary"
                size="large"
                :loading="checkInLoading"
                :disabled="!selectedTaskId"
                @click="handleCheckIn"
              >
                <template #icon><CalendarOutlined /></template>
                {{ checkInLoading ? '打卡中...' : '立即打卡' }}
              </a-button>

              <div v-if="lastCheckIn" class="last-check-in">
                <a-divider />
                <p class="label">上次打卡</p>
                <a-descriptions :column="{ xs: 1, sm: 1, md: 2 }" bordered size="small">
                  <a-descriptions-item label="时间">
                    {{ formatDateTime(lastCheckIn.check_in_time) }}
                  </a-descriptions-item>
                  <a-descriptions-item label="状态">
                    <a-tag
                      :color="lastCheckIn.status === 'success' ? 'success' :
                             lastCheckIn.status === 'out_of_time' ? 'default' :
                             lastCheckIn.status === 'unknown' ? 'warning' : 'error'"
                    >
                      {{
                        lastCheckIn.status === 'success' ? '成功' :
                        lastCheckIn.status === 'out_of_time' ? '时间范围外' :
                        lastCheckIn.status === 'unknown' ? '异常' : '失败'
                      }}
                    </a-tag>
                  </a-descriptions-item>
                  <a-descriptions-item label="打卡响应" :span="2">
                    {{ lastCheckIn.response_text || lastCheckIn.error_message || '-' }}
                  </a-descriptions-item>
                </a-descriptions>
              </div>
            </div>
          </a-card>
        </a-col>

        <!-- 用户信息卡片 -->
        <a-col :xs="24" :sm="24" :md="24">
          <a-card>
            <template #title>
              <div class="card-header">
                <UserOutlined />
                <span>个人信息</span>
              </div>
            </template>

            <a-descriptions :column="{ xs: 1, sm: 1, md: 2 }" bordered>
              <a-descriptions-item label="用户名">
                {{ authStore.user?.alias }}
              </a-descriptions-item>
              <a-descriptions-item label="角色">
                <a-tag :color="authStore.isAdmin ? 'error' : 'blue'">
                  {{ authStore.isAdmin ? '管理员' : '普通用户' }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="邮箱" :span="2">
                {{ authStore.user?.email || '未设置' }}
              </a-descriptions-item>
              <a-descriptions-item label="注册时间" :span="2">
                {{ formatDateTime(authStore.user?.created_at, false) }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>
      </a-row>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { CalendarOutlined, KeyOutlined, UserOutlined } from '@ant-design/icons-vue'
import Layout from '@/components/Layout.vue'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
import { useTaskStore } from '@/stores/task'
import { useCheckInStore } from '@/stores/checkIn'
import { formatDateTime } from '@/utils/helpers'

const authStore = useAuthStore()
const userStore = useUserStore()
const taskStore = useTaskStore()
const checkInStore = useCheckInStore()

const tokenStatusLoading = ref(false)
const checkInLoading = ref(false)
const selectedTaskId = ref(null)

const tokenStatus = computed(() => userStore.tokenStatus)
const lastCheckIn = computed(() => {
  if (checkInStore.myRecords.length > 0) {
    return checkInStore.myRecords[0]
  }
  return null
})

const formatExpireTime = computed(() => {
  if (!tokenStatus.value || !tokenStatus.value.expires_at) return '-'
  return formatDateTime(tokenStatus.value.expires_at * 1000)
})

const formatRemainTime = computed(() => {
  if (!tokenStatus.value || !tokenStatus.value.expires_at) return '-'

  const now = Date.now()
  const expireTime = tokenStatus.value.expires_at * 1000
  const diff = expireTime - now

  if (diff <= 0) return '已过期'

  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))

  if (days > 0) return `${days} 天 ${hours} 小时`
  if (hours > 0) return `${hours} 小时 ${minutes} 分钟`
  return `${minutes} 分钟`
})

// 获取 Token 状态
const fetchTokenStatus = async () => {
  tokenStatusLoading.value = true
  try {
    await userStore.fetchTokenStatus()
  } catch (error) {
    message.error(error.message || '获取 Token 状态失败')
  } finally {
    tokenStatusLoading.value = false
  }
}

// 手动打卡
const handleCheckIn = async () => {
  if (!selectedTaskId.value) {
    message.warning('请先选择要打卡的任务')
    return
  }

  checkInLoading.value = true

  try {
    // 调用异步打卡接口，立即返回 record_id
    const result = await taskStore.checkInTask(selectedTaskId.value)

    // 获取 record_id
    const recordId = result.record_id
    if (!recordId) {
      message.error('打卡请求失败：未获取到记录ID')
      checkInLoading.value = false
      return
    }

    // 如果初始状态就是失败,显示错误并刷新记录
    if (result.status === 'failure') {
      message.error(result.message || '打卡失败')
      checkInLoading.value = false
      checkInStore.fetchMyRecords({ limit: 1 })
      return
    }

    // 显示提示消息
    message.info('打卡任务已启动，正在后台处理...')

    // 用于存储 interval ID，以便在超时时清理
    let pollIntervalId = null

    // 开始轮询检查打卡状态
    pollIntervalId = setInterval(async () => {
      try {
        const status = await taskStore.getCheckInRecordStatus(recordId)

        // 只要状态不是 pending，说明打卡请求已经处理完成
        if (status.status !== 'pending') {
          clearInterval(pollIntervalId)
          checkInLoading.value = false

          if (status.status === 'success') {
            // 打卡成功
            message.success('打卡成功！')
            checkInStore.fetchMyRecords({ limit: 1 })
          } else {
            // 打卡失败或其他状态 (failure, out_of_time, unknown 等)
            const errorMsg = status.error_message || status.response_text || '打卡失败'
            message.error(errorMsg)
            checkInStore.fetchMyRecords({ limit: 1 })
          }
        }
        // status === 'pending' 时继续轮询
      } catch (error) {
        // 查询状态失败，停止轮询
        console.error('轮询状态失败:', error)
        clearInterval(pollIntervalId)
        checkInLoading.value = false
        message.error('查询打卡状态失败')
      }
    }, 2000) // 每 2 秒查询一次

    // 设置超时保护（30 秒后停止轮询）
    setTimeout(() => {
      if (checkInLoading.value) {
        clearInterval(pollIntervalId)
        checkInLoading.value = false
        message.warning('打卡处理时间较长，请稍后查看打卡记录')
      }
    }, 30000)

  } catch (error) {
    console.error('启动打卡失败:', error)
    checkInLoading.value = false
    message.error(error.message || '启动打卡任务失败')
  }
}

onMounted(async () => {
  fetchTokenStatus()
  checkInStore.fetchMyRecords({ limit: 1 })

  // 加载任务列表
  try {
    await taskStore.fetchMyTasks()
    // 如果只有一个任务，自动选中（优先选择启用的任务）
    if (taskStore.activeTasks.length === 1) {
      selectedTaskId.value = taskStore.activeTasks[0].id
    } else if (taskStore.tasks.length === 1) {
      selectedTaskId.value = taskStore.tasks[0].id
    }
  } catch (error) {
    message.error(error.message || '加载任务列表失败')
  }
})
</script>

<style scoped>
.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.loading-container {
  padding: 20px;
}

.token-status {
  padding: 10px 0;
}

.check-in-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}

.hint {
  margin-bottom: 20px;
  color: #909399;
  font-size: 14px;
}

.last-check-in {
  width: 100%;
  margin-top: 20px;
}

.label {
  font-weight: bold;
  margin-bottom: 10px;
  color: #606266;
}

.status-card {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

/* 修复按钮图标对齐 */
:deep(.ant-btn) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

:deep(.ant-btn .anticon) {
  display: inline-flex;
  align-items: center;
  vertical-align: middle;
}
</style>
