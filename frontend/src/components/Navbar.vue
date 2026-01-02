<template>
  <div class="sticky top-0 z-50 glass-effect border-b border-gray-200/50 shadow-md3-2">
    <nav class="max-w-7xl mx-auto px-6 py-4">
      <div class="flex items-center justify-between">
        <!-- Logo and Brand -->
        <div class="flex items-center space-x-8">
          <router-link to="/" class="flex items-center space-x-3 group">
            <div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-md3 flex items-center justify-center transform group-hover:scale-110 transition-transform">
              <CheckCircleOutlined class="text-white text-xl" />
            </div>
            <span class="text-xl font-bold text-gradient">接龙自动打卡</span>
          </router-link>

          <!-- Desktop Navigation Links -->
          <div v-if="!isMobile" class="hidden md:flex items-center space-x-2">
            <router-link
              to="/dashboard"
              v-slot="{ isActive }"
              custom
            >
              <a
                @click="router.push('/dashboard')"
                :class="[
                  'px-4 py-2 rounded-full font-medium transition-all cursor-pointer',
                  isActive
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-700 hover:bg-gray-100'
                ]"
              >
                <div class="flex items-center space-x-2">
                  <HomeOutlined />
                  <span>仪表盘</span>
                </div>
              </a>
            </router-link>

            <router-link
              to="/tasks"
              v-slot="{ isActive }"
              custom
            >
              <a
                @click="router.push('/tasks')"
                :class="[
                  'px-4 py-2 rounded-full font-medium transition-all cursor-pointer',
                  isActive
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-700 hover:bg-gray-100'
                ]"
              >
                <div class="flex items-center space-x-2">
                  <FileTextOutlined />
                  <span>任务管理</span>
                </div>
              </a>
            </router-link>

            <router-link
              to="/records"
              v-slot="{ isActive }"
              custom
            >
              <a
                @click="router.push('/records')"
                :class="[
                  'px-4 py-2 rounded-full font-medium transition-all cursor-pointer',
                  isActive
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-700 hover:bg-gray-100'
                ]"
              >
                <div class="flex items-center space-x-2">
                  <UnorderedListOutlined />
                  <span>打卡记录</span>
                </div>
              </a>
            </router-link>

            <!-- Admin Dropdown Menu -->
            <a-dropdown v-if="authStore.isAdmin" :trigger="['hover']">
              <a
                :class="[
                  'px-4 py-2 rounded-full font-medium transition-all flex items-center space-x-2 cursor-pointer',
                  isAdminPath ? 'bg-secondary-100 text-secondary-700' : 'text-gray-700 hover:bg-gray-100'
                ]"
              >
                <SettingOutlined />
                <span>管理后台</span>
                <DownOutlined class="text-xs" />
              </a>
              <template #overlay>
                <a-menu>
                  <a-menu-item key="users" @click="router.push('/admin/users')">
                    <UserOutlined />
                    <span class="ml-2">用户管理</span>
                  </a-menu-item>
                  <a-menu-item key="templates" @click="router.push('/admin/templates')">
                    <FileOutlined />
                    <span class="ml-2">模板管理</span>
                  </a-menu-item>
                  <a-menu-item key="records" @click="router.push('/admin/records')">
                    <CheckSquareOutlined />
                    <span class="ml-2">打卡记录</span>
                  </a-menu-item>
                  <a-menu-item key="stats" @click="router.push('/admin/stats')">
                    <BarChartOutlined />
                    <span class="ml-2">统计信息</span>
                  </a-menu-item>
                  <a-menu-item key="logs" @click="router.push('/admin/logs')">
                    <FileTextOutlined />
                    <span class="ml-2">系统日志</span>
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </div>
        </div>

        <!-- User Menu & Mobile Hamburger -->
        <div class="flex items-center space-x-4">
          <!-- Token Status Indicator (Desktop) -->
          <a-tooltip v-if="!isMobile && showTokenStatus" :title="tokenStatusTooltip">
            <div
              class="px-3 py-1.5 rounded-full cursor-pointer transition-all hover:bg-gray-100 flex items-center space-x-2"
              @click="handleTokenStatusClick"
            >
              <a-badge :status="tokenBadgeStatus" />
              <ClockCircleOutlined :class="tokenIconClass" />
              <span class="text-sm">{{ tokenBadgeText }}</span>
              <!-- 过期时显示刷新按钮 -->
              <a-button
                v-if="remainingMinutes !== null && remainingMinutes < 0"
                type="primary"
                size="small"
                @click.stop="handleRefreshToken"
              >
                刷新
              </a-button>
            </div>
          </a-tooltip>

          <!-- Desktop User Menu -->
          <a-dropdown v-if="!isMobile" :trigger="['hover']">
            <a class="flex items-center space-x-3 px-4 py-2 rounded-full hover:bg-gray-100 transition-all cursor-pointer">
              <a-avatar :style="{ backgroundColor: '#f56a00' }">
                {{ userInitial }}
              </a-avatar>
              <span class="hidden md:block font-medium text-gray-700">{{ authStore.user?.alias || '用户' }}</span>
              <DownOutlined class="text-xs text-gray-500" />
            </a>
            <template #overlay>
              <a-menu>
                <a-menu-item key="info" disabled>
                  <div class="px-2 py-1">
                    <p class="text-sm font-medium text-gray-900">{{ authStore.user?.alias }}</p>
                    <p class="text-xs text-gray-500 mt-1">{{ authStore.isAdmin ? '管理员' : '普通用户' }}</p>
                  </div>
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item key="settings" @click="router.push('/settings')">
                  <SettingOutlined />
                  <span class="ml-2">个人设置</span>
                </a-menu-item>
                <a-menu-item key="logout" @click="handleLogout" danger>
                  <LogoutOutlined />
                  <span class="ml-2">退出登录</span>
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>

          <!-- Mobile Hamburger Button -->
          <a-button
            v-if="isMobile"
            type="text"
            @click="drawerVisible = true"
            class="!p-2"
          >
            <MenuOutlined class="text-xl" />
          </a-button>
        </div>
      </div>
    </nav>

    <!-- Mobile Drawer -->
    <a-drawer
      v-model:open="drawerVisible"
      placement="left"
      :width="280"
      title="菜单"
    >
      <!-- User Info in Drawer -->
      <div class="mb-6 pb-4 border-b border-gray-200">
        <div class="flex items-center space-x-3">
          <a-avatar :size="48" :style="{ backgroundColor: '#f56a00' }">
            {{ userInitial }}
          </a-avatar>
          <div>
            <p class="font-medium text-gray-900">{{ authStore.user?.alias || '用户' }}</p>
            <p class="text-xs text-gray-500">{{ authStore.isAdmin ? '管理员' : '普通用户' }}</p>
          </div>
        </div>
      </div>

      <!-- Mobile Navigation Menu -->
      <a-menu
        mode="inline"
        :selected-keys="[currentMenuKey]"
        @click="handleMenuClick"
      >
        <a-menu-item key="dashboard">
          <template #icon><HomeOutlined /></template>
          仪表盘
        </a-menu-item>
        <a-menu-item key="tasks">
          <template #icon><FileTextOutlined /></template>
          任务管理
        </a-menu-item>
        <a-menu-item key="records">
          <template #icon><UnorderedListOutlined /></template>
          打卡记录
        </a-menu-item>

        <!-- Admin Menu Group -->
        <a-sub-menu v-if="authStore.isAdmin" key="admin">
          <template #icon><SettingOutlined /></template>
          <template #title>管理后台</template>
          <a-menu-item key="admin-users">
            <template #icon><UserOutlined /></template>
            用户管理
          </a-menu-item>
          <a-menu-item key="admin-templates">
            <template #icon><FileOutlined /></template>
            模板管理
          </a-menu-item>
          <a-menu-item key="admin-records">
            <template #icon><CheckSquareOutlined /></template>
            打卡记录
          </a-menu-item>
          <a-menu-item key="admin-stats">
            <template #icon><BarChartOutlined /></template>
            统计信息
          </a-menu-item>
          <a-menu-item key="admin-logs">
            <template #icon><FileTextOutlined /></template>
            系统日志
          </a-menu-item>
        </a-sub-menu>

        <a-menu-divider />

        <a-menu-item key="settings">
          <template #icon><SettingOutlined /></template>
          个人设置
        </a-menu-item>
        <a-menu-item key="logout" danger>
          <template #icon><LogoutOutlined /></template>
          退出登录
        </a-menu-item>
      </a-menu>
    </a-drawer>

    <!-- Token 刷新 QR 码模态框 -->
    <QRCodeModal
      v-model:visible="qrcodeModalVisible"
      :alias="authStore.user?.alias || ''"
      @success="handleQRCodeSuccess"
      @error="handleQRCodeError"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
