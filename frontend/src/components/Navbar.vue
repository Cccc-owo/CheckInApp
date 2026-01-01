<template>
  <div class="sticky top-0 z-50 glass-effect border-b border-gray-200/50 shadow-md3-2">
    <nav class="max-w-7xl mx-auto px-6 py-4">
      <div class="flex items-center justify-between">
        <!-- Logo and Brand -->
        <div class="flex items-center space-x-8">
          <router-link to="/" class="flex items-center space-x-3 group">
            <div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-md3 flex items-center justify-center transform group-hover:scale-110 transition-transform">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <span class="text-xl font-bold text-gradient">接龙自动打卡</span>
          </router-link>

          <!-- Navigation Links -->
          <div class="hidden md:flex items-center space-x-2">
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
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
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
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
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
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                  </svg>
                  <span>打卡记录</span>
                </div>
              </a>
            </router-link>

            <!-- Admin Menu -->
            <div v-if="authStore.isAdmin" class="relative" @mouseenter="showAdminMenu = true" @mouseleave="showAdminMenu = false">
              <button
                :class="[
                  'px-4 py-2 rounded-full font-medium transition-all flex items-center space-x-2',
                  isAdminPath ? 'bg-secondary-100 text-secondary-700' : 'text-gray-700 hover:bg-gray-100'
                ]"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span>管理后台</span>
                <svg class="w-4 h-4 transition-transform" :class="{ 'rotate-180': showAdminMenu }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              <!-- Admin Dropdown -->
              <transition
                enter-active-class="transition ease-out duration-200"
                enter-from-class="opacity-0 translate-y-1"
                enter-to-class="opacity-100 translate-y-0"
                leave-active-class="transition ease-in duration-150"
                leave-from-class="opacity-100 translate-y-0"
                leave-to-class="opacity-0 translate-y-1"
              >
                <div v-show="showAdminMenu" class="absolute top-full left-0 mt-2 w-48 glass-effect rounded-md3 shadow-md3-3 py-2 border border-gray-200/50">
                  <router-link
                    to="/admin/users"
                    class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                  >
                    <div class="flex items-center space-x-2">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                      </svg>
                      <span>用户管理</span>
                    </div>
                  </router-link>
                  <router-link
                    to="/admin/templates"
                    class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                  >
                    <div class="flex items-center space-x-2">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span>模板管理</span>
                    </div>
                  </router-link>
                  <router-link
                    to="/admin/records"
                    class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                  >
                    <div class="flex items-center space-x-2">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                      </svg>
                      <span>打卡记录</span>
                    </div>
                  </router-link>
                  <router-link
                    to="/admin/stats"
                    class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                  >
                    <div class="flex items-center space-x-2">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                      <span>统计信息</span>
                    </div>
                  </router-link>
                  <router-link
                    to="/admin/logs"
                    class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                  >
                    <div class="flex items-center space-x-2">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span>系统日志</span>
                    </div>
                  </router-link>
                </div>
              </transition>
            </div>
          </div>
        </div>

        <!-- User Menu -->
        <div class="flex items-center space-x-4">
          <!-- User Avatar and Menu -->
          <div class="relative" @mouseenter="showUserMenu = true" @mouseleave="showUserMenu = false">
            <button class="flex items-center space-x-3 px-4 py-2 rounded-full hover:bg-gray-100 transition-all">
              <div class="w-8 h-8 bg-gradient-to-br from-accent-400 to-accent-600 rounded-full flex items-center justify-center text-white font-semibold">
                {{ userInitial }}
              </div>
              <span class="hidden md:block font-medium text-gray-700">{{ authStore.user?.alias || '用户' }}</span>
              <svg class="w-4 h-4 text-gray-500 transition-transform" :class="{ 'rotate-180': showUserMenu }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            <!-- User Dropdown -->
            <transition
              enter-active-class="transition ease-out duration-200"
              enter-from-class="opacity-0 translate-y-1"
              enter-to-class="opacity-100 translate-y-0"
              leave-active-class="transition ease-in duration-150"
              leave-from-class="opacity-100 translate-y-0"
              leave-to-class="opacity-0 translate-y-1"
            >
              <div v-show="showUserMenu" class="absolute top-full right-0 mt-2 w-48 glass-effect rounded-md3 shadow-md3-3 py-2 border border-gray-200/50">
                <div class="px-4 py-2 border-b border-gray-200/50">
                  <p class="text-sm font-medium text-gray-900">{{ authStore.user?.alias }}</p>
                  <p class="text-xs text-gray-500 mt-1">{{ authStore.isAdmin ? '管理员' : '普通用户' }}</p>
                </div>
                <button
                  @click="router.push('/settings')"
                  class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors flex items-center space-x-2"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span>个人设置</span>
                </button>
                <button
                  @click="handleLogout"
                  class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors flex items-center space-x-2"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  <span>退出登录</span>
                </button>
              </div>
            </transition>
          </div>
        </div>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const showAdminMenu = ref(false)
const showUserMenu = ref(false)

const isAdminPath = computed(() => route.path.startsWith('/admin'))

const userInitial = computed(() => {
  const name = authStore.user?.alias || 'U'
  return name.charAt(0).toUpperCase()
})

const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      authStore.logout()
      router.push('/login')
    })
    .catch(() => {
      // 取消操作
    })
}
</script>

<style scoped>
/* Additional component-specific styles if needed */
</style>
