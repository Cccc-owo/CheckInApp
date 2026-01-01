import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false, title: '登录' },
  },
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/pending-approval',
    name: 'PendingApproval',
    component: () => import('@/views/PendingApprovalView.vue'),
    meta: { requiresAuth: true, title: '等待审批' },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { requiresAuth: true, title: '我的仪表盘' },
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: () => import('@/views/TasksView.vue'),
    meta: { requiresAuth: true, title: '任务管理' },
  },
  {
    path: '/tasks/:taskId/records',
    name: 'TaskRecords',
    component: () => import('@/views/TaskRecordsView.vue'),
    meta: { requiresAuth: true, title: '任务打卡记录' },
  },
  {
    path: '/records',
    name: 'Records',
    component: () => import('@/views/RecordsView.vue'),
    meta: { requiresAuth: true, title: '打卡记录' },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { requiresAuth: true, title: '个人设置' },
  },
  {
    path: '/admin',
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UsersView.vue'),
        meta: { requiresAuth: true, requiresAdmin: true, title: '用户管理' },
      },
      {
        path: 'records',
        name: 'AdminRecords',
        component: () => import('@/views/admin/RecordsView.vue'),
        meta: { requiresAuth: true, requiresAdmin: true, title: '打卡记录' },
      },
      {
        path: 'logs',
        name: 'AdminLogs',
        component: () => import('@/views/admin/LogsView.vue'),
        meta: { requiresAuth: true, requiresAdmin: true, title: '系统日志' },
      },
      {
        path: 'stats',
        name: 'AdminStats',
        component: () => import('@/views/admin/StatsView.vue'),
        meta: { requiresAuth: true, requiresAdmin: true, title: '统计信息' },
      },
      {
        path: 'templates',
        name: 'AdminTemplates',
        component: () => import('@/views/admin/TemplatesView.vue'),
        meta: { requiresAuth: true, requiresAdmin: true, title: '模板管理' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { requiresAuth: false, title: '页面未找到' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局前置守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 接龙自动打卡系统` : '接龙自动打卡系统'

  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      // 未登录，重定向到登录页
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }

    // 检查用户审批状态（除了待审批页面本身）
    if (to.name !== 'PendingApproval') {
      try {
        const { userAPI } = await import('@/api')
        const status = await userAPI.getUserStatus()

        if (!status.is_approved) {
          // 未审批用户只能访问待审批页面
          next({ name: 'PendingApproval' })
          return
        }
      } catch (error) {
        console.error('检查审批状态失败:', error)
        // 如果检查失败，允许继续访问（避免阻塞正常用户）
      }
    } else {
      // 访问待审批页面时，检查是否已审批
      try {
        const { userAPI } = await import('@/api')
        const status = await userAPI.getUserStatus()

        if (status.is_approved) {
          // 已审批用户不能访问待审批页面
          next({ name: 'Dashboard' })
          return
        }
      } catch (error) {
        console.error('检查审批状态失败:', error)
      }
    }

    // 检查是否需要管理员权限
    if (to.meta.requiresAdmin && !authStore.isAdmin) {
      // 非管理员，重定向到仪表盘
      next({ name: 'Dashboard' })
      return
    }
  } else {
    // 不需要认证的页面，如果已登录则重定向到仪表盘
    if (to.name === 'Login' && authStore.isAuthenticated) {
      next({ name: 'Dashboard' })
      return
    }
  }

  next()
})

export default router
