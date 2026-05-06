import { apiClient } from './client'
import type {
  AdminApprovalResponse,
  AdminStats,
  CheckInRecord,
  CheckInRecordStatus,
  CheckInStartResponse,
  CreateTaskFromTemplatePayload,
  CronValidation,
  EmailNotificationSettings,
  EmailNotificationSettingsUpdate,
  LoginResponse,
  LogsResponse,
  PaginatedResponse,
  QRCodeRequestResponse,
  QRCodeStatusResponse,
  Task,
  Template,
  TemplatePreview,
  TokenStatus,
  User,
  UserStatus,
} from './types'

export const authApi = {
  aliasLogin: (alias: string, password: string) =>
    apiClient.post<LoginResponse>('/api/auth/alias_login', { alias, password }),
  requestQRCode: (alias: string) =>
    apiClient.post<QRCodeRequestResponse>('/api/auth/request_qrcode', { alias }),
  getQRCodeStatus: (sessionId: string) =>
    apiClient.get<QRCodeStatusResponse>(`/api/auth/qrcode_status/${sessionId}`),
  cancelQRCodeSession: (sessionId: string) =>
    apiClient.delete<{ success?: boolean; message?: string }>(
      `/api/auth/qrcode_session/${sessionId}`,
    ),
  verifyToken: (authorization: string) =>
    apiClient.post<{ is_valid: boolean; message: string; user_id?: number }>(
      '/api/auth/verify_token',
      {
        authorization,
      },
    ),
}

export const userApi = {
  me: () => apiClient.get<User>('/api/users/me'),
  status: () => apiClient.get<UserStatus>('/api/users/me/status'),
  tokenStatus: () => apiClient.get<TokenStatus>('/api/users/me/token_status'),
  setEmail: (email: string) => apiClient.put<User>('/api/users/me/email', { email }),
  verifyEmail: (code: string) => apiClient.post<User>('/api/users/me/email/verify', { code }),
  updateProfile: (payload: {
    alias?: string
    email?: string
    current_password?: string
    new_password?: string
  }) => apiClient.put<User>('/api/users/me/profile', payload),
  list: (params: Record<string, unknown> = {}) => apiClient.get<User[]>('/api/users', params),
  create: (payload: Partial<User> & { password?: string }) =>
    apiClient.post<User>('/api/users', payload),
  update: (
    userId: number,
    payload: Partial<User> & {
      password?: string
      reset_password?: boolean
      allow_unverified_email?: boolean
    },
  ) => apiClient.put<User | AdminApprovalResponse>(`/api/users/${userId}`, payload),
  delete: (userId: number) => apiClient.delete<void>(`/api/users/${userId}`),
}

export const taskApi = {
  list: (params: Record<string, unknown> = {}) => apiClient.get<Task[]>('/api/tasks/', params),
  detail: (taskId: number) => apiClient.get<Task>(`/api/tasks/${taskId}`),
  update: (taskId: number, payload: Partial<Task>) =>
    apiClient.put<Task>(`/api/tasks/${taskId}`, payload),
  delete: (taskId: number) => apiClient.delete<void>(`/api/tasks/${taskId}`),
  toggle: (taskId: number) => apiClient.post<Task>(`/api/tasks/${taskId}/toggle`),
  validateCron: (cron_expression: string) =>
    apiClient.post<CronValidation>('/api/tasks/validate-cron', { cron_expression }),
}

export const checkInApi = {
  manual: (taskId: number) =>
    apiClient.post<CheckInStartResponse>(`/api/check_in/manual/${taskId}`, {}, 120000),
  status: (recordId: number) =>
    apiClient.get<CheckInRecordStatus>(`/api/check_in/record/${recordId}/status`),
  taskRecords: (taskId: number, params: Record<string, unknown> = {}) =>
    apiClient.get<PaginatedResponse<CheckInRecord>>(`/api/check_in/task/${taskId}/records`, params),
  myRecords: (params: Record<string, unknown> = {}) =>
    apiClient.get<PaginatedResponse<CheckInRecord>>('/api/check_in/my-records', params),
  allRecords: (params: Record<string, unknown> = {}) =>
    apiClient.get<PaginatedResponse<CheckInRecord>>('/api/check_in/records', params),
}

export const templateApi = {
  list: (params: Record<string, unknown> = {}) =>
    apiClient.get<Template[]>('/api/templates/', params),
  active: (params: Record<string, unknown> = {}) =>
    apiClient.get<Template[]>('/api/templates/active', params),
  detail: (templateId: number) => apiClient.get<Template>(`/api/templates/${templateId}`),
  preview: (templateId: number) =>
    apiClient.get<TemplatePreview>(`/api/templates/${templateId}/preview`),
  create: (payload: Partial<Template>) => apiClient.post<Template>('/api/templates/', payload),
  update: (templateId: number, payload: Partial<Template>) =>
    apiClient.put<Template>(`/api/templates/${templateId}`, payload),
  delete: (templateId: number) =>
    apiClient.delete<{ message: string }>(`/api/templates/${templateId}`),
  createTask: (payload: CreateTaskFromTemplatePayload) =>
    apiClient.post<Task>('/api/templates/create-task', payload),
}

export const adminApi = {
  pendingUsers: () => apiClient.get<User[]>('/api/admin/users/pending'),
  approveUser: (userId: number, payload: { allow_unverified_email?: boolean } = {}) =>
    apiClient.post<AdminApprovalResponse>(`/api/admin/users/${userId}/approve`, payload),
  rejectUser: (userId: number) =>
    apiClient.delete<{ success: boolean; message: string }>(`/api/admin/users/${userId}/reject`),
  stats: () => apiClient.get<AdminStats>('/api/admin/stats'),
  logs: (lines: number) => apiClient.get<LogsResponse>('/api/admin/logs', { lines }),
  batchToggleTasks: (task_ids: number[], is_active: boolean) =>
    apiClient.post<{ success: boolean; message: string; count: number }>(
      '/api/admin/batch_toggle_tasks',
      {
        task_ids,
        is_active,
      },
    ),
  batchCheckIn: (task_ids: number[]) =>
    apiClient.post<unknown>('/api/admin/batch_check_in', { task_ids }),
  emailSettings: () => apiClient.get<EmailNotificationSettings>('/api/admin/email_settings'),
  updateEmailSettings: (payload: EmailNotificationSettingsUpdate) =>
    apiClient.put<EmailNotificationSettings>('/api/admin/email_settings', payload),
}

export type * from './types'
