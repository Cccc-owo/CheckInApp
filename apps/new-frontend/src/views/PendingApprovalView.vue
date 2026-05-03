<script setup lang="ts">
import { RefreshCw } from 'lucide-vue-next'
import { ref } from 'vue'
import { userApi } from '@/api'
import { useAuth } from '@/app/auth'
import { useRouter } from '@/app/router'
import { buttonBase, buttonTone } from '@/components/ui'
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
  <section class="mx-auto max-w-2xl rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
    <h2 class="text-xl font-semibold">账号等待审批</h2>
    <p class="mt-2 text-sm text-zinc-500">
      当前账号
      {{ auth.state.user?.alias ?? '未知用户' }} 已完成登录，但还需要管理员审批后才能访问工作台。
    </p>
    <dl class="mt-5 grid gap-3 sm:grid-cols-2">
      <div class="rounded-md border border-zinc-200 p-3">
        <dt class="text-xs text-zinc-500">创建时间</dt>
        <dd class="mt-1 text-sm font-medium">
          {{ formatFullDateTime(auth.state.user?.created_at) }}
        </dd>
      </div>
      <div class="rounded-md border border-zinc-200 p-3">
        <dt class="text-xs text-zinc-500">审批状态</dt>
        <dd class="mt-1 text-sm font-medium">待审批</dd>
      </div>
    </dl>
    <div
      v-if="error"
      class="mt-4 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700"
    >
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
  </section>
</template>
