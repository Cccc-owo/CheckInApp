<script setup lang="ts">
import {
  ArrowDown,
  ArrowUp,
  Braces,
  ChevronDown,
  ChevronRight,
  ListTree,
  Plus,
  Trash2,
} from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'
import {
  addFieldAtPath,
  createDefaultFieldConfig,
  createDefaultNode,
  deleteFieldAtPath,
  isFieldConfig,
  isPlainObject,
  moveFieldAtPath,
  nodeKind,
  nodeKindLabel,
  renameFieldAtPath,
  updateFieldAtPath,
  type FieldNodeKind,
  type FieldPath,
  type TemplateFieldConfigItem,
  type TemplateFieldConfigNode,
  type TemplateFieldConfigRoot,
} from './template-config'
import { buttonBase, buttonTone, inputClass, labelClass, textareaClass } from '@/components/ui'

const props = defineProps<{
  root: TemplateFieldConfigRoot
  node: TemplateFieldConfigNode
  fieldKey: string
  path: FieldPath
  depth?: number
}>()

const emit = defineEmits<{
  change: [TemplateFieldConfigRoot]
  error: [string]
}>()

const collapsed = ref(false)
const keyDraft = ref(props.fieldKey)
const addKey = ref('')
const addKind = ref<FieldNodeKind>('field')
const localError = ref('')

const depth = computed(() => props.depth ?? 0)
const kind = computed(() => nodeKind(props.node))
const isNamedField = computed(() => typeof props.path[props.path.length - 1] === 'string')
const fieldNode = computed(() =>
  isFieldConfig(props.node) ? (props.node as TemplateFieldConfigItem) : null,
)
const kindBadge = computed(() => nodeKindLabel(kind.value))
const pathLabel = computed(() => props.path.map(String).join('.') || 'root')
const unknownKeys = computed(() => {
  const field = fieldNode.value
  if (!field) return []
  const known = new Set([
    'display_name',
    'field_type',
    'value_type',
    'default_value',
    'required',
    'hidden',
    'placeholder',
    'options',
  ])
  return Object.keys(field).filter((key) => !known.has(key))
})

const children = computed(() => {
  if (Array.isArray(props.node)) {
    return props.node.map((node, index) => ({
      id: String(index),
      label: `元素 ${index + 1}`,
      path: [...props.path, index],
      node,
    }))
  }

  if (isPlainObject(props.node) && !isFieldConfig(props.node)) {
    return Object.entries(props.node).map(([key, node]) => ({
      id: key,
      label: key,
      path: [...props.path, key],
      node: node as TemplateFieldConfigNode,
    }))
  }

  return []
})

const canAddChildren = computed(() => kind.value === 'array' || kind.value === 'object')
const addKeyRequired = computed(() => kind.value === 'object')

watch(
  () => props.fieldKey,
  (value) => {
    keyDraft.value = value
  },
)

function createNodeFor(kindValue: FieldNodeKind, name: string) {
  if (kindValue === 'field') return createDefaultFieldConfig(name || '字段')
  return createDefaultNode(kindValue)
}

function reportError(error: unknown) {
  const message = error instanceof Error ? error.message : '字段配置更新失败'
  localError.value = message
  emit('error', message)
}

function commit(nextRoot: TemplateFieldConfigRoot) {
  localError.value = ''
  emit('change', nextRoot)
}

function updateNode(nextNode: TemplateFieldConfigNode) {
  try {
    commit(updateFieldAtPath(props.root, props.path, nextNode))
  } catch (error) {
    reportError(error)
  }
}

function updateField(property: keyof TemplateFieldConfigItem, value: unknown) {
  const field = fieldNode.value
  if (!field) return
  const next: TemplateFieldConfigItem = { ...field, [property]: value }
  if (property === 'field_type' && value === 'select' && !Array.isArray(next.options)) {
    next.options = []
  }
  if (property === 'hidden' && value) {
    next.required = false
  }
  updateNode(next)
}

function commitRename() {
  if (!isNamedField.value || keyDraft.value === props.fieldKey) return
  try {
    commit(renameFieldAtPath(props.root, props.path, keyDraft.value))
  } catch (error) {
    keyDraft.value = props.fieldKey
    reportError(error)
  }
}

function addChild() {
  try {
    const key = addKey.value.trim()
    if (addKeyRequired.value && !key) throw new Error('字段名不能为空')
    const node = createNodeFor(addKind.value, key)
    commit(addFieldAtPath(props.root, props.path, key, node))
    addKey.value = ''
    addKind.value = 'field'
  } catch (error) {
    reportError(error)
  }
}

function deleteNode() {
  try {
    commit(deleteFieldAtPath(props.root, props.path))
  } catch (error) {
    reportError(error)
  }
}

