<script setup lang="ts">
import { Check, Edit3, Play, Plus, RefreshCw, Trash2 } from 'lucide-vue-next'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  checkInApi,
  taskApi,
  templateApi,
  type CheckInRecordStatus,
  type Task,
  type Template,
  type TemplateFieldConfigItem,
  type TemplatePreview,
} from '@/api'
import { useRouter } from '@/app/router'
import StateBlock from '@/components/StateBlock.vue'
import {
  buttonBase,
  buttonTone,
  cardClass,
  inputClass,
  textareaClass,
  toneClass,
} from '@/components/ui'
import {
  cronLabel,
  extractErrorMessage,
  parseJson,
  statusLabel,
  statusTone,
  stringifyJson,
} from '@/utils/format'

const router = useRouter()
const loading = ref(true)
const error = ref('')
const message = ref('')
const tasks = ref<Task[]>([])
const templates = ref<Template[]>([])
const selectedTemplateId = ref<number | null>(null)
const preview = ref<TemplatePreview | null>(null)
const creating = ref(false)
const actionId = ref<number | null>(null)
const polling = ref<Record<number, CheckInRecordStatus>>({})
const editingTaskId = ref<number | null>(null)
let pollTimer: number | undefined

const createForm = reactive({
  task_name: '',
  thread_id: '',
  cron_expression: '0 20 * * *',
  field_values: {} as Record<string, string>,
})

const editForm = reactive({
  name: '',
  cron_expression: '',
  payload_config: '',
})

