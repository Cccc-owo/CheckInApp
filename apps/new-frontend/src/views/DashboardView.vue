<script setup lang="ts">
import { Activity, CheckCircle2, Clock, KeyRound } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import {
  checkInApi,
  taskApi,
  userApi,
  type CheckInRecord,
  type Task,
  type TokenStatus,
} from '@/api'
import { useRouter } from '@/app/router'
import StateBlock from '@/components/StateBlock.vue'
import { cardClass, toneClass } from '@/components/ui'
import {
  cronLabel,
  extractErrorMessage,
  formatDateTime,
  statusLabel,
  statusTone,
} from '@/utils/format'

const router = useRouter()
const loading = ref(true)
const error = ref('')
const tasks = ref<Task[]>([])
const records = ref<CheckInRecord[]>([])
const tokenStatus = ref<TokenStatus | null>(null)

const activeTasks = computed(() => tasks.value.filter((task) => task.is_active).length)
const successToday = computed(
  () => records.value.filter((record) => record.status === 'success').length,
)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [taskList, token, recordPage] = await Promise.all([
      taskApi.list(),
      userApi.tokenStatus().catch(() => null),
      checkInApi.myRecords({ limit: 6 }),
    ])
    tasks.value = taskList
    tokenStatus.value = token
    records.value = recordPage.records
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <StateBlock v-if="loading" title="正在加载仪表盘" type="loading" />
  <StateBlock
    v-else-if="error"
    title="仪表盘加载失败"
    :description="error"
    type="error"
    action-label="重试"
    @action="load"
  />
  <div v-else class="grid gap-5">
    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div :class="[cardClass, 'p-4']">
        <div class="flex items-center justify-between">
          <span class="text-sm text-zinc-500">任务总数</span>
          <CheckCircle2 class="size-4 text-emerald-600" />
        </div>
        <div class="mt-3 text-3xl font-semibold">{{ tasks.length }}</div>
        <p class="mt-1 text-sm text-zinc-500">{{ activeTasks }} 个启用</p>
      </div>
      <div :class="[cardClass, 'p-4']">
        <div class="flex items-center justify-between">
          <span class="text-sm text-zinc-500">打卡 Token</span>
          <KeyRound class="size-4 text-sky-600" />
        </div>
        <div class="mt-3 text-lg font-semibold">
          {{ tokenStatus?.is_valid ? '可用' : '需要更新' }}
        </div>
        <p class="mt-1 text-sm text-zinc-500">
          {{
            tokenStatus?.days_until_expiry == null
              ? '未获取到过期信息'
              : `${tokenStatus.days_until_expiry} 天后过期`
          }}
        </p>
      </div>
      <div :class="[cardClass, 'p-4']">
        <div class="flex items-center justify-between">
          <span class="text-sm text-zinc-500">最近成功</span>
          <Activity class="size-4 text-zinc-700" />
        </div>
        <div class="mt-3 text-3xl font-semibold">{{ successToday }}</div>
        <p class="mt-1 text-sm text-zinc-500">最近记录中的成功数</p>
      </div>
      <div :class="[cardClass, 'p-4']">
        <div class="flex items-center justify-between">
          <span class="text-sm text-zinc-500">下次定时</span>
          <Clock class="size-4 text-amber-600" />
        </div>
        <div class="mt-3 text-lg font-semibold">
          {{ cronLabel(tasks.find((task) => task.is_active)?.cron_expression) }}
        </div>
        <p class="mt-1 text-sm text-zinc-500">来自首个启用任务</p>
      </div>
    </div>

    <div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
      <section :class="[cardClass, 'overflow-hidden']">
        <div class="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
          <h2 class="font-semibold">任务概览</h2>
          <button
            class="text-sm font-medium text-zinc-700 hover:text-zinc-950"
            type="button"
            @click="router.navigate('/tasks')"
          >
            管理任务
          </button>
        </div>
        <StateBlock
          v-if="tasks.length === 0"
          title="暂无任务"
          description="从模板创建任务后，这里会显示任务状态。"
          action-label="去创建"
          @action="router.navigate('/tasks')"
        />
        <div v-else class="divide-y divide-zinc-200">
          <div
            v-for="task in tasks.slice(0, 6)"
            :key="task.id"
            class="grid gap-2 px-4 py-3 sm:grid-cols-[1fr_auto] sm:items-center"
          >
            <div>
              <div class="font-medium">{{ task.name || `任务 #${task.id}` }}</div>
              <div class="mt-1 text-sm text-zinc-500">
                ThreadId: {{ task.thread_id || '未解析' }} · {{ cronLabel(task.cron_expression) }}
              </div>
            </div>
            <span :class="toneClass(task.is_active ? 'success' : 'neutral')">{{
              task.is_active ? '启用' : '停用'
            }}</span>
          </div>
        </div>
      </section>

      <section :class="[cardClass, 'overflow-hidden']">
        <div class="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
          <h2 class="font-semibold">最近记录</h2>
          <button
            class="text-sm font-medium text-zinc-700 hover:text-zinc-950"
            type="button"
            @click="router.navigate('/records')"
          >
            查看全部
          </button>
        </div>
        <StateBlock
          v-if="records.length === 0"
          title="暂无记录"
          description="手动或定时打卡后会生成记录。"
        />
        <div v-else class="divide-y divide-zinc-200">
          <div v-for="record in records" :key="record.id" class="px-4 py-3">
            <div class="flex items-center justify-between gap-3">
              <span class="font-medium">{{ record.task_name || `任务 #${record.task_id}` }}</span>
              <span :class="toneClass(statusTone(record.status))">{{
                statusLabel(record.status)
              }}</span>
            </div>
            <div class="mt-1 text-sm text-zinc-500">{{ formatDateTime(record.check_in_time) }}</div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
