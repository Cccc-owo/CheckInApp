import type { TemplateFieldOption } from '@/api'

export type FieldNodeKind = 'field' | 'array' | 'object'
export type FieldPath = Array<string | number>

export interface TemplateFieldConfigItem {
  display_name: string
  field_type: 'text' | 'textarea' | 'number' | 'select' | string
  value_type?: 'string' | 'int' | 'double' | 'bool' | 'json' | string
  default_value?: unknown
  required?: boolean
  hidden?: boolean
  placeholder?: string | null
  options?: TemplateFieldOption[] | null
  [key: string]: unknown
}

export interface TemplateFieldConfigArray extends Array<TemplateFieldConfigNode> {}

export interface TemplateFieldConfigObject {
  [key: string]: TemplateFieldConfigNode
}

export type TemplateFieldConfigNode =
  | TemplateFieldConfigItem
  | TemplateFieldConfigArray
  | TemplateFieldConfigObject

export interface TemplateFieldConfigRoot {
  [key: string]: TemplateFieldConfigNode
}

export interface ParseResult {
  ok: boolean
  config: TemplateFieldConfigRoot
  message?: string
}

export interface ValidationResult {
  ok: boolean
  message?: string
}

export interface KeyValidationResult extends ValidationResult {
  key: string
}

export function cloneConfig<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

export function createDefaultFieldConfig(displayName = ''): TemplateFieldConfigItem {
  return {
    display_name: displayName,
    field_type: 'text',
    default_value: '',
    required: false,
    hidden: false,
    placeholder: '',
    value_type: 'string',
    options: [],
  }
}

export function createDefaultNode(kind: FieldNodeKind): TemplateFieldConfigNode {
  if (kind === 'array') return []
  if (kind === 'object') return {}
  return createDefaultFieldConfig()
}

export function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function isFieldConfig(value: unknown): value is TemplateFieldConfigItem {
  return isPlainObject(value) && 'display_name' in value
}

export function nodeKind(value: unknown): FieldNodeKind {
  if (Array.isArray(value)) return 'array'
  if (isFieldConfig(value)) return 'field'
  return 'object'
}

export function nodeKindLabel(kind: FieldNodeKind) {
  if (kind === 'array') return '数组'
  if (kind === 'object') return '对象'
  return '字段'
}

export function parseTemplateFieldConfig(value: string): ParseResult {
  try {
    const parsed = JSON.parse(value) as unknown
    if (!isPlainObject(parsed)) {
      return { ok: false, config: {}, message: '字段配置必须是 JSON 对象' }
    }
    return { ok: true, config: parsed as TemplateFieldConfigRoot }
  } catch (error) {
    return {
      ok: false,
      config: {},
      message: error instanceof Error ? error.message : '字段配置 JSON 解析失败',
    }
  }
}

export function serializeTemplateFieldConfig(config: TemplateFieldConfigRoot) {
  return JSON.stringify(config, null, 2)
}

function validateNode(value: TemplateFieldConfigNode, path: FieldPath): ValidationResult {
  if (Array.isArray(value)) {
    for (let index = 0; index < value.length; index += 1) {
      const result = validateNode(value[index], [...path, index])
      if (!result.ok) return result
    }
    return { ok: true }
  }

  if (!isPlainObject(value)) {
    return { ok: false, message: `字段 ${path.join('.')} 不是有效配置` }
  }

  if (isFieldConfig(value)) {
    if (!String(value.display_name ?? '').trim()) {
      return { ok: false, message: `字段 ${path.join('.')} 缺少显示名称` }
    }
    if (!String(value.field_type ?? '').trim()) {
      return { ok: false, message: `字段 ${path.join('.')} 缺少字段类型` }
    }
    if (value.field_type === 'select') {
      const options = Array.isArray(value.options) ? value.options : []
      if (options.length === 0) return { ok: false, message: `字段 ${path.join('.')} 缺少选项` }
      const invalid = options.some((option) => !option.label || option.value == null)
      if (invalid) return { ok: false, message: `字段 ${path.join('.')} 存在无效选项` }
    }
    return { ok: true }
  }

  for (const [key, child] of Object.entries(value)) {
    if (!key.trim()) return { ok: false, message: '字段名不能为空' }
    const result = validateNode(child as TemplateFieldConfigNode, [...path, key])
    if (!result.ok) return result
  }
  return { ok: true }
}

export function validateFieldConfig(config: unknown): ValidationResult {
  if (!isPlainObject(config)) return { ok: false, message: '字段配置必须是对象' }
  return validateNode(config as TemplateFieldConfigNode, [])
}

function assertValidKey(target: Record<string, TemplateFieldConfigNode>, key: string) {
  if (!key.trim()) throw new Error('字段名不能为空')
  if (Object.prototype.hasOwnProperty.call(target, key)) throw new Error('字段已存在')
}

export function validateSiblingKey(
  root: TemplateFieldConfigRoot,
  parentPath: FieldPath,
  key: string,
  currentKey?: string,
): KeyValidationResult {
  const normalized = key.trim()
  if (!normalized) return { ok: false, key: normalized, message: '字段名不能为空' }

  try {
    const parent = getContainer(root, parentPath)
    if (Array.isArray(parent)) return { ok: true, key: normalized }
    if (normalized !== currentKey && Object.prototype.hasOwnProperty.call(parent, normalized)) {
      return { ok: false, key: normalized, message: '字段已存在' }
    }
    return { ok: true, key: normalized }
  } catch (error) {
    return {
      ok: false,
      key: normalized,
      message: error instanceof Error ? error.message : '字段路径无效',
    }
  }
}

