import axios from 'axios'

// 创建 axios 实例
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加 Token
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 统一错误处理
client.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      // 服务器返回错误状态码
      const { status, data } = error.response

      if (status === 401) {
        // Token 过期或无效，清除登录状态
        localStorage.removeItem('token')
        localStorage.removeItem('user')

        // 延迟跳转，避免阻塞当前异步请求的错误处理
        setTimeout(() => {
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
        }, 100)
      }

      // 返回统一的错误对象
      return Promise.reject({
        status,
        message: data.detail || data.message || '请求失败',
        data,
      })
    } else if (error.request) {
      // 请求已发出但没有收到响应（超时或网络错误）
      return Promise.reject({
        status: 0,
        message: error.code === 'ECONNABORTED' ? '请求超时，请稍后重试' : '网络错误，请检查您的网络连接',
        data: null,
      })
    } else {
      // 发生了触发请求错误的问题
      return Promise.reject({
        status: 0,
        message: error.message || '请求配置错误',
        data: null,
      })
    }
  }
)

export default client
