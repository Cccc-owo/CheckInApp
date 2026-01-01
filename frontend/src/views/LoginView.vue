<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>接龙自动打卡系统</h2>
          <p class="subtitle">{{ loginMode === 'qrcode' ? 'QQ 扫码登录/注册' : '用户名密码登录' }}</p>
        </div>
      </template>

      <!-- 登录模式切换 -->
      <div class="mode-switch">
        <el-segmented v-model="loginMode" :options="loginModeOptions" block />
      </div>

      <!-- QR码登录表单 -->
      <el-form
        v-if="loginMode === 'qrcode'"
        :model="qrcodeForm"
        :rules="qrcodeRules"
        ref="qrcodeFormRef"
        label-width="0"
        @submit.prevent="handleQRCodeLogin"
      >
        <el-form-item prop="alias">
          <el-input
            v-model="qrcodeForm.alias"
            placeholder="请输入您的用户名"
            size="large"
            clearable
            @keyup.enter="handleQRCodeLogin"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            @click="handleQRCodeLogin"
          >
            {{ loading ? '正在登录...' : '扫码登录/注册' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 别名+密码登录表单 -->
      <el-form
        v-else
        :model="passwordForm"
        :rules="passwordRules"
        ref="passwordFormRef"
        label-width="0"
      >
        <el-form-item prop="alias">
          <el-input
            v-model="passwordForm.alias"
            placeholder="请输入您的用户名"
            size="large"
            clearable
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="passwordForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
            clearable
            @keyup.enter="handlePasswordLogin"
          >
            <template #prefix>
              <el-icon><Key /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            @click="handlePasswordLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>

        <div class="tips-link">
          <el-link type="info" @click="loginMode = 'qrcode'">
            没有密码？使用扫码登录
          </el-link>
        </div>
      </el-form>

      <div class="tips">
        <el-alert
          :title="loginMode === 'qrcode' ? '扫码登录提示' : '密码登录提示'"
          type="info"
          :closable="false"
          show-icon
        >
          <template v-if="loginMode === 'qrcode'">
            <p>1. 输入您的用户名（用于标识身份）</p>
            <p>2. 点击"扫码登录/注册"按钮</p>
            <p>3. 使用手机 QQ 扫描弹出的二维码</p>
            <p>4. 扫码成功后即可登录系统</p>
            <p class="tip-note">💡 新用户首次扫码将自动注册账户</p>
          </template>
          <template v-else>
            <p>1. 输入您的用户名和密码</p>
            <p>2. 点击"登录"按钮直接登录</p>
            <p>3. 首次使用请先扫码登录/注册，然后在设置中设置密码</p>
          </template>
        </el-alert>
      </div>
    </el-card>

    <!-- QR 码弹窗 -->
    <QRCodeModal
      v-model:visible="qrcodeVisible"
      :alias="qrcodeForm.alias"
      @success="handleLoginSuccess"
      @error="handleLoginError"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Key } from '@element-plus/icons-vue'
import { authAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'
import QRCodeModal from '@/components/QRCodeModal.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const qrcodeFormRef = ref(null)
const passwordFormRef = ref(null)
const loading = ref(false)
const qrcodeVisible = ref(false)

// 登录模式
const loginMode = ref('qrcode')
const loginModeOptions = [
  { label: '扫码登录', value: 'qrcode' },
  { label: '密码登录', value: 'password' }
]

// 监听登录模式切换，同步用户名
watch(loginMode, () => {
  // 从密码登录切换到扫码登录
  if (loginMode.value === 'qrcode' && passwordForm.value.alias) {
    qrcodeForm.value.alias = passwordForm.value.alias
  }
  // 从扫码登录切换到密码登录
  else if (loginMode.value === 'password' && qrcodeForm.value.alias) {
    passwordForm.value.alias = qrcodeForm.value.alias
  }
})

// QR码登录表单
const qrcodeForm = ref({
  alias: '',
})

const qrcodeRules = {
  alias: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' },
  ],
}

// 密码登录表单
const passwordForm = ref({
  alias: '',
  password: '',
})

const passwordRules = {
  alias: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' },
  ],
}

// QR码登录
const handleQRCodeLogin = async () => {
  if (!qrcodeFormRef.value) return

  try {
    const valid = await qrcodeFormRef.value.validate()
    if (!valid) return

    // 显示 QR 码弹窗
    qrcodeVisible.value = true
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

// 密码登录
const handlePasswordLogin = async () => {
  if (!passwordFormRef.value) return

  try {
    const valid = await passwordFormRef.value.validate()
    if (!valid) return

    loading.value = true

    const response = await authAPI.aliasLogin(
      passwordForm.value.alias,
      passwordForm.value.password
    )

    if (response.success) {
      // 使用 authStore 保存认证信息
      const user = {
        id: response.user_id,
        alias: response.alias,
        role: response.role || 'user',
        is_approved: response.is_approved !== false,
      }
      authStore.setAuth(response.authorization, user)

      // 如果有 Token 警告，显示提示
      if (response.token_warning && response.warning_message) {
        ElMessage({
          type: 'warning',
          duration: 5000,
          showClose: true,
          message: response.warning_message,
        })
      } else {
        ElMessage.success(`欢迎回来，${response.alias}！`)
      }

      // 跳转到重定向页面或仪表盘
      const redirect = route.query.redirect || '/dashboard'
      router.push(redirect)
    } else {
      // 根据不同错误类型提供友好提示
      handlePasswordLoginError(response.message)
    }
  } catch (error) {
    console.error('密码登录失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '登录失败，请稍后重试'
    handlePasswordLoginError(errorMsg)
  } finally {
    loading.value = false
  }
}

// 处理密码登录错误
const handlePasswordLoginError = (message) => {
  if (!message) {
    ElMessage.error('登录失败，请稍后重试')
    return
  }

  // 用户不存在或密码错误
  if (message.includes('用户名或密码错误')) {
    ElMessage.error('用户名或密码错误')
    return
  }

  // 未设置密码
  if (message.includes('未设置密码')) {
    ElMessage.warning('该账户未设置密码，请使用扫码登录')
    return
  }

  // 用户不存在
  if (message.includes('用户不存在')) {
    ElMessage.error('用户不存在，请检查用户名或使用扫码登录注册')
    return
  }

  // 其他错误
  ElMessage.error(message || '登录失败，请稍后重试')
}

const handleLoginSuccess = (user) => {
  ElMessage.success(`欢迎回来，${user.alias}！`)

  // 跳转到重定向页面或仪表盘
  const redirect = route.query.redirect || '/dashboard'
  router.push(redirect)
}

const handleLoginError = (error) => {
  ElMessage.error(error.message || '登录失败')
}
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 450px;
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.subtitle {
  margin: 10px 0 0 0;
  font-size: 14px;
  color: #909399;
}

.mode-switch {
  margin-bottom: 20px;
}

.login-button {
  width: 100%;
}

.tips-link {
  text-align: center;
  margin-top: 10px;
}

.tips {
  margin-top: 20px;
}

.tips p {
  margin: 5px 0;
  font-size: 14px;
  line-height: 1.5;
}

.tip-note {
  margin-top: 12px !important;
  padding-top: 8px;
  border-top: 1px dashed #e0e0e0;
  color: #606266;
  font-weight: 500;
}
</style>
