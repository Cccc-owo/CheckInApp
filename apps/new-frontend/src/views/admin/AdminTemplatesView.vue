<script setup lang="ts">
import { Eye, Plus, Save, Trash2 } from 'lucide-vue-next'
import { computed, onMounted, reactive, ref } from 'vue'
import { templateApi, type Template, type TemplatePreview } from '@/api'
import StateBlock from '@/components/StateBlock.vue'
import TemplateConfigEditor from '@/components/templates/TemplateConfigEditor.vue'
import {
  buildTemplatePreviewPayload,
  parseTemplateFieldConfig,
  validateFieldConfig,
} from '@/components/templates/template-config'
import {
  alertClass,
  buttonBase,
  buttonTone,
  cardClass,
  inputClass,
  sectionHeaderClass,
  toneClass,
} from '@/components/ui'
import { extractErrorMessage, formatDateTime, stringifyJson } from '@/utils/format'

const loading = ref(true)
const error = ref('')
const message = ref('')
const templates = ref<Template[]>([])
const editingId = ref<number | 'new' | null>(null)
const preview = ref<TemplatePreview | null>(null)
const editorValid = ref(true)
const form = reactive({
  name: '',
  description: '',
  field_config:
    '{\n  "signature": {\n    "display_name": "姓名",\n    "field_type": "text",\n    "default_value": "",\n    "required": true\n  }\n}',
  is_active: true,
})