export function getContainer(
  root: TemplateFieldConfigRoot,
  path: FieldPath,
): Record<string, TemplateFieldConfigNode> | TemplateFieldConfigNode[] {
  let current: TemplateFieldConfigNode = root
  for (const segment of path) {
    if (Array.isArray(current) && typeof segment === 'number') {
      current = current[segment]
      continue
    }
    if (isPlainObject(current) && typeof segment === 'string') {
      current = current[segment] as TemplateFieldConfigNode
      continue
    }
    throw new Error('字段路径无效')
  }
  if (!Array.isArray(current) && !isPlainObject(current)) throw new Error('字段路径无效')
  return current as Record<string, TemplateFieldConfigNode> | TemplateFieldConfigNode[]
}

export function addFieldAtPath(
  root: TemplateFieldConfigRoot,
  parentPath: FieldPath,
  key: string,
  value: TemplateFieldConfigNode,
): TemplateFieldConfigRoot {
  const next = cloneConfig(root)
  const parent = getContainer(next, parentPath)
  if (Array.isArray(parent)) {
    if (key.trim()) {
      parent.push({ [key]: cloneConfig(value) })
    } else {
      parent.push(cloneConfig(value))
    }
    return next
  }
  assertValidKey(parent, key)
  parent[key] = cloneConfig(value)
  return next
}

export function updateFieldAtPath(
  root: TemplateFieldConfigRoot,
  path: FieldPath,
  value: TemplateFieldConfigNode,
): TemplateFieldConfigRoot {
  if (path.length === 0) {
    if (!isPlainObject(value) || Array.isArray(value)) throw new Error('根配置必须是对象')
    return cloneConfig(value as TemplateFieldConfigRoot)
  }
  const next = cloneConfig(root)
  const parent = getContainer(next, path.slice(0, -1))
  const segment = path[path.length - 1]
  if (Array.isArray(parent) && typeof segment === 'number') parent[segment] = cloneConfig(value)
  else if (!Array.isArray(parent) && typeof segment === 'string')
    parent[segment] = cloneConfig(value)
  else throw new Error('字段路径无效')
  return next
}

export function renameFieldAtPath(
  root: TemplateFieldConfigRoot,
  path: FieldPath,
  nextKey: string,
): TemplateFieldConfigRoot {
  if (path.length === 0) return root
  const segment = path[path.length - 1]
  if (typeof segment !== 'string') throw new Error('字段路径无效')

  const parentPath = path.slice(0, -1)
  const validated = validateSiblingKey(root, parentPath, nextKey, segment)
  if (!validated.ok) throw new Error(validated.message)
  if (validated.key === segment) return root

  const next = cloneConfig(root)
  const parent = getContainer(next, parentPath)
  if (Array.isArray(parent)) throw new Error('字段路径无效')

  const entries = Object.entries(parent)
  for (const key of Object.keys(parent)) delete parent[key]
  for (const [key, value] of entries) {
    parent[key === segment ? validated.key : key] = value
  }
  return next
}

export function deleteFieldAtPath(root: TemplateFieldConfigRoot, path: FieldPath) {
  if (path.length === 0) return {}
  const next = cloneConfig(root)
  const parent = getContainer(next, path.slice(0, -1))
  const segment = path[path.length - 1]
  if (Array.isArray(parent) && typeof segment === 'number') parent.splice(segment, 1)
  else if (!Array.isArray(parent) && typeof segment === 'string') delete parent[segment]
  else throw new Error('字段路径无效')
  return next
}

export function moveFieldAtPath(
  root: TemplateFieldConfigRoot,
  path: FieldPath,
  direction: 'up' | 'down',
): TemplateFieldConfigRoot {
  if (path.length === 0) return root
  const next = cloneConfig(root)
  const parent = getContainer(next, path.slice(0, -1))
  const segment = path[path.length - 1]
  const offset = direction === 'up' ? -1 : 1

  if (Array.isArray(parent) && typeof segment === 'number') {
    const target = segment + offset
    if (target < 0 || target >= parent.length) return next
    const [item] = parent.splice(segment, 1)
    parent.splice(target, 0, item)
    return next
  }

  if (!Array.isArray(parent) && typeof segment === 'string') {
    const entries = Object.entries(parent)
    const index = entries.findIndex(([key]) => key === segment)
    const target = index + offset
    if (index < 0 || target < 0 || target >= entries.length) return next
    const [entry] = entries.splice(index, 1)
    entries.splice(target, 0, entry)
    for (const key of Object.keys(parent)) delete parent[key]
    for (const [key, value] of entries) parent[key] = value
    return next
  }

  throw new Error('字段路径无效')
}

function buildPreviewNode(node: TemplateFieldConfigNode): unknown {
  if (Array.isArray(node)) return node.map((item) => buildPreviewNode(item))
  if (isFieldConfig(node)) return node.default_value ?? ''
  if (!isPlainObject(node)) return null

  const payload: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(node)) {
    payload[key] = buildPreviewNode(value as TemplateFieldConfigNode)
  }
  return payload
}

export function buildTemplatePreviewPayload(config: TemplateFieldConfigRoot) {
  return buildPreviewNode(config) as Record<string, unknown>
}
