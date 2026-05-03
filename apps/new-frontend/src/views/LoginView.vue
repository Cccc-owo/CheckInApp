<script setup lang="ts">
import { KeyRound, QrCode, RotateCw } from 'lucide-vue-next'
import { onBeforeUnmount, ref } from 'vue'
import { authApi } from '@/api'
import { useAuth } from '@/app/auth'
import { useRouter } from '@/app/router'
import { buttonBase, buttonTone, inputClass } from '@/components/ui'
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
let pollTimer: number | undefined

function loginRedirect() {
  const redirect = router.query.value.get('redirect') || '/dashboard'
  void auth.refreshCurrentUser().finally(() => router.replace(redirect))
}

async function loginWithPassword() {
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
      if (status.qrcode_image) qrImage.value = status.qrcode_image
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
    class="grid min-h-[100dvh] bg-zinc-50 px-4 py-8 text-zinc-950 lg:grid-cols-[minmax(0,1fr)_440px] lg:p-0"
  >
    <section
      class="hidden border-r border-zinc-200 bg-white p-10 lg:flex lg:flex-col lg:justify-between"
    >
      <div>
        <div class="text-sm font-semibold text-zinc-500">CheckIn App</div>
        <h1 class="mt-6 max-w-xl text-4xl font-semibold leading-tight tracking-normal">
          接龙自动打卡系统的新前端工作台
        </h1>
        <p class="mt-4 max-w-lg text-base text-zinc-600">
          使用账号密码或 QQ 扫码登录，管理任务、模板、记录和系统状态。
        </p>
      </div>
      <div class="grid grid-cols-3 gap-3 text-sm">
        <div class="rounded-lg border border-zinc-200 p-4">
          <div class="text-2xl font-semibold">1</div>
          <div class="mt-1 text-zinc-500">用户审批</div>
        </div>
        <div class="rounded-lg border border-zinc-200 p-4">
          <div class="text-2xl font-semibold">N</div>
          <div class="mt-1 text-zinc-500">多任务</div>
        </div>
        <div class="rounded-lg border border-zinc-200 p-4">
          <div class="text-2xl font-semibold">24h</div>
          <div class="mt-1 text-zinc-500">自动调度</div>
        </div>
      </div>
    </section>

    <section class="mx-auto flex w-full max-w-md flex-col justify-center lg:px-8">
      <div class="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
        <h2 class="text-xl font-semibold">登录</h2>
        <p class="mt-1 text-sm text-zinc-500">输入别名登录；没有或需要更新授权时使用 QQ 扫码。</p>

        <form class="mt-6 grid gap-4" @submit.prevent="loginWithPassword">
          <label class="grid gap-2">
            <span class="text-xs font-semibold text-zinc-500">别名</span>
            <input v-model="alias" :class="inputClass" required placeholder="例如 zhangsan" />
          </label>
          <label class="grid gap-2">
            <span class="text-xs font-semibold text-zinc-500">密码</span>
            <input
              v-model="password"
              :class="inputClass"
              type="password"
              placeholder="已设置密码时可用"
            />
          </label>

          <div
            v-if="error"
            class="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700"
          >
            {{ error }}
          </div>
          <div
            v-if="info"
            class="rounded-md border border-sky-200 bg-sky-50 px-3 py-2 text-sm text-sky-700"
          >
            {{ info }}
          </div>

          <button
            :class="[buttonBase, buttonTone.primary]"
            :disabled="loading || !alias || !password"
            type="submit"
          >
            <KeyRound class="size-4" />
            {{ loading ? '处理中' : '密码登录' }}
          </button>
        </form>

        <div class="mt-5 border-t border-zinc-200 pt-5">
          <button
            :class="[buttonBase, buttonTone.secondary, 'w-full']"
            :disabled="loading || !alias"
            type="button"
            @click="requestQrCode"
          >
            <QrCode class="size-4" />
            请求 QQ 扫码
          </button>
          <div
            v-if="qrImage"
            class="mt-4 rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-center"
          >
            <img
              :src="qrImage.startsWith('data:') ? qrImage : `data:image/png;base64,${qrImage}`"
              alt="QQ 登录二维码"
              class="mx-auto size-48 rounded-md bg-white object-contain"
            />
            <button
              class="mt-3 inline-flex items-center gap-2 text-sm text-zinc-600 hover:text-zinc-900"
              type="button"
              @click="requestQrCode"
            >
              <RotateCw class="size-4" />
              刷新会话
            </button>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>
