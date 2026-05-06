export type Role = 'admin' | 'user'

export interface User {
  id: number
  alias: string
  role: Role | string
  is_approved: boolean
  jwt_exp: string
  email?: string | null
  email_verified?: boolean
  email_verified_at?: string | null
  has_password?: boolean
  created_at: string
  updated_at?: string | null
}

export interface UserStatus {
  user_id: number
  alias: string
  is_approved: boolean
  created_at?: string | null
}

export interface TokenStatus {
  is_valid: boolean
  jwt_exp: string
  expires_at?: number | null
  days_until_expiry?: number | null
  expiring_soon: boolean
}

export interface AuthUserPayload {
  id?: number
  user_id?: number
  alias?: string
  role?: Role | string
  is_approved?: boolean
  jwt_exp?: string
  email?: string | null
  email_verified?: boolean
  email_verified_at?: string | null
  has_password?: boolean
  created_at?: string
  updated_at?: string | null
}

export interface LoginResponse {
  success?: boolean
  message?: string
  token?: string
  authorization?: string
  user?: AuthUserPayload
  user_id?: number
  alias?: string
  role?: Role | string
  is_approved?: boolean
  warning?: string
}

export interface QRCodeRequestResponse {
  session_id: string
  status?: string
  qrcode_image?: string
  qrcode_base64?: string
  qr_code?: string
  message?: string
}

export interface QRCodeStatusResponse extends LoginResponse {
  status: 'pending' | 'waiting_scan' | 'success' | 'error' | string
  qrcode_image?: string
}

export interface Task {
  id: number
  user_id: number
  payload_config: string
  name?: string | null
  is_active?: boolean | null
  created_at: string
  updated_at?: string | null
  cron_expression?: string | null
  is_scheduled_enabled?: boolean | null
  last_check_in_time?: string | null
  last_check_in_status?: string | null
  thread_id?: string | null
}

export interface TemplateFieldOption {
  label: string
  value: string
}

export interface TemplateFieldConfigItem {
  display_name: string
  field_type: 'text' | 'textarea' | 'number' | 'select' | string
  default_value?: string
  required?: boolean
  hidden?: boolean
  placeholder?: string | null
  value_type?: 'string' | 'int' | 'double' | string
  options?: TemplateFieldOption[] | null
}

export interface TemplateFieldConfig {
  signature?: TemplateFieldConfigItem
  texts?: TemplateFieldConfigItem
  values?: Record<string, TemplateFieldConfigItem>
}

export interface Template {
  id: number
  name: string
  description?: string | null
  parent_id?: number | null
  field_config: string
  is_active: boolean
  created_at: string
  updated_at?: string | null
}

export interface TemplatePreview {
  template_id: number
  template_name: string
  preview_payload: Record<string, unknown>
  field_config: TemplateFieldConfig
}

export interface CreateTaskFromTemplatePayload {
  template_id: number
  thread_id: string
  field_values: Record<string, unknown>
  task_name?: string | null
  cron_expression?: string | null
}

export interface CheckInRecord {
  id: number
  task_id: number
  status: string
  response_text?: string | null
  error_message?: string | null
  location?: string | null
  trigger_type?: string | null
  check_in_time?: string | null
  user_id?: number | null
  user_email?: string | null
  user_alias?: string | null
  task_name?: string | null
  thread_id?: string | null
}

export interface PaginatedResponse<T> {
  records: T[]
  total: number
  skip: number
  limit: number
}

export interface CheckInStartResponse {
  success?: boolean
  message?: string
  record_id?: number
  id?: number
  status?: string
}

export interface CheckInRecordStatus {
  record_id: number
  task_id: number
  status: string
  response_text?: string | null
  error_message?: string | null
  trigger_type?: string | null
  check_in_time?: string | null
}

export interface AdminStats {
  users: {
    total: number
    admin: number
    regular: number
    active: number
  }
  tasks: {
    total: number
    active: number
    inactive: number
  }
  check_in_records: {
    total: number
    today: number
    today_success: number
    today_failure: number
    today_out_of_time: number
    today_unknown: number
  }
  tokens: {
    expiring_soon: number
  }
}

export interface LogsResponse {
  success: boolean
  message: string
  logs: string
}

export interface EmailNotificationSettings {
  id: number
  smtp_server: string
  smtp_port: number
  smtp_sender_email: string
  smtp_use_ssl: boolean
  notify_token_expiring: boolean
  notify_check_in_success: boolean
  require_admin_approval_for_registration: boolean
  warn_unverified_email_before_approval: boolean
  has_smtp_sender_password: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface EmailNotificationSettingsUpdate {
  smtp_server: string
  smtp_port: number
  smtp_sender_email: string
  smtp_use_ssl: boolean
  notify_token_expiring: boolean
  notify_check_in_success: boolean
  require_admin_approval_for_registration: boolean
  warn_unverified_email_before_approval: boolean
  smtp_sender_password?: string
  clear_smtp_sender_password?: boolean
}

export interface AdminApprovalResponse {
  success: boolean
  message: string
  user_id?: number
  requires_override?: boolean
  warning_code?: string
}

export interface CronValidation {
  valid: boolean
  message: string
  next_times: string[]
  description: string
}

export interface ApiErrorData {
  detail?: string
  message?: string
  error?: {
    code?: string
    message?: string
    field?: string | null
  }
}
