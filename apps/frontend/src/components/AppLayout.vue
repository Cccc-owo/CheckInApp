<script setup lang="ts">
import {
  BarChart3,
  CheckCircle2,
  CheckSquare,
  ClipboardList,
  FileText,
  LayoutDashboard,
  LogOut,
  Mail,
  Menu,
  Monitor,
  MoonStar,
  ScrollText,
  Settings,
  Shield,
  Sun,
  UserRound,
  Users,
  X,
} from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { useAuth } from '@/app/auth'
import { useRouter } from '@/app/router'
import { type ThemeMode, useTheme } from '@/app/theme'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

const { state: authState, isAdmin, logout } = useAuth()
const router = useRouter()
const theme = useTheme()
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
  { path: '/admin/email-settings', label: '邮件', icon: Mail },
]

const title = computed(() => router.current.value.title)
const isAdminRoute = computed(() => router.state.path.startsWith('/admin'))
const approvalLabel = computed(() => (authState.user?.is_approved ? '已审批' : '待审批'))
const roleLabel = computed(() => (isAdmin.value ? '管理员' : '普通用户'))
const themeLabel = computed(() => theme.modeLabel.value)
const themeModes = [
  { mode: 'light', label: '亮色', icon: Sun },
  { mode: 'dark', label: '暗色', icon: MoonStar },
  { mode: 'system', label: '设备', icon: Monitor },
] as const

