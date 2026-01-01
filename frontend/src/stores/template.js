import { defineStore } from 'pinia'
import { templateAPI } from '@/api'

export const useTemplateStore = defineStore('template', {
  state: () => ({
    templates: [],
    currentTemplate: null,
    loading: false,
    error: null,
  }),

  getters: {
    activeTemplates: (state) => state.templates.filter((t) => t.is_active),

    getTemplateById: (state) => (id) => {
      return state.templates.find((t) => t.id === id)
    },
  },

  actions: {
    async fetchTemplates(isActive = null) {
      this.loading = true
      this.error = null
      try {
        const params = {}
        if (isActive !== null) {
          params.is_active = isActive
        }
        this.templates = await templateAPI.getTemplates(params)
        return this.templates
      } catch (error) {
        this.error = error.message || '获取模板列表失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchActiveTemplates() {
      this.loading = true
      this.error = null
      try {
        this.templates = await templateAPI.getActiveTemplates()
        return this.templates
      } catch (error) {
        this.error = error.message || '获取启用模板失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchTemplate(id) {
      this.loading = true
      this.error = null
      try {
        this.currentTemplate = await templateAPI.getTemplate(id)
        return this.currentTemplate
      } catch (error) {
        this.error = error.message || '获取模板详情失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    async previewTemplate(id) {
      this.loading = true
      this.error = null
      try {
        const preview = await templateAPI.previewTemplate(id)
        return preview
      } catch (error) {
        this.error = error.message || '预览模板失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    async createTemplate(templateData) {
      this.loading = true
      this.error = null
      try {
        const newTemplate = await templateAPI.createTemplate(templateData)
        this.templates.unshift(newTemplate)
        return newTemplate
      } catch (error) {
        this.error = error.message || '创建模板失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    async updateTemplate(id, templateData) {
      this.loading = true
      this.error = null
      try {
        const updatedTemplate = await templateAPI.updateTemplate(id, templateData)
        const index = this.templates.findIndex((t) => t.id === id)
        if (index !== -1) {
          this.templates[index] = updatedTemplate
        }
        if (this.currentTemplate && this.currentTemplate.id === id) {
          this.currentTemplate = updatedTemplate
        }
        return updatedTemplate
      } catch (error) {
        this.error = error.message || '更新模板失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    async deleteTemplate(id) {
      this.loading = true
      this.error = null
      try {
        await templateAPI.deleteTemplate(id)
        this.templates = this.templates.filter((t) => t.id !== id)
        if (this.currentTemplate && this.currentTemplate.id === id) {
          this.currentTemplate = null
        }
        return true
      } catch (error) {
        this.error = error.message || '删除模板失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    async createTaskFromTemplate(templateId, threadId, fieldValues, taskName = null) {
      this.loading = true
      this.error = null
      try {
        const task = await templateAPI.createTaskFromTemplate({
          template_id: templateId,
          thread_id: threadId,
          field_values: fieldValues,
          task_name: taskName,
        })
        return task
      } catch (error) {
        this.error = error.message || '从模板创建任务失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    clearCurrentTemplate() {
      this.currentTemplate = null
    },

    clearError() {
      this.error = null
    },
  },
})
