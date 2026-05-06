<script setup lang="ts">
import { MailCheck, RefreshCw, Send } from 'lucide-vue-next'
import { computed, reactive, ref } from 'vue'
import { userApi } from '@/api'
import { useAuth } from '@/app/auth'
import { useRouter } from '@/app/router'
import { alertClass, cardClass, inputClass, labelClass, toneClass } from '@/components/ui'
import { Button } from '@/components/ui/button'
import { extractErrorMessage, formatFullDateTime } from '@/utils/format'

const auth = useAuth()
const router = useRouter()
const loading = ref(false)
const sendingCode = ref(false)
const verifying = ref(false)
const error = ref('')
const emailMessage = ref('')
const emailForm = reactive({
  email: auth.state.user?.email ?? '',
  code: '',
})

const emailVerified = computed(() => Boolean(auth.state.user?.email_verified))

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    const status = await userApi.status()
    if (status.is_approved) {
      await auth.refreshCurrentUser()
      await router.replace('/dashboard')
    }
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

async function requestEmailCode() {
  sendingCode.value = true
  error.value = ''
  emailMessage.value = ''
  try {
    const user = await userApi.setEmail(emailForm.email)
    auth.state.user = user
    emailForm.email = user.email ?? emailForm.email
    emailMessage.value = '验证码已发送，请检查邮箱'
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    sendingCode.value = false
  }
}

async function verifyEmail() {
  verifying.value = true
  error.value = ''
  emailMessage.value = ''
  try {
    const user = await userApi.verifyEmail(emailForm.code)
    auth.state.user = user
    emailMessage.value = '邮箱已验证，账号已进入正常审批流程'
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    verifying.value = false
  }
}
</script>

<template>
  <section :class="[cardClass, 'mx-auto max-w-2xl overflow-hidden']">
    <div class="border-b border-[var(--tone-warning-border)] bg-[var(--tone-warning-bg)] p-6">
      <span :class="toneClass('warning')">待审批</span>
      <h2 class="mt-3 text-xl font-semibold">账号等待审批</h2>
      <p class="mt-2 text-sm text-muted-foreground">
        当前账号
        {{ auth.state.user?.alias ?? '未知用户' }} 已完成登录，但还需要管理员审批后才能访问工作台。
      </p>
      <p class="mt-3 text-sm font-medium text-[var(--tone-warning-fg)]">
        请填写并验证邮箱。只有邮箱完成验证后账号才会进入正常审批流程；未验证的待审批账号可能会在清理窗口后自动吊销。
      </p>
    </div>
    <div class="p-6">
      <dl class="mt-5 grid gap-3 sm:grid-cols-2">
        <div class="rounded-md border border-border bg-background p-3">
          <dt class="text-xs text-muted-foreground">创建时间</dt>
          <dd class="mt-1 text-sm font-medium">
            {{ formatFullDateTime(auth.state.user?.created_at) }}
          </dd>
        </div>
        <div class="rounded-md border border-border bg-background p-3">
          <dt class="text-xs text-muted-foreground">审批状态</dt>
          <dd class="mt-1 text-sm font-medium">待审批</dd>
        </div>
        <div class="rounded-md border border-border bg-background p-3">
          <dt class="text-xs text-muted-foreground">邮箱状态</dt>
          <dd class="mt-1 text-sm font-medium">
            {{ emailVerified ? '已验证' : '未验证' }}
          </dd>
        </div>
      </dl>

      <form class="mt-5 grid gap-4 rounded-md border border-border bg-background p-4">
        <div class="flex items-center justify-between gap-3">
          <div>
            <h3 class="font-semibold">邮箱验证</h3>
          </div>
          <span :class="toneClass(emailVerified ? 'success' : 'warning')">
            {{ emailVerified ? '已验证' : '待验证' }}
          </span>
        </div>
        <label class="grid gap-2">
          <span :class="labelClass">邮箱</span>
          <input
            v-model.trim="emailForm.email"
            :class="inputClass"
            type="email"
            placeholder="用于审批通知"
            :disabled="emailVerified"
          />
        </label>
        <div class="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
          <label class="grid gap-2">
            <span :class="labelClass">验证码</span>
            <input
              v-model.trim="emailForm.code"
              :class="inputClass"
              inputmode="numeric"
              placeholder="请输入邮箱验证码"
              :disabled="emailVerified"
            />
          </label>
          <div class="flex items-end gap-2">
            <Button
              variant="outline"
              type="button"
              :disabled="sendingCode || emailVerified || !emailForm.email"
              @click="requestEmailCode"
            >
              <Send class="size-4" :class="{ 'animate-spin': sendingCode }" />
              发送验证码
            </Button>
            <Button
              type="button"
              :disabled="verifying || emailVerified || !emailForm.code"
              @click="verifyEmail"
            >
              <MailCheck class="size-4" :class="{ 'animate-spin': verifying }" />
              验证
            </Button>
          </div>
        </div>
        <div v-if="emailMessage" :class="alertClass.success">
          {{ emailMessage }}
        </div>
      </form>

      <div v-if="error" :class="[alertClass.danger, 'mt-4']">
        {{ error }}
      </div>
      <Button class="mt-5" :disabled="loading" type="button" @click="refresh">
        <RefreshCw class="size-4" :class="{ 'animate-spin': loading }" />
        刷新审批状态
      </Button>
    </div>
  </section>
</template>
