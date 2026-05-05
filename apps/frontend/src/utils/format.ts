import type { ApiError } from '@/api/client'

export function formatDateTime(value?: string | null) {
  if (!value) return '未记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function formatFullDateTime(value?: string | null) {
  if (!value) return '未记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(date)
}

export function statusLabel(status?: string | null) {
  const labels: Record<string, string> = {
    success: '成功',
    failure: '失败',
    failed: '失败',
    pending: '进行中',
    running: '进行中',
    already_submitted: '已提交',
    out_of_time: '超出时间',
    token_expired: '凭证过期',
    unknown: '未知',
    manual: '手动',
    scheduler: '定时',
    scheduled: '定时',
    admin: '管理员',
  }
  return labels[status ?? ''] ?? status ?? '未知'
}

export function statusTone(status?: string | null) {
  if (status === 'success' || status === 'already_submitted') return 'success'
  if (status === 'pending' || status === 'running') return 'warning'
  if (
    status === 'failure' ||
    status === 'failed' ||
    status === 'out_of_time' ||
    status === 'token_expired'
  ) {
    return 'danger'
  }
  return 'neutral'
}

export function cronLabel(value?: string | null) {
  if (!value) return '未启用定时'
  if (value === '0 20 * * *') return '每天 20:00'
  return value
}

export function parseJson<T>(value?: string | null, fallback: T = {} as T) {
  if (!value) return fallback
  try {
    return JSON.parse(value) as T
  } catch {
    return fallback
  }
}

export function stringifyJson(value: unknown) {
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

export function extractErrorMessage(error: unknown) {
  if (typeof error === 'object' && error && 'message' in error) {
    return String((error as ApiError).message)
  }
  if (error instanceof Error) return error.message
  return '操作失败，请稍后重试'
}

export function boolLabel(value?: boolean | null) {
  return value ? '是' : '否'
}

export function clampText(value?: string | null, fallback = '未命名') {
  const trimmed = value?.trim()
  return trimmed || fallback
}
