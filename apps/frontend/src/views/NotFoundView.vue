<script setup lang="ts">
import { useRouter } from '@/app/router'
import { Button } from '@/components/ui/button'

const router = useRouter()
</script>

<template>
  <section
    class="rounded-lg border border-border bg-card p-8 text-center text-card-foreground shadow-sm dark:shadow-none"
  >
    <h2 class="text-xl font-semibold">页面不存在</h2>
    <p class="mt-2 text-sm text-muted-foreground">当前地址没有对应的新前端页面。</p>
    <Button type="button" class="mt-5" @click="router.navigate('/dashboard')"> 返回仪表盘 </Button>
  </section>
</template>
