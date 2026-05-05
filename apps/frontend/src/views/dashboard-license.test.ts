import assert from 'node:assert/strict'
import test from 'node:test'
import type { TokenStatus } from '@/api'
import {
  canRefreshAuthorization,
  formatAuthorizationExpiryTooltip,
  formatRemainingDays,
} from './dashboard-license.ts'

test('formats authorization expiry tooltip with concrete expiration time', () => {
  const token: TokenStatus = {
    is_valid: true,
    jwt_exp: '',
    expires_at: Date.UTC(2026, 4, 6, 16, 30, 12) / 1000,
    days_until_expiry: 0,
    expiring_soon: true,
  }

  assert.equal(
    formatAuthorizationExpiryTooltip(token, 'zh-CN', 'UTC'),
    '过期时间：2026-05-06 16:30:12',
  )
})

test('omits authorization expiry tooltip when expiration timestamp is missing', () => {
  assert.equal(formatAuthorizationExpiryTooltip(null), null)
  assert.equal(
    formatAuthorizationExpiryTooltip({
      is_valid: false,
      jwt_exp: '',
      expires_at: null,
      days_until_expiry: null,
      expiring_soon: false,
    }),
    null,
  )
})

test('allows QR refresh only for expired or invalid authorization', () => {
  assert.equal(canRefreshAuthorization(null), false)
  assert.equal(
    canRefreshAuthorization({
      is_valid: true,
      jwt_exp: '',
      expires_at: 1_778_111_412,
      days_until_expiry: 0,
      expiring_soon: true,
    }),
    false,
  )
  assert.equal(
    canRefreshAuthorization({
      is_valid: false,
      jwt_exp: '',
      expires_at: null,
      days_until_expiry: null,
      expiring_soon: false,
    }),
    true,
  )
})

test('formats remaining days label consistently', () => {
  assert.equal(formatRemainingDays(null), '未知')
  assert.equal(formatRemainingDays(0), '0 天')
  assert.equal(formatRemainingDays(12), '12 天')
})
