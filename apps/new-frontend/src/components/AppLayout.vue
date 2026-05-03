<script setup lang="ts">
import {
  BarChart3,
  CheckSquare,
  ClipboardList,
  FileText,
  LayoutDashboard,
  LogOut,
  Menu,
  ScrollText,
  Settings,
  Shield,
  UserRound,
  Users,
  X,
} from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { useAuth } from '@/app/auth'
import { useRouter } from '@/app/router'

const { state: authState, isAdmin, logout } = useAuth()
const router = useRouter()
const mobileOpen = ref(false)

const userLinks = [
  { path: '/dashboard', label: '仪表盘', icon: LayoutDashboard },
  { path: '/tasks', label: '任务', icon: CheckSquare },
  { path: '/records', label: '记录', icon: ClipboardList },
  { path: '/settings', label: '设置', icon: Settings },
]

const adminLinks = [
  { path: '/admin/users', label: '用户', icon: Users },
  { path: '/admin/templates', label: '模板', icon: FileText },
  { path: '/admin/records', label: '全量记录', icon: ScrollText },
  { path: '/admin/logs', label: '日志', icon: Shield },
  { path: '/admin/stats', label: '统计', icon: BarChart3 },
]

const title = computed(() => router.current.value.title)

function go(path: string) {
  mobileOpen.value = false
  void router.navigate(path)
}

function signOut() {
  logout()
  void router.replace('/login')
}
</script>

<template>
  <div class="min-h-[100dvh] bg-zinc-50 text-zinc-950">
    <header class="sticky top-0 z-20 border-b border-zinc-200 bg-white/95 backdrop-blur">
      <div class="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="inline-flex size-9 items-center justify-center rounded-md border border-zinc-200 text-zinc-700 lg:hidden"
            @click="mobileOpen = !mobileOpen"
          >
            <X v-if="mobileOpen" class="size-4" />
            <Menu v-else class="size-4" />
          </button>
          <button class="text-left" type="button" @click="go('/dashboard')">
            <div class="text-sm font-semibold leading-4">接龙自动打卡</div>
            <div class="text-xs text-zinc-500">CheckIn workspace</div>
          </button>
        </div>

        <div class="flex items-center gap-3">
          <div class="hidden text-right sm:block">
            <div class="text-sm font-medium">{{ authState.user?.alias ?? '未登录' }}</div>
            <div class="text-xs text-zinc-500">{{ isAdmin ? '管理员' : '普通用户' }}</div>
          </div>
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-md border border-zinc-200 px-3 py-2 text-sm text-zinc-700 transition hover:bg-zinc-50"
            @click="signOut"
          >
            <LogOut class="size-4" />
            <span class="hidden sm:inline">退出</span>
          </button>
        </div>
      </div>
    </header>

    <div class="mx-auto grid max-w-7xl grid-cols-1 lg:grid-cols-[220px_minmax(0,1fr)]">
      <aside
        class="border-b border-zinc-200 bg-white px-4 py-3 lg:min-h-[calc(100dvh-3.5rem)] lg:border-b-0 lg:border-r"
        :class="mobileOpen ? 'block' : 'hidden lg:block'"
      >
        <nav class="grid gap-1">
          <button
            v-for="link in userLinks"
            :key="link.path"
            type="button"
            class="flex items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition hover:bg-zinc-100"
            :class="
              router.state.path === link.path
                ? 'bg-zinc-900 text-white hover:bg-zinc-900'
                : 'text-zinc-700'
            "
            @click="go(link.path)"
          >
            <component :is="link.icon" class="size-4" />
            {{ link.label }}
          </button>
        </nav>

        <div v-if="isAdmin" class="mt-5 border-t border-zinc-200 pt-4">
          <div class="mb-2 px-3 text-xs font-semibold uppercase tracking-normal text-zinc-500">
            管理员
          </div>
          <nav class="grid gap-1">
            <button
              v-for="link in adminLinks"
              :key="link.path"
              type="button"
              class="flex items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition hover:bg-zinc-100"
              :class="
                router.state.path === link.path
                  ? 'bg-zinc-900 text-white hover:bg-zinc-900'
                  : 'text-zinc-700'
              "
              @click="go(link.path)"
            >
              <component :is="link.icon" class="size-4" />
              {{ link.label }}
            </button>
          </nav>
        </div>
      </aside>

      <main class="min-w-0 px-4 py-5 sm:px-6 lg:px-8">
        <div class="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 class="text-2xl font-semibold tracking-normal text-zinc-950">{{ title }}</h1>
            <p class="mt-1 text-sm text-zinc-500">管理打卡任务、授权状态和系统记录。</p>
          </div>
          <div
            class="inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs text-zinc-600"
          >
            <UserRound class="size-3.5" />
            {{ authState.user?.is_approved ? '已审批' : '待审批' }}
          </div>
        </div>
        <slot />
      </main>
    </div>
  </div>
</template>
