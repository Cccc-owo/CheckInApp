<script setup lang="ts">
import { Braces, Plus, TreePine } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'
import TemplateFieldNode from './TemplateFieldNode.vue'
import {
  addFieldAtPath,
  buildTemplatePreviewPayload,
  createDefaultFieldConfig,
  createDefaultNode,
  parseTemplateFieldConfig,
  serializeTemplateFieldConfig,
  validateFieldConfig,
  type FieldNodeKind,
  type TemplateFieldConfigRoot,
} from './template-config'
import {
  alertClass,
  buttonBase,
  buttonTone,
  inputClass,
  labelClass,
  textareaClass,
} from '@/components/ui'
import { stringifyJson } from '@/utils/format'

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [string]
  valid: [boolean]
}>()

const mode = ref<'structured' | 'json'>('structured')
const config = ref<TemplateFieldConfigRoot>({})
const jsonDraft = ref(props.modelValue)
const error = ref('')
const addKey = ref('')
const addKind = ref<FieldNodeKind>('field')

const parsed = computed(() => parseTemplateFieldConfig(props.modelValue))
const validation = computed(() => validateFieldConfig(config.value))
const previewPayload = computed(() => buildTemplatePreviewPayload(config.value))
const rootEntries = computed(() => Object.entries(config.value))
const isValid = computed(() => validation.value.ok && !error.value)

watch(
  () => props.modelValue,
  (value) => {
    if (value === serializeTemplateFieldConfig(config.value)) return
    jsonDraft.value = value
    const result = parseTemplateFieldConfig(value)
    if (result.ok) {
      config.value = result.config
      error.value = ''
    } else if (mode.value === 'json') {
      config.value = result.config
      error.value = result.message ?? '字段配置无效'
    } else {
      config.value = result.config
      mode.value = 'json'
      error.value = result.message ?? '字段配置无效，请先在 JSON 模式修复'
    }
  },
  { immediate: true },
)

watch(isValid, (value) => emit('valid', value), { immediate: true })

function commit(nextConfig: TemplateFieldConfigRoot) {
  config.value = nextConfig
  const nextJson = serializeTemplateFieldConfig(nextConfig)
  jsonDraft.value = nextJson
  error.value = ''
  emit('update:modelValue', nextJson)
}

function addRootField() {
  try {
    const key = addKey.value.trim()
    if (!key) throw new Error('字段名不能为空')
    const node =
      addKind.value === 'field' ? createDefaultFieldConfig(key) : createDefaultNode(addKind.value)
    commit(addFieldAtPath(config.value, [], key, node))
    addKey.value = ''
    addKind.value = 'field'
  } catch (err) {
    error.value = err instanceof Error ? err.message : '添加字段失败'
  }
}

function switchMode(nextMode: 'structured' | 'json') {
  if (nextMode === mode.value) return
  if (nextMode === 'json') {
    jsonDraft.value = serializeTemplateFieldConfig(config.value)
    mode.value = 'json'
    return
  }

  const result = parseTemplateFieldConfig(jsonDraft.value)
  if (!result.ok) {
    error.value = result.message ?? 'JSON 无法切换到结构化编辑'
    return
  }
  commit(result.config)
  mode.value = 'structured'
}

function applyJsonDraft() {
  const result = parseTemplateFieldConfig(jsonDraft.value)
  if (!result.ok) {
    error.value = result.message ?? 'JSON 无效'
    return
  }
  commit(result.config)
}

function handleNodeError(message: string) {
  error.value = message
}
</script>

<template>
  <div class="grid gap-4">
    <div
      class="rounded-lg border border-zinc-200 bg-zinc-50 p-2 dark:border-zinc-800 dark:bg-zinc-950"
    >
      <div
        class="grid grid-cols-2 rounded-md border border-zinc-200 bg-white p-1 text-sm dark:border-zinc-700 dark:bg-zinc-900"
      >
        <button
          type="button"
          class="inline-flex items-center justify-center gap-2 rounded px-3 py-1.5 font-medium transition"
          :class="
            mode === 'structured'
              ? 'bg-emerald-700 text-white shadow-sm dark:bg-emerald-600'
              : 'text-zinc-600 hover:text-zinc-950 dark:text-zinc-300 dark:hover:text-zinc-50'
          "
          @click="switchMode('structured')"
        >
          <TreePine class="size-4" />
          结构化
        </button>
        <button
          type="button"
          class="inline-flex items-center justify-center gap-2 rounded px-3 py-1.5 font-medium transition"
          :class="
            mode === 'json'
              ? 'bg-zinc-900 text-white shadow-sm dark:bg-zinc-700'
              : 'text-zinc-600 hover:text-zinc-950 dark:text-zinc-300 dark:hover:text-zinc-50'
          "
          @click="switchMode('json')"
        >
          <Braces class="size-4" />
          JSON
        </button>
      </div>
    </div>

    <div v-if="error" :class="alertClass.danger">{{ error }}</div>
    <div v-else-if="!validation.ok" :class="alertClass.warning">{{ validation.message }}</div>
    <div v-else-if="!parsed.ok && mode === 'structured'" :class="alertClass.warning">
      已保留原始 JSON，请切换到 JSON 模式修复：{{ parsed.message }}
    </div>

    <div v-if="mode === 'structured'" class="grid gap-3">
      <div
        class="grid gap-2 rounded-lg border border-zinc-200 bg-white p-3 sm:grid-cols-[1fr_130px_auto] dark:border-zinc-800 dark:bg-zinc-900"
      >
        <label class="grid gap-1.5">
          <span :class="labelClass">新增根字段</span>
          <input v-model="addKey" :class="inputClass" placeholder="例如 signature 或 values" />
        </label>
        <label class="grid gap-1.5">
          <span :class="labelClass">类型</span>
          <select v-model="addKind" :class="inputClass">
            <option value="field">字段</option>
            <option value="object">对象</option>
            <option value="array">数组</option>
          </select>
        </label>
        <button
          :class="[buttonBase, buttonTone.secondary, 'self-end']"
          type="button"
          @click="addRootField"
        >
          <Plus class="size-4" />
          添加
        </button>
      </div>

      <div v-if="rootEntries.length" class="grid gap-3">
        <TemplateFieldNode
          v-for="[key, node] in rootEntries"
          :key="key"
          :root="config"
          :node="node"
          :field-key="key"
          :path="[key]"
          @change="commit"
          @error="handleNodeError"
        />
      </div>
      <div
        v-else
        class="rounded-lg border border-dashed border-zinc-200 bg-zinc-50 p-4 text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-400"
      >
        暂无字段配置
      </div>
    </div>

    <div v-else class="grid gap-3">
      <label class="grid gap-2">
        <span :class="labelClass">字段配置 JSON</span>
        <textarea v-model="jsonDraft" :class="[textareaClass, 'min-h-80']" spellcheck="false" />
      </label>
      <div class="flex flex-wrap gap-2">
        <button :class="[buttonBase, buttonTone.primary]" type="button" @click="applyJsonDraft">
          应用 JSON
        </button>
        <button
          :class="[buttonBase, buttonTone.secondary]"
          type="button"
          @click="switchMode('structured')"
        >
          返回结构化
        </button>
      </div>
    </div>

    <details
      class="rounded-lg border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-950"
    >
      <summary class="cursor-pointer text-sm font-semibold">当前 Payload 预览</summary>
      <pre
        class="mt-3 max-h-64 overflow-auto rounded-md bg-zinc-950 p-3 text-xs leading-5 text-zinc-100"
        >{{ stringifyJson(previewPayload) }}</pre
      >
    </details>
  </div>
</template>
