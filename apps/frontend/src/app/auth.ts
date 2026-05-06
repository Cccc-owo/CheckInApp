import { computed, reactive } from 'vue'
import {
  clearStoredAuth,
  getStoredToken,
  getStoredUser,
  setStoredToken,
  setStoredUser,
} from '@/api/client'
import { userApi } from '@/api'
import type { LoginResponse, User } from '@/api'

interface AuthState {
  token: string | null
  user: User | null
  initialized: boolean
  loading: boolean
}

const state = reactive<AuthState>({
  token: getStoredToken(),
  user: getStoredUser<User>(),
  initialized: false,
  loading: false,
})

function userFromLogin(payload: LoginResponse): User | null {
  const raw = payload.user
  if (raw?.id || raw?.user_id || payload.user_id) {
    return {
      id: raw?.id ?? raw?.user_id ?? payload.user_id ?? 0,
      alias: raw?.alias ?? payload.alias ?? '未命名用户',
      role: raw?.role ?? payload.role ?? 'user',
      is_approved: raw?.is_approved ?? payload.is_approved ?? false,
      jwt_exp: raw?.jwt_exp ?? '',
      email: raw?.email ?? null,
      email_verified: raw?.email_verified ?? false,
      email_verified_at: raw?.email_verified_at ?? null,
      has_password: raw?.has_password,
      created_at: raw?.created_at ?? new Date().toISOString(),
      updated_at: raw?.updated_at ?? null,
    }
  }
  return null
}

async function refreshCurrentUser() {
  if (!state.token) {
    state.user = null
    state.initialized = true
    return null
  }

  state.loading = true
  try {
    const user = await userApi.me()
    state.user = user
    setStoredUser(user)
    return user
  } catch (error) {
    clearStoredAuth()
    state.token = null
    state.user = null
    throw error
  } finally {
    state.loading = false
    state.initialized = true
  }
}

function applyLogin(payload: LoginResponse) {
  const token = payload.authorization ?? payload.token
  if (!token) throw new Error(payload.message || '登录响应缺少 token')

  state.token = token
  setStoredToken(token)

  const user = userFromLogin(payload)
  if (user) {
    state.user = user
    setStoredUser(user)
  }
}

function logout() {
  clearStoredAuth()
  state.token = null
  state.user = null
  state.initialized = true
}

export function useAuth() {
  return {
    state,
    isAuthenticated: computed(() => Boolean(state.token)),
    isAdmin: computed(() => state.user?.role === 'admin'),
    isApproved: computed(() => Boolean(state.user?.is_approved)),
    applyLogin,
    refreshCurrentUser,
    logout,
  }
}
