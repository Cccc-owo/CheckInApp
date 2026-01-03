<template>
  <a-card class="md3-card text-center" style="padding: 48px 20px;">
    <!-- 图标 -->
    <div v-if="icon" class="mb-6">
      <component
        :is="icon"
        class="text-8xl mx-auto"
        :class="iconColorClass"
      />
    </div>

    <!-- 标题 -->
    <h3 class="md3-title-large text-on-surface mb-2">
      {{ title || '暂无数据' }}
    </h3>

    <!-- 描述 -->
    <p class="md3-body-medium text-on-surface-variant mb-6">
      {{ description || '当前没有内容可显示' }}
    </p>

    <!-- 操作按钮（可选） -->
    <div v-if="$slots.action || actionText">
      <slot name="action">
        <a-button
          v-if="actionText"
          type="primary"
          @click="handleAction"
          :loading="loading"
        >
          <template v-if="actionIcon" #icon>
            <component :is="actionIcon" />
          </template>
          {{ actionText }}
        </a-button>
      </slot>
    </div>
  </a-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /**
   * 图标组件
   */
  icon: {
    type: Object,
    default: null
  },

  /**
   * 标题文本
   */
  title: {
    type: String,
    default: ''
  },

  /**
   * 描述文本
   */
  description: {
    type: String,
    default: ''
  },

  /**
   * 操作按钮文本
   */
  actionText: {
    type: String,
    default: ''
  },

  /**
   * 操作按钮图标
   */
  actionIcon: {
    type: Object,
    default: null
  },

  /**
   * 加载状态
   */
  loading: {
    type: Boolean,
    default: false
  },

  /**
   * 图标颜色
   */
  iconColor: {
    type: String,
    default: 'neutral',
    validator: (v) => ['primary', 'neutral', 'success', 'warning', 'error'].includes(v)
  }
})

const emit = defineEmits(['action'])

const handleAction = () => {
  emit('action')
}

const iconColorClass = computed(() => {
  const colors = {
    primary: 'text-primary',
    neutral: 'text-on-surface-variant',
    success: 'text-green-500',
    warning: 'text-orange-500',
    error: 'text-error'
  }
  return colors[props.iconColor]
})
</script>
