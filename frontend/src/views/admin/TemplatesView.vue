<template>
  <Layout>
    <div class="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 p-6">
      <div class="max-w-7xl mx-auto">
        <!-- Header -->
        <div class="mb-8 animate-fade-in">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h1 class="text-3xl font-bold text-gradient mb-2">任务模板管理</h1>
              <p class="text-gray-600">JSON 映射架构 - 配置即结构，字段名保持原样</p>
            </div>
            <button @click="showCreateDialog" class="md3-button-filled">
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              新建模板
            </button>
          </div>
        </div>

        <!-- Templates List -->
        <div v-if="loading && templates.length === 0" class="space-y-4">
          <div v-for="i in 3" :key="i" class="fluent-card p-6">
            <div class="skeleton h-6 w-1/3 mb-3"></div>
            <div class="skeleton h-4 w-full mb-2"></div>
            <div class="skeleton h-4 w-2/3"></div>
          </div>
        </div>

        <div v-else-if="templates.length === 0" class="fluent-card p-12 text-center">
          <svg class="w-20 h-20 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 class="text-xl font-semibold text-gray-700 mb-2">暂无模板</h3>
          <p class="text-gray-500 mb-4">创建第一个模板，让用户更轻松地创建打卡任务</p>
          <button @click="showCreateDialog" class="md3-button-filled">新建模板</button>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="template in templates"
            :key="template.id"
            class="fluent-card p-6 hover:shadow-xl transition-all animate-slide-up"
          >
            <div class="flex items-start justify-between mb-4">
              <div class="flex-1">
                <h3 class="text-lg font-semibold text-gray-800 mb-2">{{ template.name }}</h3>
                <p class="text-sm text-gray-600 mb-3">{{ template.description || '无描述' }}</p>
                <span :class="template.is_active ? 'status-success' : 'status-info'">
                  {{ template.is_active ? '已启用' : '已禁用' }}
                </span>
              </div>
            </div>

            <div class="flex items-center gap-2 mt-4">
              <button @click="previewTemplate(template)" class="md3-button-outlined text-sm">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                预览
              </button>
              <button @click="editTemplate(template)" class="md3-button-outlined text-sm">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                编辑
              </button>
              <button @click="deleteTemplate(template)" class="md3-button-text text-sm text-red-600">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                删除
              </button>
            </div>
          </div>
        </div>

        <!-- Create/Edit Dialog -->
        <el-dialog
          v-model="dialogVisible"
          :title="dialogMode === 'create' ? '新建模板' : '编辑模板'"
          width="95%"
          :close-on-click-modal="false"
          class="template-editor-dialog"
        >
          <el-form :model="formData" label-width="120px" ref="formRef">
            <el-form-item label="模板名称" required>
              <el-input v-model="formData.name" placeholder="请输入模板名称" maxlength="100" show-word-limit />
            </el-form-item>

            <el-form-item label="模板描述">
              <el-input v-model="formData.description" type="textarea" :rows="2" placeholder="请输入模板描述" />
            </el-form-item>

            <el-form-item label="父模板">
              <el-select v-model="formData.parent_id" placeholder="可选，继承父模板的字段配置" clearable class="w-full">
                <el-option
                  v-for="template in availableParentTemplates"
                  :key="template.id"
                  :label="template.name"
                  :value="template.id"
                  :disabled="template.id === currentTemplateId"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="是否启用">
              <el-switch v-model="formData.is_active" />
            </el-form-item>

            <el-divider content-position="left">
              <span class="text-lg font-bold">Payload 配置 (JSON 映射)</span>
            </el-divider>

            <el-alert
              title="💡 JSON 映射架构"
              type="info"
              :closable="false"
              class="mb-4"
            >
              <p class="text-sm mb-2">
                <strong>配置即结构</strong>：模板配置完全映射到生成的 Payload 结构
              </p>
              <p class="text-sm mb-2">
                <strong>字段名保持原样</strong>：不进行任何大小写转换
              </p>
              <p class="text-sm">
                <strong>ThreadId</strong> 由用户填写，无需在模板中配置
              </p>
            </el-alert>

            <!-- 字段配置编辑器 -->
            <div class="field-config-editor">
              <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold text-gray-800">字段配置</h3>
                <el-dropdown @command="handleAddField">
                  <el-button type="primary">
                    添加字段
                    <el-icon class="el-icon--right"><arrow-down /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="field">
                        <svg class="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                        </svg>
                        普通字段
                      </el-dropdown-item>
                      <el-dropdown-item command="array">
                        <svg class="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                        </svg>
                        数组字段
                      </el-dropdown-item>
                      <el-dropdown-item command="object">
                        <svg class="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        对象字段
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>

              <!-- 递归渲染字段树 -->
              <div v-if="Object.keys(formData.field_config).length === 0" class="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
                <svg class="w-16 h-16 mx-auto text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 class="text-lg font-semibold text-gray-700 mb-2">暂无字段配置</h3>
                <p class="text-sm text-gray-500">点击上方"添加字段"开始配置模板</p>
              </div>

              <div v-else class="space-y-3">
                <FieldTreeNode
                  v-for="(config, key) in formData.field_config"
                  :key="key"
                  :field-key="key"
                  :field-config="config"
                  :path="[key]"
                  @update="(event) => updateField(event.path, event.value)"
                  @delete="(path) => deleteField(path)"
                  @move="(event) => moveField(event.path, event.direction)"
                />
              </div>
            </div>

            <!-- JSON 预览 -->
            <el-divider content-position="left">
              <span class="text-lg font-bold">JSON 预览</span>
            </el-divider>

            <div class="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-auto max-h-96">
              <pre>{{ JSON.stringify(formData.field_config, null, 2) }}</pre>
            </div>
          </el-form>

          <template #footer>
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="handleSubmit" :loading="submitting">
              {{ dialogMode === 'create' ? '创建' : '更新' }}
            </el-button>
          </template>
        </el-dialog>

        <!-- Add Field Dialog -->
        <el-dialog v-model="addFieldDialogVisible" :title="`添加${fieldTypeLabel}`" width="500px">
          <el-form @submit.prevent="confirmAddField">
            <el-form-item label="字段名">
              <el-input
                v-model="newFieldName"
                placeholder="例如: Id, Group1, DateTarget"
                @keyup.enter="confirmAddField"
              />
              <span class="text-xs text-gray-500 mt-1">
                💡 字段名将保持原样，不会进行大小写转换
              </span>
            </el-form-item>
          </el-form>

          <template #footer>
            <el-button @click="addFieldDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="confirmAddField">确定</el-button>
          </template>
        </el-dialog>

        <!-- Preview Dialog -->
        <el-dialog v-model="previewDialogVisible" title="模板预览" width="90%">
          <div v-if="previewData" class="space-y-4">
            <div class="bg-gray-50 rounded p-4">
              <h4 class="font-semibold mb-2">生成的 Payload（使用默认值）：</h4>
              <pre class="text-xs bg-white p-3 rounded border overflow-auto max-h-96">{{ JSON.stringify(previewData.preview_payload, null, 2) }}</pre>
            </div>

            <div class="bg-gray-50 rounded p-4">
              <h4 class="font-semibold mb-2">字段配置：</h4>
              <pre class="text-xs bg-white p-3 rounded border overflow-auto max-h-96">{{ JSON.stringify(previewData.field_config, null, 2) }}</pre>
            </div>
          </div>

          <template #footer>
            <el-button @click="previewDialogVisible = false">关闭</el-button>
          </template>
        </el-dialog>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, ElIcon } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import Layout from '@/components/Layout.vue'