const localPreviewPayload = computed(() => {
  const result = parseTemplateFieldConfig(form.field_config)
  if (!result.ok) return null
  return buildTemplatePreviewPayload(result.config)
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    templates.value = await templateApi.list()
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

function startCreate() {
  editingId.value = 'new'
  preview.value = null
  form.name = ''
  form.description = ''
  form.field_config =
    '{\n  "signature": {\n    "display_name": "姓名",\n    "field_type": "text",\n    "default_value": "",\n    "required": true\n  }\n}'
  form.is_active = true
}

function startEdit(template: Template) {
  editingId.value = template.id
  preview.value = null
  form.name = template.name
  form.description = template.description ?? ''
  try {
    form.field_config = stringifyJson(JSON.parse(template.field_config))
  } catch {
    form.field_config = template.field_config
  }
  form.is_active = template.is_active
}

async function save() {
  error.value = ''
  message.value = ''
  try {
    const parsed = parseTemplateFieldConfig(form.field_config)
    if (!parsed.ok) throw new Error(parsed.message || '字段配置无效')
    const validation = validateFieldConfig(parsed.config)
    if (!validation.ok) throw new Error(validation.message || '字段配置无效')
    const payload = {
      name: form.name,
      description: form.description || null,
      field_config: form.field_config,
      is_active: form.is_active,
    }
    if (editingId.value === 'new') {
      await templateApi.create(payload)
    } else if (typeof editingId.value === 'number') {
      await templateApi.update(editingId.value, payload)
    }
    editingId.value = null
    message.value = '模板已保存'
    await load()
  } catch (err) {
    error.value = extractErrorMessage(err)
  }
}

async function showPreview(template: Template) {
  error.value = ''
  try {
    preview.value = await templateApi.preview(template.id)
  } catch (err) {
    error.value = extractErrorMessage(err)
  }
}

async function remove(template: Template) {
  if (!window.confirm(`确认删除模板「${template.name}」？`)) return
  error.value = ''
  try {
    await templateApi.delete(template.id)
    await load()
  } catch (err) {
    error.value = extractErrorMessage(err)
  }
}

onMounted(load)
</script>

<template>
  <div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_420px]">
    <section :class="[cardClass, 'overflow-hidden']">
      <div :class="sectionHeaderClass">
        <div>
          <h2 class="font-semibold">模板管理</h2>
          <p class="mt-1 text-sm text-zinc-500">维护创建任务时可选择的字段配置和模板状态。</p>
        </div>
        <button :class="[buttonBase, buttonTone.primary]" type="button" @click="startCreate">
          <Plus class="size-4" />
          新建模板
        </button>
      </div>
      <StateBlock v-if="loading" title="正在加载模板" type="loading" />
      <StateBlock
        v-else-if="error && templates.length === 0"
        title="模板加载失败"
        :description="error"
        type="error"
        action-label="重试"
        @action="load"
      />
      <div v-else class="divide-y divide-zinc-200">
        <article
          v-for="template in templates"
          :key="template.id"
          class="flex flex-wrap items-center justify-between gap-3 p-4"
        >
          <div>
            <div class="flex items-center gap-2">
              <h3 class="font-semibold">{{ template.name }}</h3>
              <span :class="toneClass(template.is_active ? 'success' : 'neutral')">{{
                template.is_active ? '启用' : '停用'
              }}</span>
            </div>
            <p class="mt-1 text-sm text-zinc-500">
              {{ template.description || '无描述' }} · {{ formatDateTime(template.created_at) }}
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              :class="[buttonBase, buttonTone.secondary]"
              type="button"
              @click="showPreview(template)"
            >
              <Eye class="size-4" />
              预览
            </button>
            <button
              :class="[buttonBase, buttonTone.secondary]"
              type="button"
              @click="startEdit(template)"
            >
              编辑
            </button>
            <button
              :class="[buttonBase, buttonTone.danger]"
              type="button"
              @click="remove(template)"
            >
              <Trash2 class="size-4" />
              删除
            </button>
          </div>
        </article>
      </div>
    </section>

    <aside class="grid gap-5">
      <form
        v-if="editingId"
        :class="[cardClass, 'grid gap-4 overflow-hidden']"
        @submit.prevent="save"
      >
        <div
          class="border-b border-zinc-200 bg-zinc-50/70 px-5 py-4 dark:border-zinc-800 dark:bg-zinc-950/50"
        >
          <h2 class="font-semibold">{{ editingId === 'new' ? '新建模板' : '编辑模板' }}</h2>
          <p class="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            使用结构化字段编辑器维护配置，必要时切换 JSON 修复。
          </p>
        </div>
        <div class="grid gap-4 p-5">
          <label class="grid gap-2">
            <span class="text-xs font-semibold text-zinc-500 dark:text-zinc-400">名称</span>
            <input v-model="form.name" :class="inputClass" required />
          </label>
          <label class="grid gap-2">
            <span class="text-xs font-semibold text-zinc-500 dark:text-zinc-400">描述</span>
            <input v-model="form.description" :class="inputClass" />
          </label>
          <label class="flex items-center gap-2 text-sm">
            <input v-model="form.is_active" type="checkbox" />
            启用模板
          </label>
          <TemplateConfigEditor v-model="form.field_config" @valid="editorValid = $event" />
          <div v-if="error" :class="alertClass.danger">
            {{ error }}
          </div>
          <div v-if="message" :class="alertClass.success">
            {{ message }}
          </div>
          <div class="flex gap-2">
            <button
              :class="[buttonBase, buttonTone.primary]"
              :disabled="!editorValid"
              type="submit"
            >
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

      <section v-if="preview" :class="[cardClass, 'p-5']">
        <h2 class="font-semibold">{{ preview.template_name }} 预览</h2>
        <pre
          class="mt-3 max-h-96 overflow-auto rounded-md bg-zinc-950 p-3 text-xs leading-5 text-zinc-100"
          >{{ stringifyJson(preview.preview_payload) }}</pre
        >
      </section>

      <section v-else-if="editingId && localPreviewPayload" :class="[cardClass, 'p-5']">
        <h2 class="font-semibold">当前配置预览</h2>
        <pre
          class="mt-3 max-h-96 overflow-auto rounded-md bg-zinc-950 p-3 text-xs leading-5 text-zinc-100"
          >{{ stringifyJson(localPreviewPayload) }}</pre
        >
      </section>
    </aside>
  </div>
</template>
