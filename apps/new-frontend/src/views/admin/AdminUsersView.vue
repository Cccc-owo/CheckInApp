<script setup lang="ts">
import { Check, Save, Search, Trash2, UserPlus } from 'lucide-vue-next'
import { onMounted, reactive, ref } from 'vue'
import { adminApi, userApi, type User } from '@/api'
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
import { Button } from '@/components/ui/button'
import { extractErrorMessage, formatDateTime } from '@/utils/format'

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
  await adminApi.approveUser(userId)
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
      await userApi.update(editingId.value, payload)
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
        class="grid gap-3 border-b border-zinc-200 bg-zinc-50/70 p-4 sm:grid-cols-[minmax(0,1fr)_auto_auto] dark:border-zinc-800 dark:bg-zinc-950/50"
      >
        <input v-model="search" :class="inputClass" class="max-w-sm" placeholder="搜索别名" />
        <button :class="[buttonBase, buttonTone.secondary]" type="button" @click="load">
          <Search class="size-4" />
          搜索
        </button>
        <button :class="[buttonBase, buttonTone.primary]" type="button" @click="startCreate">
          <UserPlus class="size-4" />
          创建用户
        </button>
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
      <div v-else class="divide-y divide-zinc-200 dark:divide-zinc-800">
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
            <div
              class="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-sm text-zinc-500 dark:text-zinc-400"
            >
              <span>{{ user.email || '未设置邮箱' }}</span>
              <span>{{ formatDateTime(user.created_at) }}</span>
            </div>
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              v-if="!user.is_approved"
              :class="[buttonBase, buttonTone.primary]"
              type="button"
              @click="approve(user.id)"
            >
              <Check class="size-4" />
              审批
            </button>
            <button :class="[buttonBase, buttonTone.danger]" type="button" @click="reject(user.id)">
              <Trash2 class="size-4" />
              删除
            </button>
            <button
              :class="[buttonBase, buttonTone.secondary]"
              type="button"
              @click="startEdit(user)"
            >
              <UserPlus class="size-4" />
              编辑
            </button>
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
          class="inline-flex size-12 items-center justify-center rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/50 dark:text-emerald-300"
        >
          <UserPlus class="size-5" />
        </span>
        <div class="grid gap-1">
          <h2 class="font-semibold">未选择用户</h2>
          <p class="text-sm text-zinc-500 dark:text-zinc-400">创建或从列表编辑</p>
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
      <div
        class="border-b border-zinc-200 bg-zinc-50/70 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950/50"
      >
        <h2 class="font-semibold">{{ editingId === 'new' ? '创建用户' : '编辑用户' }}</h2>
      </div>
      <div class="grid gap-4 p-4">
        <label class="grid gap-2">
          <span class="text-xs font-semibold text-zinc-500 dark:text-zinc-400">别名</span>
          <input v-model="form.alias" :class="inputClass" required />
        </label>
        <label class="grid gap-2">
          <span class="text-xs font-semibold text-zinc-500 dark:text-zinc-400">邮箱</span>
          <input v-model="form.email" :class="inputClass" type="email" />
        </label>
        <label class="grid gap-2">
          <span class="text-xs font-semibold text-zinc-500 dark:text-zinc-400">角色</span>
          <select v-model="form.role" :class="inputClass">
            <option value="user">user</option>
            <option value="admin">admin</option>
          </select>
        </label>
        <label class="grid gap-2">
          <span class="text-xs font-semibold text-zinc-500 dark:text-zinc-400">密码</span>
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
          <button :class="[buttonBase, buttonTone.primary]" type="submit">
            <Save class="size-4" />
            保存
          </button>
          <button
            :class="[buttonBase, buttonTone.secondary]"
            type="button"
            @click="editingId = null"
          >
            取消
          </button>
        </div>
      </div>
    </form>
  </div>
</template>
