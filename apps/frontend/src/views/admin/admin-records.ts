import type { CheckInRecord } from '@/api'

export function visibleRecordRange(total: number, skip: number, limit: number) {
  if (total <= 0) return '当前 0 - 0'
  const start = Math.min(skip + 1, total)
  const end = Math.min(skip + limit, total)
  return `当前 ${start} - ${end}`
}

export function formatRecordDetailContent(value?: string | null) {
  const text = value?.trim()
  if (!text) return '无内容'

  try {
    return JSON.stringify(JSON.parse(text), null, 2)
  } catch {
    return text
  }
}

function parsedRecordMessage(value?: string | null) {
  if (!value) return ''

  try {
    const payload = JSON.parse(value) as unknown
    if (typeof payload !== 'object' || payload === null) return ''
    const data = payload as Record<string, unknown>
    const candidates = [data.Data, data.Description, data.message, data.error]
    const hit = candidates.find((candidate) => typeof candidate === 'string' && candidate.trim())
    return typeof hit === 'string' ? hit.trim() : ''
  } catch {
    return ''
  }
}

export function recordResponseSummary(
  record: Pick<CheckInRecord, 'response_text' | 'error_message'>,
  maxLength = 96,
) {
  const source = record.response_text || record.error_message || ''
  const parsed = parsedRecordMessage(source)
  const raw = parsed || source.trim() || '无响应内容'
  const normalized = raw.replace(/\s+/g, ' ')
  if (normalized.length <= maxLength) return normalized
  return `${normalized.slice(0, Math.max(0, maxLength - 1))}…`
}
