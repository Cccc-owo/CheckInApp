<template>
  <div class="login-container">
    <a-row justify="center" align="middle" style="height: 100%">
      <a-col :xs="22" :sm="18" :md="12" :lg="10" :xl="8">
        <a-card class="login-card">
          <template #title>
            <div class="card-header">
              <h2>接龙自动打卡系统</h2>
              <p class="subtitle">
                {{ loginMode === 'qrcode' ? 'QQ 扫码登录/注册' : '用户名密码登录' }}
              </p>
            </div>
          </template>

          <!-- 登录模式切换 -->
          <div class="mode-switch">
            <a-segmented v-model:value="loginMode" :options="loginModeOptions" block />
          </div>

          <!-- QR码登录表单 -->
          <a-form
            v-if="loginMode === 'qrcode'"
            ref="qrcodeFormRef"
            :model="qrcodeForm"
            :rules="qrcodeRules"
            layout="vertical"
            @submit.prevent="handleQRCodeLogin"
          >
            <a-form-item name="alias">
              <a-input
                v-model:value="qrcodeForm.alias"
                placeholder="请输入您的用户名"
                size="large"
                allow-clear
                @keyup.enter="handleQRCodeLogin"
              >
                <template #prefix>
                  <UserOutlined />
                </template>
              </a-input>
            </a-form-item>

            <a-form-item>
              <a-button
                type="primary"
                size="large"
                block
                :loading="loading"
                @click="handleQRCodeLogin"
              >
                {{ loading ? '正在登录...' : '扫码登录/注册' }}
              </a-button>
            </a-form-item>
          </a-form>

          <!-- 别名+密码登录表单 -->
          <a-form
            v-else
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            layout="vertical"
          >
            <a-form-item name="alias">
              <a-input
                v-model:value="passwordForm.alias"
                placeholder="请输入您的用户名"
                size="large"
                allow-clear
              >
                <template #prefix>
                  <UserOutlined />
                </template>
              </a-input>
            </a-form-item>

            <a-form-item name="password">
              <a-input-password
                v-model:value="passwordForm.password"
                placeholder="请输入密码"
                size="large"
                @keyup.enter="handlePasswordLogin"
              >
                <template #prefix>
                  <KeyOutlined />
                </template>
              </a-input-password>
            </a-form-item>

            <a-form-item>
              <a-button
                type="primary"
                size="large"
                block
                :loading="loading"
                @click="handlePasswordLogin"
              >
                {{ loading ? '登录中...' : '登录' }}
              </a-button>
            </a-form-item>

            <div class="tips-link">
              <a class="link-text" @click="loginMode = 'qrcode'"> 没有密码？使用扫码登录 </a>
            </div>
          </a-form>

          <div class="tips">
            <a-alert
              :message="loginMode === 'qrcode' ? '扫码登录提示' : '密码登录提示'"
              type="info"
              :closable="false"
              show-icon
            >
              <template #description>
                <template v-if="loginMode === 'qrcode'">
                  <p>1. 输入您的用户名(用于标识身份)</p>
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
              </template>
            </a-alert>
          </div>
        </a-card>
      </a-col>
    </a-row>

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
import { ref, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { message } from 'ant-design-vue';
import { UserOutlined, KeyOutlined } from '@ant-design/icons-vue';
import { authAPI } from '@/api';
import { useAuthStore } from '@/stores/auth';
import QRCodeModal from '@/components/QRCodeModal.vue';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const qrcodeFormRef = ref(null);
const passwordFormRef = ref(null);
const loading = ref(false);
const qrcodeVisible = ref(false);

// 登录模式
const loginMode = ref('qrcode');
const loginModeOptions = [
  { label: '扫码登录', value: 'qrcode' },
  { label: '密码登录', value: 'password' },
];

// 监听登录模式切换，同步用户名
watch(loginMode, () => {
  // 从密码登录切换到扫码登录
  if (loginMode.value === 'qrcode' && passwordForm.value.alias) {
    qrcodeForm.value.alias = passwordForm.value.alias;
  }
  // 从扫码登录切换到密码登录
  else if (loginMode.value === 'password' && qrcodeForm.value.alias) {
    passwordForm.value.alias = qrcodeForm.value.alias;
  }
});

// QR码登录表单
const qrcodeForm = ref({
  alias: '',
});

const qrcodeRules = {
  alias: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' },
  ],
};

// 密码登录表单
const passwordForm = ref({
  alias: '',
  password: '',
});

const passwordRules = {
  alias: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' },
  ],
};

// QR码登录
const handleQRCodeLogin = async () => {
  if (!qrcodeFormRef.value) return;

  try {
    await qrcodeFormRef.value.validate();
    // 显示 QR 码弹窗
    qrcodeVisible.value = true;
  } catch {
    // 表单验证失败，不需要打印错误（由 Ant Design 自动显示错误提示）
  }
};

