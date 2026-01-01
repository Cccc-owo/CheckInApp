<template>
  <Layout>
    <div class="admin-users-container">
      <el-card>
        <template #header>
          <div class="card-header">
            <div>
              <el-icon><UserFilled /></el-icon>
              <span>用户管理</span>
            </div>
            <div class="actions">
              <el-button type="success" :icon="Plus" @click="handleCreate">
                创建用户
              </el-button>
              <el-button type="primary" :icon="Refresh" @click="handleRefresh">
                刷新
              </el-button>
            </div>
          </div>
        </template>

        <!-- Tab 切换 -->
        <el-tabs v-model="activeTab" @tab-change="handleTabChange">
          <!-- 待审批用户 Tab -->
          <el-tab-pane label="待审批用户" name="pending">
            <el-table
              :data="pendingUsers"
              v-loading="loading"
              stripe
              border
            >
              <el-table-column prop="id" label="ID" width="80" />
              <el-table-column prop="alias" label="用户名" min-width="150" />
              <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
              <el-table-column prop="registered_ip" label="注册IP" width="150" />

              <el-table-column prop="created_at" label="注册时间" width="180">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </el-table-column>

              <el-table-column label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <el-button type="success" size="small" @click="handleApprove(row)">
                    通过
                  </el-button>
                  <el-button type="danger" size="small" @click="handleReject(row)">
                    拒绝
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <el-empty v-if="!loading && pendingUsers.length === 0" description="暂无待审批用户" />
          </el-tab-pane>

          <!-- 所有用户 Tab -->
          <el-tab-pane label="所有用户" name="all">
            <!-- 用户表格 -->
            <el-table
              :data="userStore.users"
              v-loading="loading"
              stripe
              border
              @selection-change="handleSelectionChange"
            >
              <el-table-column type="selection" width="55" />
              <el-table-column prop="id" label="ID" width="80" />
              <el-table-column prop="alias" label="用户名" min-width="150" show-overflow-tooltip />
              <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />

              <el-table-column prop="role" label="角色" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'">
                    {{ row.role === 'admin' ? '管理员' : '用户' }}
                  </el-tag>
                </template>
              </el-table-column>

              <el-table-column prop="is_approved" label="审批状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.is_approved ? 'success' : 'warning'">
                    {{ row.is_approved ? '已审批' : '待审批' }}
                  </el-tag>
                </template>
              </el-table-column>

              <el-table-column prop="registered_ip" label="注册IP" width="150" />

              <el-table-column prop="jwt_exp" label="Token 过期时间" width="180">
                <template #default="{ row }">
                  {{ row.jwt_exp && row.jwt_exp !== '0' ? formatDateTime(parseInt(row.jwt_exp) * 1000) : '-' }}
                </template>
              </el-table-column>

              <el-table-column prop="created_at" label="创建时间" width="180">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </el-table-column>

              <el-table-column label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" size="small" @click="handleEdit(row)">
                    编辑
                  </el-button>
                  <el-button type="danger" size="small" @click="handleDelete(row)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 批量操作 -->
            <div class="batch-actions" v-if="selectedUsers.length > 0">
              <el-alert
                :title="`已选择 ${selectedUsers.length} 个用户`"
                type="info"
                :closable="false"
              >
                <template #default>
                  <div style="margin-top: 10px;">
                    <el-button type="success" size="small" @click="handleBatchApprove">
                      批量审批
                    </el-button>
                    <el-button type="danger" size="small" @click="handleBatchDelete">
                      批量删除
                    </el-button>
                  </div>
                </template>
              </el-alert>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <!-- 创建/编辑用户对话框 -->
      <el-dialog
        :title="dialogMode === 'create' ? '创建用户' : '编辑用户'"
        v-model="dialogVisible"
        width="600px"
      >
        <el-form
          ref="formRef"
          :model="formData"
          :rules="formRules"
          label-width="120px"
        >
          <el-form-item label="用户名" prop="alias">
            <el-input v-model="formData.alias" placeholder="请输入用户名" />
          </el-form-item>

          <el-form-item label="邮箱" prop="email">
            <el-input v-model="formData.email" placeholder="请输入邮箱" />
          </el-form-item>

          <el-form-item label="角色" prop="role">
            <el-select v-model="formData.role" placeholder="请选择角色">
              <el-option label="用户" value="user" />
              <el-option label="管理员" value="admin" />
            </el-select>
          </el-form-item>

          <el-form-item label="审批状态" prop="is_approved">
            <el-switch v-model="formData.is_approved" />
            <span class="form-hint">是否已审批通过</span>
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="formData.password"
              type="password"
              :placeholder="dialogMode === 'create' ? '请输入密码' : '留空则不修改密码'"
              show-password
            />
            <span class="form-hint" v-if="dialogMode === 'edit'">
              留空则不修改密码
            </span>
          </el-form-item>

          <el-form-item label="重置密码" v-if="dialogMode === 'edit'">
            <el-switch v-model="formData.reset_password" />
            <span class="form-hint-danger" v-if="formData.reset_password">
              ⚠️ 将重置为默认密码
            </span>
          </el-form-item>
        </el-form>

        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            确定
          </el-button>
        </template>
      </el-dialog>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UserFilled, Plus, Refresh } from '@element-plus/icons-vue'
import Layout from '@/components/Layout.vue'
import { useUserStore } from '@/stores/user'
import { useAdminStore } from '@/stores/admin'
import adminAPI from '@/api/index'

