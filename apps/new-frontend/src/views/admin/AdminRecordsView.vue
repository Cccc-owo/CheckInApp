<script setup lang="ts">
import { Search } from 'lucide-vue-next'
import { onMounted, reactive, ref } from 'vue'
import { checkInApi, type CheckInRecord } from '@/api'
import StateBlock from '@/components/StateBlock.vue'
import { buttonBase, buttonTone, cardClass, inputClass, toneClass } from '@/components/ui'
import { extractErrorMessage, formatFullDateTime, statusLabel, statusTone } from '@/utils/format'

const loading = ref(true)
const error = ref('')
const records = ref<CheckInRecord[]>([])
const filters = reactive({ task_id: '', status: '', limit: 50 })

async function load() {
  loading.value = true
  error.value = ''
  try {
    const page = await checkInApi.allRecords({
      limit: filters.limit,
      task_id: filters.task_id,
      status: filters.status,
    })
    records.value = page.records
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section :class="[cardClass, 'overflow-hidden']">
    <div class="grid gap-3 border-b border-zinc-200 p-4 md:grid-cols-[1fr_160px_160px_auto]">
      <h2 class="font-semibold">全量记录</h2>
      <input v-model="filters.task_id" :class="inputClass" placeholder="任务 ID" />
      <select v-model="filters.status" :class="inputClass">
        <option value="">全部状态</option>
        <option value="success">成功</option>
        <option value="failure">失败</option>
        <option value="out_of_time">超出时间</option>
      </select>
      <button :class="[buttonBase, buttonTone.secondary]" type="button" @click="load">
        <Search class="size-4" />
        筛选
      </button>
    </div>
    <StateBlock v-if="loading" title="正在加载记录" type="loading" />
    <StateBlock
      v-else-if="error"
      title="记录加载失败"
      :description="error"
      type="error"
      action-label="重试"
      @action="load"
    />
    <div v-else class="divide-y divide-zinc-200">
      <article
        v-for="record in records"
        :key="record.id"
        class="grid gap-2 p-4 md:grid-cols-[1fr_auto] md:items-center"
      >
        <div>
          <div class="font-medium">
            {{ record.user_alias || record.user_email || `任务 #${record.task_id}` }}
          </div>
          <div class="mt-1 text-sm text-zinc-500">
            {{ formatFullDateTime(record.check_in_time) }}
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span :class="toneClass(statusTone(record.status))">{{
            statusLabel(record.status)
          }}</span>
          <span class="text-sm text-zinc-500">{{
            record.task_name || record.thread_id || '无任务名'
          }}</span>
        </div>
      </article>
    </div>
  </section>
</template>
