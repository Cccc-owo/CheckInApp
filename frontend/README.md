# 接龙自动打卡系统 - 前端

基于 Vue 3 + Vite + Element Plus 的现代化前端应用。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite
- **UI 库**: Element Plus
- **路由**: Vue Router 4
- **状态管理**: Pinia
- **HTTP 客户端**: Axios
- **图标**: @element-plus/icons-vue

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API 接口
│   │   ├── client.js     # Axios 客户端配置
│   │   └── index.js      # API 方法封装
│   ├── assets/           # 静态资源
│   ├── components/       # 公共组件
│   │   ├── Layout.vue    # 布局组件
│   │   ├── Navbar.vue    # 导航栏
│   │   └── QRCodeModal.vue  # QR 码扫码组件
│   ├── router/           # 路由配置
│   │   └── index.js
│   ├── stores/           # Pinia 状态管理
│   │   ├── auth.js       # 认证状态
│   │   ├── user.js       # 用户状态
│   │   ├── checkIn.js    # 打卡状态
│   │   └── admin.js      # 管理员状态
│   ├── utils/            # 工具函数
│   │   └── helpers.js    # 通用辅助函数
│   ├── views/            # 页面组件
│   │   ├── LoginView.vue        # 登录页
│   │   ├── DashboardView.vue    # 用户仪表盘
│   │   ├── RecordsView.vue      # 打卡记录
│   │   ├── NotFoundView.vue     # 404 页面
│   │   └── admin/               # 管理员页面
│   │       ├── UsersView.vue    # 用户管理
│   │       ├── RecordsView.vue  # 所有打卡记录
│   │       ├── StatsView.vue    # 统计信息
│   │       └── LogsView.vue     # 系统日志
│   ├── App.vue           # 根组件
│   ├── main.js           # 入口文件
│   └── style.css         # 全局样式
├── .env                  # 环境变量
├── .env.development      # 开发环境变量
├── .env.production       # 生产环境变量
├── vite.config.js        # Vite 配置
├── package.json          # 依赖配置
└── README.md             # 本文件
```

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 生产构建

```bash
npm run build
```

构建产物在 `dist/` 目录。

### 预览生产构建

```bash
npm run preview
```

## 功能特性

### 用户功能

- **QQ 扫码登录**: 支持 QQ 扫码认证
- **个人仪表盘**: 查看 Token 状态、手动打卡
- **打卡记录**: 查看个人打卡历史和统计
- **Token 管理**: 实时监控 Token 过期状态

### 管理员功能

- **用户管理**: CRUD 操作、批量启用/禁用、批量打卡
- **打卡记录**: 查看所有用户的打卡记录
- **统计信息**: 系统整体运行数据统计
- **系统日志**: 实时查看系统运行日志

## API 代理配置

开发环境下，Vite 会自动代理 `/api` 请求到后端服务器：

```javascript
// vite.config.js
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

## 环境变量

创建 `.env.local` 文件自定义配置：

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 路由结构

- `/login` - 登录页面
- `/dashboard` - 用户仪表盘（需登录）
- `/records` - 打卡记录（需登录）
- `/admin/users` - 用户管理（需管理员权限）
- `/admin/records` - 所有打卡记录（需管理员权限）
- `/admin/stats` - 统计信息（需管理员权限）
- `/admin/logs` - 系统日志（需管理员权限）

## 状态管理

使用 Pinia 进行全局状态管理：

- **authStore**: 认证状态（Token、用户信息）
- **userStore**: 用户管理相关
- **checkInStore**: 打卡记录相关
- **adminStore**: 管理员功能相关

## 组件说明

### QRCodeModal

QQ 扫码登录组件，支持：
- 自动获取二维码
- 轮询扫码状态
- 倒计时和进度显示
- 二维码过期提示和刷新

### Navbar

导航栏组件，支持：
- 基于角色的菜单显示
- 当前路由高亮
- 用户信息显示
- 退出登录

### Layout

页面布局组件，包含：
- 顶部导航栏
- 主内容区域
- 响应式布局

## 开发规范

1. **组件命名**: 使用 PascalCase
2. **文件命名**: 组件文件使用 PascalCase，工具文件使用 camelCase
3. **API 调用**: 统一通过 stores 调用，不直接在组件中调用
4. **错误处理**: 使用 try-catch 并显示友好的错误提示
5. **Loading 状态**: 异步操作需显示加载状态

## 浏览器支持

- Chrome >= 87
- Firefox >= 78
- Safari >= 14
- Edge >= 88

## 常见问题

### 启动时端口被占用

修改 `vite.config.js` 中的 `server.port` 配置。

### API 请求失败

检查后端服务是否启动，默认应在 http://localhost:8000 运行。

### 构建产物过大

Element Plus 已配置按需加载，如需进一步优化，可以：
- 使用动态导入 (dynamic import)
- 配置 CDN 引入
- 启用 gzip 压缩

## 部署

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/checkin/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 许可证

MIT
