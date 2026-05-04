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
const total = ref(0)
const filters = reactive({ status: '', trigger_type: '', skip: 0, limit: 20 })

async function load() {
  loading.value = true
  error.value = ''
  try {
    const page = await checkInApi.myRecords(filters)
    records.value = page.records
    total.value = page.total
    filters.skip = page.skip
    filters.limit = page.limit
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

function page(delta: number) {
  filters.skip = Math.max(0, filters.skip + delta * filters.limit)
  void load()
}

onMounted(load)
</script>

<template>
  <section :class="[cardClass, 'overflow-hidden']">
    <div :class="[sectionHeaderClass, 'md:grid-cols-[1fr_180px_180px_auto]']">
      <div>
        <h2 class="font-semibold">个人打卡记录</h2>
      </div>
      <select v-model="filters.status" :class="inputClass">
        <option value="">全部状态</option>
        <option value="success">成功</option>
        <option value="failure">失败</option>
        <option value="out_of_time">超出时间</option>
      </select>
      <select v-model="filters.trigger_type" :class="inputClass">
        <option value="">全部触发</option>
        <option value="manual">手动</option>
        <option value="scheduler">定时</option>
        <option value="admin">管理员</option>
      </select>
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
    <div v-else>
      <div class="divide-y divide-border">
        <article
          v-for="record in records"
          :key="record.id"
          class="grid gap-3 p-3 lg:grid-cols-[180px_minmax(0,1fr)_auto] lg:items-center"
        >
          <div class="min-w-0">
            <div class="truncate text-sm font-semibold">
              {{ record.task_name || `任务 #${record.task_id}` }}
            </div>
            <div class="mt-1 text-xs text-muted-foreground">
              {{ formatFullDateTime(record.check_in_time) }}
            </div>
          </div>
          <div class="min-w-0">
            <p class="truncate text-sm text-foreground">
              {{ record.response_text || record.error_message || '无响应内容' }}
            </p>
            <p class="mt-1 text-xs text-muted-foreground">
              触发方式：{{ statusLabel(record.trigger_type) }}
            </p>
          </div>
          <div class="lg:text-right">
            <span :class="toneClass(statusTone(record.status))">{{
              statusLabel(record.status)
            }}</span>
          </div>
        </article>
      </div>
      <div
        class="flex flex-wrap items-center justify-between gap-3 border-t border-border bg-muted/55 px-4 py-3 text-sm text-muted-foreground"
      >
        <span
          >共 {{ total }} 条，当前 {{ filters.skip + 1 }} -
          {{ Math.min(filters.skip + filters.limit, total) }}</span
        >
        <div class="flex gap-2">
          <Button variant="outline" :disabled="filters.skip === 0" type="button" @click="page(-1)">
            上一页
          </Button>
          <Button
            variant="outline"
            :disabled="filters.skip + filters.limit >= total"
            type="button"
            @click="page(1)"
          >
            下一页
          </Button>
        </div>
      </div>
    </div>
  </section>
</template>
