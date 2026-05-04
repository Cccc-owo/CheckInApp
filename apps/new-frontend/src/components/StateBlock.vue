<script setup lang="ts">
import { AlertCircle, Loader2, Search } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'

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
    class="grid gap-4 rounded-xl border border-dashed border-border bg-card p-4 text-left text-card-foreground shadow-sm sm:grid-cols-[auto_minmax(0,1fr)_auto] sm:items-center dark:shadow-none"
  >
    <div
      class="flex size-10 items-center justify-center rounded-lg border border-border bg-muted text-muted-foreground"
      :class="{
        'border-[var(--tone-danger-border)] bg-[var(--tone-danger-bg)] text-[var(--tone-danger-fg)]':
          type === 'error',
        'border-[var(--tone-info-border)] bg-[var(--tone-info-bg)] text-[var(--tone-info-fg)]':
          type === 'loading',
      }"
    >
      <Loader2 v-if="type === 'loading'" class="size-5 animate-spin" />
      <AlertCircle v-else-if="type === 'error'" class="size-5" />
      <Search v-else class="size-5" />
    </div>
    <div class="min-w-0">
      <div class="text-sm font-semibold text-foreground">{{ title }}</div>
      <p v-if="description" class="mt-1 text-sm leading-5 text-muted-foreground">
        {{ description }}
      </p>
    </div>
    <Button
      v-if="actionLabel"
      type="button"
      variant="outline"
      class="sm:justify-self-end"
      @click="$emit('action')"
    >
      {{ actionLabel }}
    </Button>
  </div>
</template>
