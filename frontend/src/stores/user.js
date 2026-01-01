import { defineStore } from 'pinia'
import { userAPI } from '@/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    tokenStatus: null, // Token 状态信息
    users: [], // 用户列表（管理员）
    currentPage: 1,
    pageSize: 20,
    total: 0,
  }),

  getters: {
    isTokenExpiring: (state) => {
      if (!state.tokenStatus) return false
      return state.tokenStatus.expiring_soon || false
    },

    tokenExpireTime: (state) => {
      if (!state.tokenStatus || !state.tokenStatus.expires_at) return null
      return new Date(state.tokenStatus.expires_at * 1000)
    },
  },

  actions: {
    // 获取 Token 状态
    async fetchTokenStatus() {
      try {
        const status = await userAPI.getTokenStatus()
        this.tokenStatus = status
        return status
      } catch (error) {
        throw new Error(error.message || '获取 Token 状态失败')
      }
    },

    // 获取用户列表（管理员）
    async fetchUsers(params = {}) {
      try {
        const data = await userAPI.getUsers(params)
        this.users = data.users || data
        this.total = data.total || this.users.length
        return data
      } catch (error) {
        throw new Error(error.message || '获取用户列表失败')
      }
    },

    // 创建用户（管理员）
    async createUser(userData) {
      try {
        const newUser = await userAPI.createUser(userData)
        // 刷新用户列表
        await this.fetchUsers()
        return newUser
      } catch (error) {
        throw new Error(error.message || '创建用户失败')
      }
    },

    // 更新用户
    async updateUser(userId, userData) {
      try {
        // 过滤空密码字段
        const cleanedData = { ...userData }
        if (cleanedData.password === '' || cleanedData.password === null || cleanedData.password === undefined) {
          delete cleanedData.password
        }

        const updatedUser = await userAPI.updateUser(userId, cleanedData)
        // 刷新用户列表
        await this.fetchUsers()
        return updatedUser
      } catch (error) {
        throw new Error(error.message || '更新用户失败')
      }
    },

    // 删除用户
    async deleteUser(userId) {
      try {
        await userAPI.deleteUser(userId)
        // 刷新用户列表
        await this.fetchUsers()
      } catch (error) {
        throw new Error(error.message || '删除用户失败')
      }
    },
  },
})
