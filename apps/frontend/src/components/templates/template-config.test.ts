import assert from 'node:assert/strict'
import test from 'node:test'
import {
  addFieldAtPath,
  createDefaultFieldConfig,
  buildTemplatePreviewPayload,
  deleteFieldAtPath,
  isFieldConfig,
  moveFieldAtPath,
  parseTemplateFieldConfig,
  renameFieldAtPath,
  serializeTemplateFieldConfig,
  type TemplateFieldConfigRoot,
  type TemplateFieldConfigItem,
  updateFieldAtPath,
  validateFieldConfig,
} from './template-config.ts'

test('parses and serializes valid template field config', () => {
  const parsed = parseTemplateFieldConfig(
    '{"signature":{"display_name":"姓名","field_type":"text","required":true}}',
  )

  assert.equal(parsed.ok, true)
  const signature = parsed.config.signature
  assert.ok(isFieldConfig(signature))
  assert.equal(signature.display_name, '姓名')
  assert.match(serializeTemplateFieldConfig(parsed.config), /"signature"/)
})

test('parses field-like configs so structured editor can repair metadata', () => {
  const parsed = parseTemplateFieldConfig('{"signature":{"display_name":"姓名"}}')

  assert.equal(parsed.ok, true)
  assert.ok(isFieldConfig(parsed.config.signature))

  const validation = validateFieldConfig(parsed.config)
  assert.equal(validation.ok, false)
  assert.match(validation.message ?? '', /字段类型/)
})

test('default field preserves expected editing metadata', () => {
  const field = createDefaultFieldConfig('体温')

  assert.equal(field.display_name, '体温')
  assert.equal(field.field_type, 'text')
  assert.equal(field.value_type, 'string')
  assert.equal(field.required, false)
  assert.equal(field.hidden, false)
  assert.deepEqual(field.options, [])
})

test('adds updates deletes and reorders root fields immutably', () => {
  const config: TemplateFieldConfigRoot = {
    signature: createDefaultFieldConfig('姓名'),
    status: createDefaultFieldConfig('状态'),
  }
  const withLocation = addFieldAtPath(config, [], 'location', createDefaultFieldConfig('位置'))
  const locationField = withLocation.location as TemplateFieldConfigItem
  const updated = updateFieldAtPath(withLocation, ['location'], {
    ...locationField,
    field_type: 'select',
    options: [{ label: '教学楼', value: 'teaching' }],
    legacy_hint: 'preserved',
  })
  const moved = moveFieldAtPath(updated, ['location'], 'up')
  const deleted = deleteFieldAtPath(moved, ['status'])

  assert.deepEqual(Object.keys(config), ['signature', 'status'])
  assert.deepEqual(Object.keys(moved), ['signature', 'location', 'status'])
  const updatedLocation = updated.location as TemplateFieldConfigItem
  assert.ok(isFieldConfig(updatedLocation))
  assert.equal(updatedLocation.legacy_hint, 'preserved')
  assert.deepEqual(Object.keys(deleted), ['signature', 'location'])
})

test('renames fields without disturbing sibling order', () => {
  const config: TemplateFieldConfigRoot = {
    signature: createDefaultFieldConfig('姓名'),
    profile: {
      city: createDefaultFieldConfig('城市'),
      region: createDefaultFieldConfig('区域'),
    },
  }

  const renamed = renameFieldAtPath(config, ['profile', 'city'], 'location')

  assert.deepEqual(Object.keys(renamed), ['signature', 'profile'])
  const renamedProfile = renamed.profile as Record<string, TemplateFieldConfigItem>
  assert.ok(!Array.isArray(renamedProfile) && !isFieldConfig(renamedProfile))
  assert.deepEqual(Object.keys(renamedProfile), ['location', 'region'])
  const renamedLocation = renamedProfile.location
  assert.ok(isFieldConfig(renamedLocation))
  assert.equal(renamedLocation.display_name, '城市')
})

test('builds preview payload from nested field config', () => {
  const config: TemplateFieldConfigRoot = {
    signature: { ...createDefaultFieldConfig('姓名'), default_value: '张三' },
    profile: {
      city: { ...createDefaultFieldConfig('城市'), default_value: '上海' },
    },
    tags: [{ ...createDefaultFieldConfig('标签'), default_value: '新生' }],
  }

  assert.deepEqual(buildTemplatePreviewPayload(config), {
    signature: '张三',
    profile: { city: '上海' },
    tags: ['新生'],
  })
})

test('validates duplicate or empty keys before mutation', () => {
  const config = { signature: createDefaultFieldConfig('姓名') }

  assert.throws(() => addFieldAtPath(config, [], '', createDefaultFieldConfig()), /字段名/)
  assert.throws(() => addFieldAtPath(config, [], 'signature', createDefaultFieldConfig()), /已存在/)
})

test('validates malformed config shapes', () => {
  const result = validateFieldConfig({
    signature: { display_name: '姓名', field_type: 'select', options: [{ label: '' }] },
  })

  assert.equal(result.ok, false)
  assert.match(result.message ?? '', /选项/)
})
