<template>
  <Layout>
    <div class="admin-users-container">
      <a-card>
        <template #title>
          <div class="card-header">
            <div>
              <UserOutlined />
              <span>用户管理</span>
            </div>
            <a-space class="actions">
              <a-button type="primary" @click="handleCreate">
                <template #icon><PlusOutlined /></template>
                创建用户
              </a-button>
              <a-button @click="handleRefresh">
                <template #icon><ReloadOutlined /></template>
                刷新
              </a-button>
            </a-space>
          </div>
        </template>

        <!-- Tab 切换 -->
        <a-tabs v-model:active-key="activeTab" @change="handleTabChange">
          <!-- 待审批用户 Tab -->
          <a-tab-pane key="pending" tab="待审批用户">
            <!-- 桌面端表格 -->
            <a-table
              v-if="!isMobile"
              :data-source="pendingUsers"
              :columns="pendingColumns"
              :loading="loading"
              :row-key="record => record.id"
              :scroll="{ x: 'max-content' }"
              bordered
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'created_at'">
                  {{ formatDateTime(record.created_at) }}
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-space>
                    <a-button type="primary" size="small" @click="handleApprove(record)">
                      通过
                    </a-button>
                    <a-button danger size="small" @click="handleReject(record)"> 拒绝 </a-button>
                  </a-space>
                </template>
              </template>
            </a-table>

            <!-- 移动端卡片视图 -->
            <a-space v-else direction="vertical" :size="16" style="width: 100%">
              <a-card v-for="user in pendingUsers" :key="user.id" size="small" :loading="loading">
                <a-descriptions :column="1" size="small" bordered>
                  <a-descriptions-item label="ID">{{ user.id }}</a-descriptions-item>
                  <a-descriptions-item label="用户名">{{ user.alias }}</a-descriptions-item>
                  <a-descriptions-item label="邮箱">{{ user.email || '-' }}</a-descriptions-item>
                  <a-descriptions-item label="注册时间">{{
                    formatDateTime(user.created_at)
                  }}</a-descriptions-item>
                </a-descriptions>
                <a-space class="mt-3" style="width: 100%">
                  <a-button type="primary" size="small" block @click="handleApprove(user)"
                    >通过</a-button
                  >
                  <a-button danger size="small" block @click="handleReject(user)">拒绝</a-button>
                </a-space>
              </a-card>
              <a-empty v-if="!loading && pendingUsers.length === 0" description="暂无数据" />
            </a-space>
          </a-tab-pane>

          <!-- 所有用户 Tab -->
          <a-tab-pane key="all" tab="所有用户">
            <!-- 桌面端表格 -->
            <a-table
              v-if="!isMobile"
              :data-source="userStore.users"
              :columns="allColumns"
              :loading="loading"
              :row-key="record => record.id"
              :row-selection="rowSelection"
              :scroll="{ x: 'max-content' }"
              bordered
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'role'">
                  <a-tag :color="record.role === 'admin' ? 'error' : 'blue'">
                    {{ record.role === 'admin' ? '管理员' : '用户' }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'is_approved'">
                  <a-tag :color="record.is_approved ? 'success' : 'warning'">
                    {{ record.is_approved ? '已审批' : '待审批' }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'jwt_exp'">
                  {{
                    record.jwt_exp && record.jwt_exp !== '0'
                      ? formatDateTime(parseInt(record.jwt_exp) * 1000)
                      : '-'
                  }}
                </template>
                <template v-else-if="column.key === 'created_at'">
                  {{ formatDateTime(record.created_at) }}
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-space>
                    <a-button type="primary" size="small" @click="handleEdit(record)">
                      编辑
                    </a-button>
                    <a-button danger size="small" @click="handleDelete(record)"> 删除 </a-button>
                  </a-space>
                </template>
              </template>
            </a-table>

            <!-- 移动端卡片视图 -->
            <a-space v-else direction="vertical" :size="16" style="width: 100%">
              <a-card
                v-for="user in userStore.users"
                :key="user.id"
                size="small"
                :loading="loading"
              >
                <a-descriptions :column="1" size="small" bordered>
                  <a-descriptions-item label="ID">{{ user.id }}</a-descriptions-item>
                  <a-descriptions-item label="用户名">{{ user.alias }}</a-descriptions-item>
                  <a-descriptions-item label="邮箱">{{ user.email || '-' }}</a-descriptions-item>
                  <a-descriptions-item label="角色">
                    <a-tag :color="user.role === 'admin' ? 'error' : 'blue'">
                      {{ user.role === 'admin' ? '管理员' : '用户' }}
                    </a-tag>
                  </a-descriptions-item>
                  <a-descriptions-item label="审批状态">
                    <a-tag :color="user.is_approved ? 'success' : 'warning'">
                      {{ user.is_approved ? '已审批' : '待审批' }}
                    </a-tag>
                  </a-descriptions-item>
                  <a-descriptions-item label="Token过期">
                    {{
                      user.jwt_exp && user.jwt_exp !== '0'
                        ? formatDateTime(parseInt(user.jwt_exp) * 1000)
                        : '-'
                    }}
                  </a-descriptions-item>
                  <a-descriptions-item label="创建时间">{{
                    formatDateTime(user.created_at)
                  }}</a-descriptions-item>
                </a-descriptions>
                <a-space class="mt-3" style="width: 100%">
                  <a-button type="primary" size="small" block @click="handleEdit(user)"
                    >编辑</a-button
                  >
                  <a-button danger size="small" block @click="handleDelete(user)">删除</a-button>
                </a-space>
              </a-card>
            </a-space>

            <!-- 批量操作 -->
            <div v-if="selectedUsers.length > 0" class="batch-actions">
              <a-alert
                :message="`已选择 ${selectedUsers.length} 个用户`"
                type="info"
                :closable="false"
              >
                <template #description>
                  <a-space style="margin-top: 10px">
                    <a-button type="primary" size="small" @click="handleBatchApprove">
                      批量审批
                    </a-button>
                    <a-button danger size="small" @click="handleBatchDelete"> 批量删除 </a-button>
                  </a-space>
                </template>
              </a-alert>
            </div>
          </a-tab-pane>
        </a-tabs>
      </a-card>

      <!-- 创建/编辑用户对话框 -->
      <a-modal
        v-model:open="dialogVisible"
        :title="dialogMode === 'create' ? '创建用户' : '编辑用户'"
        :width="isMobile ? '100%' : 600"
        :style="isMobile ? { top: 0, maxWidth: '100vw' } : {}"
      >
        <a-form ref="formRef" :model="formData" :rules="formRules" layout="vertical">
          <a-form-item label="用户名" name="alias">
            <a-input v-model:value="formData.alias" placeholder="请输入用户名" />
          </a-form-item>

          <a-form-item label="邮箱" name="email">
            <a-input v-model:value="formData.email" placeholder="请输入邮箱" />
          </a-form-item>

          <a-form-item label="角色" name="role">
            <a-select v-model:value="formData.role" placeholder="请选择角色">
              <a-select-option value="user">用户</a-select-option>
              <a-select-option value="admin">管理员</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="审批状态" name="is_approved">
            <a-switch v-model:checked="formData.is_approved" />
            <span class="form-hint">是否已审批通过</span>
          </a-form-item>

          <a-form-item label="密码" name="password">
            <a-input-password
              v-model:value="formData.password"
              :placeholder="dialogMode === 'create' ? '请输入密码' : '留空则不修改密码'"
            />
            <span v-if="dialogMode === 'edit'" class="form-hint"> 留空则不修改密码 </span>
          </a-form-item>

          <a-form-item v-if="dialogMode === 'edit'" label="重置密码">
            <a-switch v-model:checked="formData.reset_password" />
            <span v-if="formData.reset_password" class="form-hint-danger">
              ⚠️ 将重置为默认密码
            </span>
          </a-form-item>
        </a-form>

        <template #footer>
          <a-button @click="dialogVisible = false">取消</a-button>
          <a-button type="primary" :loading="submitting" @click="handleSubmit"> 确定 </a-button>
        </template>
      </a-modal>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { UserOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons-vue';
import Layout from '@/components/Layout.vue';
import { useBreakpoint } from '@/composables/useBreakpoint';
import { useUserStore } from '@/stores/user';
import { adminAPI } from '@/api/index';

const userStore = useUserStore();
const { isMobile } = useBreakpoint();

// 状态
const loading = ref(false);
const activeTab = ref('all'); // 默认展示所有用户
const pendingUsers = ref([]);
const selectedUsers = ref([]);
const selectedRowKeys = ref([]);
const dialogVisible = ref(false);
const dialogMode = ref('create');
const submitting = ref(false);

// 表单
const formRef = ref(null);
const formData = ref({
  alias: '',
  role: 'user',
  is_approved: true,
  email: '',
  password: '',
  reset_password: false,
});

// 表单验证规则
const formRules = {
  alias: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  email: [{ type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }],
};

// 时间格式化
const formatDateTime = timestamp => {
  if (!timestamp) return '-';
  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

// 待审批用户表格列
const pendingColumns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: '用户名', dataIndex: 'alias', key: 'alias', ellipsis: true },
  { title: '邮箱', dataIndex: 'email', key: 'email', ellipsis: true },
  { title: '注册时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '操作', key: 'actions', width: 200, fixed: 'right' },
];

// 所有用户表格列
const allColumns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: '用户名', dataIndex: 'alias', key: 'alias', ellipsis: true },
  { title: '邮箱', dataIndex: 'email', key: 'email', ellipsis: true },
  { title: '角色', dataIndex: 'role', key: 'role', width: 100 },
  { title: '审批状态', dataIndex: 'is_approved', key: 'is_approved', width: 100 },
  { title: 'Token 过期时间', dataIndex: 'jwt_exp', key: 'jwt_exp', width: 180 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '操作', key: 'actions', width: 200, fixed: 'right' },
];

// 行选择配置
const rowSelection = {
  selectedRowKeys: selectedRowKeys,
  onChange: (keys, rows) => {
    selectedRowKeys.value = keys;
    selectedUsers.value = rows;
  },
};

// 获取待审批用户
const fetchPendingUsers = async () => {
  loading.value = true;
  try {
    pendingUsers.value = await adminAPI.getPendingUsers();
  } catch (error) {
    message.error(error.message || '获取待审批用户失败');
  } finally {
    loading.value = false;
  }
};

// Tab 切换
const handleTabChange = tab => {
  if (tab === 'pending') {
    fetchPendingUsers();
  } else {
    handleRefresh();
  }
};

// 审批通过用户
const handleApprove = async user => {
  Modal.confirm({
    title: '审批确认',
    content: `确认通过用户 "${user.alias}" 的审批吗？`,
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        await adminAPI.approveUser(user.id);
        message.success('审批成功');
        fetchPendingUsers();
      } catch (error) {
        message.error(error.message || '审批失败');
      }
    },
  });
};

