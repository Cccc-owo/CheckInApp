<script setup lang="ts">
import { Info, KeyRound, QrCode, RotateCw, UserRound } from 'lucide-vue-next'
import { computed, onBeforeUnmount, ref } from 'vue'
import { authApi } from '@/api'
import { useAuth } from '@/app/auth'
import { useRouter } from '@/app/router'
import { alertClass, buttonBase, buttonTone, cardClass, inputClass } from '@/components/ui'
import { extractErrorMessage } from '@/utils/format'

const router = useRouter()
const auth = useAuth()

const alias = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const info = ref('')
const qrImage = ref('')
const qrSessionId = ref('')
const loginMode = ref<'qrcode' | 'password'>('qrcode')
let pollTimer: number | undefined

const currentSubtitle = computed(() =>
  loginMode.value === 'qrcode' ? 'QQ 扫码登录/注册' : '用户名密码登录',
)
const canSubmitPassword = computed(
  () => Boolean(alias.value.trim()) && Boolean(password.value) && !loading.value,
)
const canRequestQr = computed(() => Boolean(alias.value.trim()) && !loading.value)

function switchMode(mode: 'qrcode' | 'password') {
  loginMode.value = mode
  error.value = ''
  info.value = ''
  if (mode === 'password' && qrSessionId.value) void cancelQr()
}

function loginRedirect() {
  const redirect = router.query.value.get('redirect') || '/dashboard'
  void auth.refreshCurrentUser().finally(() => router.replace(redirect))
}

