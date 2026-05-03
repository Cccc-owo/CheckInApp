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
  <div class="rounded-lg border border-dashed border-zinc-200 bg-white p-6 text-center">
    <div
      class="mx-auto mb-3 flex size-10 items-center justify-center rounded-md bg-zinc-100 text-zinc-600"
    >
      <Loader2 v-if="type === 'loading'" class="size-5 animate-spin" />
      <AlertCircle v-else-if="type === 'error'" class="size-5" />
      <Search v-else class="size-5" />
    </div>
    <div class="text-sm font-semibold text-zinc-900">{{ title }}</div>
    <p v-if="description" class="mx-auto mt-1 max-w-md text-sm text-zinc-500">{{ description }}</p>
    <button
      v-if="actionLabel"
      type="button"
      class="mt-4 inline-flex items-center rounded-md border border-zinc-200 px-3 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 active:translate-y-px"
      @click="$emit('action')"
    >
      {{ actionLabel }}
    </button>
  </div>
</template>
