<script setup lang="ts">
import { MailCheck, Save, Send } from 'lucide-vue-next'
import { computed, onMounted, reactive, ref } from 'vue'
import { userApi, type TokenStatus } from '@/api'
import { useAuth } from '@/app/auth'
import StateBlock from '@/components/StateBlock.vue'
import {
  alertClass,
  cardClass,
  inputClass,
  labelClass,
  sectionHeaderClass,
  toneClass,
} from '@/components/ui'
import { Button } from '@/components/ui/button'
import { extractErrorMessage } from '@/utils/format'

const auth = useAuth()
const loading = ref(true)
const saving = ref(false)
const sendingCode = ref(false)
const verifyingEmail = ref(false)
const error = ref('')
const message = ref('')
const emailMessage = ref('')
const token = ref<TokenStatus | null>(null)
const form = reactive({
  alias: '',
  current_password: '',
  new_password: '',
})
const emailForm = reactive({
  email: '',
  code: '',
})
const emailVerified = computed(() => Boolean(auth.state.user?.email_verified))

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [user, tokenStatus] = await Promise.all([
      userApi.me(),
      userApi.tokenStatus().catch(() => null),
    ])
    auth.state.user = user
    token.value = tokenStatus
    form.alias = user.alias
    emailForm.email = user.email ?? ''
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  error.value = ''
  message.value = ''
  try {
    const user = await userApi.updateProfile({
      alias: form.alias,
      current_password: form.current_password || undefined,
      new_password: form.new_password || undefined,
    })
    auth.state.user = user
    form.current_password = ''
    form.new_password = ''
    message.value = '个人信息已更新'
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    saving.value = false
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
    emailForm.code = ''
    emailMessage.value = '验证码已发送，请检查邮箱'
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    sendingCode.value = false
  }
}

async function verifyEmail() {
  verifyingEmail.value = true
  error.value = ''
  emailMessage.value = ''
  try {
    const user = await userApi.verifyEmail(emailForm.code)
    auth.state.user = user
    emailForm.email = user.email ?? emailForm.email
    emailForm.code = ''
    emailMessage.value = '邮箱已验证'
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    verifyingEmail.value = false
  }
}

onMounted(load)
</script>

<template>
  <StateBlock v-if="loading" title="正在加载设置" type="loading" />
  <StateBlock
    v-else-if="error && !auth.state.user"
    title="设置加载失败"
    :description="error"
    type="error"
    action-label="重试"
    @action="load"
  />
  <div v-else class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
    <form :class="[cardClass, 'overflow-hidden']" @submit.prevent="save">
      <div :class="sectionHeaderClass">
        <h2 class="font-semibold">个人资料</h2>
      </div>
      <div class="grid gap-4 p-4">
        <label class="grid gap-2">
          <span :class="labelClass">别名</span>
          <input v-model="form.alias" :class="inputClass" required />
        </label>
        <div class="grid gap-4 md:grid-cols-2">
          <label class="grid gap-2">
            <span :class="labelClass">当前密码</span>
            <input
              v-model="form.current_password"
              :class="inputClass"
              type="password"
              placeholder="修改密码时填写"
            />
          </label>
          <label class="grid gap-2">
            <span :class="labelClass">新密码</span>
            <input
              v-model="form.new_password"
              :class="inputClass"
              type="password"
              placeholder="至少 6 位"
            />
          </label>
        </div>
        <div v-if="error" :class="alertClass.danger">
          {{ error }}
        </div>
        <div v-if="message" :class="alertClass.success">
          {{ message }}
        </div>
        <Button class="w-fit" :disabled="saving" type="submit">
          <Save class="size-4" />
          {{ saving ? '保存中' : '保存设置' }}
        </Button>
      </div>
    </form>

    <section :class="[cardClass, 'overflow-hidden lg:col-span-2']">
      <div :class="sectionHeaderClass">
        <div class="flex items-center gap-2">
          <h2 class="font-semibold">邮箱验证</h2>
          <span :class="toneClass(emailVerified ? 'success' : 'warning')">
            {{ emailVerified ? '已验证' : '待验证' }}
          </span>
        </div>
      </div>
      <div class="grid gap-4 p-4">
        <label class="grid gap-2">
          <span :class="labelClass">邮箱</span>
          <input
            v-model.trim="emailForm.email"
            :class="inputClass"
            type="email"
            placeholder="用于审批与打卡通知"
          />
        </label>
        <div class="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto]">
          <label class="grid gap-2">
            <span :class="labelClass">验证码</span>
            <input
              v-model.trim="emailForm.code"
              :class="inputClass"
              inputmode="numeric"
              placeholder="请输入邮箱验证码"
            />
          </label>
          <div class="flex items-end gap-2">
            <Button
              variant="outline"
              type="button"
              :disabled="sendingCode || !emailForm.email"
              @click="requestEmailCode"
            >
              <Send class="size-4" :class="{ 'animate-spin': sendingCode }" />
              发送验证码
            </Button>
            <Button
              type="button"
              :disabled="verifyingEmail || !emailForm.code"
              @click="verifyEmail"
            >
              <MailCheck class="size-4" :class="{ 'animate-spin': verifyingEmail }" />
              验证
            </Button>
          </div>
        </div>
        <div v-if="emailMessage" :class="alertClass.success">
          {{ emailMessage }}
        </div>
      </div>
    </section>

    <aside :class="[cardClass, 'h-fit overflow-hidden']">
      <div
        class="grid gap-2 border-b px-4 py-3"
        :class="
          token?.is_valid
            ? 'border-[var(--tone-success-border)] bg-[var(--tone-success-bg)]'
            : 'border-[var(--tone-danger-border)] bg-[var(--tone-danger-bg)]'
        "
      >
        <div class="flex items-center justify-between gap-2">
          <h2 class="font-semibold">授权状态</h2>
          <span :class="toneClass(token?.is_valid ? 'success' : 'danger')">{{
            token?.is_valid ? '可用' : '不可用'
          }}</span>
        </div>
      </div>
      <div class="p-4">
        <div class="grid gap-3 text-sm">
          <div class="flex items-center justify-between">
            <span class="text-muted-foreground">状态</span>
            <span :class="toneClass(token?.is_valid ? 'success' : 'danger')">{{
              token?.is_valid ? '可用' : '不可用'
            }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-muted-foreground">即将过期</span>
            <span>{{ token?.expiring_soon ? '是' : '否' }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-muted-foreground">剩余天数</span>
            <span>{{ token?.days_until_expiry ?? '未知' }}</span>
          </div>
        </div>
      </div>
    </aside>
  </div>
</template>
