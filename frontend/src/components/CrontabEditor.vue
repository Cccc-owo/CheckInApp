<template>
  <div class="crontab-editor">
    <!-- 模式选择 Tab -->
    <div class="mode-tabs">
      <button
        v-for="m in modes"
        :key="m"
        :class="{ active: mode === m }"
        @click.prevent="switchMode(m)"
        class="mode-tab"
        type="button"
      >
        {{ modeLabels[m] }}
      </button>
    </div>

    <!-- 快速模式：仅日期 20:00 -->
    <div v-if="mode === 'quick'" class="mode-content">
      <div class="quick-option">
        <el-radio v-model="selectedQuick" label="20:00">
          <span class="option-label">每天 20:00（默认）</span>
          <span class="option-desc">推荐的默认时间</span>
        </el-radio>
      </div>
    </div>

    <!-- 自定义模式：可视化构建器 -->
    <div v-if="mode === 'custom'" class="mode-content">
      <el-form label-width="120px">
        <el-form-item label="时间">
          <el-time-select
            v-model="customTime"
            :start="'00:00'"
            :end="'23:30'"
            step="00:30"
            format="HH:mm"
            placeholder="选择时间"
          />
        </el-form-item>
        <el-form-item label="频率">
          <el-select v-model="customFrequency">
            <el-option label="每天" value="daily" />
            <el-option label="工作日（周一-周五）" value="weekday" />
            <el-option label="周末（周六-周日）" value="weekend" />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <!-- 高级模式：原始 Crontab 表达式 -->
    <div v-if="mode === 'advanced'" class="mode-content">
      <div class="expression-input">
        <el-input
          v-model="advancedExpression"
          type="textarea"
          placeholder="输入 crontab 表达式（例如：0 20 * * *）"
          :rows="2"
          @input="validateExpression"
        />
        <div class="help-text">
          格式: 分钟 小时 日期 月份 星期
          <a href="https://crontab.guru" target="_blank">了解更多</a>
        </div>
      </div>
    </div>

    <!-- 预览部分 -->
    <div v-if="nextExecutions.length" class="preview-section">
      <h4>下一个执行时间：</h4>
      <ul class="execution-list">
        <li v-for="(time, idx) in nextExecutions" :key="idx">{{ time }}</li>
      </ul>
    </div>

    <!-- 验证消息 -->
    <div v-if="validationMessage" :class="['validation-message', validationStatus]">
      {{ validationMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import client from '@/api/client'

const props = defineProps({
  modelValue: String, // 当前 cron 表达式
})

const emit = defineEmits(['update:modelValue'])

const mode = ref('quick')
const modeLabels = {
  quick: '快速',
  custom: '自定义',
  advanced: '高级'
}
const modes = ['quick', 'custom', 'advanced']

// 快速模式
const selectedQuick = ref('20:00')

// 自定义模式
const customTime = ref('20:00')
const customFrequency = ref('daily')

// 高级模式
const advancedExpression = ref(props.modelValue || '0 20 * * *')
const validationMessage = ref('')
const validationStatus = ref('')

// 通用
const nextExecutions = ref([])

// 切换模式 - 防止页面刷新
function switchMode(newMode) {
  mode.value = newMode
}

// 监听 - 只在有效值时更新
watch(selectedQuick, () => {
  const cron = buildCrontabFromQuick()
  emit('update:modelValue', cron)
  if (cron) validateAndPreview(cron)
})

watch(customFrequency, () => {
  const cron = buildCrontabFromCustom()
  emit('update:modelValue', cron)
  if (cron) validateAndPreview(cron)
})

watch(customTime, () => {
  const cron = buildCrontabFromCustom()
  emit('update:modelValue', cron)
  if (cron) validateAndPreview(cron)
})

// 工具函数
function buildCrontabFromQuick() {
  if (selectedQuick.value === '20:00') {
    return '0 20 * * *' // 每天 20:00
  }
  return null
}

function buildCrontabFromCustom() {
  const [hour, minute] = customTime.value.split(':')

  let dow = '*' // 星期
  if (customFrequency.value === 'weekday') {
    dow = '1-5' // 周一至周五
  } else if (customFrequency.value === 'weekend') {
    dow = '0,6' // 周六和周日
  }

  return `${minute} ${hour} * * ${dow}`
}

async function validateExpression() {
  if (!advancedExpression.value.trim()) {
    validationMessage.value = ''
    nextExecutions.value = []
    return
  }

  await validateAndPreview(advancedExpression.value)
}

async function validateAndPreview(expr) {
  if (!expr) {
    validationMessage.value = ''
    nextExecutions.value = []
    return
  }

  try {
    const response = await client.post('/api/tasks/validate-cron', {
      cron_expression: expr
    })

    if (response.valid) {
      validationStatus.value = 'success'
      validationMessage.value = `有效: ${response.description}`
      nextExecutions.value = response.next_times
    }
  } catch (error) {
    validationStatus.value = 'error'
    validationMessage.value = error.message || '无效的 crontab 表达式'
    nextExecutions.value = []
  }
}

// 初始化
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    advancedExpression.value = newVal
  }
}, { immediate: true })
</script>

<style scoped>
.crontab-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 16px;
  background: #f5f7fa;
}

.mode-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  border-bottom: 2px solid #ebeef5;
}

.mode-tab {
  padding: 8px 16px;
  background: none;
  border: none;
  cursor: pointer;
  color: #909399;
  font-weight: 500;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.3s;
}

.mode-tab.active {
  color: #409eff;
  border-bottom-color: #409eff;
}

.mode-content {
  margin: 16px 0;
}

.quick-option {
  padding: 12px;
  background: white;
  border-radius: 4px;
}

.option-label {
  font-weight: 600;
}

.option-desc {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}

.expression-input {
  margin: 12px 0;
}

.help-text {
  margin-top: 8px;
  color: #909399;
  font-size: 12px;
}

.help-text a {
  color: #409eff;
  text-decoration: none;
}

.help-text a:hover {
  text-decoration: underline;
}

.preview-section {
  margin: 16px 0;
  padding: 12px;
  background: white;
  border-radius: 4px;
}

.preview-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
}

.execution-list {
  margin: 0;
  padding-left: 20px;
  font-size: 12px;
  color: #606266;
}

.validation-message {
  padding: 8px 12px;
  border-radius: 4px;
  margin-top: 12px;
  font-size: 12px;
}

.validation-message.success {
  background: #f0f9ff;
  color: #67c23a;
  border: 1px solid #c6e2ff;
}

.validation-message.error {
  background: #fef0f0;
  color: #f56c6c;
  border: 1px solid #fde7e7;
}

.validation-message.info {
  background: #f4f4f5;
  color: #909399;
  border: 1px solid #ebeef5;
}
</style>
