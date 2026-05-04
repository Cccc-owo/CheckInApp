<script setup lang="ts">
import { RefreshCw } from 'lucide-vue-next'
import { ref } from 'vue'
import { userApi } from '@/api'
import { useAuth } from '@/app/auth'
import { useRouter } from '@/app/router'
import { alertClass, buttonBase, buttonTone, cardClass, toneClass } from '@/components/ui'
import { extractErrorMessage, formatFullDateTime } from '@/utils/format'

const auth = useAuth()
const router = useRouter()
const loading = ref(false)
const error = ref('')

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    const status = await userApi.status()
    if (status.is_approved) {
      await auth.refreshCurrentUser()
      await router.replace('/dashboard')
    }
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section :class="[cardClass, 'mx-auto max-w-2xl overflow-hidden']">
    <div
      class="border-b border-amber-200 bg-amber-50/80 p-6 dark:border-amber-900/70 dark:bg-amber-950/30"
    >
      <span :class="toneClass('warning')">待审批</span>
      <h2 class="mt-3 text-xl font-semibold">账号等待审批</h2>
      <p class="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
        当前账号
        {{ auth.state.user?.alias ?? '未知用户' }} 已完成登录，但还需要管理员审批后才能访问工作台。
      </p>
    </div>
    <div class="p-6">
      <dl class="mt-5 grid gap-3 sm:grid-cols-2">
        <div class="rounded-md border border-zinc-200 p-3 dark:border-zinc-800 dark:bg-zinc-950">
          <dt class="text-xs text-zinc-500 dark:text-zinc-400">创建时间</dt>
          <dd class="mt-1 text-sm font-medium">
            {{ formatFullDateTime(auth.state.user?.created_at) }}
          </dd>
        </div>
        <div class="rounded-md border border-zinc-200 p-3 dark:border-zinc-800 dark:bg-zinc-950">
          <dt class="text-xs text-zinc-500 dark:text-zinc-400">审批状态</dt>
          <dd class="mt-1 text-sm font-medium">待审批</dd>
        </div>
      </dl>
      <div v-if="error" :class="[alertClass.danger, 'mt-4']">
        {{ error }}
      </div>
      <button
        :class="[buttonBase, buttonTone.primary, 'mt-5']"
        :disabled="loading"
        type="button"
        @click="refresh"
      >
        <RefreshCw class="size-4" :class="{ 'animate-spin': loading }" />
        刷新审批状态
      </button>
    </div>
  </section>
</template>
