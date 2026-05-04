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
  cardClass,
  inputClass,
  labelClass,
  sectionHeaderClass,
  toneClass,
} from '@/components/ui'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
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
const editorOpen = computed({
  get: () => editingId.value !== null,
  set: (open: boolean) => {
    if (!open) editingId.value = null
  },
})
const editorTitle = computed(() => (editingId.value === 'new' ? '新建模板' : '编辑模板'))

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
  <div class="grid gap-5">
    <section :class="[cardClass, 'overflow-hidden']">
      <div :class="sectionHeaderClass">
        <div>
          <h2 class="font-semibold">模板管理</h2>
        </div>
        <Button type="button" @click="startCreate">
          <Plus class="size-4" />
          新建模板
        </Button>
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
      <StateBlock
        v-else-if="templates.length === 0"
        title="暂无模板"
        action-label="新建模板"
        @action="startCreate"
      />
      <div v-else class="divide-y divide-zinc-200 dark:divide-zinc-800">
        <article
          v-for="template in templates"
          :key="template.id"
          class="flex flex-wrap items-center justify-between gap-3 p-3 sm:p-4"
        >
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <h3 class="truncate font-semibold">{{ template.name }}</h3>
              <span :class="toneClass(template.is_active ? 'success' : 'neutral')">{{
                template.is_active ? '启用' : '停用'
              }}</span>
            </div>
            <div
              class="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-sm text-zinc-500 dark:text-zinc-400"
            >
              <span>{{ template.description || '无描述' }}</span>
              <span>{{ formatDateTime(template.created_at) }}</span>
            </div>
          </div>
          <div class="flex flex-wrap gap-2">
            <Button type="button" variant="outline" @click="showPreview(template)">
              <Eye class="size-4" />
              预览
            </Button>
            <Button type="button" variant="outline" @click="startEdit(template)"> 编辑 </Button>
            <Button
              type="button"
              variant="outline"
              class="border-rose-200 bg-rose-50 text-rose-700 hover:border-rose-300 hover:bg-rose-100 dark:border-rose-900/70 dark:bg-rose-950/50 dark:text-rose-300 dark:hover:border-rose-800 dark:hover:bg-rose-900/40"
              @click="remove(template)"
            >
              <Trash2 class="size-4" />
              删除
            </Button>
          </div>
        </article>
      </div>
    </section>

    <section v-if="preview" :class="[cardClass, 'p-5']">
      <details open>
        <summary class="cursor-pointer text-sm font-semibold">
          {{ preview.template_name }} 预览
        </summary>
        <pre
          class="mt-3 max-h-96 overflow-auto rounded-md bg-zinc-950 p-3 text-xs leading-5 text-zinc-100"
          >{{ stringifyJson(preview.preview_payload) }}</pre
        >
      </details>
    </section>

    <Dialog v-model:open="editorOpen">
      <DialogContent
        class="grid max-h-[calc(100dvh-2rem)] grid-rows-[auto_minmax(0,1fr)] gap-0 overflow-hidden p-0 sm:max-w-[min(960px,calc(100vw-2rem))] lg:max-w-[min(1120px,calc(100vw-3rem))]"
      >
        <DialogHeader
          class="border-b border-zinc-200 bg-zinc-50/70 px-5 py-4 dark:border-zinc-800 dark:bg-zinc-950/50"
        >
          <DialogTitle>{{ editorTitle }}</DialogTitle>
        </DialogHeader>

        <form class="min-h-0 overflow-y-auto" @submit.prevent="save">
          <div class="grid gap-4 p-4 sm:p-5">
            <div class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] lg:items-end">
              <label class="grid gap-2">
                <span :class="labelClass">名称</span>
                <input v-model="form.name" :class="inputClass" required />
              </label>
              <label class="grid gap-2">
                <span :class="labelClass">描述</span>
                <input v-model="form.description" :class="inputClass" />
              </label>
              <label
                class="flex min-h-9 items-center gap-2 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950"
              >
                <input v-model="form.is_active" type="checkbox" />
                启用模板
              </label>
            </div>

            <TemplateConfigEditor v-model="form.field_config" @valid="editorValid = $event" />

            <div
              v-if="localPreviewPayload"
              class="rounded-lg border border-zinc-200 p-3 dark:border-zinc-800"
            >
              <details>
                <summary class="cursor-pointer text-sm font-semibold">当前配置预览</summary>
                <pre
                  class="mt-3 max-h-64 overflow-auto rounded-md bg-zinc-950 p-3 text-xs leading-5 text-zinc-100"
                  >{{ stringifyJson(localPreviewPayload) }}</pre
                >
              </details>
            </div>

            <div v-if="error" :class="alertClass.danger">
              {{ error }}
            </div>
            <div v-if="message" :class="alertClass.success">
              {{ message }}
            </div>
          </div>

          <DialogFooter
            class="sticky bottom-0 border-t border-zinc-200 bg-white/95 px-5 py-4 backdrop-blur dark:border-zinc-800 dark:bg-zinc-900/95"
          >
            <Button type="button" variant="outline" @click="editingId = null">取消</Button>
            <Button :disabled="!editorValid" type="submit">
              <Save class="size-4" />
              保存
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </div>
</template>
