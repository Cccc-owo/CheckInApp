<script setup lang="ts">
import {
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Eye,
  FilterX,
  RefreshCw,
  Search,
} from 'lucide-vue-next'
import { computed, onMounted, reactive, ref } from 'vue'
import { checkInApi, type CheckInRecord } from '@/api'
import StateBlock from '@/components/StateBlock.vue'
import { cardClass, inputClass, labelClass, sectionHeaderClass, toneClass } from '@/components/ui'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { extractErrorMessage, formatFullDateTime, statusLabel, statusTone } from '@/utils/format'
import {
  formatRecordDetailContent,
  recordResponseSummary,
  visibleRecordRange,
} from './admin-records'

const loading = ref(true)
const error = ref('')
const records = ref<CheckInRecord[]>([])
const total = ref(0)
const selectedRecord = ref<CheckInRecord | null>(null)
const filters = reactive({ task_id: '', status: '', trigger_type: '', skip: 0, limit: 50 })

const rangeLabel = computed(() => visibleRecordRange(total.value, filters.skip, filters.limit))
const hasActiveFilters = computed(
  () => Boolean(filters.task_id || filters.status || filters.trigger_type) || filters.limit !== 50,
)
const activeFilterLabels = computed(() => {
  const labels: string[] = []
  if (filters.task_id) labels.push(`任务 #${filters.task_id}`)
  if (filters.status) labels.push(`状态：${statusLabel(filters.status)}`)
  if (filters.trigger_type) labels.push(`触发：${statusLabel(filters.trigger_type)}`)
  if (filters.limit !== 50) labels.push(`每页 ${filters.limit}`)
  return labels
})
const selectedRecordTitle = computed(() => {
  if (!selectedRecord.value) return '记录详情'
  return (
    selectedRecord.value.task_name ||
    selectedRecord.value.thread_id ||
    `任务 #${selectedRecord.value.task_id}`
  )
})