import FieldTreeNode from '@/components/FieldTreeNode.vue'
import { useTemplateStore } from '@/stores/template'

const templateStore = useTemplateStore()

const templates = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref('create')
const currentTemplateId = ref(null)
const submitting = ref(false)

const previewDialogVisible = ref(false)
const previewData = ref(null)

const addFieldDialogVisible = ref(false)
const newFieldName = ref('')
const newFieldType = ref('field')

const formData = ref({
  name: '',
  description: '',
  parent_id: null,
  is_active: true,
  field_config: {}
})

const availableParentTemplates = computed(() => {
  if (dialogMode.value === 'create') {
    return templates.value
  }
  return templates.value.filter(t => t.id !== currentTemplateId.value)
})

const fieldTypeLabel = computed(() => {
  const labels = {
    field: '普通字段',
    array: '数组字段',
    object: '对象字段'
  }
  return labels[newFieldType.value] || '字段'
})

function createDefaultFieldConfig() {
  return {
    display_name: '',
    field_type: 'text',
    default_value: '',
    required: false,
    hidden: false,
    placeholder: '',
    value_type: 'string',
    options: []
  }
}

const fetchTemplates = async () => {
  loading.value = true
  try {
    templates.value = await templateStore.fetchTemplates()
  } catch (error) {
    ElMessage.error(error.message || '获取模板列表失败')
  } finally {
    loading.value = false
  }
}

