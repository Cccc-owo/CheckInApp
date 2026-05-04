<script setup lang="ts">
import { AlertCircle, Loader2, Search } from 'lucide-vue-next'

defineProps<{
  title: string
  description?: string
  type?: 'loading' | 'empty' | 'error'
  actionLabel?: string
}>()

defineEmits<{
  action: []
}>()
</script>

<template>
  <div
    class="rounded-lg border border-dashed border-zinc-200 bg-white p-6 text-center shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
  >
    <div
      class="mx-auto mb-3 flex size-10 items-center justify-center rounded-md border border-zinc-200 bg-zinc-50 text-zinc-600 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-300"
      :class="{
        'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900/70 dark:bg-rose-950/50 dark:text-rose-300':
          type === 'error',
        'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/50 dark:text-emerald-300':
          type === 'loading',
      }"
    >
      <Loader2 v-if="type === 'loading'" class="size-5 animate-spin" />
      <AlertCircle v-else-if="type === 'error'" class="size-5" />
      <Search v-else class="size-5" />
    </div>
    <div class="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{{ title }}</div>
    <p v-if="description" class="mx-auto mt-1 max-w-md text-sm text-zinc-500 dark:text-zinc-400">
      {{ description }}
    </p>
    <button
      v-if="actionLabel"
      type="button"
      class="mt-4 inline-flex min-h-9 items-center rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm font-medium text-zinc-700 shadow-sm transition hover:bg-zinc-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-700/20 active:translate-y-px dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200 dark:hover:bg-zinc-800"
      @click="$emit('action')"
    >
      {{ actionLabel }}
    </button>
  </div>
</template>
