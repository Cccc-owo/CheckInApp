<script setup lang="ts">
import { Mail, RefreshCw, Save } from 'lucide-vue-next'
import { computed, onMounted, reactive, ref } from 'vue'
import { adminApi, type EmailNotificationSettings } from '@/api'
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
import { extractErrorMessage, formatFullDateTime } from '@/utils/format'

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const savedMessage = ref('')
const settings = ref<EmailNotificationSettings | null>(null)
const form = reactive({
  smtp_server: '',
  smtp_port: 465,
  smtp_sender_email: '',
  smtp_sender_password: '',
  clear_smtp_sender_password: false,
  smtp_use_ssl: true,
  notify_token_expiring: true,
  notify_check_in_success: true,
  require_admin_approval_for_registration: true,
  require_verified_email_for_approval: true,
})

const passwordState = computed(() => {
  if (form.clear_smtp_sender_password) return '保存后清空'
  if (form.smtp_sender_password) return '保存后替换'
  if (settings.value?.has_smtp_sender_password) return '已保存'
  return '未设置'
})

function hydrate(next: EmailNotificationSettings) {
  settings.value = next
  form.smtp_server = next.smtp_server
  form.smtp_port = next.smtp_port
  form.smtp_sender_email = next.smtp_sender_email
  form.smtp_sender_password = ''
  form.clear_smtp_sender_password = false
  form.smtp_use_ssl = next.smtp_use_ssl
  form.notify_token_expiring = next.notify_token_expiring
  form.notify_check_in_success = next.notify_check_in_success
  form.require_admin_approval_for_registration = next.require_admin_approval_for_registration
  form.require_verified_email_for_approval = next.require_verified_email_for_approval
}

