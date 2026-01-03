<template>
  <a-modal
    v-model:open="dialogVisible"
    title="QQ 扫码登录"
    :width="isMobile ? '100%' : 400"
    :style="isMobile ? { top: 0, paddingBottom: 0, maxWidth: '100vw' } : {}"
    :maskClosable="false"
    @cancel="handleClose"
    :footer="null"
  >
    <div class="qrcode-container">
      <!-- 加载中 -->
      <div v-if="status === 'loading'" class="status-container">
        <a-spin size="large" />
        <p class="status-text">正在获取二维码...</p>
      </div>

      <!-- 显示二维码 -->
      <div v-else-if="status === 'pending'" class="qrcode-wrapper">
        <img :src="qrcodeUrl" alt="QR Code" class="qrcode-image" />
        <p class="hint-text">请使用手机 QQ 扫描二维码登录</p>
        <a-progress :percent="progress" :show-info="false" />
        <p class="countdown-text">{{ countdown }}s</p>
      </div>

      <!-- 扫码成功 -->
      <div v-else-if="status === 'success'" class="status-container">
        <CheckCircleFilled class="status-icon success-icon" />
        <p class="status-text success">登录成功！</p>
      </div>

      <!-- 二维码过期 -->
      <div v-else-if="status === 'expired'" class="status-container">
        <WarningFilled class="status-icon warning-icon" />
        <p class="status-text">二维码已过期</p>
        <a-button type="primary" @click="refreshQRCode" class="mt-4">刷新二维码</a-button>
      </div>

      <!-- 失败 -->
      <div v-else-if="status === 'failed'" class="status-container">
        <CloseCircleFilled class="status-icon error-icon" />
        <p class="status-text error">{{ errorMessage }}</p>
        <a-button type="primary" @click="refreshQRCode" class="mt-4">重试</a-button>
      </div>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { usePollStatus } from '@/composables/usePollStatus'
import { message } from 'ant-design-vue'
import {
  CheckCircleFilled,
  WarningFilled,
  CloseCircleFilled,
} from '@ant-design/icons-vue'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
  alias: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['update:visible', 'success', 'error'])

const authStore = useAuthStore()
const { isMobile } = useBreakpoint()

// 使用轮询 composable
const { startPolling: startQRPolling, stopPolling } = usePollStatus({
  interval: 2000,
  maxRetries: 90,  // 3分钟 = 180秒 / 2秒间隔 = 90次
  backoff: false
})

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
})

const status = ref('loading') // loading, pending, success, expired, failed
const qrcodeUrl = ref('')
const sessionId = ref('')
const errorMessage = ref('')
const countdown = ref(180) // 倒计时 3 分钟
const progress = ref(100)

let countdownTimer = null

// 获取二维码
const fetchQRCode = async () => {
  status.value = 'loading'
  try {
    const result = await authStore.loginWithQRCode(props.alias)
    sessionId.value = result.session_id
    qrcodeUrl.value = `data:image/png;base64,${result.qrcode_base64}`
    status.value = 'pending'

    // 开始轮询扫码状态（使用 composable）
    startQRPolling(
      async () => {
        const result = await authStore.checkQRCodeStatus(sessionId.value)

        // 检查是否完成（成功、过期或失败）
        const completed = result.status === 'expired' || result.status === 'failed' || result.success

        return {
          completed,
          success: result.success === true,
          data: result
        }
      },
      {
        onSuccess: (result) => {
          status.value = 'success'
          stopCountdown()
          message.success('登录成功！')

          // 延迟关闭对话框
          setTimeout(() => {
            emit('success', result.user)
            handleClose()
          }, 1500)
        },
        onFailure: (result) => {
          if (result.status === 'expired') {
            status.value = 'expired'
          } else {
            status.value = 'failed'
            errorMessage.value = result.message || '扫码失败'
          }
          stopCountdown()
        },
        onTimeout: () => {
          status.value = 'expired'
          stopCountdown()
        }
      }
    )

    startCountdown()
  } catch (error) {
    status.value = 'failed'
    errorMessage.value = error.message || '获取二维码失败'
    emit('error', error)
  }
}

// 开始倒计时
const startCountdown = () => {
  countdown.value = 180

  if (countdownTimer) {
    clearInterval(countdownTimer)
  }

  countdownTimer = setInterval(() => {
    countdown.value--
    progress.value = (countdown.value / 180) * 100

    if (countdown.value <= 0) {
      status.value = 'expired'
      stopPolling()  // 停止轮询
      stopCountdown()
    }
  }, 1000)
}

// 停止倒计时
const stopCountdown = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

// 刷新二维码
const refreshQRCode = () => {
  fetchQRCode()
}

// 关闭对话框
const handleClose = () => {
  stopPolling()  // 停止轮询
  stopCountdown()

  // 如果有未完成的会话,取消它
  if (sessionId.value && status.value !== 'success') {
    try {
      authStore.cancelQRCodeSession(sessionId.value)
    } catch (error) {
      console.error('取消会话失败:', error)
    }
  }

  dialogVisible.value = false
}

// 监听对话框显示状态
watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      fetchQRCode()
    } else {
      stopPolling()
      stopCountdown()
    }
  }
)

// 组件卸载时清理定时器，防止内存泄漏
onBeforeUnmount(() => {
  stopPolling()
  stopCountdown()
})
</script>

<style scoped>
.qrcode-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  min-height: 300px;
}

.status-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.status-icon {
  font-size: 60px;
}

.success-icon {
  color: #4caf50;
}

.dark .success-icon {
  color: #81c784;
}

.warning-icon {
  color: #ff9800;
}

.dark .warning-icon {
  color: #ffb74d;
}

.error-icon {
  color: #f44336;
}

.dark .error-icon {
  color: #ef5350;
}

.status-text {
  margin-top: 20px;
  font-size: 16px;
  color: var(--md-sys-color-on-surface-variant);
}

.status-text.success {
  color: #4caf50;
  font-weight: bold;
}

.dark .status-text.success {
  color: #81c784;
}

.status-text.error {
  color: #f44336;
}

.dark .status-text.error {
  color: #ef5350;
}

.qrcode-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.qrcode-image {
  width: 240px;
  height: 240px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 8px;
  padding: 10px;
  background-color: var(--md-sys-color-surface);
}

.hint-text {
  margin-top: 20px;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
}

.countdown-text {
  margin-top: 10px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.mt-4 {
  margin-top: 16px;
}
</style>
