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
        <a-radio-group v-model:value="selectedQuick">
          <a-radio value="20:00">
            <span class="option-label">每天 20:00（默认）</span>
            <span class="option-desc">推荐的默认时间</span>
          </a-radio>
        </a-radio-group>
      </div>
    </div>

    <!-- 自定义模式:可视化构建器 -->
    <div v-if="mode === 'custom'" class="mode-content">
      <a-form layout="vertical">
        <a-form-item label="时间" name="customTime">
          <a-time-picker
            id="cron-custom-time"
            v-model:value="customTimeValue"
            format="HH:mm"
            placeholder="选择时间"
            :minute-step="30"
            @change="onCustomTimeChange"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="频率" name="customFrequency">
          <a-select
            id="cron-custom-frequency"
            v-model:value="customFrequency"
            style="width: 100%"
          >
            <a-select-option value="daily">每天</a-select-option>
            <a-select-option value="weekday">工作日（周一-周五）</a-select-option>
            <a-select-option value="weekend">周末（周六-周日）</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </div>

    <!-- 高级模式：原始 Crontab 表达式 -->
    <div v-if="mode === 'advanced'" class="mode-content">
      <div class="expression-input">
        <a-textarea
          v-model:value="advancedExpression"
          placeholder="输入 crontab 表达式（例如：0 20 * * *）"
          :rows="2"
          @input="handleAdvancedInput"
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
import { ref, watch, onBeforeUnmount } from 'vue'
import dayjs from 'dayjs'
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
const customTimeValue = ref(dayjs('20:00', 'HH:mm'))
const customFrequency = ref('daily')

// 高级模式
const advancedExpression = ref(props.modelValue || '0 20 * * *')
const validationMessage = ref('')
const validationStatus = ref('')

// 通用
const nextExecutions = ref([])

// 标志：是否正在手动编辑高级模式（防止自动解析导致模式切换）
let isManualEditing = false

// 切换模式 - 防止页面刷新
function switchMode(newMode) {
  mode.value = newMode

  // 切换到快速模式时，自动选择默认值并触发保存
  if (newMode === 'quick') {
    selectedQuick.value = '20:00'
    const cron = buildCrontabFromQuick()
    advancedExpression.value = cron
    emit('update:modelValue', cron)
    if (cron) validateAndPreview(cron)
  }
  // 切换到自定义模式时，基于当前值构建 cron
  else if (newMode === 'custom') {
    const cron = buildCrontabFromCustom()
    advancedExpression.value = cron
    emit('update:modelValue', cron)
    if (cron) validateAndPreview(cron)
  }
  // 切换到高级模式时，使用当前的 advancedExpression
  else if (newMode === 'advanced') {
    if (advancedExpression.value) {
      emit('update:modelValue', advancedExpression.value)
      validateAndPreview(advancedExpression.value)
    }
  }
}

// 处理时间选择器变化
function onCustomTimeChange(time) {
  if (time) {
    customTime.value = time.format('HH:mm')
  }
}

// 监听 - 只在有效值时更新
watch(selectedQuick, () => {
  const cron = buildCrontabFromQuick()
  advancedExpression.value = cron
  emit('update:modelValue', cron)
  if (cron) validateAndPreview(cron)
})

watch(customFrequency, () => {
  const cron = buildCrontabFromCustom()
  advancedExpression.value = cron
  emit('update:modelValue', cron)
  if (cron) validateAndPreview(cron)
})