const showCreateDialog = () => {
  dialogMode.value = 'create'
  currentTemplateId.value = null
  formData.value = {
    name: '',
    description: '',
    parent_id: null,
    is_active: true,
    field_config: {}
  }
  dialogVisible.value = true
}

const editTemplate = (template) => {
  dialogMode.value = 'edit'
  currentTemplateId.value = template.id

  const fieldConfig = JSON.parse(template.field_config)

  formData.value = {
    name: template.name,
    description: template.description || '',
    parent_id: template.parent_id || null,
    is_active: template.is_active,
    field_config: fieldConfig
  }

  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formData.value.name) {
    ElMessage.warning('请输入模板名称')
    return
  }

  submitting.value = true
  try {
    const templateData = {
      name: formData.value.name,
      description: formData.value.description,
      parent_id: formData.value.parent_id,
      is_active: formData.value.is_active,
      field_config: JSON.stringify(formData.value.field_config)
    }

    if (dialogMode.value === 'create') {
      await templateStore.createTemplate(templateData)
      ElMessage.success('模板创建成功')
    } else {
      await templateStore.updateTemplate(currentTemplateId.value, templateData)
      ElMessage.success('模板更新成功')
    }

    dialogVisible.value = false
    await fetchTemplates()
  } catch (error) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const deleteTemplate = async (template) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板"${template.name}"吗？此操作不可撤销。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await templateStore.deleteTemplate(template.id)
    ElMessage.success('模板删除成功')
    await fetchTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const previewTemplate = async (template) => {
  try {
    previewData.value = await templateStore.previewTemplate(template.id)
    previewDialogVisible.value = true
  } catch (error) {
    ElMessage.error(error.message || '预览失败')
  }
}

const handleAddField = (type) => {
  newFieldType.value = type
  newFieldName.value = ''
  addFieldDialogVisible.value = true
}

const confirmAddField = () => {
  if (!newFieldName.value) {
    ElMessage.warning('请输入字段名')
    return
  }

  if (formData.value.field_config[newFieldName.value]) {
    ElMessage.warning('该字段已存在')
    return
  }

  // 创建对应类型的字段
  if (newFieldType.value === 'field') {
    formData.value.field_config[newFieldName.value] = createDefaultFieldConfig()
  } else if (newFieldType.value === 'array') {
    formData.value.field_config[newFieldName.value] = []
  } else if (newFieldType.value === 'object') {
    formData.value.field_config[newFieldName.value] = {}
  }

  addFieldDialogVisible.value = false
  ElMessage.success('字段添加成功')
}

