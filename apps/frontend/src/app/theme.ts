import { computed, reactive } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

export const THEME_STORAGE_KEY = 'checkin.theme.mode'

type ThemeStorage = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>

interface ThemeState {
  mode: ThemeMode
  resolved: ResolvedTheme
  initialized: boolean
}

const state = reactive<ThemeState>({
  mode: 'system',
  resolved: 'light',
  initialized: false,
})

let mediaQuery: MediaQueryList | null = null
let mediaUnsubscribe: (() => void) | null = null

function canUseDom() {
  return typeof window !== 'undefined' && typeof document !== 'undefined'
}

export function coerceThemeMode(value: unknown): ThemeMode {
  return value === 'light' || value === 'dark' || value === 'system' ? value : 'system'
}

export function getResolvedTheme(mode: ThemeMode, prefersDark: boolean): ResolvedTheme {
  if (mode === 'dark') return 'dark'
  if (mode === 'light') return 'light'
  return prefersDark ? 'dark' : 'light'
}

export function getStoredThemeMode(storage?: ThemeStorage): ThemeMode {
  if (!storage) return 'system'
  return coerceThemeMode(storage.getItem(THEME_STORAGE_KEY))
}

export function persistThemeMode(mode: ThemeMode, storage?: ThemeStorage) {
  if (!storage) return
  storage.setItem(THEME_STORAGE_KEY, mode)
}

export function nextThemeMode(mode: ThemeMode): ThemeMode {
  if (mode === 'light') return 'dark'
  if (mode === 'dark') return 'system'
  return 'light'
}

function applyResolvedTheme(resolved: ResolvedTheme) {
  if (!canUseDom()) return
  document.documentElement.classList.toggle('dark', resolved === 'dark')
  document.documentElement.style.colorScheme = resolved
}

function currentPrefersDark() {
  if (!canUseDom()) return false
  mediaQuery = mediaQuery ?? window.matchMedia('(prefers-color-scheme: dark)')
  return mediaQuery.matches
}

function syncResolvedTheme() {
  state.resolved = getResolvedTheme(state.mode, currentPrefersDark())
  applyResolvedTheme(state.resolved)
}

function subscribeSystemPreference() {
  if (!canUseDom() || mediaUnsubscribe) return
  mediaQuery = mediaQuery ?? window.matchMedia('(prefers-color-scheme: dark)')
  const listener = () => {
    if (state.mode === 'system') syncResolvedTheme()
  }
  mediaQuery.addEventListener('change', listener)
  mediaUnsubscribe = () => mediaQuery?.removeEventListener('change', listener)
}

export function initTheme() {
  if (!canUseDom()) return
  state.mode = getStoredThemeMode(window.localStorage)
  syncResolvedTheme()
  subscribeSystemPreference()
  state.initialized = true
}

export function setThemeMode(mode: ThemeMode) {
  state.mode = mode
  if (canUseDom()) persistThemeMode(mode, window.localStorage)
  syncResolvedTheme()
}

export function cycleThemeMode() {
  setThemeMode(nextThemeMode(state.mode))
}

export function disposeThemeListener() {
  mediaUnsubscribe?.()
  mediaUnsubscribe = null
}

export function useTheme() {
  return {
    state,
    modeLabel: computed(() => {
      if (state.mode === 'light') return '亮色'
      if (state.mode === 'dark') return '暗色'
      return '设备'
    }),
    setThemeMode,
    cycleThemeMode,
  }
}
