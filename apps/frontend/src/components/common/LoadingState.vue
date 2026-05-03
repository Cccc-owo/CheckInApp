<template>
  <div v-if="loading" class="loading-state">
    <!-- 卡片骨架屏 -->
    <div v-if="type === 'card'" class="grid grid-cols-1 gap-4">
      <a-card v-for="i in count" :key="i" class="md3-card">
        <a-skeleton :active="true" :paragraph="{ rows: paragraphRows }" :avatar="showAvatar" />
      </a-card>
    </div>

    <!-- 列表骨架屏 -->
    <div v-else-if="type === 'list'" class="space-y-4">
      <a-card v-for="i in count" :key="i" class="md3-card">
        <a-skeleton :active="true" :paragraph="{ rows: 1 }" :avatar="showAvatar" />
      </a-card>
    </div>

    <!-- 表格骨架屏 -->
    <a-card v-else-if="type === 'table'" class="md3-card">
      <a-skeleton :active="true" :paragraph="{ rows: count * 2 }" />
    </a-card>

    <!-- 默认骨架屏 -->
    <a-card v-else class="md3-card">
      <a-skeleton :active="true" :paragraph="{ rows: paragraphRows }" :avatar="showAvatar" />
    </a-card>
  </div>
</template>

<script setup>
defineProps({
  /**
   * 是否显示加载状态
   */
  loading: {
    type: Boolean,
    default: true,
  },

  /**
   * 骨架屏类型
   */
  type: {
    type: String,
    default: 'card',
    validator: v => ['card', 'list', 'table', 'default'].includes(v),
  },

  /**
   * 骨架屏数量
   */
  count: {
    type: Number,
    default: 3,
  },

  /**
   * 段落行数
   */
  paragraphRows: {
    type: Number,
    default: 4,
  },

  /**
   * 是否显示头像
   */
  showAvatar: {
    type: Boolean,
    default: false,
  },
});
</script>

<style scoped>
.loading-state {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