const updateField = (path, newValue) => {
  // 通过路径更新嵌套字段
  let target = formData.value.field_config
  for (let i = 0; i < path.length - 1; i++) {
    target = target[path[i]]
  }
  target[path[path.length - 1]] = newValue
}

const deleteField = (path) => {
  // 通过路径删除嵌套字段
  console.log('🗑️ 删除字段 - 路径:', path)

  if (!path || path.length === 0) return

  // 创建一个新的 field_config 副本以触发响应性
  const newConfig = JSON.parse(JSON.stringify(formData.value.field_config))
  let target = newConfig

  // 导航到父对象/数组
  for (let i = 0; i < path.length - 1; i++) {
    if (!target || typeof target !== 'object') {
      console.error('❌ 删除失败：路径无效', path, 'at index', i)
      return
    }
    target = target[path[i]]
  }

  if (!target || typeof target !== 'object') {
    console.error('❌ 删除失败：父对象不存在', path)
    return
  }

  const lastKey = path[path.length - 1]

  // 如果父容器是数组，使用 splice；如果是对象，使用 delete
  if (Array.isArray(target)) {
    target.splice(lastKey, 1)
  } else {
    delete target[lastKey]
  }

  // 替换整个 field_config 以触发 Vue 响应性
  formData.value.field_config = newConfig

  console.log('✅ 字段已删除:', path)
}

const moveField = (path, direction) => {
  // 通过路径移动字段
  if (!path || path.length === 0) return

  // 创建一个新的 field_config 副本以触发响应性
  const newConfig = JSON.parse(JSON.stringify(formData.value.field_config))
  let parent = newConfig

  // 导航到父对象/数组
  for (let i = 0; i < path.length - 1; i++) {
    if (!parent || typeof parent !== 'object') {
      console.error('移动失败：路径无效', path, 'at index', i)
      return
    }
    parent = parent[path[i]]
  }

  if (!parent || typeof parent !== 'object') {
    console.error('移动失败：父对象不存在', path)
    return
  }

  const fieldKey = path[path.length - 1]

  if (Array.isArray(parent)) {
    // 数组：使用索引移动
    const index = fieldKey
    if (direction === 'up' && index > 0) {
      // 向上移动
      const temp = parent[index]
      parent[index] = parent[index - 1]
      parent[index - 1] = temp
    } else if (direction === 'down' && index < parent.length - 1) {
      // 向下移动
      const temp = parent[index]
      parent[index] = parent[index + 1]
      parent[index + 1] = temp
    } else {
      // 已经在边界，无需移动
      return
    }
  } else {
    // 对象：需要重建对象以改变键的顺序
    const keys = Object.keys(parent)
    const currentIndex = keys.indexOf(fieldKey)

    if (currentIndex === -1) return

    let newIndex = currentIndex
    if (direction === 'up' && currentIndex > 0) {
      newIndex = currentIndex - 1
    } else if (direction === 'down' && currentIndex < keys.length - 1) {
      newIndex = currentIndex + 1
    } else {
      // 已经在边界，无需移动
      return
    }

    if (newIndex !== currentIndex) {
      // 交换键的位置
      const temp = keys[currentIndex]
      keys[currentIndex] = keys[newIndex]
      keys[newIndex] = temp

      // 重建对象
      const newParent = {}
      keys.forEach(key => {
        newParent[key] = parent[key]
      })

      // 更新父对象的所有键
      Object.keys(parent).forEach(key => delete parent[key])
      Object.assign(parent, newParent)
    }
  }

  // 替换整个 field_config 以触发 Vue 响应性
  formData.value.field_config = newConfig

  console.log('✅ 字段已移动:', path, direction)
}

onMounted(() => {
  fetchTemplates()
})
</script>

<style scoped>
.field-config-editor {
  min-height: 200px;
}

.template-editor-dialog :deep(.el-dialog__body) {
  max-height: 70vh;
  overflow-y: auto;
}
</style>
