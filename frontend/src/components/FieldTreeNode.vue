<template>
  <div class="field-tree-node border-2 rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition-shadow">
    <!-- 普通字段 -->
    <div v-if="isFieldConfig" class="field-config">
      <div class="flex items-center justify-between mb-3 pb-2 border-b border-gray-200">
        <div class="flex items-center gap-3">
          <button
            type="button"
            @click="isCollapsed = !isCollapsed"
            class="hover:bg-gray-100 rounded p-1 transition-colors"
          >
            <svg
              class="w-4 h-4 text-gray-600 transition-transform"
              :class="{ 'rotate-180': !isCollapsed }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
          </svg>
          <span class="font-mono text-base font-bold text-blue-700">{{ fieldKey }}</span>
          <a-tag type="primary" size="small">普通字段</a-tag>
        </div>
        <div class="flex gap-2">
          <a-button size="small" @click="handleMove('up')" title="上移">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
            </svg>
          </a-button>
          <a-button size="small" @click="handleMove('down')" title="下移">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </a-button>
          <a-button size="small" type="danger" plain @click="handleDelete">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            删除
          </a-button>
        </div>
      </div>

      <div v-show="!isCollapsed" class="bg-gray-50 rounded-lg p-3">
        <FieldConfigEditor v-model="localFieldConfig" :field-key="fieldKey" />
      </div>
    </div>

    <!-- 数组字段 -->
    <div v-else-if="isArray" class="array-field">
      <div class="flex items-center justify-between mb-3 pb-2 border-b border-purple-200">
        <div class="flex items-center gap-3">
          <button
            type="button"
            @click="isCollapsed = !isCollapsed"
            class="hover:bg-gray-100 rounded p-1 transition-colors"
          >
            <svg
              class="w-4 h-4 text-gray-600 transition-transform"
              :class="{ 'rotate-180': !isCollapsed }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
          </svg>
          <span class="font-mono text-base font-bold text-purple-700">{{ fieldKey }}</span>
          <a-tag type="warning" size="small">数组字段</a-tag>
        </div>
        <div class="flex gap-2">
          <a-button size="small" @click="handleMove('up')" title="上移">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
            </svg>
          </a-button>
          <a-button size="small" @click="handleMove('down')" title="下移">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </a-button>
          <a-button size="small" type="primary" @click="addArrayItem">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            添加元素
          </a-button>
          <a-button size="small" type="danger" plain @click="handleDelete">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            删除
          </a-button>
        </div>
      </div>

      <div v-show="!isCollapsed">
        <div v-if="localFieldConfig.length === 0" class="text-center py-6 bg-purple-50 rounded-lg border border-dashed border-purple-300">
          <p class="text-sm text-gray-500 mb-2">数组为空</p>
          <a-button size="small" type="primary" @click="addArrayItem">添加第一个元素</a-button>
        </div>

        <div v-else class="space-y-3 mt-3">
          <div
            v-for="(item, index) in localFieldConfig"
            :key="index"
            class="border-2 border-purple-200 rounded-lg p-3 bg-purple-50"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-semibold text-purple-700">元素 #{{ index + 1 }}</span>
              <a-button size="small" type="danger" plain @click="removeArrayItem(index)">
                删除元素
              </a-button>
            </div>

            <!-- 如果数组元素是字段配置对象，直接渲染为字段编辑器 -->
            <div v-if="typeof item === 'object' && !Array.isArray(item) && 'display_name' in item" class="bg-white rounded-lg p-3">
              <FieldConfigEditor :model-value="item" @update:model-value="updateArrayItemField(index, $event)" :field-key="`元素${index + 1}`" />
            </div>

            <!-- 如果数组元素是对象（但不是字段配置），递归渲染其中的字段 -->
            <div v-else-if="typeof item === 'object' && !Array.isArray(item)" class="space-y-2">
              <FieldTreeNode
                v-for="(subConfig, subKey) in item"
                :key="subKey"
                :field-key="subKey"
                :field-config="subConfig"
                :path="[...path, index, subKey]"
                @update="$emit('update', $event)"
                @delete="$emit('delete', $event)"
                @move="$emit('move', $event)"
              />

              <a-button class="w-full" size="small" type="primary" plain @click="addFieldToArrayItem(index)">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                添加字段
              </a-button>
            </div>

            <!-- 如果数组元素是数组，递归渲染 -->
            <div v-else-if="Array.isArray(item)">
              <FieldTreeNode
                :field-key="`元素${index + 1}`"
                :field-config="item"
                :path="[...path, index]"
                @update="$emit('update', $event)"
                @delete="$emit('delete', $event)"
                @move="$emit('move', $event)"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 对象字段 -->
    <div v-else-if="isObject" class="object-field">
      <div class="flex items-center justify-between mb-3 pb-2 border-b border-green-200">
        <div class="flex items-center gap-3">
          <button
            type="button"
            @click="isCollapsed = !isCollapsed"
            class="hover:bg-gray-100 rounded p-1 transition-colors"
          >
            <svg
              class="w-4 h-4 text-gray-600 transition-transform"
              :class="{ 'rotate-180': !isCollapsed }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span class="font-mono text-base font-bold text-green-700">{{ fieldKey }}</span>
          <a-tag type="success" size="small">对象字段</a-tag>
        </div>
        <div class="flex gap-2">
          <a-button size="small" @click="handleMove('up')" title="上移">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
            </svg>
          </a-button>
          <a-button size="small" @click="handleMove('down')" title="下移">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </a-button>
          <a-button size="small" type="primary" @click="addFieldToObject">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            添加子字段
          </a-button>
          <a-button size="small" type="danger" plain @click="handleDelete">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            删除
          </a-button>
        </div>
      </div>

      <div v-show="!isCollapsed">
        <div v-if="Object.keys(localFieldConfig).length === 0" class="text-center py-6 bg-green-50 rounded-lg border border-dashed border-green-300">
          <p class="text-sm text-gray-500 mb-2">对象为空</p>
          <a-button size="small" type="primary" @click="addFieldToObject">添加第一个子字段</a-button>
        </div>

        <div v-else class="space-y-3 mt-3 pl-4 border-l-4 border-green-300">
        <!-- 递归渲染对象中的字段 -->
        <FieldTreeNode
          v-for="(subConfig, subKey) in localFieldConfig"
          :key="subKey"
          :field-key="subKey"
          :field-config="subConfig"
          :path="[...path, subKey]"
          @update="$emit('update', $event)"
          @delete="$emit('delete', $event)"
          @move="$emit('move', $event)"
        />
        </div>
      </div>
    </div>

    <!-- 添加字段对话框 -->
    <a-modal v-model:open="addFieldDialogVisible" :title="currentArrayIndex === -1 ? '添加数组元素' : '添加字段'" width="400px">
      <a-form>
        <a-form-item :label="currentArrayIndex === -1 ? '字段名（可选）' : '字段名'">
          <a-input
            v-model:value="newFieldName"
            :placeholder="currentArrayIndex === -1 ? '留空则作为数组元素，填写则作为对象字段' : '例如: FieldId, Values, Texts'"
          />
        </a-form-item>
        <a-form-item label="元素类型">
          <a-radio-group v-model:value="newFieldType">
            <a-radio value="field">普通字段</a-radio>
            <a-radio value="array">数组字段</a-radio>
            <a-radio value="object">对象字段</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>

      <template #footer>
        <a-button @click="addFieldDialogVisible = false">取消</a-button>
        <a-button type="primary" @click="confirmAddField">确定</a-button>
      </template>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import FieldConfigEditor from './FieldConfigEditor.vue'

