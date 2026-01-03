<template>
  <div class="field-config-editor space-y-4">
    <!-- Row 1: Display Name and Field Type -->
    <div class="grid grid-cols-2 gap-4">
      <a-form-item label="显示名称" class="mb-0">
        <a-input
          :value="modelValue.display_name"
          @change="e => updateField('display_name', e.target.value)"
          placeholder="在表单中显示的名称"
          allow-clear
        />
        <span class="text-xs text-gray-500 mt-1">显示名称</span>
      </a-form-item>

      <a-form-item label="字段类型" class="mb-0">
        <a-select
          :value="modelValue.field_type"
          @change="handleFieldTypeChange"
          placeholder="选择输入控件类型"
          class="w-full"
        >
          <a-select-option label="📝 单行文本" value="text" />
          <a-select-option label="📄 多行文本" value="textarea" />
          <a-select-option label="🔢 数字输入" value="number" />
          <a-select-option label="📋 下拉选择" value="select" />
        </a-select>
        <span class="text-xs text-gray-500 mt-1">用户填写时使用的输入控件</span>
      </a-form-item>
    </div>

    <!-- Row 2: Value Type and Default Value -->
    <div class="grid grid-cols-2 gap-4">
      <a-form-item label="值类型" class="mb-0">
        <a-select
          :value="modelValue.value_type"
          @change="value => updateField('value_type', value)"
          placeholder="选择数据类型"
          class="w-full"
        >
          <a-select-option label="字符串 (string)" value="string">
            <span class="text-xs text-gray-500">字符串 (string)</span>
          </a-select-option>
          <a-select-option label="整数 (int)" value="int">
            <span class="text-xs text-gray-500">整数 (int)</span>
          </a-select-option>
          <a-select-option label="浮点数 (double)" value="double">
            <span class="text-xs text-gray-500">浮点数 (double)</span>
          </a-select-option>
          <a-select-option label="布尔值 (bool)" value="bool">
            <span class="text-xs text-gray-500">布尔值 (bool)</span>
          </a-select-option>
          <a-select-option label="JSON对象 (json)" value="json">
            <span class="text-xs text-gray-500">JSON对象 (json) - 用于Values字段</span>
          </a-select-option>
        </a-select>
        <span class="text-xs text-gray-500 mt-1">数据存储时的类型</span>
      </a-form-item>

      <a-form-item label="默认值" class="mb-0">
        <a-input
          v-if="modelValue.value_type !== 'json'"
          :value="modelValue.default_value"
          @change="e => updateField('default_value', e.target.value)"
          placeholder="字段的默认值"
          allow-clear
        />
        <a-textarea
          v-else
          :value="modelValue.default_value"
          @change="e => updateField('default_value', e.target.value)"
          placeholder="字段的默认值"
          :rows="3"
          allow-clear
        />
        <span class="text-xs text-gray-500 mt-1">
          <template v-if="modelValue.value_type === 'json'">
            <p>输入JSON对象,会自动序列化为字符串</p>
            <p>如:{"key1":value1,"key2":value2}</p>
          </template>
          <template v-else>
            用户未填写时使用此值
          </template>
        </span>
      </a-form-item>
    </div>

    <!-- Row 3: Placeholder -->
    <a-form-item label="占位符提示" class="mb-0">
      <a-input
        :value="modelValue.placeholder"
        @change="e => updateField('placeholder', e.target.value)"
        placeholder="输入框的灰色提示文本"
        allow-clear
      />
      <span class="text-xs text-gray-500 mt-1">占位符</span>
    </a-form-item>

    <!-- Row 4: Switches -->
    <div class="grid grid-cols-2 gap-4 p-3 bg-blue-50 rounded-lg">
      <div class="flex items-center justify-between">
        <div>
          <label class="text-sm font-medium text-gray-700">是否必填</label>
          <p class="text-xs text-gray-500">用户必须填写此字段</p>
        </div>
        <a-switch
          :checked="modelValue.required"
          @change="handleRequiredChange"
          :disabled="modelValue.hidden"
        />
      </div>

      <div class="flex items-center justify-between">
        <div>
          <label class="text-sm font-medium text-gray-700">是否隐藏</label>
          <p class="text-xs text-gray-500">直接使用默认值，不在表单中显示</p>
        </div>
        <a-switch
          :checked="modelValue.hidden"
          @change="handleHiddenChange"
        />
      </div>
    </div>

    <a-alert
      v-if="modelValue.hidden"
      message="💡 提示"
      type="info"
      :closable="false"
      class="mt-3"
    >
      <template #description>
        <p class="text-xs">
          隐藏字段将自动使用默认值，不会在创建任务表单中显示。请确保设置了合适的默认值。
        </p>
      </template>
    </a-alert>

    <!-- Options for select type -->
    <div v-if="modelValue.field_type === 'select'" class="border-t pt-4 mt-4">
      <a-form-item label="选项列表" class="mb-0">
        <div class="space-y-2">
          <div
            v-for="(option, index) in modelValue.options || []"
            :key="index"
            class="flex items-center gap-2 p-2 bg-gray-50 rounded"
          >
            <span class="text-xs text-gray-500 w-8">{{ index + 1 }}.</span>
            <a-input
              :value="option.label"
              @change="e => updateOption(index, 'label', e.target.value)"
              placeholder="显示文本（如：健康）"
              size="small"
              class="flex-1"
            />
            <a-input
              :value="option.value"
              @change="e => updateOption(index, 'value', e.target.value)"
              placeholder="选项值（如：healthy）"
              size="small"
              class="flex-1"
            />
            <a-button
              size="small"
              danger
              @click="removeOption(index)"
            >
              <template #icon><DeleteOutlined /></template>
            </a-button>
          </div>

          <a-button size="small" type="primary" @click="addOption" class="w-full">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            添加选项
          </a-button>

          <p class="text-xs text-gray-500 mt-2">
            💡 提示：显示文本是用户看到的内容，选项值是实际保存的数据
          </p>
        </div>
      </a-form-item>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'
import { DeleteOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  fieldKey: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

// Update single field
const updateField = (field, value) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [field]: value
  })
}

// Handle required change
const handleRequiredChange = (value) => {
  updateField('required', value)
}

// Handle hidden change - 当隐藏时，自动设置 required 为 false
const handleHiddenChange = (value) => {
  const updated = {
    ...props.modelValue,
    hidden: value
  }

  // 如果设置为隐藏，则取消必填
  if (value) {
    updated.required = false
  }

  emit('update:modelValue', updated)
}

// Handle field type change
const handleFieldTypeChange = (newType) => {
  const updated = {
    ...props.modelValue,
    field_type: newType
  }

  if (newType === 'select' && !updated.options) {
    updated.options = []
  }

  emit('update:modelValue', updated)
}

// Add option
const addOption = () => {
  const options = [...(props.modelValue.options || [])]
  options.push({ label: '', value: '' })

  emit('update:modelValue', {
    ...props.modelValue,
    options
  })
}

// Update option
const updateOption = (index, field, value) => {
  const options = [...(props.modelValue.options || [])]
  options[index] = {
    ...options[index],
    [field]: value
  }

  emit('update:modelValue', {
    ...props.modelValue,
    options
  })
}

// Remove option
const removeOption = (index) => {
  const options = [...(props.modelValue.options || [])]
  options.splice(index, 1)

  emit('update:modelValue', {
    ...props.modelValue,
    options
  })
}
</script>

<style scoped>
/* 样式已移至全局 CSS (style.css) 以保持统一性 */
</style>
