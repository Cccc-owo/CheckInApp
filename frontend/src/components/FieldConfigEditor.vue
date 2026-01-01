<template>
  <div class="field-config-editor space-y-4">
    <!-- Row 1: Display Name and Field Type -->
    <div class="grid grid-cols-2 gap-4">
      <el-form-item label="显示名称" class="mb-0">
        <el-input
          :model-value="modelValue.display_name"
          @update:model-value="updateField('display_name', $event)"
          placeholder="在表单中显示的名称"
          clearable
        />
        <span class="text-xs text-gray-500 mt-1">显示名称</span>
      </el-form-item>

      <el-form-item label="字段类型" class="mb-0">
        <el-select
          :model-value="modelValue.field_type"
          @update:model-value="handleFieldTypeChange"
          placeholder="选择输入控件类型"
          class="w-full"
        >
          <el-option label="📝 单行文本" value="text" />
          <el-option label="📄 多行文本" value="textarea" />
          <el-option label="🔢 数字输入" value="number" />
          <el-option label="📋 下拉选择" value="select" />
        </el-select>
        <span class="text-xs text-gray-500 mt-1">用户填写时使用的输入控件</span>
      </el-form-item>
    </div>

    <!-- Row 2: Value Type and Default Value -->
    <div class="grid grid-cols-2 gap-4">
      <el-form-item label="值类型" class="mb-0">
        <el-select
          :model-value="modelValue.value_type"
          @update:model-value="updateField('value_type', $event)"
          placeholder="选择数据类型"
          class="w-full"
        >
          <el-option label="字符串 (string)" value="string">
            <span class="text-xs text-gray-500">字符串 (string)</span>
          </el-option>
          <el-option label="整数 (int)" value="int">
            <span class="text-xs text-gray-500">整数 (int)</span>
          </el-option>
          <el-option label="浮点数 (double)" value="double">
            <span class="text-xs text-gray-500">浮点数 (double)</span>
          </el-option>
          <el-option label="布尔值 (bool)" value="bool">
            <span class="text-xs text-gray-500">布尔值 (bool)</span>
          </el-option>
          <el-option label="JSON对象 (json)" value="json">
            <span class="text-xs text-gray-500">JSON对象 (json) - 用于Values字段</span>
          </el-option>
        </el-select>
        <span class="text-xs text-gray-500 mt-1">数据存储时的类型</span>
      </el-form-item>

      <el-form-item label="默认值" class="mb-0">
        <el-input
          v-if="modelValue.value_type !== 'json'"
          :model-value="modelValue.default_value"
          @update:model-value="updateField('default_value', $event)"
          placeholder="字段的默认值"
          clearable
        />
        <el-input
          v-else
          type="textarea"
          :model-value="modelValue.default_value"
          @update:model-value="updateField('default_value', $event)"
          placeholder="字段的默认值"
          :rows="3"
          clearable
        />
        <span class="text-xs text-gray-500 mt-1">
          <template v-if="modelValue.value_type === 'json'">
            <p>输入JSON对象，会自动序列化为字符串</p>
            <p>如：{"key1":value1,"key2":value2}</p>
          </template>
          <template v-else>
            用户未填写时使用此值
          </template>
        </span>
      </el-form-item>
    </div>

    <!-- Row 3: Placeholder -->
    <el-form-item label="占位符提示" class="mb-0">
      <el-input
        :model-value="modelValue.placeholder"
        @update:model-value="updateField('placeholder', $event)"
        placeholder="输入框的灰色提示文本"
        clearable
      />
      <span class="text-xs text-gray-500 mt-1">占位符</span>
    </el-form-item>

    <!-- Row 4: Switches -->
    <div class="grid grid-cols-2 gap-4 p-3 bg-blue-50 rounded-lg">
      <div class="flex items-center justify-between">
        <div>
          <label class="text-sm font-medium text-gray-700">是否必填</label>
          <p class="text-xs text-gray-500">用户必须填写此字段</p>
        </div>
        <el-switch
          :model-value="modelValue.required"
          @update:model-value="handleRequiredChange"
          :disabled="modelValue.hidden"
        />
      </div>

      <div class="flex items-center justify-between">
        <div>
          <label class="text-sm font-medium text-gray-700">是否隐藏</label>
          <p class="text-xs text-gray-500">直接使用默认值，不在表单中显示</p>
        </div>
        <el-switch
          :model-value="modelValue.hidden"
          @update:model-value="handleHiddenChange"
        />
      </div>
    </div>

    <el-alert
      v-if="modelValue.hidden"
      title="💡 提示"
      type="info"
      :closable="false"
      class="mt-3"
    >
      <p class="text-xs">
        隐藏字段将自动使用默认值，不会在创建任务表单中显示。请确保设置了合适的默认值。
      </p>
    </el-alert>

    <!-- Options for select type -->
    <div v-if="modelValue.field_type === 'select'" class="border-t pt-4 mt-4">
      <el-form-item label="选项列表" class="mb-0">
        <div class="space-y-2">
          <div
            v-for="(option, index) in modelValue.options || []"
            :key="index"
            class="flex items-center gap-2 p-2 bg-gray-50 rounded"
          >
            <span class="text-xs text-gray-500 w-8">{{ index + 1 }}.</span>
            <el-input
              :model-value="option.label"
              @update:model-value="updateOption(index, 'label', $event)"
              placeholder="显示文本（如：健康）"
              size="small"
              class="flex-1"
            />
            <el-input
              :model-value="option.value"
              @update:model-value="updateOption(index, 'value', $event)"
              placeholder="选项值（如：healthy）"
              size="small"
              class="flex-1"
            />
            <el-button
              size="small"
              type="danger"
              :icon="Delete"
              @click="removeOption(index)"
              circle
            />
          </div>

          <el-button size="small" type="primary" plain @click="addOption" class="w-full">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            添加选项
          </el-button>

          <p class="text-xs text-gray-500 mt-2">
            💡 提示：显示文本是用户看到的内容，选项值是实际保存的数据
          </p>
        </div>
      </el-form-item>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'
import { Delete } from '@element-plus/icons-vue'

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
.field-config-editor {
  background-color: #fafafa;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #374151;
}
</style>
