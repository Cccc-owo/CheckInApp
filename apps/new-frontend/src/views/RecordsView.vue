<script setup lang="ts">
import { Search } from 'lucide-vue-next'
import { onMounted, reactive, ref } from 'vue'
import { checkInApi, type CheckInRecord } from '@/api'
import StateBlock from '@/components/StateBlock.vue'
import { buttonBase, buttonTone, cardClass, inputClass, toneClass } from '@/components/ui'
import { extractErrorMessage, formatFullDateTime, statusLabel, statusTone } from '@/utils/format'

const loading = ref(true)
const error = ref('')
const records = ref<CheckInRecord[]>([])
const total = ref(0)
const filters = reactive({ status: '', trigger_type: '', skip: 0, limit: 20 })

async function load() {
  loading.value = true
  error.value = ''
  try {
    const page = await checkInApi.myRecords(filters)
    records.value = page.records
    total.value = page.total
    filters.skip = page.skip
    filters.limit = page.limit
  } catch (err) {
    error.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

function page(delta: number) {
  filters.skip = Math.max(0, filters.skip + delta * filters.limit)
  void load()
}

onMounted(load)
</script>

<template>
  <section :class="[cardClass, 'overflow-hidden']">
    <div class="grid gap-3 border-b border-zinc-200 p-4 md:grid-cols-[1fr_180px_180px_auto]">
      <div>
        <h2 class="font-semibold">个人打卡记录</h2>
        <p class="mt-1 text-sm text-zinc-500">按状态和触发方式查看最近的打卡结果。</p>
      </div>
      <select v-model="filters.status" :class="inputClass">
        <option value="">全部状态</option>
        <option value="success">成功</option>
        <option value="failure">失败</option>
        <option value="out_of_time">超出时间</option>
      </select>
      <select v-model="filters.trigger_type" :class="inputClass">
        <option value="">全部触发</option>
        <option value="manual">手动</option>
        <option value="scheduler">定时</option>
        <option value="admin">管理员</option>
      </select>
      <button :class="[buttonBase, buttonTone.secondary]" type="button" @click="load">
        <Search class="size-4" />
        筛选
      </button>
    </div>

    <StateBlock v-if="loading" title="正在加载记录" type="loading" />
    <StateBlock
      v-else-if="error"
      title="记录加载失败"
      :description="error"
      type="error"
      action-label="重试"
      @action="load"
    />
    <StateBlock
      v-else-if="records.length === 0"
      title="暂无记录"
      description="当前筛选条件下没有打卡记录。"
    />
    <div v-else>
      <div class="divide-y divide-zinc-200">
        <article
          v-for="record in records"
          :key="record.id"
          class="grid gap-3 p-4 lg:grid-cols-[180px_1fr_auto]"
        >
          <div>
            <div class="text-sm font-semibold">
              {{ record.task_name || `任务 #${record.task_id}` }}
            </div>
            <div class="mt-1 text-xs text-zinc-500">
              {{ formatFullDateTime(record.check_in_time) }}
            </div>
          </div>
          <div class="min-w-0">
            <p class="truncate text-sm text-zinc-700">
              {{ record.response_text || record.error_message || '无响应内容' }}
            </p>
            <p class="mt-1 text-xs text-zinc-500">
              触发方式：{{ statusLabel(record.trigger_type) }}
            </p>
          </div>
          <span :class="toneClass(statusTone(record.status))">{{
            statusLabel(record.status)
          }}</span>
        </article>
      </div>
      <div
        class="flex items-center justify-between border-t border-zinc-200 px-4 py-3 text-sm text-zinc-500"
      >
        <span
          >共 {{ total }} 条，当前 {{ filters.skip + 1 }} -
          {{ Math.min(filters.skip + filters.limit, total) }}</span
        >
        <div class="flex gap-2">
          <button
            :class="[buttonBase, buttonTone.secondary]"
            :disabled="filters.skip === 0"
            type="button"
            @click="page(-1)"
          >
            上一页
          </button>
          <button
            :class="[buttonBase, buttonTone.secondary]"
            :disabled="filters.skip + filters.limit >= total"
            type="button"
            @click="page(1)"
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
