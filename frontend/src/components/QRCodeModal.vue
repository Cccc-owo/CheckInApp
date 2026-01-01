<template>
  <el-dialog
    v-model="dialogVisible"
    title="QQ 扫码登录"
    width="400px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="qrcode-container">
      <!-- 加载中 -->
      <div v-if="status === 'loading'" class="status-container">
        <el-icon class="is-loading" :size="60">
          <Loading />
        </el-icon>
        <p class="status-text">正在获取二维码...</p>
      </div>

      <!-- 显示二维码 -->
      <div v-else-if="status === 'pending'" class="qrcode-wrapper">
        <img :src="qrcodeUrl" alt="QR Code" class="qrcode-image" />
        <p class="hint-text">请使用手机 QQ 扫描二维码登录</p>
        <el-progress :percentage="progress" :show-text="false" />
        <p class="countdown-text">{{ countdown }}s</p>
      </div>

      <!-- 扫码成功 -->
      <div v-else-if="status === 'success'" class="status-container">
        <el-icon :size="60" color="#67c23a">
          <SuccessFilled />
        </el-icon>
        <p class="status-text success">登录成功！</p>
      </div>

      <!-- 二维码过期 -->
      <div v-else-if="status === 'expired'" class="status-container">
        <el-icon :size="60" color="#e6a23c">
          <WarningFilled />
        </el-icon>
        <p class="status-text">二维码已过期</p>
        <el-button type="primary" @click="refreshQRCode">刷新二维码</el-button>
      </div>

      <!-- 失败 -->
      <div v-else-if="status === 'failed'" class="status-container">
        <el-icon :size="60" color="#f56c6c">
          <CircleCloseFilled />
        </el-icon>
        <p class="status-text error">{{ errorMessage }}</p>
        <el-button type="primary" @click="refreshQRCode">重试</el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

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

let pollingTimer = null
let countdownTimer = null

// 获取二维码
const fetchQRCode = async () => {
  status.value = 'loading'
  try {
    const result = await authStore.loginWithQRCode(props.alias)
    sessionId.value = result.session_id
    qrcodeUrl.value = `data:image/png;base64,${result.qrcode_base64}`
    status.value = 'pending'

    // 开始轮询扫码状态
    startPolling()
    startCountdown()
  } catch (error) {
    status.value = 'failed'
    errorMessage.value = error.message || '获取二维码失败'
    emit('error', error)
  }
}

// 开始轮询扫码状态
const startPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
  }

  pollingTimer = setInterval(async () => {
    try {
      const result = await authStore.checkQRCodeStatus(sessionId.value)

      if (result.success) {
        // 扫码成功
        status.value = 'success'
        stopPolling()
        stopCountdown()

        ElMessage.success('登录成功！')

        // 延迟关闭对话框
        setTimeout(() => {
          emit('success', result.user)
          handleClose()
        }, 1500)
      } else if (result.status === 'expired') {
        // 二维码过期
        status.value = 'expired'
        stopPolling()
        stopCountdown()
      } else if (result.status === 'failed') {
        // 扫码失败
        status.value = 'failed'
        errorMessage.value = result.message || '扫码失败'
        stopPolling()
        stopCountdown()
      }
      // 否则继续轮询（pending 状态）
    } catch (error) {
      console.error('轮询扫码状态失败:', error)
      // 继续轮询，不中断
    }
  }, 2000) // 每 2 秒轮询一次
}

// 停止轮询
const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
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
      stopPolling()
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
  stopPolling()
  stopCountdown()
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

.status-text {
  margin-top: 20px;
  font-size: 16px;
  color: #606266;
}

.status-text.success {
  color: #67c23a;
  font-weight: bold;
}

.status-text.error {
  color: #f56c6c;
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
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  background-color: #fff;
}

.hint-text {
  margin-top: 20px;
  font-size: 14px;
  color: #909399;
}

.countdown-text {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}

.el-progress {
  width: 100%;
  margin-top: 10px;
}
</style>
