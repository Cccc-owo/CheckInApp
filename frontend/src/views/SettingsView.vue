<template>
  <Layout>
    <div class="settings-view">
      <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-bold text-gray-800 mb-6">个人设置</h1>

        <!-- 基本信息卡片 -->
        <div class="md3-card p-6 mb-6">
          <h2 class="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <UserOutlined class="mr-2" />
            基本信息
          </h2>

          <a-descriptions :column="1" bordered>
            <a-descriptions-item label="用户ID">{{ user?.id }}</a-descriptions-item>
            <a-descriptions-item label="当前用户名">{{ user?.alias }}</a-descriptions-item>
            <a-descriptions-item label="角色">
              <a-tag :color="user?.role === 'admin' ? 'error' : 'success'">
                {{ user?.role === 'admin' ? '管理员' : '普通用户' }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="密码状态">
              <a-tag :color="hasPassword ? 'success' : 'warning'">
                {{ hasPassword ? '已设置' : '未设置' }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="创建时间">
              {{ formatDate(user?.created_at) }}
            </a-descriptions-item>
          </a-descriptions>
        </div>

        <!-- 修改邮箱 -->
        <div class="md3-card p-6 mb-6">
          <h2 class="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <EditOutlined class="mr-2" />
            修改个人信息
          </h2>

          <a-form
            :model="profileForm"
            :rules="profileRules"
            ref="profileFormRef"
            layout="vertical"
          >
            <a-form-item label="邮箱" name="email">
              <a-input
                v-model:value="profileForm.email"
                placeholder="请输入邮箱地址（可选）"
                allow-clear
              />
            </a-form-item>

            <a-alert
              message="用户名无法修改"
              description="用户名只能由管理员修改，如需修改请联系管理员"
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 24px"
            />

            <a-form-item style="margin-top: 8px">
              <a-space>
                <a-button
                  type="primary"
                  :loading="profileLoading"
                  @click="handleUpdateProfile"
                >
                  保存
                </a-button>
                <a-button @click="resetProfileForm">重置</a-button>
              </a-space>
            </a-form-item>
          </a-form>
        </div>

        <!-- 设置/修改密码 -->
        <div class="md3-card p-6">
          <h2 class="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <KeyOutlined class="mr-2" />
            {{ hasPassword ? '修改密码' : '设置密码' }}
          </h2>

          <a-alert
            v-if="!hasPassword"
            message="您还未设置密码"
            description="设置密码后，您可以使用用户名+密码的方式快速登录"
            type="warning"
            class="mb-4"
            show-icon
            :closable="false"
          />

          <a-form
            :model="passwordForm"
            layout="vertical"
          >
            <a-form-item
              v-if="hasPassword"
              label="当前密码"
            >
              <a-input-password
                v-model:value="passwordForm.currentPassword"
                placeholder="请输入当前密码"
                allow-clear
              />
            </a-form-item>

            <a-form-item label="新密码">
              <a-input-password
                v-model:value="passwordForm.newPassword"
                placeholder="请输入新密码（至少6个字符）"
                allow-clear
              />
            </a-form-item>

            <a-form-item label="确认新密码">
              <a-input-password
                v-model:value="passwordForm.confirmPassword"
                placeholder="请再次输入新密码"
                allow-clear
              />
            </a-form-item>

            <a-form-item style="margin-top: 8px">
              <a-space>
                <a-button
                  type="primary"
                  :loading="passwordLoading"
                  @click="handleUpdatePassword"
                >
                  {{ hasPassword ? '修改密码' : '设置密码' }}
                </a-button>
                <a-button @click="resetPasswordForm">重置</a-button>
              </a-space>
            </a-form-item>
          </a-form>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { UserOutlined, EditOutlined, KeyOutlined } from '@ant-design/icons-vue'
import { userAPI } from '@/api'
import Layout from '@/components/Layout.vue'

const profileFormRef = ref(null)
const profileLoading = ref(false)
const passwordLoading = ref(false)

const user = ref(null)
const hasPassword = ref(false)

// 个人信息表单
const profileForm = ref({
  email: '',
})

const profileRules = {
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
  ],
}

// 密码表单
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

// 加载用户信息
const loadUserInfo = async () => {
  try {
    user.value = await userAPI.getCurrentUser()
    profileForm.value.email = user.value.email || ''

    // 从后端返回的数据中获取密码状态
    hasPassword.value = user.value.has_password || false
  } catch (error) {
    message.error(error.message || '加载用户信息失败')
  }
}

// 更新个人信息
const handleUpdateProfile = async () => {
  if (!profileFormRef.value) return

  try {
    await profileFormRef.value.validate()
    profileLoading.value = true

    await userAPI.updateProfile({
      email: profileForm.value.email || null,
    })

    message.success('个人信息修改成功')
    await loadUserInfo()
  } catch (error) {
    if (error.errorFields) return // 验证错误
    const errorMsg = error.response?.data?.detail || error.message || '修改失败'
    message.error(errorMsg)
  } finally {
    profileLoading.value = false
  }
}

// 重置个人信息表单
const resetProfileForm = () => {
  profileForm.value.email = user.value?.email || ''
  profileFormRef.value?.clearValidate()
}

// 更新密码
const handleUpdatePassword = async () => {
  try {
    // 手动验证
    if (hasPassword.value && !passwordForm.value.currentPassword) {
      message.error('请输入当前密码')
      return
    }

    if (!passwordForm.value.newPassword) {
      message.error('请输入新密码')
      return
    }

    if (passwordForm.value.newPassword.length < 6) {
      message.error('密码至少需要6个字符')
      return
    }

    if (!passwordForm.value.confirmPassword) {
      message.error('请再次输入新密码')
      return
    }

    if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
      message.error('两次输入的密码不一致')
      return
    }

    passwordLoading.value = true

    const updateData = {
      new_password: passwordForm.value.newPassword,
    }

    if (hasPassword.value) {
      updateData.current_password = passwordForm.value.currentPassword
    }

    await userAPI.updateProfile(updateData)

    message.success(hasPassword.value ? '密码修改成功' : '密码设置成功')
    hasPassword.value = true
    resetPasswordForm()
  } catch (error) {
    const errorMsg = error.response?.data?.detail || error.message || '操作失败'
    message.error(errorMsg)
  } finally {
    passwordLoading.value = false
  }
}

// 重置密码表单
const resetPasswordForm = () => {
  passwordForm.value = {
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  loadUserInfo()
})
</script>

<style scoped>
.md3-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px 1px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.md3-card:hover {
  box-shadow: 0 4px 8px 3px rgba(0, 0, 0, 0.10);
}
</style>