const userStore = useUserStore()
const adminStore = useAdminStore()

// 状态
const loading = ref(false)
const activeTab = ref('all') // 默认展示所有用户
const pendingUsers = ref([])
const selectedUsers = ref([])
const dialogVisible = ref(false)
const dialogMode = ref('create')
const submitting = ref(false)

// 表单
const formRef = ref(null)
const formData = ref({
  alias: '',
  role: 'user',
  is_approved: true,
  email: '',
  password: '',
  reset_password: false,
})

// 表单验证规则
const formRules = {
  alias: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
  ],
}

// 时间格式化
const formatDateTime = (timestamp) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

// 获取待审批用户
const fetchPendingUsers = async () => {
  loading.value = true
  try {
    pendingUsers.value = await adminAPI.getPendingUsers()
  } catch (error) {
    ElMessage.error(error.message || '获取待审批用户失败')
  } finally {
    loading.value = false
  }
}

// Tab 切换
const handleTabChange = (tab) => {
  if (tab === 'pending') {
    fetchPendingUsers()
  } else {
    handleRefresh()
  }
}

// 审批通过用户
const handleApprove = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确认通过用户 "${user.alias}" 的审批吗？`,
      '审批确认',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'success',
      }
    )

    await adminAPI.approveUser(user.id)
    ElMessage.success('审批成功')
    fetchPendingUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '审批失败')
    }
  }
}

// 拒绝用户
const handleReject = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确认拒绝用户 "${user.alias}" 的申请吗？拒绝后将删除该用户。`,
      '拒绝确认',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await adminAPI.rejectUser(user.id)
    ElMessage.success('已拒绝并删除用户')
    fetchPendingUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '操作失败')
    }
  }
}

// 刷新数据
const handleRefresh = async () => {
  if (activeTab.value === 'pending') {
    await fetchPendingUsers()
  } else {
    loading.value = true
    try {
      await userStore.fetchUsers()
      ElMessage.success('刷新成功')
    } catch (error) {
      ElMessage.error(error.message || '刷新失败')
    } finally {
      loading.value = false
    }
  }
}

// 创建用户
const handleCreate = () => {
  dialogMode.value = 'create'
  formData.value = {
    alias: '',
    role: 'user',
    is_approved: true,
    email: '',
    password: '',
    reset_password: false,
  }
  dialogVisible.value = true
}

// 编辑用户
const handleEdit = (user) => {
  dialogMode.value = 'edit'
  formData.value = {
    id: user.id,
    alias: user.alias,
    role: user.role,
    is_approved: user.is_approved,
    email: user.email || '',
    password: '',
    reset_password: false,
  }
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    // 检查密码设置冲突
    if (dialogMode.value === 'edit' && formData.value.password && formData.value.reset_password) {
      ElMessage.warning('不能同时设置新密码和重置密码，请选择其一')
      submitting.value = false
      return
    }

    if (dialogMode.value === 'create') {
      await userStore.createUser(formData.value)
      ElMessage.success('创建成功')
    } else {
      await userStore.updateUser(formData.value.id, formData.value)
      ElMessage.success('更新成功')
    }

    dialogVisible.value = false
    await handleRefresh()
  } catch (error) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 删除用户
const handleDelete = (user) => {
  ElMessageBox.confirm(`确定要删除用户 "${user.alias}" 吗？`, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      try {
        await userStore.deleteUser(user.id)
        ElMessage.success('删除成功')
        await handleRefresh()
      } catch (error) {
        ElMessage.error(error.message || '删除失败')
      }
    })
    .catch(() => {})
}

// 选择改变
const handleSelectionChange = (selection) => {
  selectedUsers.value = selection
}

// 批量审批
const handleBatchApprove = async () => {
  try {
    await ElMessageBox.confirm(
      `确认批量审批 ${selectedUsers.value.length} 个用户吗？`,
      '批量审批确认',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'success',
      }
    )

    const userIds = selectedUsers.value.map((u) => u.id)
    let successCount = 0
    let failureCount = 0

    for (const userId of userIds) {
      try {
        await adminAPI.approveUser(userId)
        successCount++
      } catch (error) {
        failureCount++
      }
    }

    ElMessage.success(`批量审批完成：成功 ${successCount}，失败 ${failureCount}`)
    await handleRefresh()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '批量审批失败')
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedUsers.value.length} 个用户吗？此操作不可恢复！`,
      '批量删除警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    const userIds = selectedUsers.value.map((u) => u.id)
    let successCount = 0
    let failureCount = 0

    for (const userId of userIds) {
      try {
        await userStore.deleteUser(userId)
        successCount++
      } catch (error) {
        failureCount++
      }
    }

    ElMessage.success(`批量删除完成：成功 ${successCount}，失败 ${failureCount}`)
    await handleRefresh()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '批量删除失败')
    }
  }
}

onMounted(() => {
  // 默认加载所有用户
  handleRefresh()
})
</script>

<style scoped>
.admin-users-container {
  max-width: 1600px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header > div {
  display: flex;
  align-items: center;
  gap: 8px;
}

.actions {
  gap: 10px;
}

.batch-actions {
  margin-top: 15px;
}

.form-hint {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}

.form-hint-danger {
  color: #f56c6c;
  font-weight: 500;
  display: block;
  margin-left: 0;
  margin-top: 4px;
}
</style>
