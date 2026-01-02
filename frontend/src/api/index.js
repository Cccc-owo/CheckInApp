import client from './client'

/**
 * 认证 API
 */
export const authAPI = {
  // 请求 QR 码
  requestQRCode: (alias) => {
    return client.post('/api/auth/request_qrcode', { alias })
  },

  // 查询扫码状态
  getQRCodeStatus: (sessionId) => {
    return client.get(`/api/auth/qrcode_status/${sessionId}`)
  },

  // 取消 QR 码登录会话
  cancelQRCodeSession: (sessionId) => {
    return client.delete(`/api/auth/qrcode_session/${sessionId}`)
  },

  // 别名+密码登录
  aliasLogin: (alias, password) => {
    return client.post('/api/auth/alias_login', { alias, password })
  },

  // 验证 Token
  verifyToken: (token) => {
    return client.post('/api/auth/verify_token', { token })
  },
}

/**
 * 用户 API
 */
export const userAPI = {
  // 获取当前用户信息
  getCurrentUser: () => {
    return client.get('/api/users/me')
  },

  // 获取当前用户审批状态
  getUserStatus: () => {
    return client.get('/api/users/me/status')
  },

  // 获取当前用户 Token 状态
  getTokenStatus: () => {
    return client.get('/api/users/me/token_status')
  },

  // 更新当前用户个人信息
  updateProfile: (profileData) => {
    return client.put('/api/users/me/profile', profileData)
  },

  // 创建用户（管理员）
  createUser: (userData) => {
    return client.post('/api/users', userData)
  },

  // 获取所有用户（管理员）
  getUsers: (params = {}) => {
    return client.get('/api/users', { params })
  },

  // 获取指定用户
  getUser: (userId) => {
    return client.get(`/api/users/${userId}`)
  },

  // 更新用户
  updateUser: (userId, userData) => {
    return client.put(`/api/users/${userId}`, userData)
  },

  // 删除用户
  deleteUser: (userId) => {
    return client.delete(`/api/users/${userId}`)
  },
}

/**
 * 任务 API (V2 新增)
 */
export const taskAPI = {
  // 获取当前用户的任务列表
  getMyTasks: (params = {}) => {
    return client.get('/api/tasks', { params })
  },

  // 创建任务
  createTask: (taskData) => {
    return client.post('/api/tasks', taskData)
  },

  // 获取任务详情
  getTask: (taskId) => {
    return client.get(`/api/tasks/${taskId}`)
  },

  // 更新任务
  updateTask: (taskId, taskData) => {
    return client.put(`/api/tasks/${taskId}`, taskData)
  },

  // 删除任务
  deleteTask: (taskId) => {
    return client.delete(`/api/tasks/${taskId}`)
  },

  // 切换任务启用状态
  toggleTask: (taskId) => {
    return client.post(`/api/tasks/${taskId}/toggle`)
  },

  // 手动触发任务打卡（异步，立即返回）
  checkInTask: (taskId) => {
    return client.post(`/api/check_in/manual/${taskId}`)
  },

  // 查询打卡记录状态
  getCheckInRecordStatus: (recordId) => {
    return client.get(`/api/check_in/record/${recordId}/status`)
  },

  // 获取任务的打卡记录
  getTaskRecords: (taskId, params = {}) => {
    return client.get(`/api/check_in/task/${taskId}/records`, { params })
  },
}

/**
 * 打卡 API
 */
export const checkInAPI = {
  // 手动打卡（兼容旧版，推荐使用 taskAPI.checkInTask）
  manualCheckIn: (taskId) => {
    // 打卡操作耗时较长，设置 120 秒超时
    return client.post(`/api/check_in/manual/${taskId}`, {}, {
      timeout: 120000  // 120 秒
    })
  },

  // 获取任务打卡记录（兼容旧版，推荐使用 taskAPI.getTaskRecords）
  getMyRecords: (params = {}) => {
    return client.get('/api/check_in/my-records', { params })
  },

  // 获取所有打卡记录（管理员）
  getAllRecords: (params = {}) => {
    return client.get('/api/check_in/records', { params })
  },

  // 统计打卡记录数
  getRecordsCount: (params = {}) => {
    return client.get('/api/check_in/records/count', { params })
  },
}

/**
 * 管理员 API
 */
export const adminAPI = {
  // 获取待审批用户
  getPendingUsers: () => {
    return client.get('/api/admin/users/pending')
  },

  // 审批通过用户
  approveUser: (userId) => {
    return client.post(`/api/admin/users/${userId}/approve`)
  },

  // 拒绝用户
  rejectUser: (userId) => {
    return client.delete(`/api/admin/users/${userId}/reject`)
  },

  // 批量启用/禁用任务（V2 更新）
  batchToggleTasks: (taskIds, isActive) => {
    return client.post('/api/admin/batch_toggle_tasks', {
      task_ids: taskIds,
      is_active: isActive
    })
  },

  // 批量触发打卡（V2 更新）
  batchCheckIn: (taskIds) => {
    return client.post('/api/admin/batch_check_in', {
      task_ids: taskIds
    })
  },

  // 查看系统日志
  getLogs: (params = {}) => {
    return client.get('/api/admin/logs', { params })
  },

  // 系统统计信息
  getStats: () => {
    return client.get('/api/admin/stats')
  },
}

/**
 * 模板 API
 */
export const templateAPI = {
  // 获取所有模板列表
  getTemplates: (params = {}) => {
    return client.get('/api/templates', { params })
  },

  // 获取启用的模板列表
  getActiveTemplates: (params = {}) => {
    return client.get('/api/templates/active', { params })
  },

  // 获取单个模板详情
  getTemplate: (templateId) => {
    return client.get(`/api/templates/${templateId}`)
  },

  // 预览模板生成的 payload
  previewTemplate: (templateId) => {
    return client.get(`/api/templates/${templateId}/preview`)
  },

  // 创建模板（管理员）
  createTemplate: (templateData) => {
    return client.post('/api/templates', templateData)
  },

  // 更新模板（管理员）
  updateTemplate: (templateId, templateData) => {
    return client.put(`/api/templates/${templateId}`, templateData)
  },

  // 删除模板（管理员）
  deleteTemplate: (templateId) => {
    return client.delete(`/api/templates/${templateId}`)
  },

  // 从模板创建任务
  createTaskFromTemplate: (requestData) => {
    return client.post('/api/templates/create-task', requestData)
  },
}

// 导出所有 API
export default {
  auth: authAPI,
  user: userAPI,
  task: taskAPI,    // V2 新增
  checkIn: checkInAPI,
  admin: adminAPI,
  template: templateAPI,  // V2.2 新增
}
