import type { TokenStatus } from '@/api'
import type { Tone } from '@/components/ui'

const SECONDS_PER_DAY = 24 * 60 * 60

export interface UserAuthorizationSummary {
  label: string
  tone: Tone
}

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

export function formatUserAuthorizationSummary(
  jwtExp?: string | null,
  nowSeconds = Math.floor(Date.now() / 1000),
): UserAuthorizationSummary {
  const expiresAt = Number(jwtExp)
  if (!jwtExp || jwtExp === '0' || !Number.isFinite(expiresAt) || expiresAt <= 0) {
    return { label: '未绑定凭证', tone: 'neutral' }
  }

  if (expiresAt <= nowSeconds) {
    return { label: '凭证过期', tone: 'danger' }
  }

  const remainingDays = Math.ceil((expiresAt - nowSeconds) / SECONDS_PER_DAY)
  return {
    label: `${remainingDays} 天后过期`,
    tone: remainingDays <= 7 ? 'warning' : 'success',
  }
}
