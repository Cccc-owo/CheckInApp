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

        <div class="info-table">
          <div class="info-row">
            <div class="info-label">用户名</div>
            <div class="info-value">{{ user?.alias || '加载中...' }}</div>
          </div>
          <div class="info-row">
            <div class="info-label">注册时间</div>
            <div class="info-value">{{ formatDate(user?.created_at) }}</div>
          </div>
          <div class="info-row">
            <div class="info-label">审批状态</div>
            <div class="info-value">
              <span class="status-tag warning">待审批</span>
            </div>
          </div>
        </div>

        <div class="alert-box">
          <div class="alert-title">⚠️ 审批说明</div>
          <ul class="tips-list">
            <li>管理员将在 <strong>24 小时内</strong> 审核您的注册申请</li>
            <li>审核通过后，您将可以使用所有功能</li>
            <li>如超过 24 小时未审批，账户将被自动删除</li>
            <li>您可以随时刷新此页面查看最新状态</li>
          </ul>
        </div>

        <div class="actions">
          <button class="btn btn-primary" @click="checkStatus">
            刷新状态
          </button>
          <button class="btn btn-default" @click="logout">
            退出登录
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const user = ref(null)

const checkStatus = async () => {
  try {
    const response = await userAPI.getUserStatus()
    user.value = response

    if (response.is_approved) {
      alert('恭喜！您的账户已通过审批')
      router.push('/dashboard')
    } else {
      alert('仍在等待审批中')
    }
  } catch (error) {
    console.error('获取状态失败:', error)
    alert('获取状态失败：' + (error.message || '未知错误'))
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

.info-table {
  background: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 30px;
}

.info-row {
  display: flex;
  border-bottom: 1px solid #ddd;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  flex: 0 0 120px;
  padding: 15px 20px;
  background: #f5f5f5;
  font-weight: bold;
  color: #303133;
  border-right: 1px solid #ddd;
}

.info-value {
  flex: 1;
  padding: 15px 20px;
  color: #606266;
}

.status-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
}

.status-tag.warning {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffc107;
}

.alert-box {
  background: #e7f3ff;
  border-left: 4px solid #409eff;
  padding: 20px;
  margin-bottom: 30px;
  border-radius: 4px;
}

.alert-title {
  font-weight: bold;
  margin-bottom: 10px;
  color: #303133;
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
}

.btn {
  padding: 12px 30px;
  border: none;
  border-radius: 5px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: #409eff;
  color: white;
}

.btn-primary:hover {
  background: #66b1ff;
}

.btn-default {
  background: #f5f5f5;
  color: #606266;
  border: 1px solid #dcdfe6;
}

.btn-default:hover {
  background: #e8e8e8;
}
</style>
