<template>
  <div class="pending-container">
    <div class="pending-card">
      <div class="card-header">
        <h2>🕐 等待审批</h2>
      </div>

      <div class="pending-content">
        <div class="result-icon">
          <span class="info-icon">ℹ️</span>
        </div>

        <h3 class="result-title">您的账户正在等待管理员审批</h3>

        <div class="result-subtitle">
          <p>您已成功注册，账户信息如下：</p>
        </div>

        <a-descriptions :column="1" bordered class="mb-6">
          <a-descriptions-item label="用户名">
            {{ user?.alias || '加载中...' }}
          </a-descriptions-item>
          <a-descriptions-item label="邮箱">
            <template v-if="user?.email">
              {{ user.email }}
            </template>
            <template v-else>
              <a-tag color="warning">未设置</a-tag>
            </template>
          </a-descriptions-item>
          <a-descriptions-item label="密码">
            <template v-if="user?.has_password">
              <a-tag color="success">已设置</a-tag>
            </template>
            <template v-else>
              <a-tag color="warning">未设置</a-tag>
            </template>
          </a-descriptions-item>
          <a-descriptions-item label="注册时间">
            {{ formatDate(user?.created_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="审批状态">
            <a-tag color="warning">待审批</a-tag>
          </a-descriptions-item>
        </a-descriptions>

        <a-alert
          message="⚠️ 审批说明"
          type="info"
          :closable="false"
          show-icon
          class="mb-6"
        >
          <template #description>
            <ul class="tips-list">
              <li>管理员将在 <strong>24 小时内</strong> 审核您的注册申请</li>
              <li>审核通过后，您将可以使用所有功能</li>
              <li>如超过 24 小时未审批，账户将被自动删除</li>
              <li><strong>建议：</strong>审批期间可以设置邮箱和密码，方便后续使用</li>
              <li>您可以随时刷新此页面查看最新状态</li>
            </ul>
          </template>
        </a-alert>

        <div class="actions">
          <a-button type="primary" size="large" @click="checkStatus">
            <template #icon><ReloadOutlined /></template>
            刷新状态
          </a-button>
          <a-button size="large" @click="showProfileModal = true">
            <template #icon><SettingOutlined /></template>
            完善信息
          </a-button>
          <a-button size="large" @click="logout">
            <template #icon><LogoutOutlined /></template>
            退出登录
          </a-button>
        </div>
      </div>
    </div>

    <!-- 完善信息弹窗 -->
    <a-modal
      v-model:open="showProfileModal"
      title="完善个人信息"
      :confirm-loading="profileLoading"
      @ok="handleUpdateProfile"
      @cancel="resetProfileForm"
      width="500px"
    >
      <a-form :model="profileForm" layout="vertical">
        <a-form-item label="邮箱地址（可选）" name="email">
          <a-input
            v-model:value="profileForm.email"
            placeholder="用于接收审批通知"
            type="email"
          />
          <div class="form-hint">建议设置邮箱，方便接收审批结果通知</div>
        </a-form-item>

        <a-form-item
          label="新密码（可选）"
          name="new_password"
          :help="user?.has_password ? '留空表示不修改密码' : '设置密码后可以使用密码登录'"
        >
          <a-input-password
            v-model:value="profileForm.new_password"
            placeholder="至少6位字符"
            autocomplete="new-password"
          />
        </a-form-item>

        <a-form-item
          v-if="profileForm.new_password"
          label="确认密码"
          name="confirm_password"
        >
          <a-input-password
            v-model:value="profileForm.confirm_password"
            placeholder="再次输入新密码"
            autocomplete="new-password"
          />
        </a-form-item>

        <a-form-item
          v-if="user?.has_password && profileForm.new_password"
          label="当前密码"
          name="current_password"
        >
          <a-input-password
            v-model:value="profileForm.current_password"
            placeholder="修改密码时需要提供当前密码"
            autocomplete="current-password"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { ReloadOutlined, LogoutOutlined, SettingOutlined } from '@ant-design/icons-vue'
import { userAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const user = ref(null)
const showProfileModal = ref(false)
const profileLoading = ref(false)

const profileForm = ref({
  email: '',
  new_password: '',
  confirm_password: '',
  current_password: '',
})

const checkStatus = async () => {
  try {
    const response = await userAPI.getUserStatus()
    user.value = response

    if (response.is_approved) {
      message.success('恭喜！您的账户已通过审批')
      router.push('/dashboard')
    } else {
      message.info('仍在等待审批中')
    }
  } catch (error) {
    console.error('获取状态失败:', error)
    message.error('获取状态失败：' + (error.message || '未知错误'))
  }
}

const loadUserInfo = async () => {
  try {
    const response = await userAPI.getCurrentUser()
    user.value = response
    // 初始化表单
    profileForm.value.email = response.email || ''
  } catch (error) {
    console.error('加载用户信息失败:', error)
  }
}

const handleUpdateProfile = async () => {
  // 验证
  if (profileForm.value.new_password && profileForm.value.new_password.length < 6) {
    message.error('密码至少需要 6 位字符')
    return
  }

  if (profileForm.value.new_password !== profileForm.value.confirm_password) {
    message.error('两次输入的密码不一致')
    return
  }

  if (user.value?.has_password && profileForm.value.new_password && !profileForm.value.current_password) {
    message.error('修改密码时需要提供当前密码')
    return
  }

  profileLoading.value = true

  try {
    const updateData = {}

    // 只提交有变化的字段
    if (profileForm.value.email !== (user.value?.email || '')) {
      updateData.email = profileForm.value.email || null
    }

    if (profileForm.value.new_password) {
      updateData.new_password = profileForm.value.new_password
      if (user.value?.has_password) {
        updateData.current_password = profileForm.value.current_password
      }
    }

    // 如果没有要更新的字段
    if (Object.keys(updateData).length === 0) {
      message.info('没有需要更新的信息')
      showProfileModal.value = false
      return
    }

    await userAPI.updateProfile(updateData)
    message.success('个人信息更新成功')
    showProfileModal.value = false
    resetProfileForm()

    // 重新加载用户信息
    await loadUserInfo()

    // 如果设置了密码，更新本地存储的用户信息
    if (updateData.new_password) {
      const currentUser = authStore.user
      if (currentUser) {
        currentUser.has_password = true
        localStorage.setItem('user', JSON.stringify(currentUser))
      }
    }
  } catch (error) {
    console.error('更新个人信息失败:', error)
    message.error(error.message || '更新失败，请重试')
  } finally {
    profileLoading.value = false
  }
}

const resetProfileForm = () => {
  profileForm.value = {
    email: user.value?.email || '',
    new_password: '',
    confirm_password: '',
    current_password: '',
  }
}

const logout = () => {
  authStore.logout()
  router.push('/login')
}

const formatDate = (dateStr) => {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadUserInfo()
  checkStatus()
})
</script>

<style scoped>
.pending-container {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.pending-card {
  width: 100%;
  max-width: 700px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 30px;
  text-align: center;
}

.card-header h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
}

.pending-content {
  padding: 40px;
}

.result-icon {
  text-align: center;
  margin-bottom: 20px;
}

.info-icon {
  font-size: 64px;
  display: inline-block;
}

.result-title {
  text-align: center;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 10px 0;
}

.result-subtitle {
  text-align: center;
  color: #606266;
  margin-bottom: 30px;
}

.mb-6 {
  margin-bottom: 30px;
}

.tips-list {
  text-align: left;
  padding-left: 20px;
  line-height: 1.8;
  margin: 0;
  color: #606266;
}

.tips-list li {
  margin: 8px 0;
}

.actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
}

.form-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
