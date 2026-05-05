<script setup lang="ts">
import {
  Activity,
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  Clock,
  KeyRound,
  QrCode,
  UserRound,
} from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import {
  checkInApi,
  taskApi,
  userApi,
  type CheckInRecord,
  type CheckInRecordStatus,
  type Task,
  type TokenStatus,
} from '@/api'
import { useAuth } from '@/app/auth'
import { useRouter } from '@/app/router'
import StateBlock from '@/components/StateBlock.vue'
import { alertClass, cardClass, inputClass, sectionHeaderClass, toneClass } from '@/components/ui'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import {
  cronLabel,
  extractErrorMessage,
  formatDateTime,
  statusLabel,
  statusTone,
} from '@/utils/format'
import {
  canRefreshAuthorization,
  formatAuthorizationExpiryTooltip,
  formatRemainingDays,
} from './dashboard-license'

const router = useRouter()
const auth = useAuth()
const loading = ref(true)
const error = ref('')
const message = ref('')
const tasks = ref<Task[]>([])
const records = ref<CheckInRecord[]>([])
const tokenStatus = ref<TokenStatus | null>(null)
const selectedTaskId = ref<number | null>(null)
const checkInLoading = ref(false)
const latestStatus = ref<CheckInRecordStatus | null>(null)
let pollTimer: number | undefined

const activeTasks = computed(() => tasks.value.filter((task) => task.is_active).length)
const inactiveTasks = computed(() => Math.max(0, tasks.value.length - activeTasks.value))
const selectedTask = computed(() => tasks.value.find((task) => task.id === selectedTaskId.value))
const lastRecord = computed(() => records.value[0] ?? null)
const nextActiveTask = computed(() => tasks.value.find((task) => task.is_active) ?? null)
const successToday = computed(
  () => records.value.filter((record) => record.status === 'success').length,
)
const tokenTone = computed(() =>
  tokenStatus.value?.is_valid
    ? tokenStatus.value.expiring_soon
      ? 'warning'
      : 'success'
    : 'danger',
)
const tokenLabel = computed(() => {
  if (!tokenStatus.value) return '未知'
  if (!tokenStatus.value.is_valid) return '无效'
  return tokenStatus.value.expiring_soon ? '即将过期' : '有效'
})
const tokenDetail = computed(() => {
  if (!tokenStatus.value) return '未获取到业务 Token 状态。'
  if (!tokenStatus.value.is_valid) return '打卡凭证已过期，无法自动打卡。请使用扫码登录刷新授权。'
  if (tokenStatus.value.expiring_soon) return 'Token 即将过期，建议准备刷新授权。'
  return `业务 Token 正常，${tokenStatus.value.days_until_expiry ?? '未知'} 天后过期。`
})
const remainingDaysLabel = computed(() => formatRemainingDays(tokenStatus.value?.days_until_expiry))
const expiryTooltip = computed(() => formatAuthorizationExpiryTooltip(tokenStatus.value))
const canRefreshToken = computed(() => canRefreshAuthorization(tokenStatus.value))
const needsEmail = computed(() => !auth.state.user?.email)
const needsPassword = computed(() => auth.state.user?.has_password === false)

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
    if (!selectedTaskId.value || !taskList.some((task) => task.id === selectedTaskId.value)) {
      selectedTaskId.value = taskList.find((task) => task.is_active)?.id ?? taskList[0]?.id ?? null
    }
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

async function manualCheckIn() {
  if (!selectedTaskId.value) return
  checkInLoading.value = true
  error.value = ''
  message.value = ''
  latestStatus.value = null
  try {
    const result = await checkInApi.manual(selectedTaskId.value)
    const recordId = result.record_id ?? result.id
    message.value = result.message || '已启动打卡任务'
    if (recordId) startRecordPolling(recordId)
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    checkInLoading.value = false
  }
}

function startRecordPolling(recordId: number) {
  window.clearInterval(pollTimer)
  pollTimer = window.setInterval(async () => {
    try {
      const status = await checkInApi.status(recordId)
      latestStatus.value = status
      if (!['pending', 'running'].includes(status.status)) {
        window.clearInterval(pollTimer)
        await load()
      }
    } catch {
      window.clearInterval(pollTimer)
    }
  }, 1800)
}

onMounted(load)
</script>