function themeModeButtonClass(mode: ThemeMode) {
  if (theme.state.mode === mode) {
    return 'bg-foreground text-background shadow-sm hover:bg-foreground hover:text-background'
  }
  return 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
}

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
  <div class="min-h-[100dvh] bg-background text-foreground">
    <header class="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
      <div class="flex h-14 w-full items-center justify-between px-4 sm:px-6 lg:px-8">
        <div class="flex items-center gap-3">
          <Button
            type="button"
            variant="outline"
            size="icon"
            class="lg:hidden"
            @click="mobileOpen = !mobileOpen"
          >
            <X v-if="mobileOpen" class="size-4" />
            <Menu v-else class="size-4" />
          </Button>
          <button class="flex items-center gap-3 text-left" type="button" @click="go('/dashboard')">
            <span
              class="hidden size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm sm:inline-flex"
            >
              <CheckCircle2 class="size-5" />
            </span>
            <span>
              <div class="text-sm font-semibold leading-4 text-foreground">接龙自动打卡</div>
              <div class="text-xs text-muted-foreground">CheckIn workspace</div>
            </span>
          </button>
        </div>

        <div class="flex items-center gap-3">
          <div class="hidden text-right sm:block">
            <div class="text-sm font-medium text-foreground">
              {{ authState.user?.alias ?? '未登录' }}
            </div>
            <div class="text-xs text-muted-foreground">{{ roleLabel }} · {{ approvalLabel }}</div>
          </div>
          <TooltipProvider>
            <div
              class="inline-flex items-center rounded-lg border border-border bg-background p-0.5 shadow-sm"
              :aria-label="`主题模式，当前${themeLabel}`"
            >
              <Tooltip v-for="item in themeModes" :key="item.mode">
                <TooltipTrigger as-child>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    :class="themeModeButtonClass(item.mode)"
                    :aria-label="`切换为${item.label}模式`"
                    :aria-pressed="theme.state.mode === item.mode"
                    @click="theme.setThemeMode(item.mode)"
                  >
                    <component :is="item.icon" class="size-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  {{ item.label }}
                </TooltipContent>
              </Tooltip>
            </div>
          </TooltipProvider>
          <Button type="button" variant="outline" @click="signOut">
            <LogOut class="size-4" />
            <span class="hidden sm:inline">退出</span>
          </Button>
        </div>
      </div>
    </header>

    <div
      class="grid min-h-[calc(100dvh-3.5rem)] w-full grid-cols-1 lg:grid-cols-[220px_minmax(0,1fr)]"
    >
      <aside
        class="border-b border-border bg-card px-3 py-3 shadow-sm lg:min-h-[calc(100dvh-3.5rem)] lg:border-b-0 lg:border-r lg:shadow-none"
        :class="mobileOpen ? 'block' : 'hidden lg:block'"
      >
        <div class="mb-4 rounded-lg border border-border bg-muted p-3 lg:hidden">
          <div class="text-sm font-semibold text-foreground">
            {{ authState.user?.alias ?? '未登录' }}
          </div>
          <div class="mt-1 text-xs text-muted-foreground">
            {{ roleLabel }} · {{ approvalLabel }}
          </div>
        </div>
        <div
          class="mb-2 px-3 text-xs font-semibold uppercase tracking-normal text-muted-foreground"
        >
          工作台
        </div>
        <nav class="grid gap-1">
          <button
            v-for="link in userLinks"
            :key="link.path"
            type="button"
            class="flex min-h-9 items-center gap-2 rounded-md px-3 py-2 text-left text-sm font-medium transition hover:bg-accent hover:text-accent-foreground"
            :class="
              router.state.path === link.path
                ? 'bg-primary text-primary-foreground shadow-sm hover:bg-primary hover:text-primary-foreground'
                : 'text-muted-foreground'
            "
            @click="go(link.path)"
          >
            <component :is="link.icon" class="size-4" />
            {{ link.label }}
          </button>
        </nav>

        <div v-if="isAdmin" class="mt-5 border-t border-border pt-4">
          <div
            class="mb-2 flex items-center justify-between rounded-md border border-[var(--tone-info-border)] bg-[var(--tone-info-bg)] px-3 py-2 text-xs font-semibold text-[var(--tone-info-fg)]"
          >
            <span>管理员工作区</span>
            <Shield class="size-3.5" />
          </div>
          <nav class="grid gap-1">
            <button
              v-for="link in adminLinks"
              :key="link.path"
              type="button"
              class="flex min-h-9 items-center gap-2 rounded-md px-3 py-2 text-left text-sm font-medium transition hover:bg-accent hover:text-accent-foreground"
              :class="
                router.state.path === link.path
                  ? 'bg-[var(--tone-info-strong)] text-white shadow-sm hover:bg-[var(--tone-info-strong-hover)] hover:text-white'
                  : 'text-muted-foreground'
              "
              @click="go(link.path)"
            >
              <component :is="link.icon" class="size-4" />
              {{ link.label }}
            </button>
          </nav>
        </div>
      </aside>

      <main class="min-w-0 bg-background px-4 py-4 sm:px-6 lg:px-8">
        <div
          class="mb-5 grid gap-3 rounded-xl border border-border bg-card px-4 py-3 shadow-sm dark:shadow-none"
          :class="{
            'border-[var(--tone-info-border)] bg-[var(--tone-info-bg)]': isAdminRoute,
          }"
        >
          <div class="min-w-0">
            <div
              v-if="isAdminRoute"
              class="mb-1 inline-flex items-center gap-1 rounded-full border border-[var(--tone-info-border)] bg-background px-2 py-0.5 text-xs font-medium text-[var(--tone-info-fg)]"
            >
              <Shield class="size-3" />
              管理员
            </div>
            <h1 class="truncate text-2xl font-semibold tracking-normal text-foreground">
              {{ title }}
            </h1>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <div
              class="inline-flex items-center gap-2 rounded-full border bg-background px-3 py-1 text-xs font-medium"
              :class="
                authState.user?.is_approved
                  ? 'border-[var(--tone-success-border)] text-[var(--tone-success-fg)]'
                  : 'border-[var(--tone-warning-border)] text-[var(--tone-warning-fg)]'
              "
            >
              <UserRound class="size-3.5" />
              {{ approvalLabel }}
            </div>
            <div
              v-if="isAdminRoute"
              class="inline-flex items-center gap-2 rounded-full border border-[var(--tone-info-border)] bg-background px-3 py-1 text-xs font-medium text-[var(--tone-info-fg)]"
            >
              <Shield class="size-3.5" />
              管理员工作区
            </div>
          </div>
        </div>
        <slot />
      </main>
    </div>
  </div>
</template>
