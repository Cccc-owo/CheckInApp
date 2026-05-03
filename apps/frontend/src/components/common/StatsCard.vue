<template>
  <a-card
    class="md3-card animate-slide-up transition-standard hover:elevation-3"
    :style="{ animationDelay }"
  >
    <div class="flex items-center justify-between">
      <!-- 数值和标签 -->
      <div class="flex-1">
        <p class="md3-label-medium text-on-surface-variant mb-1">{{ label }}</p>
        <p class="md3-headline-medium" :class="valueColorClass">
          {{ formattedValue }}
        </p>
        <p v-if="subtitle" class="md3-body-small text-on-surface-variant mt-1">
          {{ subtitle }}
        </p>
      </div>

      <!-- 图标 -->
      <div
        v-if="icon"
        class="w-12 h-12 rounded-md3 flex items-center justify-center flex-shrink-0 ml-4"
        :class="iconBgClass"
      >
        <component :is="icon" :class="iconColorClass" class="text-2xl" />
      </div>
    </div>

    <!-- 趋势指示器（可选） -->
    <div v-if="trend !== undefined" class="mt-3 pt-3 border-t border-outline-variant">
      <div class="flex items-center text-sm">
        <component :is="trendIcon" :class="trendColorClass" class="mr-1" />
        <span :class="trendColorClass" class="md3-label-small">
          {{ trendText }}
        </span>
      </div>
    </div>
  </a-card>
</template>

<script setup>
import { computed } from 'vue';
import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons-vue';

const props = defineProps({
  /**
   * 卡片标签
   */
  label: {
    type: String,
    required: true,
  },

  /**
   * 显示的数值
   */
  value: {
    type: [String, Number],
    required: true,
  },

  /**
   * 副标题/描述
   */
  subtitle: {
    type: String,
    default: '',
  },

  /**
   * 图标组件
   */
  icon: {
    type: Object,
    default: null,
  },

  /**
   * 颜色主题
   */
  color: {
    type: String,
    default: 'primary',
    validator: v => ['primary', 'success', 'warning', 'error', 'info', 'neutral'].includes(v),
  },

  /**
   * 动画延迟（秒）
   */
  delay: {
    type: Number,
    default: 0,
  },

  /**
   * 格式化函数
   */
  formatter: {
    type: Function,
    default: null,
  },

  /**
   * 趋势值（正数上升，负数下降，0持平）
   */
  trend: {
    type: Number,
    default: undefined,
  },

  /**
   * 趋势文本
   */
  trendText: {
    type: String,
    default: '',
  },
});

// 动画延迟
const animationDelay = computed(() => `${props.delay}s`);

// 格式化数值
const formattedValue = computed(() => {
  if (props.formatter) {
    return props.formatter(props.value);
  }
  return props.value;
});

// 颜色映射
const colorClasses = {
  primary: {
    value: 'text-primary',
    iconBg: 'bg-primary-100 dark:bg-primary-900/30',
    icon: 'text-primary',
  },
  success: {
    value: 'text-green-600 dark:text-green-400',
    iconBg: 'bg-green-100 dark:bg-green-900/30',
    icon: 'text-green-600 dark:text-green-400',
  },
  warning: {
    value: 'text-orange-600 dark:text-orange-400',
    iconBg: 'bg-orange-100 dark:bg-orange-900/30',
    icon: 'text-orange-600 dark:text-orange-400',
  },
  error: {
    value: 'text-error',
    iconBg: 'bg-red-100 dark:bg-red-900/30',
    icon: 'text-error',
  },
  info: {
    value: 'text-secondary',
    iconBg: 'bg-blue-100 dark:bg-blue-900/30',
    icon: 'text-secondary',
  },
  neutral: {
    value: 'text-on-surface',
    iconBg: 'bg-surface-container',
    icon: 'text-on-surface-variant',
  },
};

const valueColorClass = computed(() => colorClasses[props.color].value);
const iconBgClass = computed(() => colorClasses[props.color].iconBg);
const iconColorClass = computed(() => colorClasses[props.color].icon);

// 趋势图标和颜色
const trendIcon = computed(() => {
  if (props.trend === undefined) return null;
  if (props.trend > 0) return ArrowUpOutlined;
  if (props.trend < 0) return ArrowDownOutlined;
  return MinusOutlined;
});

const trendColorClass = computed(() => {
  if (props.trend === undefined) return '';
  if (props.trend > 0) return 'text-green-600 dark:text-green-400';
  if (props.trend < 0) return 'text-red-600 dark:text-red-400';
  return 'text-on-surface-variant';
});
</script>

<style scoped>
.md3-card:hover {
  transform: translateY(-2px);
}
</style>
