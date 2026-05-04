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
import {
  alertClass,
  buttonBase,
  buttonTone,
  cardClass,
  inputClass,
  sectionHeaderClass,
  toneClass,
} from '@/components/ui'
import {
  cronLabel,
  extractErrorMessage,
  formatDateTime,
  statusLabel,
  statusTone,
} from '@/utils/format'

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
    <div class="grid gap-3">
      <div v-if="needsEmail" :class="alertClass.info">
        您还未设置邮箱地址，设置后可以接收打卡任务通知。
        <button
          class="ml-2 font-semibold hover:text-sky-950"
          type="button"
          @click="router.navigate('/settings')"
        >
          立即前往设置
        </button>
      </div>
      <div v-if="needsPassword" :class="alertClass.info">
        您还未设置登录密码，设置后可以使用用户名和密码快速登录。
        <button
          class="ml-2 font-semibold hover:text-sky-950"
          type="button"
          @click="router.navigate('/settings')"
        >
          立即前往设置
        </button>
      </div>
      <div
        v-if="tokenStatus && !tokenStatus.is_valid"
        :class="[alertClass.warning, 'flex items-start gap-2']"
      >
        <AlertTriangle class="mt-0.5 size-4 shrink-0" />
        <div>
          打卡凭证已过期，无法自动打卡。请回到登录页使用扫码登录刷新 Token。
          <button
            class="ml-2 font-semibold hover:text-amber-950"
            type="button"
            @click="router.navigate('/login')"
          >
            立即刷新
          </button>
        </div>
      </div>
      <div v-if="tasks.length === 0" :class="alertClass.info">
        您还没有打卡任务。
        <button
          class="ml-2 font-semibold hover:text-sky-950"
          type="button"
          @click="router.navigate('/tasks')"
        >
          立即创建
        </button>
      </div>
    </div>

    <section :class="[cardClass, 'overflow-hidden']">
      <div :class="sectionHeaderClass">
        <div class="flex items-center gap-2">
          <KeyRound class="size-4 text-emerald-700" />
          <h2 class="font-semibold">Token 状态</h2>
        </div>
        <span :class="toneClass(tokenTone)">{{ tokenLabel }}</span>
      </div>
      <div class="grid gap-4 p-5 md:grid-cols-2">
        <div class="grid gap-3 text-sm">
          <div
            class="flex items-center justify-between rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2"
          >
            <span class="text-zinc-500">Token 状态</span>
            <span :class="toneClass(tokenTone)">{{ tokenLabel }}</span>
          </div>
          <div
            class="flex items-center justify-between rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2"
          >
            <span class="text-zinc-500">剩余时间</span>
            <span>{{
              tokenStatus?.days_until_expiry == null
                ? '未知'
                : `${tokenStatus.days_until_expiry} 天`
            }}</span>
          </div>
          <div
            class="flex items-center justify-between rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2"
          >
            <span class="text-zinc-500">即将过期</span>
            <span>{{ tokenStatus?.expiring_soon ? '是' : '否' }}</span>
          </div>
        </div>
        <div class="rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-sm text-zinc-600">
          <p>{{ tokenDetail }}</p>
          <button
            :class="[
              buttonBase,
              tokenStatus?.is_valid ? buttonTone.secondary : buttonTone.primary,
              'mt-4',
            ]"
            type="button"
            @click="router.navigate('/login')"
          >
            <QrCode class="size-4" />
            扫码刷新 Token
          </button>
        </div>
      </div>
    </section>

    <section :class="[cardClass, 'overflow-hidden']">
      <div :class="sectionHeaderClass">
        <div class="flex items-center gap-2">
          <CalendarDays class="size-4 text-emerald-700" />
          <h2 class="font-semibold">手动打卡</h2>
        </div>
        <span class="text-sm text-zinc-500">{{ activeTasks }} 个启用任务</span>
      </div>
      <div class="p-5">
        <p class="text-sm text-zinc-500">选择任务并点击下方按钮立即执行打卡操作。</p>
        <div class="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
          <select v-model.number="selectedTaskId" :class="[inputClass, 'sm:max-w-md']">
            <option v-for="task in tasks" :key="task.id" :value="task.id">
              {{ task.name || `任务 #${task.id}` }} · {{ task.is_active ? '启用' : '停用' }}
            </option>
          </select>
          <button
            :class="[buttonBase, buttonTone.primary]"
            :disabled="!selectedTaskId || checkInLoading"
            type="button"
            @click="manualCheckIn"
          >
            <CalendarDays class="size-4" />
            {{ checkInLoading ? '打卡中' : '立即打卡' }}
          </button>
        </div>
        <div
          v-if="selectedTask"
          class="mt-4 rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-sm"
        >
          <div class="font-medium text-zinc-900">
            {{ selectedTask.name || `任务 #${selectedTask.id}` }}
          </div>
          <div class="mt-1 text-zinc-500">
            ThreadId: {{ selectedTask.thread_id || '未解析' }} ·
            {{ cronLabel(selectedTask.cron_expression) }}
          </div>
        </div>
        <div v-if="message" :class="[alertClass.success, 'mt-4']">{{ message }}</div>
        <div v-if="error" :class="[alertClass.danger, 'mt-4']">{{ error }}</div>
        <div
          v-if="latestStatus"
          class="mt-4 rounded-lg border border-zinc-200 bg-white p-4 text-sm"
        >
          <div class="flex flex-wrap items-center justify-between gap-2">
            <span class="font-semibold text-zinc-900">本次打卡</span>
            <span :class="toneClass(statusTone(latestStatus.status))">{{
              statusLabel(latestStatus.status)
            }}</span>
          </div>
          <p class="mt-2 text-zinc-500">
            {{
              latestStatus.response_text || latestStatus.error_message || '正在等待后端返回结果。'
            }}
          </p>
        </div>
        <div
          v-else-if="lastRecord"
          class="mt-4 rounded-lg border border-zinc-200 bg-white p-4 text-sm"
        >
          <div class="flex flex-wrap items-center justify-between gap-2">
            <span class="font-semibold text-zinc-900">上次打卡</span>
            <span :class="toneClass(statusTone(lastRecord.status))">{{
              statusLabel(lastRecord.status)
            }}</span>
          </div>
          <p class="mt-2 text-zinc-500">
            {{ formatDateTime(lastRecord.check_in_time) }} ·
            {{ lastRecord.response_text || lastRecord.error_message || '无响应内容' }}
          </p>
        </div>
      </div>
    </section>

    <section :class="[cardClass, 'overflow-hidden']">
      <div :class="sectionHeaderClass">
        <div class="flex items-center gap-2">
          <UserRound class="size-4 text-emerald-700" />
          <h2 class="font-semibold">个人信息</h2>
        </div>
        <button
          :class="[buttonBase, buttonTone.secondary]"
          type="button"
          @click="router.navigate('/settings')"
        >
          个人设置
        </button>
      </div>
      <div class="grid gap-3 p-5 text-sm md:grid-cols-2">
        <div class="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2">
          <div class="text-zinc-500">用户名</div>
          <div class="mt-1 font-medium text-zinc-900">{{ auth.state.user?.alias || '未登录' }}</div>
        </div>
        <div class="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2">
          <div class="text-zinc-500">角色</div>
          <div class="mt-1">
            <span :class="toneClass(auth.state.user?.role === 'admin' ? 'danger' : 'info')">
              {{ auth.state.user?.role === 'admin' ? '管理员' : '普通用户' }}
            </span>
          </div>
        </div>
        <div class="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2">
          <div class="text-zinc-500">邮箱</div>
          <div class="mt-1 font-medium text-zinc-900">{{ auth.state.user?.email || '未设置' }}</div>
        </div>
        <div class="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2">
          <div class="text-zinc-500">注册时间</div>
          <div class="mt-1 font-medium text-zinc-900">
            {{ formatDateTime(auth.state.user?.created_at) }}
          </div>
        </div>
      </div>
    </section>

    <section :class="[cardClass, 'overflow-hidden']">
      <div :class="sectionHeaderClass">
        <div>
          <h2 class="font-semibold">任务概览</h2>
          <p class="mt-1 text-sm text-zinc-500">
            {{ activeTasks }} 个启用，{{ inactiveTasks }} 个停用，最近记录成功
            {{ successToday }} 条。
          </p>
        </div>
        <button
          :class="[buttonBase, buttonTone.secondary]"
          type="button"
          @click="router.navigate('/tasks')"
        >
          管理任务
        </button>
      </div>
      <div class="grid gap-4 p-4 md:grid-cols-2 xl:grid-cols-4">
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
            <span class="text-sm text-zinc-500">最近成功</span>
            <Activity class="size-4 text-zinc-700" />
          </div>
          <div class="mt-3 text-3xl font-semibold">{{ successToday }}</div>
          <p class="mt-1 text-sm text-zinc-500">最近记录中的成功数</p>
        </div>
        <div :class="[cardClass, 'p-4 md:col-span-2']">
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
    </section>

    <section :class="[cardClass, 'overflow-hidden']">
      <div :class="sectionHeaderClass">
        <div>
          <h2 class="font-semibold">最近记录</h2>
          <p class="mt-1 text-sm text-zinc-500">最近的打卡结果和状态变化会先出现在这里。</p>
        </div>
        <button
          :class="[buttonBase, buttonTone.secondary]"
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
          <div class="mt-1 text-sm text-zinc-500">
            {{ formatDateTime(record.check_in_time) }} ·
            {{ record.trigger_type ? statusLabel(record.trigger_type) : '未注明触发' }}
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