async function loginWithPassword() {
  if (!canSubmitPassword.value) return
  error.value = ''
  info.value = ''
  loading.value = true
  try {
    const result = await authApi.aliasLogin(alias.value.trim(), password.value)
    auth.applyLogin(result)
    loginRedirect()
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

async function requestQrCode() {
  if (!canRequestQr.value) return
  error.value = ''
  info.value = '正在创建扫码会话'
  loading.value = true
  try {
    if (qrSessionId.value) await authApi.cancelQRCodeSession(qrSessionId.value)
    const result = await authApi.requestQRCode(alias.value.trim())
    if (result.status === 'error') throw new Error(result.message || '创建扫码会话失败')
    qrSessionId.value = result.session_id
    qrImage.value = result.qrcode_image ?? result.qrcode_base64 ?? result.qr_code ?? ''
    info.value = '请使用 QQ 扫码完成授权'
    startPolling()
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

function startPolling() {
  window.clearInterval(pollTimer)
  pollTimer = window.setInterval(async () => {
    if (!qrSessionId.value) return
    try {
      const status = await authApi.getQRCodeStatus(qrSessionId.value)
      qrImage.value = status.qrcode_image ?? qrImage.value
      if (status.status === 'success') {
        window.clearInterval(pollTimer)
        auth.applyLogin(status)
        loginRedirect()
      } else if (status.status === 'error') {
        error.value = status.message || '扫码登录失败'
        window.clearInterval(pollTimer)
      } else {
        info.value = status.message || '等待扫码确认'
      }
    } catch (err) {
      error.value = extractErrorMessage(err)
      window.clearInterval(pollTimer)
    }
  }, 2200)
}

async function cancelQr() {
  window.clearInterval(pollTimer)
  if (qrSessionId.value) await authApi.cancelQRCodeSession(qrSessionId.value).catch(() => undefined)
  qrSessionId.value = ''
  qrImage.value = ''
  info.value = ''
}

onBeforeUnmount(() => {
  void cancelQr()
})
</script>

<template>
  <main
    class="flex min-h-[100dvh] items-center justify-center bg-zinc-50 px-4 py-8 text-zinc-950 dark:bg-zinc-950 dark:text-zinc-50"
  >
    <section class="w-full max-w-md">
      <div :class="[cardClass, 'overflow-hidden']">
        <div class="border-b border-zinc-200 px-6 py-5 text-center dark:border-zinc-800">
          <div
            class="mx-auto mb-3 flex size-11 items-center justify-center rounded-lg bg-emerald-700 text-white shadow-sm"
          >
            <QrCode class="size-5" />
          </div>
          <h1 class="text-xl font-semibold tracking-normal text-zinc-950 dark:text-zinc-50">
            接龙自动打卡系统
          </h1>
          <p class="mt-1 text-sm text-zinc-500 dark:text-zinc-400">{{ currentSubtitle }}</p>
        </div>

        <div class="p-6">
          <div
            class="grid grid-cols-2 rounded-md border border-zinc-200 bg-zinc-50 p-1 text-sm dark:border-zinc-700 dark:bg-zinc-950"
          >
            <button
              type="button"
              class="rounded px-3 py-2 text-center font-medium transition"
              :class="
                loginMode === 'qrcode'
                  ? 'bg-white text-zinc-900 shadow-sm dark:bg-zinc-800 dark:text-zinc-50'
                  : 'text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100'
              "
              @click="switchMode('qrcode')"
            >
              扫码登录
            </button>
            <button
              type="button"
              class="rounded px-3 py-2 text-center font-medium transition"
              :class="
                loginMode === 'password'
                  ? 'bg-white text-zinc-900 shadow-sm dark:bg-zinc-800 dark:text-zinc-50'
                  : 'text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100'
              "
              @click="switchMode('password')"
            >
              密码登录
            </button>
          </div>

          <form
            v-if="loginMode === 'password'"
            class="mt-6 grid gap-4"
            @submit.prevent="loginWithPassword"
          >
            <label class="grid gap-2">
              <span class="text-xs font-semibold text-zinc-500 dark:text-zinc-400">用户名</span>
              <div class="relative">
                <UserRound
                  class="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-zinc-400 dark:text-zinc-500"
                />
                <input
                  v-model="alias"
                  :class="[inputClass, 'pl-9']"
                  autocomplete="username"
                  required
                  placeholder="请输入您的用户名"
                />
              </div>
            </label>
            <label class="grid gap-2">
              <span class="text-xs font-semibold text-zinc-500 dark:text-zinc-400">密码</span>
              <div class="relative">
                <KeyRound
                  class="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-zinc-400 dark:text-zinc-500"
                />
                <input
                  v-model="password"
                  :class="[inputClass, 'pl-9']"
                  autocomplete="current-password"
                  type="password"
                  placeholder="请输入密码"
                />
              </div>
            </label>

            <div v-if="error" :class="alertClass.danger">
              {{ error }}
            </div>
            <div v-if="info" :class="alertClass.info">
              {{ info }}
            </div>

            <button
              :class="[buttonBase, buttonTone.primary, 'w-full']"
              :disabled="!canSubmitPassword"
              type="submit"
            >
              <KeyRound class="size-4" />
              {{ loading ? '登录中' : '登录' }}
            </button>
            <button
              class="text-center text-sm font-medium text-zinc-600 transition hover:text-zinc-950 dark:text-zinc-300 dark:hover:text-zinc-50"
              type="button"
              @click="switchMode('qrcode')"
            >
              没有密码？使用扫码登录
            </button>
          </form>

          <div v-else class="mt-6 grid gap-4">
            <label class="grid gap-2">
              <span class="text-xs font-semibold text-zinc-500 dark:text-zinc-400">用户名</span>
              <div class="relative">
                <UserRound
                  class="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-zinc-400 dark:text-zinc-500"
                />
                <input
                  v-model="alias"
                  :class="[inputClass, 'pl-9']"
                  autocomplete="username"
                  required
                  placeholder="请输入您的用户名"
                  @keyup.enter="requestQrCode"
                />
              </div>
            </label>

            <div v-if="error" :class="alertClass.danger">
              {{ error }}
            </div>
            <div v-if="info" :class="alertClass.info">
              {{ info }}
            </div>

            <button
              :class="[buttonBase, buttonTone.primary, 'w-full']"
              :disabled="!canRequestQr"
              type="button"
              @click="requestQrCode"
            >
              <QrCode class="size-4" />
              {{ loading ? '正在登录' : '扫码登录/注册' }}
            </button>

            <div
              v-if="qrImage"
              class="rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-center dark:border-zinc-700 dark:bg-zinc-950"
            >
              <img
                :src="qrImage.startsWith('data:') ? qrImage : `data:image/png;base64,${qrImage}`"
                alt="QQ 登录二维码"
                class="mx-auto size-48 rounded-md bg-white object-contain dark:bg-zinc-100"
              />
              <button
                class="mt-3 inline-flex items-center gap-2 text-sm font-medium text-zinc-600 transition hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-zinc-100"
                type="button"
                @click="requestQrCode"
              >
                <RotateCw class="size-4" />
                刷新会话
              </button>
            </div>
          </div>

          <div :class="[alertClass.info, 'mt-5 flex items-start gap-2']">
            <Info class="mt-0.5 size-4 shrink-0" />
            <div>
              <div class="font-semibold">
                {{ loginMode === 'qrcode' ? '扫码登录提示' : '密码登录提示' }}
              </div>
              <div v-if="loginMode === 'qrcode'" class="mt-1 space-y-1 text-sm">
                <p>1. 输入您的用户名用于标识身份</p>
                <p>2. 点击扫码登录/注册按钮</p>
                <p>3. 使用手机 QQ 扫描二维码</p>
                <p>4. 新用户首次扫码会自动注册账户</p>
              </div>
              <div v-else class="mt-1 space-y-1 text-sm">
                <p>1. 输入您的用户名和密码</p>
                <p>2. 点击登录按钮直接进入系统</p>
                <p>3. 首次使用请先扫码登录/注册，然后在设置中设置密码</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>
