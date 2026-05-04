<script setup lang="ts">
import { Search } from 'lucide-vue-next'
import { onMounted, reactive, ref } from 'vue'
import { checkInApi, type CheckInRecord } from '@/api'
import StateBlock from '@/components/StateBlock.vue'
import { cardClass, inputClass, sectionHeaderClass, toneClass } from '@/components/ui'
import { Button } from '@/components/ui/button'
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
    <div :class="[sectionHeaderClass, 'lg:grid-cols-[1fr_120px_160px_120px_auto]']">
      <div>
        <h2 class="font-semibold">全量记录</h2>
      </div>
      <input v-model="filters.task_id" :class="inputClass" placeholder="任务 ID" />
      <select v-model="filters.status" :class="inputClass">
        <option value="">全部状态</option>
        <option value="success">成功</option>
        <option value="failure">失败</option>
        <option value="out_of_time">超出时间</option>
      </select>
      <input v-model.number="filters.limit" :class="inputClass" type="number" min="1" max="200" />
      <Button variant="outline" type="button" @click="load">
        <Search class="size-4" />
        筛选
      </Button>
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
    <StateBlock v-else-if="records.length === 0" title="暂无记录" />
    <div v-else class="divide-y divide-border">
      <article
        v-for="record in records"
        :key="record.id"
        class="grid gap-3 p-3 md:grid-cols-[minmax(0,1fr)_auto] md:items-center"
      >
        <div class="min-w-0">
          <div class="truncate font-medium">
            {{ record.user_alias || record.user_email || `任务 #${record.task_id}` }}
          </div>
          <div class="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-sm text-muted-foreground">
            <span>{{ formatFullDateTime(record.check_in_time) }}</span>
            <span>{{ record.response_text || record.error_message || '无响应内容' }}</span>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-2 md:justify-end">
          <span :class="toneClass(statusTone(record.status))">{{
            statusLabel(record.status)
          }}</span>
          <span class="text-sm text-muted-foreground">{{
            record.task_name || record.thread_id || '无任务名'
          }}</span>
        </div>
      </article>
    </div>
  </section>
</template>