import { useTokenMonitor } from '@/composables/useTokenMonitor'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { Modal, message } from 'ant-design-vue'
import QRCodeModal from './QRCodeModal.vue'
import {
  MenuOutlined,
  HomeOutlined,
  FileTextOutlined,
  UnorderedListOutlined,
  SettingOutlined,
  UserOutlined,
  FileOutlined,
  CheckSquareOutlined,
  BarChartOutlined,
  LogoutOutlined,
  DownOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const userStore = useUserStore()
const { isMobile } = useBreakpoint()
const { getRemainingMinutes, tokenStatus } = useTokenMonitor()

const drawerVisible = ref(false)
const qrcodeModalVisible = ref(false)

const isAdminPath = computed(() => route.path.startsWith('/admin'))

const userInitial = computed(() => {
  const name = authStore.user?.alias || 'U'
  return name.charAt(0).toUpperCase()
})

// Token 状态计算
const remainingMinutes = computed(() => {
  return getRemainingMinutes()
})

const showTokenStatus = computed(() => {
  if (!authStore.isAuthenticated || !tokenStatus.value) return false

  const mins = remainingMinutes.value
  // 显示条件：Token 即将过期（60分钟内）或已过期（5分钟内）
  if (mins === null) return false
  return mins <= 60 || (mins < 0 && Math.abs(mins) <= 5)
})

const tokenBadgeStatus = computed(() => {
  const mins = remainingMinutes.value
  if (mins === null) return 'default'
  if (mins < 0) return 'error' // 已过期
  if (mins <= 10) return 'error' // 10分钟内过期
  if (mins <= 30) return 'warning' // 30分钟内过期
  return 'processing' // 正常但快过期
})

const tokenBadgeText = computed(() => {
  const mins = remainingMinutes.value
  if (mins === null) return ''
  if (mins < 0) return 'Token 已过期'
  if (mins < 60) return `Token 剩余：${mins}分钟`
  return ''
})

const tokenIconClass = computed(() => {
  const mins = remainingMinutes.value
  if (mins === null) return 'text-gray-500'
  if (mins < 0) return 'text-red-500' // 已过期
  if (mins <= 10) return 'text-red-500 animate-pulse' // 10分钟内，闪烁
  if (mins <= 30) return 'text-orange-500' // 30分钟内
  return 'text-blue-500' // 正常
})

const tokenStatusTooltip = computed(() => {
  const mins = remainingMinutes.value
  if (mins === null) return 'Token 状态未知'
  if (mins < 0) {
    const expiredMins = Math.abs(mins)
    return `登录凭证已过期 ${expiredMins} 分钟，点击右侧按钮刷新`
  }
  if (mins < 60) {
    return `Token 剩余时间：${mins} 分钟，过期后可刷新）`
  }
  return 'Token 状态正常'
})

const handleTokenStatusClick = () => {
  const mins = remainingMinutes.value

  //  Token 已过期时提醒刷新
  if (mins !== null && mins < 0) {
    message.info('Token 已过期，请进行刷新')
  }
  // Token 未过期时，点击无效果
}

const currentMenuKey = computed(() => {
  const path = route.path
  if (path.startsWith('/admin/users')) return 'admin-users'
  if (path.startsWith('/admin/templates')) return 'admin-templates'
  if (path.startsWith('/admin/records')) return 'admin-records'
  if (path.startsWith('/admin/stats')) return 'admin-stats'
  if (path.startsWith('/admin/logs')) return 'admin-logs'
  if (path.startsWith('/dashboard')) return 'dashboard'
  if (path.startsWith('/tasks')) return 'tasks'
  if (path.startsWith('/records')) return 'records'
  if (path.startsWith('/settings')) return 'settings'
  return ''
})

const handleMenuClick = ({ key }) => {
  const routes = {
    'dashboard': '/dashboard',
    'tasks': '/tasks',
    'records': '/records',
    'admin-users': '/admin/users',
    'admin-templates': '/admin/templates',
    'admin-records': '/admin/records',
    'admin-stats': '/admin/stats',
    'admin-logs': '/admin/logs',
    'settings': '/settings',
  }

  if (key === 'logout') {
    handleLogout()
  } else if (routes[key]) {
    router.push(routes[key])
    drawerVisible.value = false
  }
}

const handleLogout = () => {
  Modal.confirm({
    title: '提示',
    content: '确定要退出登录吗？',
    okText: '确定',
    cancelText: '取消',
    onOk() {
      authStore.logout()
      router.push('/login')
      drawerVisible.value = false
    },
  })
}

// 处理 Token 刷新
const handleRefreshToken = () => {
  qrcodeModalVisible.value = true
}

// 处理 QR 码扫码成功
const handleQRCodeSuccess = async () => {
  message.success('Token 刷新成功')
  qrcodeModalVisible.value = false

  // 刷新用户信息和 Token 状态
  try {
    await authStore.fetchCurrentUser()
    await userStore.fetchTokenStatus()
  } catch (error) {
    console.error('刷新用户信息失败:', error)
  }
}

// 处理 QR 码扫码失败
const handleQRCodeError = (error) => {
  message.error(error?.message || 'Token 刷新失败')
}
</script>

<style scoped>
/* Additional component-specific styles if needed */
</style>
