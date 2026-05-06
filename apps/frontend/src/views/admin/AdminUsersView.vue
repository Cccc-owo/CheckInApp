<script setup lang="ts">
import { Check, Save, Search, Trash2, UserPlus } from 'lucide-vue-next'
import { onMounted, reactive, ref } from 'vue'
import { adminApi, userApi, type AdminApprovalResponse, type User } from '@/api'
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
import { extractErrorMessage, formatDateTime } from '@/utils/format'
import { formatUserAuthorizationSummary } from '../dashboard-license'

const loading = ref(true)
const error = ref('')
const users = ref<User[]>([])
const search = ref('')
const editingId = ref<number | 'new' | null>(null)
const form = reactive({
  alias: '',
  email: '',
  role: 'user',
  password: '',
  is_approved: true,
})

function requiresUnverifiedEmailOverride(
  result: User | AdminApprovalResponse,
): result is AdminApprovalResponse {
  return 'requires_override' in result && result.warning_code === 'UNVERIFIED_EMAIL'
}

function userAuthorizationSummary(user: User) {
  return formatUserAuthorizationSummary(user.jwt_exp)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    users.value = await userApi.list(search.value ? { search: search.value } : {})
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

async function approve(userId: number) {
  const result = await adminApi.approveUser(userId)
  if (requiresUnverifiedEmailOverride(result)) {
    const ok = window.confirm('邮箱未验证，审批后不会发送审批通知。确认无视邮箱条件继续审批？')
    if (!ok) return
    await adminApi.approveUser(userId, { allow_unverified_email: true })
  }
  await load()
}

async function reject(userId: number) {
  if (!window.confirm('确认拒绝并删除该用户？')) return
  await adminApi.rejectUser(userId)
  await load()
}

function startCreate() {
  editingId.value = 'new'
  form.alias = ''
  form.email = ''
  form.role = 'user'
  form.password = ''
  form.is_approved = true
}

function startEdit(user: User) {
  editingId.value = user.id
  form.alias = user.alias
  form.email = user.email ?? ''
  form.role = user.role
  form.password = ''
  form.is_approved = user.is_approved
}

async function save() {
  error.value = ''
  try {
    const payload = {
      alias: form.alias,
      email: form.email || undefined,
      role: form.role,
      is_approved: form.is_approved,
      password: form.password || undefined,
    }
    if (editingId.value === 'new') {
      await userApi.create(payload)
    } else if (typeof editingId.value === 'number') {
      const result = await userApi.update(editingId.value, payload)
      if (requiresUnverifiedEmailOverride(result)) {
        const ok = window.confirm('邮箱未验证，审批后不会发送审批通知。确认无视邮箱条件继续审批？')
        if (!ok) return
        await userApi.update(editingId.value, { ...payload, allow_unverified_email: true })
      }
    }
    editingId.value = null
    await load()
  } catch (err) {
    error.value = extractErrorMessage(err)
  }
}

onMounted(load)
</script>

<template>
  <div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px] xl:items-start">
    <section :class="[cardClass, 'min-w-0 overflow-hidden']">
      <div :class="sectionHeaderClass">
        <div>
          <h2 class="font-semibold">用户审批与管理</h2>
        </div>
        <span :class="toneClass(users.some((user) => !user.is_approved) ? 'warning' : 'success')">
          {{ users.filter((user) => !user.is_approved).length }} 个待审批
        </span>
      </div>
      <div
        class="grid gap-3 border-b border-border bg-muted/55 p-4 sm:grid-cols-[minmax(0,1fr)_auto_auto]"
      >
        <input v-model="search" :class="inputClass" class="max-w-sm" placeholder="搜索别名" />
        <Button variant="outline" type="button" @click="load">
          <Search class="size-4" />
          搜索
        </Button>
        <Button type="button" @click="startCreate">
          <UserPlus class="size-4" />
          创建用户
        </Button>
      </div>
      <StateBlock v-if="loading" title="正在加载用户" type="loading" />
      <StateBlock
        v-else-if="error && users.length === 0"
        title="用户加载失败"
        :description="error"
        type="error"
        action-label="重试"
        @action="load"
      />
      <StateBlock v-else-if="users.length === 0" title="暂无用户" />
      <div v-else class="divide-y divide-border">
        <article
          v-for="user in users"
          :key="user.id"
          class="flex flex-wrap items-center justify-between gap-3 p-3 sm:p-4"
        >
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <h3 class="truncate font-semibold">{{ user.alias }}</h3>
              <span :class="toneClass(user.is_approved ? 'success' : 'warning')">{{
                user.is_approved ? '已审批' : '待审批'
              }}</span>
              <span :class="toneClass(user.role === 'admin' ? 'info' : 'neutral')">{{
                user.role
              }}</span>
            </div>
            <div class="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-sm text-muted-foreground">
              <span>{{ user.email || '未设置邮箱' }}</span>
              <span>{{ user.email_verified ? '邮箱已验证' : '邮箱未验证' }}</span>
              <span :class="toneClass(userAuthorizationSummary(user).tone)">{{
                userAuthorizationSummary(user).label
              }}</span>
              <span>{{ formatDateTime(user.created_at) }}</span>
            </div>
          </div>
          <div class="flex flex-wrap gap-2">
            <Button v-if="!user.is_approved" type="button" @click="approve(user.id)">
              <Check class="size-4" />
              审批
            </Button>
            <Button variant="danger" type="button" @click="reject(user.id)">
              <Trash2 class="size-4" />
              删除
            </Button>
            <Button variant="outline" type="button" @click="startEdit(user)">
              <UserPlus class="size-4" />
              编辑
            </Button>
          </div>
        </article>
      </div>
    </section>

    <aside
      v-if="!editingId"
      :class="[
        cardClass,
        'grid h-fit min-h-72 min-w-0 place-items-center border-dashed p-6 text-center xl:sticky xl:top-20',
      ]"
    >
      <div class="grid justify-items-center gap-4">
        <span
          class="inline-flex size-12 items-center justify-center rounded-xl border border-[var(--tone-success-border)] bg-[var(--tone-success-bg)] text-[var(--tone-success-fg)]"
        >
          <UserPlus class="size-5" />
        </span>
        <div class="grid gap-1">
          <h2 class="font-semibold">未选择用户</h2>
          <p class="text-sm text-muted-foreground">创建或从列表编辑</p>
        </div>
        <Button type="button" @click="startCreate">
          <UserPlus class="size-4" />
          创建用户
        </Button>
      </div>
    </aside>

    <form
      v-else
      :class="[
        cardClass,
        'grid h-fit min-w-0 gap-4 overflow-hidden xl:sticky xl:top-20 xl:self-start',
      ]"
      @submit.prevent="save"
    >
      <div class="border-b border-border bg-muted/55 px-4 py-3">
        <h2 class="font-semibold">{{ editingId === 'new' ? '创建用户' : '编辑用户' }}</h2>
      </div>
      <div class="grid gap-4 p-4">
        <label class="grid gap-2">
          <span :class="labelClass">别名</span>
          <input v-model="form.alias" :class="inputClass" required />
        </label>
        <label class="grid gap-2">
          <span :class="labelClass">邮箱</span>
          <input v-model="form.email" :class="inputClass" type="email" />
        </label>
        <label class="grid gap-2">
          <span :class="labelClass">角色</span>
          <select v-model="form.role" :class="inputClass">
            <option value="user">user</option>
            <option value="admin">admin</option>
          </select>
        </label>
        <label class="grid gap-2">
          <span :class="labelClass">密码</span>
          <input
            v-model="form.password"
            :class="inputClass"
            type="password"
            placeholder="留空不修改"
          />
        </label>
        <label class="flex items-center gap-2 text-sm">
          <input v-model="form.is_approved" type="checkbox" />
          已审批
        </label>
        <div v-if="error" :class="alertClass.danger">
          {{ error }}
        </div>
        <div class="flex gap-2">
          <Button type="submit">
            <Save class="size-4" />
            保存
          </Button>
          <Button variant="outline" type="button" @click="editingId = null"> 取消 </Button>
        </div>
      </div>
    </form>
  </div>
</template>
