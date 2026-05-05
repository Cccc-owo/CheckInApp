<script setup lang="ts">
import { computed, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { useAuth } from '@/app/auth'
import { useRouter } from '@/app/router'
import LoginView from '@/views/LoginView.vue'
import PendingApprovalView from '@/views/PendingApprovalView.vue'
import DashboardView from '@/views/DashboardView.vue'
import TasksView from '@/views/TasksView.vue'
import TaskRecordsView from '@/views/TaskRecordsView.vue'
import RecordsView from '@/views/RecordsView.vue'
import SettingsView from '@/views/SettingsView.vue'
import NotFoundView from '@/views/NotFoundView.vue'
import AdminUsersView from '@/views/admin/AdminUsersView.vue'
import AdminTemplatesView from '@/views/admin/AdminTemplatesView.vue'
import AdminRecordsView from '@/views/admin/AdminRecordsView.vue'
import AdminLogsView from '@/views/admin/AdminLogsView.vue'
import AdminStatsView from '@/views/admin/AdminStatsView.vue'
import AdminEmailSettingsView from '@/views/admin/AdminEmailSettingsView.vue'

const router = useRouter()
const auth = useAuth()

const view = computed(() => {
  switch (router.current.value.key) {
    case 'login':
      return LoginView
    case 'pending':
      return PendingApprovalView
    case 'dashboard':
      return DashboardView
    case 'tasks':
      return TasksView
    case 'task-records':
      return TaskRecordsView
    case 'records':
      return RecordsView
    case 'settings':
      return SettingsView
    case 'admin-users':
      return AdminUsersView
    case 'admin-templates':
      return AdminTemplatesView
    case 'admin-records':
      return AdminRecordsView
    case 'admin-logs':
      return AdminLogsView
    case 'admin-stats':
      return AdminStatsView
    case 'admin-email-settings':
      return AdminEmailSettingsView
    default:
      return NotFoundView
  }
})

const wrappedView = computed(() => {
  if (['login', 'pending', 'not-found'].includes(router.current.value.key)) return view.value
  return AppLayout
})

const usesLayout = computed(() => wrappedView.value === AppLayout)

onMounted(() => {
  void auth.refreshCurrentUser().catch(() => undefined)
  void router.guardCurrent()
})
</script>

<template>
  <AppLayout v-if="usesLayout">
    <component :is="view" />
  </AppLayout>
  <component :is="view" v-else />
</template>