const props = defineProps({
  fieldKey: {
    type: String,
    required: true
  },
  fieldConfig: {
    type: [Object, Array],
    required: true
  },
  path: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['update', 'delete', 'move'])

const localFieldConfig = ref(JSON.parse(JSON.stringify(props.fieldConfig)))
const addFieldDialogVisible = ref(false)
const newFieldName = ref('')
const newFieldType = ref('field')
const currentArrayIndex = ref(null)
const isAddingToObject = ref(false)
const isCollapsed = ref(false)

// 标志位，防止循环更新
let isUpdatingFromProps = false

// 监听 props.fieldConfig 的变化，同步更新 localFieldConfig
watch(() => props.fieldConfig, (newVal) => {
  isUpdatingFromProps = true
  localFieldConfig.value = JSON.parse(JSON.stringify(newVal))
  // 使用 nextTick 确保在下一个 tick 后重置标志
  nextTick(() => {
    isUpdatingFromProps = false
  })
}, { deep: true })

// 判断字段类型
const isFieldConfig = computed(() => {
  return typeof props.fieldConfig === 'object' &&
         !Array.isArray(props.fieldConfig) &&
         'display_name' in props.fieldConfig
})

const isArray = computed(() => {
  return Array.isArray(props.fieldConfig)
})

const isObject = computed(() => {
  return typeof props.fieldConfig === 'object' &&
         !Array.isArray(props.fieldConfig) &&
         !('display_name' in props.fieldConfig)
})

// 监听本地配置变化 - 只在非 props 更新时触发
watch(localFieldConfig, (newVal) => {
  if (!isUpdatingFromProps) {
    emit('update', { path: props.path, value: newVal })
  }
}, { deep: true })

// 删除字段
const handleDelete = () => {
  emit('delete', props.path)
}

// 移动字段
const handleMove = (direction) => {
  emit('move', { path: props.path, direction })
}

// 添加数组元素
const addArrayItem = () => {
  // 弹出对话框让用户选择添加元素类型
  currentArrayIndex.value = -1  // 标记为添加数组元素
  isAddingToObject.value = false
  newFieldName.value = ''  // 数组元素不需要字段名，但复用对话框
  newFieldType.value = 'field'
  addFieldDialogVisible.value = true
}

// 删除数组元素
const removeArrayItem = (index) => {
  localFieldConfig.value.splice(index, 1)
}

// 更新数组元素的字段配置
const updateArrayItemField = (index, newValue) => {
  localFieldConfig.value[index] = newValue
}

// 为数组元素添加字段
const addFieldToArrayItem = (index) => {
  currentArrayIndex.value = index
  isAddingToObject.value = false
  newFieldName.value = ''
  newFieldType.value = 'field'
  addFieldDialogVisible.value = true
}

// 为对象添加字段
const addFieldToObject = () => {
  currentArrayIndex.value = null
  isAddingToObject.value = true
  newFieldName.value = ''
  newFieldType.value = 'field'
  addFieldDialogVisible.value = true
}

// 确认添加字段
const confirmAddField = () => {
  // 如果是添加数组元素（currentArrayIndex === -1）
  if (currentArrayIndex.value === -1) {
    // 检查是否输入了字段名
    if (!newFieldName.value || newFieldName.value.trim() === '') {
      // 字段名为空，直接添加为数组元素
      if (newFieldType.value === 'field') {
        localFieldConfig.value.push({
          display_name: '',
          field_type: 'text',
          default_value: '',
          required: false,
          hidden: false,
          value_type: 'string',
          options: []
        })
      } else if (newFieldType.value === 'array') {
        localFieldConfig.value.push([])
      } else if (newFieldType.value === 'object') {
        localFieldConfig.value.push({})
      }

      addFieldDialogVisible.value = false
      message.success('数组元素添加成功')
      return
    } else {
      // 字段名不为空，添加为包含命名字段的对象
      const newObject = {}
      if (newFieldType.value === 'field') {
        newObject[newFieldName.value] = {
          display_name: '',
          field_type: 'text',
          default_value: '',
          required: false,
          hidden: false,
          value_type: 'string',
          options: []
        }
      } else if (newFieldType.value === 'array') {
        newObject[newFieldName.value] = []
      } else if (newFieldType.value === 'object') {
        newObject[newFieldName.value] = {}
      }

      localFieldConfig.value.push(newObject)
      addFieldDialogVisible.value = false
      message.success('带命名字段的对象添加成功')
      return
    }
  }

  // 其他情况需要字段名
  if (!newFieldName.value) {
    message.warning('请输入字段名')
    return
  }

  if (isAddingToObject.value) {
    // 添加到对象字段
    if (localFieldConfig.value[newFieldName.value]) {
      message.warning('该字段已存在')
      return
    }

    if (newFieldType.value === 'field') {
      localFieldConfig.value[newFieldName.value] = {
        display_name: '',
        field_type: 'text',
        default_value: '',
        required: false,
        hidden: false,
        value_type: 'string',
        options: []
      }
    } else if (newFieldType.value === 'array') {
      localFieldConfig.value[newFieldName.value] = []
    } else if (newFieldType.value === 'object') {
      localFieldConfig.value[newFieldName.value] = {}
    }
  } else if (currentArrayIndex.value !== null) {
    // 添加到数组元素
    const arrayItem = localFieldConfig.value[currentArrayIndex.value]
    if (arrayItem[newFieldName.value]) {
      message.warning('该字段已存在')
      return
    }

    if (newFieldType.value === 'field') {
      arrayItem[newFieldName.value] = {
        display_name: '',
        field_type: 'text',
        default_value: '',
        required: false,
        hidden: false,
        value_type: 'string',
        options: []
      }
    } else if (newFieldType.value === 'array') {
      arrayItem[newFieldName.value] = []
    } else if (newFieldType.value === 'object') {
      arrayItem[newFieldName.value] = {}
    }
  }

  addFieldDialogVisible.value = false
  message.success('字段添加成功')
}
</script>

<style scoped>
.field-tree-node {
  position: relative;
}

.rotate-180 {
  transform: rotate(180deg);
}
</style>
