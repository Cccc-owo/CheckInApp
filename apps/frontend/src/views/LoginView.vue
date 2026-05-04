<script setup lang="ts">
import { KeyRound, QrCode, RotateCw, UserRound } from 'lucide-vue-next'
import { computed, onBeforeUnmount, ref } from 'vue'
import { authApi } from '@/api'
import { useAuth } from '@/app/auth'
import { useRouter } from '@/app/router'
import { alertClass, cardClass, inputClass, labelClass } from '@/components/ui'
import { Button } from '@/components/ui/button'
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
    class="flex min-h-[100dvh] items-center justify-center bg-background px-4 py-8 text-foreground"
  >
    <section class="w-full max-w-md">
      <div :class="[cardClass, 'overflow-hidden']">
        <div class="border-b border-border px-4 py-3 text-center">
          <div
            class="mx-auto mb-3 flex size-10 items-center justify-center rounded-lg bg-[var(--tone-info-strong)] text-background shadow-sm"
          >
            <QrCode class="size-5" />
          </div>
          <h1 class="text-xl font-semibold tracking-normal text-foreground">接龙自动打卡系统</h1>
        </div>

        <div class="p-4">
          <div class="grid grid-cols-2 rounded-lg border border-border bg-muted p-1 text-sm">
            <button
              type="button"
              class="rounded-md px-3 py-2 text-center font-medium transition"
              :class="
                loginMode === 'qrcode'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              "
              @click="switchMode('qrcode')"
            >
              扫码登录
            </button>
            <button
              type="button"
              class="rounded-md px-3 py-2 text-center font-medium transition"
              :class="
                loginMode === 'password'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              "
              @click="switchMode('password')"
            >
              密码登录
            </button>
          </div>

          <form
            v-if="loginMode === 'password'"
            class="mt-5 grid gap-4"
            @submit.prevent="loginWithPassword"
          >
            <label class="grid gap-2">
              <span :class="labelClass">用户名</span>
              <div class="relative">
                <UserRound
                  class="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
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
              <span :class="labelClass">密码</span>
              <div class="relative">
                <KeyRound
                  class="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
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

            <Button class="w-full" type="submit" :disabled="!canSubmitPassword">
              <KeyRound class="size-4" />
              {{ loading ? '登录中' : '登录' }}
            </Button>
          </form>

          <div v-else class="mt-5 grid gap-4">
            <label class="grid gap-2">
              <span :class="labelClass">用户名</span>
              <div class="relative">
                <UserRound
                  class="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
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

            <Button class="w-full" type="button" :disabled="!canRequestQr" @click="requestQrCode">
              <QrCode class="size-4" />
              {{ loading ? '正在登录' : '扫码登录/注册' }}
            </Button>

            <div v-if="qrImage" class="rounded-lg border border-border bg-muted p-4 text-center">
              <img
                :src="qrImage.startsWith('data:') ? qrImage : `data:image/png;base64,${qrImage}`"
                alt="QQ 登录二维码"
                class="mx-auto size-48 rounded-md bg-background object-contain"
              />
              <button
                class="mt-3 inline-flex items-center gap-2 text-sm font-medium text-muted-foreground transition hover:text-foreground"
                type="button"
                @click="requestQrCode"
              >
                <RotateCw class="size-4" />
                刷新会话
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>
