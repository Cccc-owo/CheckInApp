<script setup lang="ts">
import { useRouter } from '@/app/router'
import { buttonBase, buttonTone } from '@/components/ui'

const router = useRouter()
</script>

<template>
  <section class="rounded-lg border border-zinc-200 bg-white p-8 text-center shadow-sm">
    <h2 class="text-xl font-semibold">页面不存在</h2>
    <p class="mt-2 text-sm text-zinc-500">当前地址没有对应的新前端页面。</p>
    <button
      :class="[buttonBase, buttonTone.primary, 'mt-5']"
      type="button"
      @click="router.navigate('/dashboard')"
    >
      返回仪表盘
    </button>
  </section>
</template>