async function load() {
  loading.value = true
  error.value = ''
  savedMessage.value = ''
  try {
    hydrate(await adminApi.emailSettings())
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!form.require_admin_approval_for_registration) {
    const ok = window.confirm(
      '关闭管理员审批后，新注册用户可能绕过人工审核直接进入系统。确认关闭管理员审批？',
    )
    if (!ok) return
  }
  saving.value = true
  error.value = ''
  savedMessage.value = ''
  try {
    const next = await adminApi.updateEmailSettings({
      smtp_server: form.smtp_server,
      smtp_port: form.smtp_port,
      smtp_sender_email: form.smtp_sender_email,
      smtp_use_ssl: form.smtp_use_ssl,
      notify_token_expiring: form.notify_token_expiring,
      notify_check_in_success: form.notify_check_in_success,
      require_admin_approval_for_registration: form.require_admin_approval_for_registration,
      require_verified_email_for_approval: form.require_verified_email_for_approval,
      smtp_sender_password: form.smtp_sender_password || undefined,
      clear_smtp_sender_password: form.clear_smtp_sender_password,
    })
    hydrate(next)
    savedMessage.value = '邮件设置已保存'
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <StateBlock v-if="loading" title="正在加载邮件设置" type="loading" />
  <StateBlock
    v-else-if="error && !settings"
    title="邮件设置加载失败"
    :description="error"
    type="error"
    action-label="重试"
    @action="load"
  />
  <form v-else class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]" @submit.prevent="save">
    <section :class="[cardClass, 'min-w-0 overflow-hidden']">
      <div :class="sectionHeaderClass">
        <div>
          <h2 class="font-semibold">SMTP 配置</h2>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <span :class="toneClass(settings?.has_smtp_sender_password ? 'success' : 'warning')">
            密码{{ passwordState }}
          </span>
          <Button variant="outline" type="button" :disabled="saving" @click="load">
            <RefreshCw class="size-4" />
            刷新
          </Button>
          <Button type="submit" :disabled="saving">
            <Save class="size-4" />
            {{ saving ? '保存中' : '保存' }}
          </Button>
        </div>
      </div>

      <div class="grid gap-4 p-4 md:grid-cols-2">
        <label class="grid gap-2 md:col-span-2">
          <span :class="labelClass">SMTP SERVER</span>
          <input
            v-model.trim="form.smtp_server"
            :class="inputClass"
            maxlength="255"
            placeholder="smtp.example.com"
          />
        </label>
        <label class="grid gap-2">
          <span :class="labelClass">SMTP PORT</span>
          <input
            v-model.number="form.smtp_port"
            :class="inputClass"
            type="number"
            min="1"
            max="65535"
            required
          />
        </label>
        <label class="grid gap-2">
          <span :class="labelClass">发件邮箱</span>
          <input
            v-model.trim="form.smtp_sender_email"
            :class="inputClass"
            type="email"
            maxlength="255"
            placeholder="mailer@example.com"
          />
        </label>
        <label class="grid gap-2 md:col-span-2">
          <span :class="labelClass">SMTP 密码</span>
          <input
            v-model="form.smtp_sender_password"
            :class="inputClass"
            type="password"
            autocomplete="new-password"
            maxlength="500"
            placeholder="留空则保持现有密码"
            :disabled="form.clear_smtp_sender_password"
          />
        </label>

        <div
          class="grid gap-3 rounded-lg border border-border bg-background p-3 md:col-span-2 sm:grid-cols-2"
        >
          <label class="flex items-center gap-3 text-sm font-medium">
            <input v-model="form.smtp_use_ssl" type="checkbox" class="size-4 accent-primary" />
            使用 SSL 连接 SMTP
          </label>
          <label class="flex items-center gap-3 text-sm font-medium">
            <input
              v-model="form.clear_smtp_sender_password"
              type="checkbox"
              class="size-4 accent-primary"
              :disabled="Boolean(form.smtp_sender_password)"
            />
            保存时清空 SMTP 密码
          </label>
        </div>
      </div>
    </section>

    <aside :class="[cardClass, 'grid h-fit gap-4 overflow-hidden xl:sticky xl:top-20']">
      <div class="border-b border-border bg-muted/55 px-4 py-3">
        <div class="flex items-center gap-2">
          <Mail class="size-4 text-muted-foreground" />
          <h2 class="font-semibold">通知策略</h2>
        </div>
      </div>

      <div class="grid gap-4 p-4">
        <label class="grid gap-2 rounded-lg border border-border bg-background p-3">
          <span class="flex items-center justify-between gap-3 text-sm font-medium">
            Token 即将过期提醒
            <input
              v-model="form.notify_token_expiring"
              type="checkbox"
              class="size-4 accent-primary"
            />
          </span>
          <span class="text-sm text-muted-foreground">只影响过期前提醒，不影响已过期通知。</span>
        </label>

        <label class="grid gap-2 rounded-lg border border-border bg-background p-3">
          <span class="flex items-center justify-between gap-3 text-sm font-medium">
            管理员审批
            <input
              v-model="form.require_admin_approval_for_registration"
              type="checkbox"
              class="size-4 accent-primary"
            />
          </span>
          <span class="text-sm text-muted-foreground"
            >默认开启。关闭管理员审批会让新注册用户绕过人工审核。</span
          >
        </label>

        <label class="grid gap-2 rounded-lg border border-border bg-background p-3">
          <span class="flex items-center justify-between gap-3 text-sm font-medium">
            审批前要求验证邮箱
            <input
              v-model="form.require_verified_email_for_approval"
              type="checkbox"
              class="size-4 accent-primary"
            />
          </span>
          <span class="text-sm text-muted-foreground"
            >开启后，管理员审批未验证邮箱用户时每次都需要确认覆盖。</span
          >
        </label>

        <label class="grid gap-2 rounded-lg border border-border bg-background p-3">
          <span class="flex items-center justify-between gap-3 text-sm font-medium">
            打卡成功通知
            <input
              v-model="form.notify_check_in_success"
              type="checkbox"
              class="size-4 accent-primary"
            />
          </span>
          <span class="text-sm text-muted-foreground"
            >关闭后仅跳过成功邮件，失败邮件仍会发送。</span
          >
        </label>

        <div v-if="settings?.updated_at" class="text-sm text-muted-foreground">
          上次保存：{{ formatFullDateTime(settings.updated_at) }}
        </div>

        <div v-if="savedMessage" :class="alertClass.success">{{ savedMessage }}</div>
        <div v-if="error" :class="alertClass.danger">{{ error }}</div>
      </div>
    </aside>
  </form>
</template>
