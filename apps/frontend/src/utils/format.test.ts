import assert from 'node:assert/strict'
import test from 'node:test'
import { statusLabel, statusTone } from './format.ts'

test('formats token_expired status for check-in records', () => {
  assert.equal(statusLabel('token_expired'), '凭证过期')
  assert.equal(statusTone('token_expired'), 'danger')
  assert.equal(statusLabel('token-expired'), 'token-expired')
})
