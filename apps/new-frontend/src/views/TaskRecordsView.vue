<script setup lang="ts">
import { ArrowLeft, Search } from 'lucide-vue-next'
import { onMounted, reactive, ref } from 'vue'
import { checkInApi, taskApi, type CheckInRecord, type Task } from '@/api'
import { useRouter } from '@/app/router'
import StateBlock from '@/components/StateBlock.vue'
import { cardClass, inputClass, sectionHeaderClass, toneClass } from '@/components/ui'
import { Button } from '@/components/ui/button'
import { extractErrorMessage, formatFullDateTime, statusLabel, statusTone } from '@/utils/format'

const router = useRouter()
const taskId = Number(router.params.value.taskId)
const task = ref<Task | null>(null)
const records = ref<CheckInRecord[]>([])
const total = ref(0)
const loading = ref(true)
const error = ref('')
const filters = reactive({ status: '', trigger_type: '', skip: 0, limit: 20 })

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [taskDetail, page] = await Promise.all([
      taskApi.detail(taskId),
      checkInApi.taskRecords(taskId, filters),
    ])
    task.value = taskDetail
    records.value = page.records
    total.value = page.total
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
    <div :class="[sectionHeaderClass, 'lg:grid-cols-[1fr_180px_180px_auto]']">
      <div>
        <button
          class="mb-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          type="button"
          @click="router.navigate('/tasks')"
        >
          <ArrowLeft class="size-4" />
          返回任务
        </button>
        <h2 class="font-semibold">{{ task?.name || `任务 #${taskId}` }} 的打卡记录</h2>
      </div>
      <select v-model="filters.status" :class="inputClass">
        <option value="">全部状态</option>
        <option value="success">成功</option>
        <option value="failure">失败</option>
      </select>
      <select v-model="filters.trigger_type" :class="inputClass">
        <option value="">全部触发</option>
        <option value="manual">手动</option>
        <option value="scheduler">定时</option>
      </select>
      <Button variant="outline" type="button" @click="load">
        <Search class="size-4" />
        筛选
      </Button>
    </div>

    <StateBlock v-if="loading" title="正在加载任务记录" type="loading" />
    <StateBlock
      v-else-if="error"
      title="任务记录加载失败"
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
        class="grid gap-3 p-3 md:grid-cols-[180px_minmax(0,1fr)_auto] md:items-center"
      >
        <div class="text-sm text-muted-foreground">
          {{ formatFullDateTime(record.check_in_time) }}
        </div>
        <div class="min-w-0">
          <div class="truncate text-sm text-foreground">
            {{ record.response_text || record.error_message || '无响应内容' }}
          </div>
          <div class="mt-1 text-xs text-muted-foreground">
            触发：{{ statusLabel(record.trigger_type) }}
          </div>
        </div>
        <div class="md:text-right">
          <span :class="toneClass(statusTone(record.status))">{{
            statusLabel(record.status)
          }}</span>
        </div>
      </article>
      <div class="border-t border-border bg-muted/55 px-4 py-3 text-sm text-muted-foreground">
        共 {{ total }} 条记录
      </div>
    </div>
  </section>
</template>
