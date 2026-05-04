import js from '@eslint/js'
import prettierConfig from '@vue/eslint-config-prettier'
import tsParser from '@typescript-eslint/parser'
import pluginVue from 'eslint-plugin-vue'
import vueParser from 'vue-eslint-parser'

const browserGlobals = {
  AbortController: 'readonly',
  DOMException: 'readonly',
  Headers: 'readonly',
  URL: 'readonly',
  URLSearchParams: 'readonly',
  console: 'readonly',
  document: 'readonly',
  fetch: 'readonly',
  localStorage: 'readonly',
  window: 'readonly',
}

export default [
  {
    ignores: ['dist/**', 'node_modules/**', 'coverage/**', '*.local', 'pnpm-lock.yaml'],
  },
  js.configs.recommended,
  {
    files: ['**/*.ts'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parser: tsParser,
      globals: browserGlobals,
    },
    rules: {
      'no-undef': 'off',
    },
  },
  ...pluginVue.configs['flat/recommended'],
  {
    files: ['**/*.vue'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parser: vueParser,
      parserOptions: {
        parser: tsParser,
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
      globals: browserGlobals,
    },
    rules: {
      'no-undef': 'off',
    },
  },
  prettierConfig,
  {
    files: ['**/*.{js,ts,vue}'],
    rules: {
      'no-console': 'warn',
      'no-unused-vars': 'off',
      'vue/multi-word-component-names': 'off',
      'vue/no-v-html': 'warn',
    },
  },
]
