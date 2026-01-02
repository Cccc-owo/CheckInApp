import { defineStore } from 'pinia'
import { authAPI, userAPI } from '@/api'

export const useAuthStore = defineStore('auth', {
  state: () => {
    // 安全地解析 localStorage 中的用户数据
    let user = null
    try {
      const userStr = localStorage.getItem('user')
      if (userStr && userStr !== 'undefined' && userStr !== 'null') {
        user = JSON.parse(userStr)
      }
    } catch (e) {
      console.warn('Failed to parse user from localStorage:', e)
      localStorage.removeItem('user')
    }

    return {
      token: localStorage.getItem('token') || null,
      user,
    }
  },

  getters: {
    // 将 isAuthenticated 改为 getter，这样它会实时反应 state.token 的变化
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
  },

  actions: {
    // 设置认证信息
    setAuth(token, user) {
      // 清理 token：移除 URL 编码的 Bearer 前缀
      let cleanToken = token
      if (cleanToken) {
        // URL 解码
        cleanToken = decodeURIComponent(cleanToken)
        // 移除 Bearer 前缀（如果存在）
        if (cleanToken.toLowerCase().startsWith('bearer ')) {
          cleanToken = cleanToken.substring(7)
        }
      }

      this.token = cleanToken
      this.user = user

      localStorage.setItem('token', cleanToken)
      localStorage.setItem('user', JSON.stringify(user))
    },

    // 清除认证信息
    clearAuth() {
      this.token = null
      this.user = null

      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },

    // QR 码登录流程
    async loginWithQRCode(alias) {
      try {
        // 1. 请求 QR 码
        const qrData = await authAPI.requestQRCode(alias)
        const { session_id, qrcode_base64 } = qrData

        // 2. 返回 session_id 和 qrcode，由组件处理轮询
        return { session_id, qrcode_base64 }
      } catch (error) {
        throw new Error(error.message || '请求二维码失败')
      }
    },

    // 检查扫码状态
    async checkQRCodeStatus(sessionId) {
      try {
        const result = await authAPI.getQRCodeStatus(sessionId)

        if (result.status === 'success') {
          // 扫码成功，保存 Token 和用户信息
          this.setAuth(result.token, result.user)
          return { success: true, user: result.user }
        } else if (result.status === 'failed') {
          return { success: false, message: result.message }
        } else {
          // pending 或 expired
          return { success: false, status: result.status }
        }
      } catch (error) {
        throw new Error(error.message || '检查扫码状态失败')
      }
    },

    // 取消扫码会话
    async cancelQRCodeSession(sessionId) {
      try {
        await authAPI.cancelQRCodeSession(sessionId)
      } catch (error) {
        console.error('取消会话失败:', error)
      }
    },

    // 验证 Token
    async verifyToken(token) {
      try {
        const userData = await authAPI.verifyToken(token)
        this.setAuth(token, userData)
        return userData
      } catch (error) {
        this.clearAuth()
        throw new Error(error.message || 'Token 验证失败')
      }
    },

    // 获取当前用户信息
    async fetchCurrentUser() {
      try {
        const userData = await userAPI.getCurrentUser()
        // 更新本地用户信息
        this.user = userData
        localStorage.setItem('user', JSON.stringify(userData))
        return userData
      } catch (error) {
        throw new Error(error.message || '获取用户信息失败')
      }
    },

    // 登出
    logout() {
      this.clearAuth()
    },
  },
})