watch(customTime, () => {
  const cron = buildCrontabFromCustom()
  advancedExpression.value = cron
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

// 处理高级模式输入 - 使用防抖以避免频繁调用API
let debounceTimer = null
function handleAdvancedInput() {
  // 设置手动编辑标志
  isManualEditing = true

  // 立即触发 emit，保证值实时同步
  emit('update:modelValue', advancedExpression.value)

  // 使用防抖延迟验证
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }

  debounceTimer = setTimeout(async () => {
    if (!advancedExpression.value.trim()) {
      validationMessage.value = ''
      nextExecutions.value = []
      return
    }

    await validateAndPreview(advancedExpression.value)
  }, 500) // 500ms 防抖延迟
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

// 解析 cron 表达式并设置对应的模式
function parseCronExpression(cron) {
  if (!cron) return

  advancedExpression.value = cron

  // 尝试匹配快速模式: 0 20 * * *
  if (cron === '0 20 * * *') {
    mode.value = 'quick'
    selectedQuick.value = '20:00'
    validateAndPreview(cron)
    return
  }

  // 尝试解析为自定义模式
  const parts = cron.trim().split(/\s+/)
  if (parts.length === 5) {
    const [minute, hour, day, month, dow] = parts

    // 检查是否是简单的每天或工作日/周末模式
    if (day === '*' && month === '*') {
      const hourNum = parseInt(hour)
      const minuteNum = parseInt(minute)

      if (!isNaN(hourNum) && !isNaN(minuteNum) && hourNum >= 0 && hourNum < 24 && minuteNum >= 0 && minuteNum < 60) {
        mode.value = 'custom'
        customTime.value = `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`
        customTimeValue.value = dayjs(customTime.value, 'HH:mm')

        // 识别频率
        if (dow === '*') {
          customFrequency.value = 'daily'
        } else if (dow === '1-5') {
          customFrequency.value = 'weekday'
        } else if (dow === '0,6' || dow === '6,0') {
          customFrequency.value = 'weekend'
        } else {
          // 不支持的星期模式，使用高级模式
          mode.value = 'advanced'
        }

        validateAndPreview(cron)
        return
      }
    }
  }

  // 其他情况使用高级模式
  mode.value = 'advanced'
  validateAndPreview(cron)
}

// 初始化 - 解析传入的 cron 表达式
watch(() => props.modelValue, (newVal) => {
  // 如果正在手动编辑高级模式，跳过自动解析
  if (isManualEditing) {
    isManualEditing = false // 重置标志
    return
  }

  if (newVal) {
    parseCronExpression(newVal)
  }
}, { immediate: true })

// 组件卸载时清理防抖定时器，防止内存泄漏
onBeforeUnmount(() => {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
})
</script>

<style scoped>
.crontab-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 16px;
  background: #f5f7fa;
  transition: all 0.3s;
}

.dark .crontab-editor {
  border-color: #3a3a3c;
  background: #2c2c2e;
}

.mode-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  border-bottom: 2px solid #ebeef5;
  transition: border-color 0.3s;
}

.dark .mode-tabs {
  border-bottom-color: #3a3a3c;
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

.dark .mode-tab {
  color: #a0a0a3;
}

.mode-tab.active {
  color: #409eff;
  border-bottom-color: #409eff;
}

.dark .mode-tab.active {
  color: #81c784;
  border-bottom-color: #81c784;
}

.mode-content {
  margin: 16px 0;
}

.quick-option {
  padding: 12px;
  background: white;
  border-radius: 4px;
  transition: background 0.3s;
}

.dark .quick-option {
  background: #1c1c1e;
}

.option-label {
  font-weight: 600;
  color: #1c1b1f;
}

.dark .option-label {
  color: #e5e5e7;
}

.option-desc {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}

.dark .option-desc {
  color: #a0a0a3;
}

.expression-input {
  margin: 12px 0;
}

.help-text {
  margin-top: 8px;
  color: #909399;
  font-size: 12px;
}

.dark .help-text {
  color: #a0a0a3;
}

.help-text a {
  color: #409eff;
  text-decoration: none;
}

.dark .help-text a {
  color: #81c784;
}

.help-text a:hover {
  text-decoration: underline;
}

.preview-section {
  margin: 16px 0;
  padding: 12px;
  background: white;
  border-radius: 4px;
  transition: background 0.3s;
}

.dark .preview-section {
  background: #1c1c1e;
}

.preview-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #1c1b1f;
}

.dark .preview-section h4 {
  color: #e5e5e7;
}

.execution-list {
  margin: 0;
  padding-left: 20px;
  font-size: 12px;
  color: #606266;
}

.dark .execution-list {
  color: #a0a0a3;
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

.dark .validation-message.success {
  background: rgba(129, 199, 132, 0.1);
  color: #81c784;
  border-color: rgba(129, 199, 132, 0.3);
}

.validation-message.error {
  background: #fef0f0;
  color: #f56c6c;
  border: 1px solid #fde7e7;
}

.dark .validation-message.error {
  background: rgba(244, 67, 54, 0.1);
  color: #ef5350;
  border-color: rgba(244, 67, 54, 0.3);
}

.validation-message.info {
  background: #f4f4f5;
  color: #909399;
  border: 1px solid #ebeef5;
}

.dark .validation-message.info {
  background: #2c2c2e;
  color: #a0a0a3;
  border-color: #3a3a3c;
}
</style>