// 拒绝用户
const handleReject = async user => {
  Modal.confirm({
    title: '拒绝确认',
    content: `确认拒绝用户 "${user.alias}" 的申请吗？拒绝后将删除该用户。`,
    okText: '确认',
    cancelText: '取消',
    okType: 'danger',
    onOk: async () => {
      try {
        await adminAPI.rejectUser(user.id);
        message.success('已拒绝并删除用户');
        fetchPendingUsers();
      } catch (error) {
        message.error(error.message || '操作失败');
      }
    },
  });
};

// 刷新数据
const handleRefresh = async () => {
  if (activeTab.value === 'pending') {
    await fetchPendingUsers();
  } else {
    loading.value = true;
    try {
      await userStore.fetchUsers();
      message.success('刷新成功');
    } catch (error) {
      message.error(error.message || '刷新失败');
    } finally {
      loading.value = false;
    }
  }
};

// 创建用户
const handleCreate = () => {
  dialogMode.value = 'create';
  formData.value = {
    alias: '',
    role: 'user',
    is_approved: true,
    email: '',
    password: '',
    reset_password: false,
  };
  dialogVisible.value = true;
};

// 编辑用户
const handleEdit = user => {
  dialogMode.value = 'edit';
  formData.value = {
    id: user.id,
    alias: user.alias,
    role: user.role,
    is_approved: user.is_approved,
    email: user.email || '',
    password: '',
    reset_password: false,
  };
  dialogVisible.value = true;
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;

  try {
    await formRef.value.validate();
    submitting.value = true;

    // 检查密码设置冲突
    if (dialogMode.value === 'edit' && formData.value.password && formData.value.reset_password) {
      message.warning('不能同时设置新密码和重置密码，请选择其一');
      submitting.value = false;
      return;
    }

    if (dialogMode.value === 'create') {
      await userStore.createUser(formData.value);
      message.success('创建成功');
    } else {
      await userStore.updateUser(formData.value.id, formData.value);
      message.success('更新成功');
    }

    dialogVisible.value = false;
    await handleRefresh();
  } catch (error) {
    message.error(error.message || '操作失败');
  } finally {
    submitting.value = false;
  }
};

