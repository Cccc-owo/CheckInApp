<template>
  <Layout>
    <div class="dashboard-container">
      <!-- 邮箱未设置提醒 -->
      <a-alert
        v-if="!authStore.user?.email"
        message="您还未设置邮箱地址"
        type="info"
        :closable="true"
        show-icon
        style="margin-bottom: 20px"
      >
        <template #description>
          <div>
            设置邮箱后可以接收打卡任务的通知和提醒。
            <a style="margin-left: 8px; cursor: pointer" @click="goToSettings"> 立即前往设置 → </a>
          </div>
        </template>
      </a-alert>

      <!-- 密码未设置提醒 -->
      <a-alert
        v-if="!authStore.user?.has_password"
        message="您还未设置登录密码"
        type="info"
        :closable="true"
        show-icon
        style="margin-bottom: 20px"
      >
        <template #description>
          <div>
            设置密码后可以使用用户名+密码快速登录。
            <a style="margin-left: 8px; cursor: pointer" @click="goToSettings"> 立即前往设置 → </a>
          </div>
        </template>
      </a-alert>

      <!-- Token 已过期提醒 -->
      <a-alert
        v-if="tokenStatus && !tokenStatus.is_valid"
        message="打卡凭证已过期"
        type="warning"
        :closable="true"
        show-icon
        style="margin-bottom: 20px"
      >
        <template #description>
          <div>
            打卡凭证已过期，无法自动打卡。请扫码刷新 Token。
            <a style="margin-left: 8px; cursor: pointer" @click="qrcodeModalVisible = true">
              立即刷新 →
            </a>
          </div>
        </template>
      </a-alert>

      <!-- 没有打卡任务提醒 -->
      <a-alert
        v-if="!taskStore.loading && taskStore.tasks.length === 0"
        message="您还没有打卡任务"
        type="info"
        :closable="true"
        show-icon
        style="margin-bottom: 20px"
      >
        <template #description>
          <div>
            创建您的第一个打卡任务，开启自动打卡之旅。
            <a style="margin-left: 8px; cursor: pointer" @click="goToTasks"> 立即创建 → </a>
          </div>
        </template>
      </a-alert>

      <a-row :gutter="[20, 20]">
        <!-- Token 状态卡片 -->
        <a-col :xs="24" :sm="24" :md="24">
          <a-card class="status-card md3-card">
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
                  <a-tag
                    v-if="tokenStatus.is_valid"
                    :color="tokenStatus.expiring_soon ? 'warning' : 'success'"
                  >
                    {{ formatRemainTime }}
                  </a-tag>
                  <a-tag v-else color="error">已过期</a-tag>
                </a-descriptions-item>

                <a-descriptions-item label="即将过期">
                  <a-tag v-if="!tokenStatus.is_valid" color="error"> 已过期 </a-tag>
                  <a-tag v-else :color="tokenStatus.expiring_soon ? 'warning' : 'success'">
                    {{ tokenStatus.expiring_soon ? '是' : '否' }}
                  </a-tag>
                </a-descriptions-item>
              </a-descriptions>

              <!-- 刷新 Token 按钮 -->
              <div style="margin-top: 24px; text-align: center">
                <!-- Token 未过期时：禁用按钮并显示提示 -->
                <a-tooltip v-if="tokenStatus.is_valid" title="Token 过期后才可以扫码刷新 Token">
                  <a-button type="primary" size="large" :disabled="true">
                    <template #icon><ReloadOutlined /></template>
                    刷新 Token
                  </a-button>
                </a-tooltip>

                <!-- Token 已过期时：启用按钮且无提示 -->
                <a-button v-else type="primary" size="large" @click="qrcodeModalVisible = true">
                  <template #icon><ReloadOutlined /></template>
                  刷新 Token
                </a-button>
              </div>

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
          <a-card class="md3-card">
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
                <a-select-option v-for="task in taskStore.tasks" :key="task.id" :value="task.id">
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
                      :color="
                        lastCheckIn.status === 'success'
                          ? 'success'
                          : lastCheckIn.status === 'out_of_time'
                            ? 'default'
                            : lastCheckIn.status === 'unknown'
                              ? 'warning'
                              : 'error'
                      "
                    >
                      {{
                        lastCheckIn.status === 'success'
                          ? '成功'
                          : lastCheckIn.status === 'out_of_time'
                            ? '时间范围外'
                            : lastCheckIn.status === 'unknown'
                              ? '异常'
                              : '失败'
                      }}
                    </a-tag>
                  </a-descriptions-item>
                  <a-descriptions-item label="打卡响应" :span="{ xs: 1, sm: 1, md: 2 }">
                    {{ lastCheckIn.response_text || lastCheckIn.error_message || '-' }}
                  </a-descriptions-item>
                </a-descriptions>
              </div>
            </div>
          </a-card>
        </a-col>

        <!-- 用户信息卡片 -->
        <a-col :xs="24" :sm="24" :md="24">
          <a-card class="md3-card">
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
              <a-descriptions-item label="邮箱">
                {{ authStore.user?.email || '未设置' }}
              </a-descriptions-item>
              <a-descriptions-item label="注册时间">
                {{ formatDateTime(authStore.user?.created_at, false) }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- QR Code Modal for Token Refresh -->
    <QRCodeModal
      v-model:visible="qrcodeModalVisible"
      :alias="authStore.user?.alias || ''"
      @success="handleQRCodeSuccess"
      @error="handleQRCodeError"
    />
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { CalendarOutlined, KeyOutlined, UserOutlined, ReloadOutlined } from '@ant-design/icons-vue';
import Layout from '@/components/Layout.vue';
import QRCodeModal from '@/components/QRCodeModal.vue';
import { useAuthStore } from '@/stores/auth';
import { useUserStore } from '@/stores/user';
import { useTaskStore } from '@/stores/task';
import { useCheckInStore } from '@/stores/checkIn';
import { formatDateTime } from '@/utils/helpers';
import { usePollStatus } from '@/composables/usePollStatus';

const router = useRouter();
const authStore = useAuthStore();
const userStore = useUserStore();
const taskStore = useTaskStore();
const checkInStore = useCheckInStore();

// 使用轮询 composable
const { startPolling } = usePollStatus({
  interval: 2000, // 每 2 秒轮询一次
  maxRetries: 15, // 最多 15 次 (30 秒)
  backoff: false, // 不使用指数退避
});

const tokenStatusLoading = ref(false);
const checkInLoading = ref(false);
const selectedTaskId = ref(null);
const qrcodeModalVisible = ref(false);

const tokenStatus = computed(() => userStore.tokenStatus);
const lastCheckIn = computed(() => {
  if (checkInStore.myRecords.length > 0) {
    return checkInStore.myRecords[0];
  }
  return null;
});

const formatExpireTime = computed(() => {
  if (!tokenStatus.value) return '-';

  // Token 无效时，尝试从 user.jwt_exp 获取过期时间
  if (!tokenStatus.value.expires_at) {
    // 如果后端没有返回 expires_at，说明 Token 可能无效或未设置
    const jwtExp = authStore.user?.jwt_exp;
    if (jwtExp && jwtExp !== '0') {
      try {
        const timestamp = parseInt(jwtExp);
        return formatDateTime(timestamp * 1000);
      } catch {
        return '-';
      }
    }
    return '-';
  }

  return formatDateTime(tokenStatus.value.expires_at * 1000);
});

const formatRemainTime = computed(() => {
  if (!tokenStatus.value || !tokenStatus.value.expires_at) return '-';

  const now = Date.now();
  const expireTime = tokenStatus.value.expires_at * 1000;
  const diff = expireTime - now;

  if (diff <= 0) return '已过期';

  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  if (days > 0) return `${days} 天 ${hours} 小时`;
  if (hours > 0) return `${hours} 小时 ${minutes} 分钟`;
  return `${minutes} 分钟`;
});

// 跳转到设置页面
const goToSettings = () => {
  router.push('/settings');
};

// 跳转到任务页面
const goToTasks = () => {
  router.push('/tasks');
};

// 获取 Token 状态
const fetchTokenStatus = async () => {
  tokenStatusLoading.value = true;
  try {
    await userStore.fetchTokenStatus();
  } catch (error) {
    message.error(error.message || '获取 Token 状态失败');
  } finally {
    tokenStatusLoading.value = false;
  }
};

// 手动打卡
const handleCheckIn = async () => {
  if (!selectedTaskId.value) {
    message.warning('请先选择要打卡的任务');
    return;
  }

  checkInLoading.value = true;

  try {
    // 调用异步打卡接口，立即返回 record_id
    const result = await taskStore.checkInTask(selectedTaskId.value);

    // 获取 record_id
    const recordId = result.record_id;
    if (!recordId) {
      message.error('打卡请求失败：未获取到记录ID');
      checkInLoading.value = false;
      return;
    }

    // 如果初始状态就是失败,显示错误并刷新记录
    if (result.status === 'failure') {
      message.error(result.message || '打卡失败');
      checkInLoading.value = false;
      checkInStore.fetchMyRecords({ limit: 1 });
      return;
    }

    // 显示提示消息
    message.info('打卡任务已启动，正在后台处理...');

    // 使用轮询 composable 检查打卡状态
    startPolling(
      async () => {
        const status = await taskStore.getCheckInRecordStatus(recordId);
        return {
          completed: status.status !== 'pending',
          success: status.status === 'success',
          data: status,
        };
      },
      {
        onSuccess: () => {
          checkInLoading.value = false;
          message.success('打卡成功！');
          checkInStore.fetchMyRecords({ limit: 1 });
        },
        onFailure: statusData => {
          checkInLoading.value = false;
          const errorMsg = statusData.error_message || statusData.response_text || '打卡失败';
          message.error(errorMsg);
          checkInStore.fetchMyRecords({ limit: 1 });
        },
        onTimeout: () => {
          checkInLoading.value = false;
          message.warning('打卡处理时间较长，请稍后查看打卡记录');
        },
      }
    );
  } catch (error) {
    console.error('启动打卡失败:', error);
    checkInLoading.value = false;
    message.error(error.message || '启动打卡任务失败');
  }
};

// 处理扫码成功（Token 刷新）
const handleQRCodeSuccess = async () => {
  try {
    // 获取最新的用户信息和 Token 状态
    await authStore.fetchCurrentUser();
    await fetchTokenStatus();
    message.success({ content: 'Token 刷新成功！', duration: 3 });
  } catch (error) {
    console.error('刷新用户信息失败:', error);
    message.error({ content: '获取最新信息失败，请刷新页面', duration: 3 });
  }
};

// 处理扫码失败
const handleQRCodeError = errorMsg => {
  message.error({ content: errorMsg || '扫码刷新 Token 失败', duration: 3 });
};

onMounted(async () => {
  // 刷新用户信息，确保 email 和 has_password 是最新的
  try {
    await authStore.fetchCurrentUser();
  } catch (error) {
    console.error('刷新用户信息失败:', error);
  }

  // 获取 Token 状态
  fetchTokenStatus();
  checkInStore.fetchMyRecords({ limit: 1 });

  // 加载任务列表
  try {
    await taskStore.fetchMyTasks();
    // 如果只有一个任务，自动选中（优先选择启用的任务）
    if (taskStore.activeTasks.length === 1) {
      selectedTaskId.value = taskStore.activeTasks[0].id;
    } else if (taskStore.tasks.length === 1) {
      selectedTaskId.value = taskStore.tasks[0].id;
    }
  } catch (error) {
    message.error(error.message || '加载任务列表失败');
  }
});
</script>

<style scoped>
.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 500;
}

.loading-container {
  padding: 20px;
}

.token-status {
  padding: 0;
}

.token-status .ant-descriptions {
  margin-bottom: 0;
}

.check-in-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 20px;
  gap: 12px;
}

.check-in-container .hint {
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
  margin: 0 0 4px 0;
  text-align: center;
}

.last-check-in {
  width: 100%;
  margin-top: 20px;
}

.last-check-in .label {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  margin: 12px 0 8px 0;
}

.ant-alert {
  margin-top: 16px;
}

.ant-select {
  margin-bottom: 0;
}
</style>
