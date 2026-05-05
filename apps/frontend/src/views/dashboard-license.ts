import type { TokenStatus } from '@/api'

export function formatRemainingDays(days?: number | null) {
  return days == null ? '未知' : `${days} 天`
}

export function canRefreshAuthorization(token?: TokenStatus | null) {
  return token?.is_valid === false
}

export function formatAuthorizationExpiryTooltip(
  token?: TokenStatus | null,
  _locale?: string,
  timeZone?: string,
) {
  if (!token?.expires_at) return null

  const expiresAt = new Date(token.expires_at * 1000)
  if (Number.isNaN(expiresAt.getTime())) return null

  const parts = new Intl.DateTimeFormat('en-CA', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hourCycle: 'h23',
    timeZone,
  })
    .formatToParts(expiresAt)
    .reduce<Record<string, string>>((values, part) => {
      if (part.type !== 'literal') values[part.type] = part.value
      return values
    }, {})

  return `过期时间：${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}:${parts.second}`
}