// 删除用户
const handleDelete = user => {
  Modal.confirm({
    title: '警告',
    content: `确定要删除用户 "${user.alias}" 吗？`,
    okText: '确定',
    cancelText: '取消',
    okType: 'danger',
    onOk: async () => {
      try {
        await userStore.deleteUser(user.id);
        message.success('删除成功');
        await handleRefresh();
      } catch (error) {
        message.error(error.message || '删除失败');
      }
    },
  });
};

// 批量审批
const handleBatchApprove = () => {
  Modal.confirm({
    title: '批量审批确认',
    content: `确认批量审批 ${selectedUsers.value.length} 个用户吗？`,
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      const userIds = selectedUsers.value.map(u => u.id);
      let successCount = 0;
      let failureCount = 0;

      for (const userId of userIds) {
        try {
          await adminAPI.approveUser(userId);
          successCount++;
        } catch {
          failureCount++;
        }
      }

      message.success(`批量审批完成：成功 ${successCount}，失败 ${failureCount}`);
      await handleRefresh();
    },
  });
};

// 批量删除
const handleBatchDelete = () => {
  Modal.confirm({
    title: '批量删除警告',
    content: `确定要删除选中的 ${selectedUsers.value.length} 个用户吗？此操作不可恢复！`,
    okText: '确定',
    cancelText: '取消',
    okType: 'danger',
    onOk: async () => {
      const userIds = selectedUsers.value.map(u => u.id);
      let successCount = 0;
      let failureCount = 0;

      for (const userId of userIds) {
        try {
          await userStore.deleteUser(userId);
          successCount++;
        } catch {
          failureCount++;
        }
      }

      message.success(`批量删除完成：成功 ${successCount}，失败 ${failureCount}`);
      await handleRefresh();
    },
  });
};

onMounted(() => {
  // 默认加载所有用户
  handleRefresh();
});
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

.mt-3 {
  margin-top: 12px;
}
</style>
