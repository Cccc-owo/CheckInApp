<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { adminApi, type AdminStats } from '@/api'
import StateBlock from '@/components/StateBlock.vue'
import { cardClass } from '@/components/ui'
import { extractErrorMessage } from '@/utils/format'

const loading = ref(true)
const error = ref('')
const stats = ref<AdminStats | null>(null)

async function load() {
  loading.value = true
  error.value = ''
  try {
    stats.value = await adminApi.stats()
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <StateBlock v-if="loading" title="正在加载统计" type="loading" />
  <StateBlock
    v-else-if="error"
    title="统计加载失败"
    :description="error"
    type="error"
    action-label="重试"
    @action="load"
  />
  <div v-else class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
    <div :class="[cardClass, 'p-4']">
      <div class="text-sm text-zinc-500">用户</div>
      <div class="mt-2 text-3xl font-semibold">{{ stats?.users.total }}</div>
      <div class="mt-1 text-sm text-zinc-500">已审批 {{ stats?.users.active }}</div>
    </div>
    <div :class="[cardClass, 'p-4']">
      <div class="text-sm text-zinc-500">任务</div>
      <div class="mt-2 text-3xl font-semibold">{{ stats?.tasks.total }}</div>
      <div class="mt-1 text-sm text-zinc-500">启用 {{ stats?.tasks.active }}</div>
    </div>
    <div :class="[cardClass, 'p-4']">
      <div class="text-sm text-zinc-500">记录</div>
      <div class="mt-2 text-3xl font-semibold">{{ stats?.check_in_records.total }}</div>
      <div class="mt-1 text-sm text-zinc-500">今日 {{ stats?.check_in_records.today }}</div>
    </div>
    <div :class="[cardClass, 'p-4']">
      <div class="text-sm text-zinc-500">Token 预警</div>
      <div class="mt-2 text-3xl font-semibold">{{ stats?.tokens.expiring_soon }}</div>
      <div class="mt-1 text-sm text-zinc-500">7 天内过期</div>
    </div>
  </div>
</template>
