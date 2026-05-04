<script setup lang="ts">
import { Save } from 'lucide-vue-next'
import { onMounted, reactive, ref } from 'vue'
import { userApi, type TokenStatus } from '@/api'
import { useAuth } from '@/app/auth'
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
import { extractErrorMessage } from '@/utils/format'

const auth = useAuth()
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const message = ref('')
const token = ref<TokenStatus | null>(null)
const form = reactive({
  alias: '',
  email: '',
  current_password: '',
  new_password: '',
})

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
    form.email = user.email ?? ''
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
      email: form.email || undefined,
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
          <span class="text-xs font-semibold text-zinc-500 dark:text-zinc-400">别名</span>
          <input v-model="form.alias" :class="inputClass" required />
        </label>
        <label class="grid gap-2">
          <span class="text-xs font-semibold text-zinc-500 dark:text-zinc-400">邮箱</span>
          <input v-model="form.email" :class="inputClass" type="email" placeholder="用于打卡通知" />
        </label>
        <div class="grid gap-4 md:grid-cols-2">
          <label class="grid gap-2">
            <span class="text-xs font-semibold text-zinc-500 dark:text-zinc-400">当前密码</span>
            <input
              v-model="form.current_password"
              :class="inputClass"
              type="password"
              placeholder="修改密码时填写"
            />
          </label>
          <label class="grid gap-2">
            <span class="text-xs font-semibold text-zinc-500 dark:text-zinc-400">新密码</span>
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
        <button :class="[buttonBase, buttonTone.primary, 'w-fit']" :disabled="saving" type="submit">
          <Save class="size-4" />
          {{ saving ? '保存中' : '保存设置' }}
        </button>
      </div>
    </form>

    <aside :class="[cardClass, 'h-fit overflow-hidden']">
      <div
        class="grid gap-2 border-b px-4 py-3"
        :class="
          token?.is_valid
            ? 'border-emerald-200 bg-emerald-50/70 dark:border-emerald-900/70 dark:bg-emerald-950/30'
            : 'border-rose-200 bg-rose-50/70 dark:border-rose-900/70 dark:bg-rose-950/30'
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
            <span class="text-zinc-500">状态</span>
            <span :class="toneClass(token?.is_valid ? 'success' : 'danger')">{{
              token?.is_valid ? '可用' : '不可用'
            }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-zinc-500">即将过期</span>
            <span>{{ token?.expiring_soon ? '是' : '否' }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-zinc-500">剩余天数</span>
            <span>{{ token?.days_until_expiry ?? '未知' }}</span>
          </div>
        </div>
      </div>
    </aside>
  </div>
</template>
