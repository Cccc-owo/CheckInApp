<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { adminApi } from '@/api'
import StateBlock from '@/components/StateBlock.vue'
import { buttonBase, buttonTone, cardClass, inputClass, sectionHeaderClass } from '@/components/ui'
import { extractErrorMessage } from '@/utils/format'

const loading = ref(true)
const error = ref('')
const lines = ref(200)
const logs = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const result = await adminApi.logs(lines.value)
    logs.value = result.logs
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section :class="[cardClass, 'overflow-hidden']">
    <div :class="sectionHeaderClass">
      <div>
        <h2 class="font-semibold">系统日志</h2>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <input
          v-model.number="lines"
          :class="inputClass"
          type="number"
          min="1"
          max="2000"
          class="max-w-40"
        />
        <button :class="[buttonBase, buttonTone.secondary]" type="button" @click="load">
          刷新日志
        </button>
      </div>
    </div>
    <StateBlock v-if="loading" title="正在加载日志" type="loading" />
    <StateBlock
      v-else-if="error"
      title="日志加载失败"
      :description="error"
      type="error"
      action-label="重试"
      @action="load"
    />
    <StateBlock v-else-if="!logs" title="暂无日志" />
    <pre
      v-else
      class="max-h-[70vh] overflow-auto bg-zinc-950 p-4 font-mono text-xs leading-5 text-zinc-100"
      >{{ logs || '无日志' }}</pre
    >
  </section>
</template>