function move(direction: 'up' | 'down') {
  try {
    commit(moveFieldAtPath(props.root, props.path, direction))
  } catch (error) {
    reportError(error)
  }
}

function addOption() {
  const field = fieldNode.value
  if (!field) return
  updateField('options', [...(field.options ?? []), { label: '', value: '' }])
}

function updateOption(index: number, property: 'label' | 'value', value: string) {
  const field = fieldNode.value
  if (!field) return
  const options = [...(field.options ?? [])]
  options[index] = { ...(options[index] ?? { label: '', value: '' }), [property]: value }
  updateField('options', options)
}

function removeOption(index: number) {
  const field = fieldNode.value
  if (!field) return
  const options = [...(field.options ?? [])]
  options.splice(index, 1)
  updateField('options', options)
}
</script>

<template>
  <article
    class="rounded-lg border border-zinc-200 bg-white p-3 shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
    :style="{ marginLeft: `${Math.min(depth, 4) * 0.5}rem` }"
  >
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div class="flex min-w-0 items-center gap-2">
        <button
          v-if="canAddChildren || fieldNode"
          type="button"
          class="inline-flex size-7 shrink-0 items-center justify-center rounded-md border border-zinc-200 text-zinc-500 transition hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
          :title="collapsed ? '展开' : '收起'"
          @click="collapsed = !collapsed"
        >
          <ChevronRight v-if="collapsed" class="size-4" />
          <ChevronDown v-else class="size-4" />
        </button>
        <div
          class="inline-flex size-7 shrink-0 items-center justify-center rounded-md border border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/50 dark:text-emerald-300"
        >
          <ListTree v-if="kind === 'array'" class="size-4" />
          <Braces v-else-if="kind === 'object'" class="size-4" />
          <span v-else class="text-xs font-semibold">Aa</span>
        </div>
        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-2">
            <input
              v-if="isNamedField"
              v-model="keyDraft"
              :class="[inputClass, 'h-8 min-h-8 w-36 font-mono text-xs sm:w-44']"
              title="字段名"
              @blur="commitRename"
              @keyup.enter="commitRename"
            />
            <span v-else class="font-mono text-sm font-semibold text-zinc-800 dark:text-zinc-100">
              {{ fieldKey }}
            </span>
            <span
              class="rounded-full border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-[11px] font-medium text-zinc-600 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
            >
              {{ kindBadge }}
            </span>
          </div>
          <div class="mt-0.5 truncate text-xs text-zinc-500 dark:text-zinc-400">
            {{ pathLabel }}
          </div>
        </div>
      </div>
      <div class="flex flex-wrap gap-1">
        <button
          type="button"
          :class="[buttonBase, buttonTone.ghost, 'size-8 min-h-8 px-0 py-0']"
          title="上移"
          @click="move('up')"
        >
          <ArrowUp class="size-4" />
        </button>
        <button
          type="button"
          :class="[buttonBase, buttonTone.ghost, 'size-8 min-h-8 px-0 py-0']"
          title="下移"
          @click="move('down')"
        >
          <ArrowDown class="size-4" />
        </button>
        <button
          type="button"
          :class="[buttonBase, buttonTone.danger, 'size-8 min-h-8 px-0 py-0']"
          title="删除"
          @click="deleteNode"
        >
          <Trash2 class="size-4" />
        </button>
      </div>
    </div>

    <p v-if="localError" class="mt-2 text-xs font-medium text-rose-600 dark:text-rose-300">
      {{ localError }}
    </p>

    <div v-if="!collapsed" class="mt-3 grid gap-3">
      <div v-if="fieldNode" class="grid gap-3">
        <div class="grid gap-3 sm:grid-cols-2">
          <label class="grid gap-1.5">
            <span :class="labelClass">显示名称</span>
            <input
              :class="inputClass"
              :value="fieldNode.display_name"
              placeholder="例如：姓名"
              @input="updateField('display_name', ($event.target as HTMLInputElement).value)"
            />
          </label>
          <label class="grid gap-1.5">
            <span :class="labelClass">字段类型</span>
            <select
              :class="inputClass"
              :value="fieldNode.field_type"
              @change="updateField('field_type', ($event.target as HTMLSelectElement).value)"
            >
              <option value="text">单行文本</option>
              <option value="textarea">多行文本</option>
              <option value="number">数字输入</option>
              <option value="select">下拉选择</option>
            </select>
          </label>
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <label class="grid gap-1.5">
            <span :class="labelClass">值类型</span>
            <select
              :class="inputClass"
              :value="fieldNode.value_type ?? 'string'"
              @change="updateField('value_type', ($event.target as HTMLSelectElement).value)"
            >
              <option value="string">string</option>
              <option value="int">int</option>
              <option value="double">double</option>
              <option value="bool">bool</option>
              <option value="json">json</option>
            </select>
          </label>
          <label class="grid gap-1.5">
            <span :class="labelClass">默认值</span>
            <textarea
              v-if="fieldNode.value_type === 'json'"
              :class="[textareaClass, 'min-h-20']"
              :value="String(fieldNode.default_value ?? '')"
              @input="updateField('default_value', ($event.target as HTMLTextAreaElement).value)"
            />
            <input
              v-else
              :class="inputClass"
              :value="String(fieldNode.default_value ?? '')"
              @input="updateField('default_value', ($event.target as HTMLInputElement).value)"
            />
          </label>
        </div>

        <label class="grid gap-1.5">
          <span :class="labelClass">占位提示</span>
          <input
            :class="inputClass"
            :value="fieldNode.placeholder ?? ''"
            placeholder="用户填写时看到的提示"
            @input="updateField('placeholder', ($event.target as HTMLInputElement).value)"
          />
        </label>

        <div
          class="grid gap-2 rounded-md border border-zinc-200 bg-zinc-50 p-3 text-sm sm:grid-cols-2 dark:border-zinc-800 dark:bg-zinc-950"
        >
          <label class="flex items-center gap-2">
            <input
              :checked="Boolean(fieldNode.required)"
              :disabled="Boolean(fieldNode.hidden)"
              type="checkbox"
              @change="updateField('required', ($event.target as HTMLInputElement).checked)"
            />
            必填
          </label>
          <label class="flex items-center gap-2">
            <input
              :checked="Boolean(fieldNode.hidden)"
              type="checkbox"
              @change="updateField('hidden', ($event.target as HTMLInputElement).checked)"
            />
            隐藏
          </label>
        </div>

        <div v-if="fieldNode.field_type === 'select'" class="grid gap-2">
          <div class="flex items-center justify-between gap-2">
            <span :class="labelClass">选项</span>
            <button
              :class="[buttonBase, buttonTone.secondary, 'min-h-8 px-2 py-1 text-xs']"
              type="button"
              @click="addOption"
            >
              <Plus class="size-3.5" />
              添加选项
            </button>
          </div>
          <div
            v-for="(option, index) in fieldNode.options ?? []"
            :key="index"
            class="grid gap-2 rounded-md border border-zinc-200 bg-zinc-50 p-2 sm:grid-cols-[1fr_1fr_auto] dark:border-zinc-800 dark:bg-zinc-950"
          >
            <input
              :class="inputClass"
              :value="option.label"
              placeholder="显示文本"
              @input="updateOption(index, 'label', ($event.target as HTMLInputElement).value)"
            />
            <input
              :class="inputClass"
              :value="option.value"
              placeholder="保存值"
              @input="updateOption(index, 'value', ($event.target as HTMLInputElement).value)"
            />
            <button
              type="button"
              :class="[buttonBase, buttonTone.danger, 'min-h-9 px-2 py-1']"
              @click="removeOption(index)"
            >
              删除
            </button>
          </div>
        </div>

        <p v-if="unknownKeys.length" class="text-xs text-zinc-500 dark:text-zinc-400">
          保留未识别属性：{{ unknownKeys.join(', ') }}
        </p>
      </div>

      <div v-else-if="canAddChildren" class="grid gap-3">
        <div v-if="children.length" class="grid gap-2">
          <TemplateFieldNode
            v-for="child in children"
            :key="child.id"
            :root="root"
            :node="child.node"
            :field-key="child.label"
            :path="child.path"
            :depth="depth + 1"
            @change="$emit('change', $event)"
            @error="$emit('error', $event)"
          />
        </div>
        <div
          v-else
          class="rounded-md border border-dashed border-zinc-200 bg-zinc-50 p-4 text-center text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-400"
        >
          当前{{ kindBadge }}为空
        </div>
        <div
          class="grid gap-2 rounded-md border border-zinc-200 bg-zinc-50 p-3 sm:grid-cols-[1fr_120px_auto] dark:border-zinc-800 dark:bg-zinc-950"
        >
          <input
            v-model="addKey"
            :class="inputClass"
            :placeholder="addKeyRequired ? '子字段名' : '数组元素名（可选）'"
          />
          <select v-model="addKind" :class="inputClass">
            <option value="field">字段</option>
            <option value="object">对象</option>
            <option value="array">数组</option>
          </select>
          <button :class="[buttonBase, buttonTone.secondary]" type="button" @click="addChild">
            <Plus class="size-4" />
            添加
          </button>
        </div>
      </div>
    </div>
  </article>
</template>