function normalizedParams() {
  return {
    skip: filters.skip,
    limit: filters.limit,
    task_id: filters.task_id.trim() || undefined,
    status: filters.status || undefined,
    trigger_type: filters.trigger_type || undefined,
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const page = await checkInApi.allRecords(normalizedParams())
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

function applyFilters() {
  filters.skip = 0
  void load()
}

function resetFilters() {
  filters.task_id = ''
  filters.status = ''
  filters.trigger_type = ''
  filters.skip = 0
  filters.limit = 50
  void load()
}

function page(delta: number) {
  filters.skip = Math.max(0, filters.skip + delta * filters.limit)
  void load()
}

onMounted(load)
</script>

<template>
  <section :class="[cardClass, 'overflow-hidden']">
    <div :class="sectionHeaderClass">
      <div class="min-w-0">
        <h2 class="font-semibold">全量记录</h2>
        <p class="mt-1 text-sm text-muted-foreground">共 {{ total }} 条，{{ rangeLabel }}</p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <span v-if="hasActiveFilters" :class="toneClass('info')">已筛选</span>
        <Button variant="outline" type="button" @click="load">
          <RefreshCw class="size-4" />
          刷新
        </Button>
      </div>
    </div>

    <div class="grid gap-3 border-b border-border bg-muted/55 p-4">
      <div
        class="grid gap-3 md:grid-cols-2 xl:grid-cols-[1fr_150px_150px_120px_auto_auto] xl:items-end"
      >
        <label class="grid gap-2">
          <span :class="labelClass">任务 ID</span>
          <input v-model="filters.task_id" :class="inputClass" placeholder="输入任务 ID" />
        </label>
        <label class="grid gap-2">
          <span :class="labelClass">状态</span>
          <select v-model="filters.status" :class="inputClass">
            <option value="">全部状态</option>
            <option value="success">成功</option>
            <option value="failure">失败</option>
            <option value="out_of_time">超出时间</option>
            <option value="token_expired">凭证过期</option>
            <option value="pending">进行中</option>
            <option value="unknown">未知</option>
          </select>
        </label>
        <label class="grid gap-2">
          <span :class="labelClass">触发方式</span>
          <select v-model="filters.trigger_type" :class="inputClass">
            <option value="">全部触发</option>
            <option value="manual">手动</option>
            <option value="scheduled">定时</option>
            <option value="scheduler">定时</option>
            <option value="admin">管理员</option>
          </select>
        </label>
        <label class="grid gap-2">
          <span :class="labelClass">每页</span>
          <input
            v-model.number="filters.limit"
            :class="inputClass"
            type="number"
            min="1"
            max="200"
          />
        </label>
        <Button variant="outline" type="button" @click="applyFilters">
          <Search class="size-4" />
          筛选
        </Button>
        <Button variant="ghost" type="button" :disabled="!hasActiveFilters" @click="resetFilters">
          <FilterX class="size-4" />
          重置
        </Button>
      </div>
      <div v-if="activeFilterLabels.length" class="flex flex-wrap gap-2">
        <span
          v-for="label in activeFilterLabels"
          :key="label"
          class="inline-flex items-center rounded-full border border-border bg-background px-2 py-0.5 text-xs font-medium text-muted-foreground"
        >
          {{ label }}
        </span>
      </div>
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
    <StateBlock
      v-else-if="records.length === 0"
      :title="hasActiveFilters ? '没有匹配记录' : '暂无记录'"
      :description="hasActiveFilters ? '调整筛选条件或重置后再试' : undefined"
      :action-label="hasActiveFilters ? '重置筛选' : undefined"
      @action="resetFilters"
    />
    <div v-else>
      <div
        class="hidden border-b border-border bg-muted/35 px-4 py-2 text-xs font-semibold uppercase tracking-normal text-muted-foreground xl:grid xl:grid-cols-[180px_minmax(160px,1.1fr)_120px_minmax(0,1.4fr)_120px] xl:gap-3"
      >
        <span>用户</span>
        <span>任务</span>
        <span>状态</span>
        <span>响应摘要</span>
        <span class="text-right">操作</span>
      </div>
      <div class="divide-y divide-border">
        <article
          v-for="record in records"
          :key="record.id"
          class="grid gap-3 p-3 sm:p-4 xl:grid-cols-[180px_minmax(160px,1.1fr)_120px_minmax(0,1.4fr)_120px] xl:items-center xl:gap-3"
        >
          <div class="min-w-0">
            <div class="truncate text-sm font-semibold">
              {{ record.user_alias || record.user_email || `用户 #${record.user_id || '未知'}` }}
            </div>
            <div class="mt-1 font-mono text-xs text-muted-foreground">
              ID {{ record.user_id || 'unknown' }}
            </div>
          </div>
          <div class="min-w-0">
            <div class="truncate text-sm font-medium">
              {{ record.task_name || `任务 #${record.task_id}` }}
            </div>
            <div class="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
              <span class="font-mono">#{{ record.task_id }}</span>
              <span v-if="record.thread_id" class="font-mono"
                >ThreadId: {{ record.thread_id }}</span
              >
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-2 xl:block">
            <span :class="toneClass(statusTone(record.status))">{{
              statusLabel(record.status)
            }}</span>
            <div class="mt-0 text-xs text-muted-foreground xl:mt-2">
              {{ statusLabel(record.trigger_type) }}
            </div>
          </div>
          <div class="min-w-0">
            <p class="line-clamp-2 text-sm leading-5 text-foreground">
              {{ recordResponseSummary(record) }}
            </p>
            <p class="mt-1 text-xs text-muted-foreground">
              {{ formatFullDateTime(record.check_in_time) }}
            </p>
          </div>
          <div class="flex justify-start xl:justify-end">
            <Button variant="outline" type="button" @click="selectedRecord = record">
              <Eye class="size-4" />
              详情
            </Button>
          </div>
        </article>
      </div>
      <div
        class="flex flex-wrap items-center justify-between gap-3 border-t border-border bg-muted/55 px-4 py-3 text-sm text-muted-foreground"
      >
        <span>共 {{ total }} 条，{{ rangeLabel }}</span>
        <div class="flex gap-2">
          <Button variant="outline" :disabled="filters.skip === 0" type="button" @click="page(-1)">
            <ChevronLeft class="size-4" />
            上一页
          </Button>
          <Button
            variant="outline"
            :disabled="filters.skip + filters.limit >= total"
            type="button"
            @click="page(1)"
          >
            下一页
            <ChevronRight class="size-4" />
          </Button>
        </div>
      </div>
    </div>
  </section>

  <Dialog :open="selectedRecord !== null" @update:open="(open) => !open && (selectedRecord = null)">
    <DialogContent
      class="grid max-h-[calc(100dvh-2rem)] grid-rows-[auto_minmax(0,1fr)] gap-0 overflow-hidden p-0 sm:max-w-[min(760px,calc(100vw-2rem))]"
    >
      <DialogHeader class="border-b border-border bg-muted/55 px-5 py-4">
        <DialogTitle class="flex items-center gap-2">
          <ClipboardList class="size-5" />
          {{ selectedRecordTitle }}
        </DialogTitle>
      </DialogHeader>
      <div v-if="selectedRecord" class="min-h-0 overflow-y-auto p-5">
        <div class="grid gap-3 text-sm sm:grid-cols-2">
          <div class="rounded-lg border border-border bg-background p-3">
            <div :class="labelClass">记录 ID</div>
            <div class="mt-1 font-mono">{{ selectedRecord.id }}</div>
          </div>
          <div class="rounded-lg border border-border bg-background p-3">
            <div :class="labelClass">状态</div>
            <div class="mt-1 flex flex-wrap gap-2">
              <span :class="toneClass(statusTone(selectedRecord.status))">{{
                statusLabel(selectedRecord.status)
              }}</span>
              <span :class="toneClass('neutral')">{{
                statusLabel(selectedRecord.trigger_type)
              }}</span>
            </div>
          </div>
          <div class="rounded-lg border border-border bg-background p-3">
            <div :class="labelClass">用户</div>
            <div class="mt-1 truncate">
              {{
                selectedRecord.user_alias ||
                selectedRecord.user_email ||
                `用户 #${selectedRecord.user_id || '未知'}`
              }}
            </div>
          </div>
          <div class="rounded-lg border border-border bg-background p-3">
            <div :class="labelClass">任务</div>
            <div class="mt-1 truncate">
              {{ selectedRecord.task_name || `任务 #${selectedRecord.task_id}` }}
            </div>
          </div>
          <div class="rounded-lg border border-border bg-background p-3">
            <div :class="labelClass">ThreadId</div>
            <div class="mt-1 truncate font-mono">{{ selectedRecord.thread_id || '未记录' }}</div>
          </div>
          <div class="rounded-lg border border-border bg-background p-3">
            <div :class="labelClass">打卡时间</div>
            <div class="mt-1">{{ formatFullDateTime(selectedRecord.check_in_time) }}</div>
          </div>
        </div>

        <div class="mt-4 grid gap-4">
          <section>
            <h3 class="text-sm font-semibold">响应内容</h3>
            <pre
              class="mt-2 max-h-64 overflow-auto rounded-lg bg-zinc-950 p-3 font-mono text-xs leading-5 text-zinc-100"
              >{{ formatRecordDetailContent(selectedRecord.response_text) }}</pre
            >
          </section>
          <section>
            <h3 class="text-sm font-semibold">错误信息</h3>
            <pre
              class="mt-2 max-h-64 overflow-auto rounded-lg bg-zinc-950 p-3 font-mono text-xs leading-5 text-zinc-100"
              >{{ formatRecordDetailContent(selectedRecord.error_message) }}</pre
            >
          </section>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>