// 密码登录
const handlePasswordLogin = async () => {
  if (!passwordFormRef.value) return;

  try {
    await passwordFormRef.value.validate();

    loading.value = true;

    const response = await authAPI.aliasLogin(
      passwordForm.value.alias,
      passwordForm.value.password
    );

    if (response.success) {
      // 使用 authStore 保存认证信息
      const user = {
        id: response.user_id,
        alias: response.alias,
        role: response.role || 'user',
        is_approved: response.is_approved !== false,
      };

      // 如果没有 authorization（测试账号），使用 user_id 作为认证凭据
      const authToken = response.authorization || `user_id:${response.user_id}`;
      authStore.setAuth(authToken, user);

      // 只有当有真实 authorization 时才获取完整用户信息
      if (response.authorization) {
        try {
          await authStore.fetchCurrentUser();
        } catch (err) {
          console.warn('获取完整用户信息失败，使用基本信息:', err);
          // 即使失败也继续登录流程
        }
      } else {
        // 没有 authorization 的测试账号，提示用户需要扫码绑定
        message.info({
          content: '您正在使用密码登录模式。如需使用打卡功能，请先扫码绑定 QQ。',
          duration: 5,
        });
      }

      // 如果有 Token 警告，显示提示
      if (response.token_warning && response.warning_message) {
        message.warning({
          content: response.warning_message,
          duration: 5,
        });
      } else if (response.authorization) {
        // 只有有 token 的用户才显示"欢迎回来"
        message.success(`欢迎回来，${response.alias}！`);
      } else {
        // 测试账号登录成功提示
        message.success(`登录成功，${response.alias}！`);
      }

      // 跳转到重定向页面或仪表盘
      const redirect = route.query.redirect || '/dashboard';
      router.push(redirect);
    } else {
      // 根据不同错误类型提供友好提示
      handlePasswordLoginError(response.message);
    }
  } catch (error) {
    console.error('密码登录失败:', error);
    const errorMsg = error.response?.data?.detail || error.message || '登录失败，请稍后重试';
    handlePasswordLoginError(errorMsg);
  } finally {
    loading.value = false;
  }
};

// 处理密码登录错误
const handlePasswordLoginError = msg => {
  if (!msg) {
    message.error('登录失败，请稍后重试');
    return;
  }

  // 用户不存在或密码错误
  if (msg.includes('用户名或密码错误')) {
    message.error('用户名或密码错误');
    return;
  }

  // 未设置密码
  if (msg.includes('未设置密码')) {
    message.warning('该账户未设置密码，请使用扫码登录');
    return;
  }

  // 用户不存在
  if (msg.includes('用户不存在')) {
    message.error('用户不存在，请检查用户名或使用扫码登录注册');
    return;
  }

  // 其他错误
  message.error(msg || '登录失败，请稍后重试');
};

const handleLoginSuccess = user => {
  message.success(`欢迎回来，${user.alias}！`);

  // 跳转到重定向页面或仪表盘
  const redirect = route.query.redirect || '/dashboard';
  router.push(redirect);
};

const handleLoginError = error => {
  message.error(error.message || '登录失败');
};
</script>

<style scoped>
.login-container {
  width: 100vw;
  height: 100vh;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow-y: auto;
  padding: 16px;
}

.login-card {
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  width: 100%;
  margin: 20px 0;
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

.tips-link {
  text-align: center;
  margin-top: 10px;
}

.link-text {
  color: #2196f3;
  cursor: pointer;
  text-decoration: none;
}

.link-text:hover {
  text-decoration: underline;
}

.tips {
  margin-top: 20px;
}

.tips :deep(p) {
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

/* 确保 Ant Design Row 占满高度 */
.login-container :deep(.ant-row) {
  width: 100%;
  min-height: 100%;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .login-container {
    padding: 12px;
  }

  .login-card {
    border-radius: 12px;
  }

  .card-header h2 {
    font-size: 20px;
  }

  .subtitle {
    font-size: 13px;
  }

  .tips :deep(p) {
    font-size: 13px;
  }

  .tips :deep(.ant-alert) {
    font-size: 13px;
  }
}

/* 小屏手机优化 */
@media (max-width: 576px) {
  .login-container {
    padding: 8px;
  }

  .login-card {
    border-radius: 8px;
    margin: 10px 0;
  }

  .card-header h2 {
    font-size: 18px;
  }

  .subtitle {
    font-size: 12px;
  }

  .mode-switch {
    margin-bottom: 16px;
  }

  .tips {
    margin-top: 16px;
  }

  .tips :deep(p) {
    font-size: 12px;
    margin: 4px 0;
  }
}

/* 横屏优化 */
@media (max-height: 600px) and (orientation: landscape) {
  .login-container {
    padding: 8px;
    align-items: flex-start;
  }

  .login-card {
    margin: 8px 0;
  }

  .card-header h2 {
    font-size: 18px;
  }

  .tips :deep(p) {
    margin: 3px 0;
    font-size: 12px;
  }

  .mode-switch {
    margin-bottom: 12px;
  }

  .tips {
    margin-top: 12px;
  }
}
</style>
