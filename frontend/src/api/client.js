import axios from 'axios';

// 创建 axios 实例
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加 Token
client.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 统一错误处理
client.interceptors.response.use(
  response => {
    return response.data;
  },
  error => {
    if (error.response) {
      // 服务器返回错误状态码
      const { status, data } = error.response;

      if (status === 401) {
        const errorDetail = data.detail || data.message || '';

        // 检查用户是否设置了密码
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const hasPassword = user.has_password || false;

        // Token 过期的情况
        if (errorDetail.includes('过期')) {
          if (hasPassword) {
            // 有密码的用户：不强制退出，只显示警告
            // 不清除 localStorage，让用户继续使用
            console.warn('Token 已过期，但用户设置了密码，允许继续使用');

            // 返回错误但不跳转登录页
            return Promise.reject({
              status,
              message: '登录凭证已过期，部分功能可能受限，建议刷新凭证',
              data,
              tokenExpired: true,
            });
          } else {
            // 没有密码的用户：必须重新登录
            localStorage.removeItem('token');
            localStorage.removeItem('user');

            // 延迟跳转，避免阻塞当前异步请求的错误处理
            setTimeout(() => {
              if (window.location.pathname !== '/login') {
                window.location.href = '/login';
              }
            }, 100);
          }
        } else {
          // 其他 401 错误（无效 Token 等）：清除登录状态
          localStorage.removeItem('token');
          localStorage.removeItem('user');

          setTimeout(() => {
            if (window.location.pathname !== '/login') {
              window.location.href = '/login';
            }
          }, 100);
        }
      }

      // 返回统一的错误对象
      return Promise.reject({
        status,
        message: data.detail || data.message || '请求失败',
        data,
      });
    } else if (error.request) {
      // 请求已发出但没有收到响应（超时或网络错误）
      return Promise.reject({
        status: 0,
        message:
          error.code === 'ECONNABORTED' ? '请求超时，请稍后重试' : '网络错误，请检查您的网络连接',
        data: null,
      });
    } else {
      // 发生了触发请求错误的问题
      return Promise.reject({
        status: 0,
        message: error.message || '请求配置错误',
        data: null,
      });
    }
  }
);

export default client;
