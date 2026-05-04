import assert from 'node:assert/strict'
import test from 'node:test'
import {
  THEME_STORAGE_KEY,
  coerceThemeMode,
  getResolvedTheme,
  getStoredThemeMode,
  nextThemeMode,
  persistThemeMode,
  type ThemeMode,
} from './theme.ts'

class MemoryStorage {
  private readonly values = new Map<string, string>()

  getItem(key: string) {
    return this.values.get(key) ?? null
  }

  setItem(key: string, value: string) {
    this.values.set(key, value)
  }

  removeItem(key: string) {
    this.values.delete(key)
  }
}

test('coerces unknown theme values to system', () => {
  assert.equal(coerceThemeMode('light'), 'light')
  assert.equal(coerceThemeMode('dark'), 'dark')
  assert.equal(coerceThemeMode('system'), 'system')
  assert.equal(coerceThemeMode('sepia'), 'system')
  assert.equal(coerceThemeMode(null), 'system')
})

test('resolves system mode from user preference', () => {
  assert.equal(getResolvedTheme('system', true), 'dark')
  assert.equal(getResolvedTheme('system', false), 'light')
  assert.equal(getResolvedTheme('dark', false), 'dark')
})

test('persists and restores theme mode', () => {
  const storage = new MemoryStorage()
  persistThemeMode('dark', storage)

  assert.equal(storage.getItem(THEME_STORAGE_KEY), 'dark')
  assert.equal(getStoredThemeMode(storage), 'dark')
})

test('cycles theme modes predictably', () => {
  const sequence: ThemeMode[] = ['light', 'dark', 'system', 'light']
  for (let index = 0; index < sequence.length - 1; index += 1) {
    assert.equal(nextThemeMode(sequence[index]), sequence[index + 1])
  }
})
