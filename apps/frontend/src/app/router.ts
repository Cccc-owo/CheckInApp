import { computed, reactive } from 'vue'
import { useAuth } from './auth'

export type RouteKey =
  | 'login'
  | 'pending'
  | 'dashboard'
  | 'tasks'
  | 'task-records'
  | 'records'
  | 'settings'
  | 'admin-users'
  | 'admin-templates'
  | 'admin-records'
  | 'admin-logs'
  | 'admin-stats'
  | 'not-found'

export interface AppRoute {
  key: RouteKey
  path: string
  title: string
  requiresAuth?: boolean
  requiresAdmin?: boolean
}

export const routes: AppRoute[] = [
  { key: 'login', path: '/login', title: '登录' },
  { key: 'pending', path: '/pending-approval', title: '等待审批', requiresAuth: true },
  { key: 'dashboard', path: '/dashboard', title: '仪表盘', requiresAuth: true },
  { key: 'tasks', path: '/tasks', title: '任务管理', requiresAuth: true },
  { key: 'task-records', path: '/tasks/:taskId/records', title: '任务记录', requiresAuth: true },
  { key: 'records', path: '/records', title: '打卡记录', requiresAuth: true },
  { key: 'settings', path: '/settings', title: '个人设置', requiresAuth: true },
  {
    key: 'admin-users',
    path: '/admin/users',
    title: '用户管理',
    requiresAuth: true,
    requiresAdmin: true,
  },
  {
    key: 'admin-templates',
    path: '/admin/templates',
    title: '模板管理',
    requiresAuth: true,
    requiresAdmin: true,
  },
  {
    key: 'admin-records',
    path: '/admin/records',
    title: '全部记录',
    requiresAuth: true,
    requiresAdmin: true,
  },
  {
    key: 'admin-logs',
    path: '/admin/logs',
    title: '系统日志',
    requiresAuth: true,
    requiresAdmin: true,
  },
  {
    key: 'admin-stats',
    path: '/admin/stats',
    title: '统计信息',
    requiresAuth: true,
    requiresAdmin: true,
  },
  { key: 'not-found', path: '/:pathMatch(.*)*', title: '页面未找到' },
]

interface RouterState {
  path: string
  params: Record<string, string>
  query: URLSearchParams
}

const state = reactive<RouterState>({
  path: window.location.pathname,
  params: {},
  query: new URLSearchParams(window.location.search),
})

interface MatchedRoute {
  route: AppRoute
  params: Record<string, string>
}

function pathnameOf(path: string) {
  return path.split('?')[0] || '/'
}

function matchRoute(path: string): MatchedRoute {
  const pathname = pathnameOf(path)

  if (pathname === '/')
    return { route: routes.find((route) => route.key === 'dashboard')!, params: {} }

  for (const route of routes) {
    if (!route.path.includes(':') && route.path === pathname) return { route, params: {} }
    if (route.path === '/tasks/:taskId/records') {
      const match = pathname.match(/^\/tasks\/(\d+)\/records$/)
      if (match) return { route, params: { taskId: match[1] } }
    }
  }

  return { route: routes.find((route) => route.key === 'not-found')!, params: {} }
}

function syncFromLocation() {
  const matched = matchRoute(window.location.pathname)
  state.path = window.location.pathname
  state.params = matched.params
  state.query = new URLSearchParams(window.location.search)
  document.title = `${matched.route.title} - 接龙自动打卡系统`
}

function buildPath(path: string, query?: Record<string, string | undefined>) {
  const params = new URLSearchParams()
  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  const suffix = params.toString()
  return suffix ? `${path}?${suffix}` : path
}

async function guardPath(path: string) {
  const { state: authState, isAdmin, refreshCurrentUser } = useAuth()
  const matched = matchRoute(path)
  const route = matched.route
  const pathname = pathnameOf(path)

  if (route.requiresAuth && !authState.token) {
    return buildPath('/login', { redirect: pathname })
  }

  if (authState.token && !authState.initialized) {
    try {
      await refreshCurrentUser()
    } catch {
      return buildPath('/login', { redirect: path })
    }
  }

  if (route.requiresAuth && route.key !== 'pending' && !authState.user?.is_approved) {
    return '/pending-approval'
  }

  if (route.key === 'pending' && authState.user?.is_approved) {
    return '/dashboard'
  }

  if (route.requiresAdmin && !isAdmin.value) {
    return '/dashboard'
  }

  if (route.key === 'login' && authState.token && authState.user?.is_approved) {
    return '/dashboard'
  }

  return null
}

async function navigate(path: string, replace = false) {
  const target = await guardPath(path)
  const next = target ?? path
  if (replace) {
    window.history.replaceState({}, '', next)
  } else {
    window.history.pushState({}, '', next)
  }
  syncFromLocation()
}

window.addEventListener('popstate', () => {
  syncFromLocation()
  void guardPath(window.location.pathname).then((target) => {
    if (target) void navigate(target, true)
  })
})

syncFromLocation()

export function useRouter() {
  return {
    state,
    current: computed(() => matchRoute(state.path).route),
    params: computed(() => state.params),
    query: computed(() => state.query),
    navigate,
    replace: (path: string) => navigate(path, true),
    guardCurrent: () => navigate(`${window.location.pathname}${window.location.search}`, true),
  }
}
