import type { ApiErrorData } from './types'

export interface ApiError {
  status: number
  message: string
  data: unknown
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const TOKEN_KEY = 'checkin.token'
const LEGACY_TOKEN_KEY = 'token'
const USER_KEY = 'checkin.user'
const LEGACY_USER_KEY = 'user'

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY) || localStorage.getItem(LEGACY_TOKEN_KEY)
}

export function setStoredToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(LEGACY_TOKEN_KEY, token)
}

export function clearStoredAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(LEGACY_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(LEGACY_USER_KEY)
}

export function setStoredUser(user: unknown) {
  const value = JSON.stringify(user)
  localStorage.setItem(USER_KEY, value)
  localStorage.setItem(LEGACY_USER_KEY, value)
}

export function getStoredUser<T>() {
  const raw = localStorage.getItem(USER_KEY) || localStorage.getItem(LEGACY_USER_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw) as T
  } catch {
    return null
  }
}

function buildUrl(path: string, params?: Record<string, unknown>) {
  const url = new URL(path, window.location.origin)
  if (API_BASE_URL) {
    const base = new URL(API_BASE_URL, window.location.origin)
    url.protocol = base.protocol
    url.host = base.host
    url.pathname = `${base.pathname.replace(/\/$/, '')}/${path.replace(/^\//, '')}`
  }

  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    url.searchParams.set(key, String(value))
  })

  return API_BASE_URL ? url.toString() : `${url.pathname}${url.search}`
}

function errorMessage(status: number, payload: ApiErrorData | null) {
  if (payload?.error?.message) return payload.error.message
  if (payload?.detail) return payload.detail
  if (payload?.message) return payload.message
  if (status === 401) return '登录已失效，请重新登录'
  if (status === 403) return '当前账号没有权限执行该操作'
  if (status === 404) return '请求的资源不存在'
  if (status === 422) return '提交内容不符合要求'
  if (status >= 500) return '服务器内部错误，请稍后重试'
  return '请求失败'
}

export async function request<T>(
  path: string,
  options: RequestInit & { params?: Record<string, unknown>; timeout?: number } = {},
) {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), options.timeout ?? 30000)
  const token = getStoredToken()
  const headers = new Headers(options.headers)

  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) headers.set('Authorization', `Bearer ${token}`)

  try {
    const response = await fetch(buildUrl(path, options.params), {
      ...options,
      headers,
      signal: controller.signal,
    })

    if (response.status === 204) return undefined as T

    const contentType = response.headers.get('content-type') ?? ''
    const payload = contentType.includes('application/json')
      ? ((await response.json()) as unknown)
      : await response.text()

    if (!response.ok) {
      if (response.status === 401) clearStoredAuth()
      const data = typeof payload === 'object' && payload ? (payload as ApiErrorData) : null
      throw {
        status: response.status,
        message: errorMessage(response.status, data),
        data: payload,
      } satisfies ApiError
    }

    return payload as T
  } catch (error) {
    if ((error as ApiError).status !== undefined) throw error
    throw {
      status: 0,
      message:
        error instanceof DOMException && error.name === 'AbortError'
          ? '请求超时，请稍后重试'
          : '网络错误，请检查后端服务是否可用',
      data: null,
    } satisfies ApiError
  } finally {
    window.clearTimeout(timeout)
  }
}

export const apiClient = {
  get: <T>(path: string, params?: Record<string, unknown>) => request<T>(path, { params }),
  post: <T>(path: string, body?: unknown, timeout?: number) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body ?? {}), timeout }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body ?? {}) }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
