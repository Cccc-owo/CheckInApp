import { computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { useAuthStore } from '@/stores/auth';
import { useUserStore } from '@/stores/user';
import { useRouter } from 'vue-router';

/**
 * Token 过期监控 Composable
 *
 * 功能：
 * 1. 定时检查 Token 状态
 * 2. Token 过期后 5 分钟内提醒用户
 * 3. 为有密码的用户提供友好的过期处理
 *
 * 注意：使用单例模式，确保全局只有一个监控实例
 */

// 全局单例：确保整个应用只有一个监控实例
let monitorTimer = null;
let warningShown = false;
let isMonitoring = false; // 新增：防止重复启动

// 检查间隔（毫秒）
const NORMAL_CHECK_INTERVAL = 15 * 60 * 1000; // 正常情况：15 分钟
const URGENT_CHECK_INTERVAL = 5 * 60 * 1000; // Token 即将过期：5 分钟

export function useTokenMonitor() {
  const authStore = useAuthStore();
  const userStore = useUserStore();
  const router = useRouter();

  const tokenStatus = computed(() => userStore.tokenStatus);
  const hasPassword = computed(() => authStore.user?.has_password || false);

  // 计算 Token 剩余分钟数
  const getRemainingMinutes = () => {
    if (!tokenStatus.value?.expires_at) return null;

    const now = Math.floor(Date.now() / 1000);
    const expiresAt = tokenStatus.value.expires_at;
    const diffSeconds = expiresAt - now;

    return Math.floor(diffSeconds / 60);
  };

  // 检查 Token 状态并显示提醒
  const checkTokenStatus = async () => {
    // 如果未登录，不检查
    if (!authStore.isAuthenticated) {
      return;
    }

    try {
      // 获取最新的 Token 状态
      await userStore.fetchTokenStatus();

      const remainingMinutes = getRemainingMinutes();

      // Token 已过期（负数分钟）
      if (remainingMinutes !== null && remainingMinutes < 0) {
        const expiredMinutes = Math.abs(remainingMinutes);

        // Token 过期后 5 分钟内提醒
        if (expiredMinutes <= 5) {
          if (hasPassword.value) {
            // 有密码的用户：友好提示
            if (!warningShown) {
              message.warning({
                content: `您的登录凭证已过期 ${expiredMinutes} 分钟，部分功能可能受限。建议您扫码刷新凭证。`,
                duration: 8,
                key: 'token-expired-warning',
              });
              warningShown = true;
            }
          } else {
            // 没有密码的用户：必须重新登录
            message.error({
              content: '您的登录凭证已过期，请重新扫码登录',
              duration: 5,
              key: 'token-expired-error',
            });

            // 清除登录状态并跳转
            authStore.logout();
            router.push('/login');
          }
        } else if (expiredMinutes > 5) {
          // 过期超过 5 分钟
          if (!hasPassword.value) {
            // 没有密码的用户：强制退出
            authStore.logout();
            router.push('/login');
          }
        }
      }
      // Token 即将过期（1小时内）
      else if (remainingMinutes !== null && remainingMinutes > 0 && remainingMinutes <= 60) {
        if (!warningShown) {
          message.warning({
            content: `您的 Token 将在 ${remainingMinutes} 分钟后过期，建议您及时刷新`,
            duration: 6,
            key: 'token-expiring-warning',
          });
          warningShown = true;
        }

        // Token 即将过期时，切换到更频繁的检查（5 分钟）
        adjustCheckInterval(URGENT_CHECK_INTERVAL);
      }
      // Token 状态正常
      else if (remainingMinutes !== null && remainingMinutes > 60) {
        // 重置警告标志
        warningShown = false;

        // 恢复正常检查频率（15 分钟）
        adjustCheckInterval(NORMAL_CHECK_INTERVAL);
      }
    } catch (error) {
      console.error('检查 Token 状态失败:', error);
    }
  };

  // 调整检查间隔
  const adjustCheckInterval = newInterval => {
    if (monitorTimer) {
      const currentInterval = monitorTimer._idleTimeout || 0;

      // 只有当新间隔与当前间隔不同时才重启定时器
      if (currentInterval !== newInterval) {
        clearInterval(monitorTimer);
        monitorTimer = setInterval(() => {
          checkTokenStatus();
        }, newInterval);
      }
    }
  };

  // 启动监控
  const startMonitoring = () => {
    // 避免重复启动（单例模式）
    if (isMonitoring || monitorTimer) {
      return;
    }

    isMonitoring = true;

    // 立即检查一次
    checkTokenStatus();

    // 默认使用正常检查频率（15 分钟）
    monitorTimer = setInterval(() => {
      checkTokenStatus();
    }, NORMAL_CHECK_INTERVAL);
  };

  // 停止监控
  const stopMonitoring = () => {
    if (monitorTimer) {
      clearInterval(monitorTimer);
      monitorTimer = null;
    }
    isMonitoring = false;
    warningShown = false;
  };

  // 手动触发检查
  const checkNow = () => {
    warningShown = false; // 重置警告标志，允许再次显示
    checkTokenStatus();
  };

  // 组件挂载时启动监控
  onMounted(() => {
    if (authStore.isAuthenticated) {
      startMonitoring();
    }
  });

  // 组件卸载时不停止监控（因为是全局单例）
  // onUnmounted 中不调用 stopMonitoring()，让监控持续运行

  return {
    tokenStatus,
    hasPassword,
    startMonitoring,
    stopMonitoring,
    checkNow,
    getRemainingMinutes,
  };
}