<template>
  <StateBlock v-if="loading" title="正在加载仪表盘" type="loading" />
  <StateBlock
    v-else-if="error && tasks.length === 0"
    title="仪表盘加载失败"
    :description="error"
    type="error"
    action-label="重试"
    @action="load"
  />
  <div v-else class="grid gap-5">
    <div
      v-if="
        needsEmail || needsPassword || (tokenStatus && !tokenStatus.is_valid) || tasks.length === 0
      "
      class="grid gap-2"
    >
      <div
        v-if="needsEmail"
        :class="[alertClass.info, 'flex flex-wrap items-center justify-between gap-2']"
      >
        <span>未设置邮箱</span>
        <Button
          variant="ghost"
          class="font-semibold"
          type="button"
          @click="router.navigate('/settings')"
        >
          设置
        </Button>
      </div>
      <div
        v-if="needsPassword"
        :class="[alertClass.info, 'flex flex-wrap items-center justify-between gap-2']"
      >
        <span>未设置登录密码</span>
        <Button
          variant="ghost"
          class="font-semibold"
          type="button"
          @click="router.navigate('/settings')"
        >
          设置
        </Button>
      </div>
      <div
        v-if="tokenStatus && !tokenStatus.is_valid"
        :class="[alertClass.warning, 'flex flex-wrap items-center justify-between gap-2']"
      >
        <span class="inline-flex items-center gap-2">
          <AlertTriangle class="size-4 shrink-0" />
          打卡凭证已过期
        </span>
        <Button
          variant="ghost"
          class="font-semibold"
          type="button"
          @click="router.navigate('/login')"
        >
          刷新
        </Button>
      </div>
      <div
        v-if="tasks.length === 0"
        :class="[alertClass.info, 'flex flex-wrap items-center justify-between gap-2']"
      >
        <span>暂无打卡任务</span>
        <Button
          variant="ghost"
          class="font-semibold"
          type="button"
          @click="router.navigate('/tasks')"
        >
          创建
        </Button>
      </div>
    </div>

    <section class="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
      <div :class="[cardClass, 'overflow-hidden']">
        <div :class="sectionHeaderClass">
          <div class="flex items-center gap-2">
            <CalendarDays class="size-4 text-[var(--tone-success-fg)]" />
            <h2 class="font-semibold">手动打卡</h2>
          </div>
          <span class="text-sm text-muted-foreground">{{ activeTasks }} 个启用</span>
        </div>
        <div class="p-4">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
            <select v-model.number="selectedTaskId" :class="[inputClass, 'sm:max-w-md']">
              <option v-for="task in tasks" :key="task.id" :value="task.id">
                {{ task.name || `任务 #${task.id}` }} · {{ task.is_active ? '启用' : '停用' }}
              </option>
            </select>
            <Button
              :disabled="!selectedTaskId || checkInLoading"
              type="button"
              @click="manualCheckIn"
            >
              <CalendarDays class="size-4" />
              {{ checkInLoading ? '打卡中' : '立即打卡' }}
            </Button>
          </div>
          <div
            v-if="selectedTask"
            class="mt-4 rounded-lg border border-border bg-muted p-4 text-sm"
          >
            <div class="font-medium text-foreground">
              {{ selectedTask.name || `任务 #${selectedTask.id}` }}
            </div>
            <div class="mt-1 text-muted-foreground">
              ThreadId: {{ selectedTask.thread_id || '未解析' }} ·
              {{ cronLabel(selectedTask.cron_expression) }}
            </div>
          </div>
          <div v-if="message" :class="[alertClass.success, 'mt-4']">{{ message }}</div>
          <div v-if="error" :class="[alertClass.danger, 'mt-4']">{{ error }}</div>
          <div
            v-if="latestStatus"
            class="mt-4 rounded-lg border border-border bg-background p-4 text-sm"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <span class="font-semibold text-foreground">本次打卡</span>
              <span :class="toneClass(statusTone(latestStatus.status))">{{
                statusLabel(latestStatus.status)
              }}</span>
            </div>
            <p class="mt-2 text-muted-foreground">
              {{
                latestStatus.response_text || latestStatus.error_message || '正在等待后端返回结果。'
              }}
            </p>
          </div>
          <div
            v-else-if="lastRecord"
            class="mt-4 rounded-lg border border-border bg-background p-4 text-sm"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <span class="font-semibold text-foreground">上次打卡</span>
              <span :class="toneClass(statusTone(lastRecord.status))">{{
                statusLabel(lastRecord.status)
              }}</span>
            </div>
            <p class="mt-2 text-muted-foreground">
              {{ formatDateTime(lastRecord.check_in_time) }} ·
              {{ lastRecord.response_text || lastRecord.error_message || '无响应内容' }}
            </p>
          </div>
        </div>
      </div>

      <div :class="[cardClass, 'overflow-hidden']">
        <div :class="sectionHeaderClass">
          <div class="flex items-center gap-2">
            <KeyRound class="size-4 text-[var(--tone-success-fg)]" />
            <h2 class="font-semibold">授权</h2>
          </div>
          <span :class="toneClass(tokenTone)">{{ tokenLabel }}</span>
        </div>
        <div class="grid gap-3 p-4 text-sm">
          <div class="flex items-center justify-between">
            <span class="text-muted-foreground">剩余</span>
            <TooltipProvider v-if="expiryTooltip">
              <Tooltip>
                <TooltipTrigger as-child>
                  <span
                    class="cursor-help font-medium underline decoration-muted-foreground/40 underline-offset-4"
                    :title="expiryTooltip"
                  >
                    {{ remainingDaysLabel }}
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  {{ expiryTooltip }}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <span v-else class="font-medium">
              {{ remainingDaysLabel }}
            </span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-muted-foreground">预警</span>
            <span>{{ tokenStatus?.expiring_soon ? '是' : '否' }}</span>
          </div>
          <div class="text-sm text-muted-foreground">{{ tokenDetail }}</div>
          <Button
            :variant="canRefreshToken ? 'default' : 'outline'"
            :disabled="!canRefreshToken"
            type="button"
            @click="router.navigate('/login')"
          >
            <QrCode class="size-4" />
            扫码刷新
          </Button>
        </div>
      </div>
    </section>

    <section :class="[cardClass, 'overflow-hidden']">
      <div :class="sectionHeaderClass">
        <div class="flex items-center gap-2">
          <UserRound class="size-4 text-[var(--tone-success-fg)]" />
          <h2 class="font-semibold">个人信息</h2>
        </div>
        <Button variant="outline" type="button" @click="router.navigate('/settings')">
          个人设置
        </Button>
      </div>
      <div class="grid gap-3 p-4 text-sm md:grid-cols-4">
        <div class="rounded-lg border border-border bg-muted px-3 py-2">
          <div class="text-muted-foreground">用户名</div>
          <div class="mt-1 font-medium text-foreground">
            {{ auth.state.user?.alias || '未登录' }}
          </div>
        </div>
        <div class="rounded-lg border border-border bg-muted px-3 py-2">
          <div class="text-muted-foreground">角色</div>
          <div class="mt-1">
            <span :class="toneClass(auth.state.user?.role === 'admin' ? 'danger' : 'info')">
              {{ auth.state.user?.role === 'admin' ? '管理员' : '普通用户' }}
            </span>
          </div>
        </div>
        <div class="rounded-lg border border-border bg-muted px-3 py-2">
          <div class="text-muted-foreground">邮箱</div>
          <div class="mt-1 font-medium text-foreground">
            {{ auth.state.user?.email || '未设置' }}
          </div>
        </div>
        <div class="rounded-lg border border-border bg-muted px-3 py-2">
          <div class="text-muted-foreground">注册时间</div>
          <div class="mt-1 font-medium text-foreground">
            {{ formatDateTime(auth.state.user?.created_at) }}
          </div>
        </div>
      </div>
    </section>

    <section :class="[cardClass, 'overflow-hidden']">
      <div :class="sectionHeaderClass">
        <div>
          <h2 class="font-semibold">任务概览</h2>
        </div>
        <Button variant="outline" type="button" @click="router.navigate('/tasks')">
          管理任务
        </Button>
      </div>
      <div class="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-4">
        <div class="rounded-lg border border-border bg-muted p-3">
          <div class="flex items-center justify-between">
            <span class="text-sm text-muted-foreground">任务总数</span>
            <CheckCircle2 class="size-4 text-[var(--tone-success-fg)]" />
          </div>
          <div class="mt-3 text-3xl font-semibold">{{ tasks.length }}</div>
          <p class="mt-1 text-sm text-muted-foreground">
            {{ activeTasks }} 启用 · {{ inactiveTasks }} 停用
          </p>
        </div>
        <div class="rounded-lg border border-border bg-muted p-3">
          <div class="flex items-center justify-between">
            <span class="text-sm text-muted-foreground">最近成功</span>
            <Activity class="size-4 text-foreground" />
          </div>
          <div class="mt-3 text-3xl font-semibold">{{ successToday }}</div>
          <p class="mt-1 text-sm text-muted-foreground">最近记录</p>
        </div>
        <div class="rounded-lg border border-border bg-muted p-3 md:col-span-2">
          <div class="flex items-center justify-between">
            <span class="text-sm text-muted-foreground">下次定时</span>
            <Clock class="size-4 text-[var(--tone-warning-fg)]" />
          </div>
          <div class="mt-3 text-lg font-semibold">
            {{ cronLabel(nextActiveTask?.cron_expression) }}
          </div>
          <p class="mt-1 text-sm text-muted-foreground">
            {{ nextActiveTask?.name || '无启用任务' }}
          </p>
        </div>
      </div>
    </section>

    <section :class="[cardClass, 'overflow-hidden']">
      <div :class="sectionHeaderClass">
        <div>
          <h2 class="font-semibold">最近记录</h2>
        </div>
        <Button variant="outline" type="button" @click="router.navigate('/records')">
          查看全部
        </Button>
      </div>
      <StateBlock v-if="records.length === 0" title="暂无记录" />
      <div v-else class="divide-y divide-border">
        <div v-for="record in records" :key="record.id" class="px-4 py-3">
          <div class="flex items-center justify-between gap-3">
            <span class="font-medium">{{ record.task_name || `任务 #${record.task_id}` }}</span>
            <span :class="toneClass(statusTone(record.status))">{{
              statusLabel(record.status)
            }}</span>
          </div>
          <div class="mt-1 text-sm text-muted-foreground">
            {{ formatDateTime(record.check_in_time) }} ·
            {{ record.trigger_type ? statusLabel(record.trigger_type) : '未注明触发' }}
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