const fieldEntries = computed(() => {
  const config = preview.value?.field_config
  if (!config) return []
  const items: Array<[string, TemplateFieldConfigItem]> = []
  if (config.signature) items.push(['signature', config.signature])
  if (config.texts) items.push(['texts', config.texts])
  Object.entries(config.values ?? {}).forEach(([key, value]) => items.push([key, value]))
  return items.filter(([, field]) => field && !field.hidden)
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [taskList, templateList] = await Promise.all([taskApi.list(), templateApi.active()])
    tasks.value = taskList
    templates.value = templateList
    if (!selectedTemplateId.value && templateList[0]) selectedTemplateId.value = templateList[0].id
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

watch(selectedTemplateId, async (id) => {
  preview.value = null
  createForm.field_values = {}
  if (!id) return
  try {
    preview.value = await templateApi.preview(id)
    fieldEntries.value.forEach(([key, field]) => {
      createForm.field_values[key] = field?.default_value ?? ''
    })
  } catch (err) {
    error.value = extractErrorMessage(err)
  }
})

async function createTask() {
  if (!selectedTemplateId.value) return
  creating.value = true
  error.value = ''
  message.value = ''
  try {
    await templateApi.createTask({
      template_id: selectedTemplateId.value,
      thread_id: createForm.thread_id,
      task_name: createForm.task_name || undefined,
      cron_expression: createForm.cron_expression || null,
      field_values: createForm.field_values,
    })
    createForm.task_name = ''
    createForm.thread_id = ''
    message.value = '任务已创建'
    await load()
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    creating.value = false
  }
}

function startEdit(task: Task) {
  editingTaskId.value = task.id
  editForm.name = task.name ?? ''
  editForm.cron_expression = task.cron_expression ?? ''
  editForm.payload_config = stringifyJson(parseJson(task.payload_config))
}

async function saveEdit(taskId: number) {
  actionId.value = taskId
  error.value = ''
  try {
    JSON.parse(editForm.payload_config)
    await taskApi.update(taskId, {
      name: editForm.name,
      cron_expression: editForm.cron_expression || null,
      payload_config: editForm.payload_config,
    })
    editingTaskId.value = null
    await load()
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    actionId.value = null
  }
}

async function toggleTask(task: Task) {
  actionId.value = task.id
  try {
    await taskApi.toggle(task.id)
    await load()
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    actionId.value = null
  }
}

async function deleteTask(task: Task) {
  if (!window.confirm(`确认删除任务「${task.name || task.id}」？关联记录也会删除。`)) return
  actionId.value = task.id
  try {
    await taskApi.delete(task.id)
    await load()
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    actionId.value = null
  }
}

async function manualCheckIn(task: Task) {
  actionId.value = task.id
  error.value = ''
  try {
    const result = await checkInApi.manual(task.id)
    const recordId = result.record_id ?? result.id
    if (recordId) startRecordPolling(recordId)
    message.value = result.message || '已启动打卡任务'
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    actionId.value = null
  }
}

function startRecordPolling(recordId: number) {
  window.clearInterval(pollTimer)
  pollTimer = window.setInterval(async () => {
    try {
      const status = await checkInApi.status(recordId)
      polling.value = { ...polling.value, [recordId]: status }
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
  <div class="grid gap-5">
    <section :class="[cardClass, 'p-5']">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 class="font-semibold">从模板创建任务</h2>
          <p class="mt-1 text-sm text-zinc-500">选择启用模板，填写接龙 ID 和字段值后创建任务。</p>
        </div>
        <button :class="[buttonBase, buttonTone.secondary]" type="button" @click="load">
          <RefreshCw class="size-4" />
          刷新
        </button>
      </div>

      <form class="mt-4 grid gap-4" @submit.prevent="createTask">
        <div class="grid gap-4 md:grid-cols-3">
          <label class="grid gap-2">
            <span class="text-xs font-semibold text-zinc-500">模板</span>
            <select v-model.number="selectedTemplateId" :class="inputClass">
              <option v-for="template in templates" :key="template.id" :value="template.id">
                {{ template.name }}
              </option>
            </select>
          </label>
          <label class="grid gap-2">
            <span class="text-xs font-semibold text-zinc-500">任务名称</span>
            <input v-model="createForm.task_name" :class="inputClass" placeholder="可选" />
          </label>
          <label class="grid gap-2">
            <span class="text-xs font-semibold text-zinc-500">接龙 ThreadId</span>
            <input v-model="createForm.thread_id" :class="inputClass" required />
          </label>
        </div>
        <label class="grid gap-2 md:max-w-xs">
          <span class="text-xs font-semibold text-zinc-500">Cron 表达式</span>
          <input
            v-model="createForm.cron_expression"
            :class="inputClass"
            placeholder="0 20 * * *"
          />
        </label>
        <div v-if="fieldEntries.length" class="grid gap-4 md:grid-cols-2">
          <label v-for="[key, field] in fieldEntries" :key="key" class="grid gap-2">
            <span class="text-xs font-semibold text-zinc-500">{{
              field?.display_name ?? key
            }}</span>
            <select
              v-if="field?.field_type === 'select'"
              v-model="createForm.field_values[key]"
              :class="inputClass"
              :required="field.required"
            >
              <option
                v-for="option in field.options ?? []"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
            <textarea
              v-else-if="field?.field_type === 'textarea'"
              v-model="createForm.field_values[key]"
              :class="textareaClass"
              :placeholder="field.placeholder ?? ''"
              :required="field.required"
            />
            <input
              v-else
              v-model="createForm.field_values[key]"
              :class="inputClass"
              :type="field?.field_type === 'number' ? 'number' : 'text'"
              :placeholder="field?.placeholder ?? ''"
              :required="field?.required"
            />
          </label>
        </div>
        <div
          v-if="error"
          class="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700"
        >
          {{ error }}
        </div>
        <div
          v-if="message"
          class="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700"
        >
          {{ message }}
        </div>
        <button
          :class="[buttonBase, buttonTone.primary, 'w-fit']"
          :disabled="creating || !selectedTemplateId || !createForm.thread_id"
          type="submit"
        >
          <Plus class="size-4" />
          {{ creating ? '创建中' : '创建任务' }}
        </button>
      </form>
    </section>

    <StateBlock v-if="loading" title="正在加载任务" type="loading" />
    <StateBlock
      v-else-if="error && tasks.length === 0"
      title="任务加载失败"
      :description="error"
      type="error"
      action-label="重试"
      @action="load"
    />
    <StateBlock
      v-else-if="tasks.length === 0"
      title="暂无任务"
      description="先从模板创建一个任务。"
    />
    <section v-else :class="[cardClass, 'overflow-hidden']">
      <div class="border-b border-zinc-200 px-4 py-3">
        <h2 class="font-semibold">任务列表</h2>
      </div>
      <div class="divide-y divide-zinc-200">
        <article v-for="task in tasks" :key="task.id" class="p-4">
          <div class="grid gap-3 lg:grid-cols-[1fr_auto]">
            <div>
              <div class="flex flex-wrap items-center gap-2">
                <h3 class="font-semibold">{{ task.name || `任务 #${task.id}` }}</h3>
                <span :class="toneClass(task.is_active ? 'success' : 'neutral')">{{
                  task.is_active ? '启用' : '停用'
                }}</span>
                <span
                  v-if="task.last_check_in_status"
                  :class="toneClass(statusTone(task.last_check_in_status))"
                >
                  {{ statusLabel(task.last_check_in_status) }}
                </span>
              </div>
              <p class="mt-1 text-sm text-zinc-500">
                ThreadId: {{ task.thread_id || '未解析' }} · {{ cronLabel(task.cron_expression) }}
              </p>
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                :class="[buttonBase, buttonTone.secondary]"
                type="button"
                @click="router.navigate(`/tasks/${task.id}/records`)"
              >
                记录
              </button>
              <button
                :class="[buttonBase, buttonTone.secondary]"
                :disabled="actionId === task.id"
                type="button"
                @click="manualCheckIn(task)"
              >
                <Play class="size-4" />
                打卡
              </button>
              <button
                :class="[buttonBase, buttonTone.secondary]"
                :disabled="actionId === task.id"
                type="button"
                @click="toggleTask(task)"
              >
                <Check class="size-4" />
                {{ task.is_active ? '停用' : '启用' }}
              </button>
              <button
                :class="[buttonBase, buttonTone.ghost]"
                type="button"
                @click="startEdit(task)"
              >
                <Edit3 class="size-4" />
                编辑
              </button>
              <button
                :class="[buttonBase, buttonTone.danger]"
                :disabled="actionId === task.id"
                type="button"
                @click="deleteTask(task)"
              >
                <Trash2 class="size-4" />
                删除
              </button>
            </div>
          </div>

          <form
            v-if="editingTaskId === task.id"
            class="mt-4 grid gap-3 rounded-lg border border-zinc-200 bg-zinc-50 p-4"
            @submit.prevent="saveEdit(task.id)"
          >
            <div class="grid gap-3 md:grid-cols-2">
              <label class="grid gap-2">
                <span class="text-xs font-semibold text-zinc-500">任务名称</span>
                <input v-model="editForm.name" :class="inputClass" />
              </label>
              <label class="grid gap-2">
                <span class="text-xs font-semibold text-zinc-500">Cron</span>
                <input v-model="editForm.cron_expression" :class="inputClass" />
              </label>
            </div>
            <label class="grid gap-2">
              <span class="text-xs font-semibold text-zinc-500">Payload JSON</span>
              <textarea v-model="editForm.payload_config" :class="textareaClass" />
            </label>
            <div class="flex gap-2">
              <button :class="[buttonBase, buttonTone.primary]" type="submit">保存</button>
              <button
                :class="[buttonBase, buttonTone.secondary]"
                type="button"
                @click="editingTaskId = null"
              >
                取消
              </button>
            </div>
          </form>
        </article>
      </div>
    </section>
  </div>
</template>
