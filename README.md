# 接龙自动打卡系统 V2

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3.5+-brightgreen.svg)](https://vuejs.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个全自动的接龙打卡系统,支持 QQ 扫码登录、定时自动打卡、Token 过期提醒等功能。采用前后端分离架构,提供完善的 Web 管理界面和 RESTful API。

## ⚡ V2 重大更新

🎉 **用户-任务分离架构** - 一个用户可以管理多个打卡任务
🎉 **全局 Token 刷新** - 扫码一次更新所有任务
🎉 **任务级别控制** - 每个任务独立配置邮箱和启用状态
🎉 **29 个 API 端点** - 更完善的功能覆盖
🎉 **任务所有权验证** - 更安全的权限控制

详见 [V2 架构文档](ARCHITECTURE_V2.md)

## ✨ 主要特性

- 🔐 **QQ 扫码登录** - 支持通过 QQ 扫码快速登录认证
- 👤 **多任务管理** - 一个用户管理多个打卡任务
- ⏰ **定时自动打卡** - 每天固定时间自动为启用的任务执行打卡
- 📧 **邮件通知** - Token 过期提醒、打卡结果通知
- 👥 **用户管理** - 完善的用户 CRUD 和权限管理
- 📋 **任务管理** - 创建、编辑、删除打卡任务
- 📊 **管理后台** - 可视化的数据统计和日志查看
- 🚀 **RESTful API** - 29 个标准化 API 端点,自动生成文档
- 🎯 **角色权限** - 普通用户和管理员角色分离
- 📱 **响应式界面** - 基于 Element Plus 的现代化 UI

## 🏗️ 技术架构

### 后端
- **Web 框架**: FastAPI 0.109+
- **服务器**: Uvicorn (ASGI)
- **ORM**: SQLAlchemy 2.0+
- **数据库**: SQLite (可迁移到 PostgreSQL)
- **任务调度**: APScheduler 3.10+
- **自动化**: Selenium 4.16+
- **认证**: JWT (python-jose)

### 前端
- **框架**: Vue 3.5+
- **构建工具**: Vite 7+
- **UI 组件**: Element Plus 2.13+
- **状态管理**: Pinia 3.0+
- **路由**: Vue Router 4.6+
- **HTTP 客户端**: Axios 1.13+

## 📦 快速开始

### 前置要求

- Python 3.9+
- Node.js 16+ (仅前端需要)
- Chrome 浏览器
- ChromeDriver

### 一键启动（推荐）

**Windows:**
```cmd
# 启动所有服务（后端 + 前端）
manage.bat start-all
```

**Linux/Mac:**
```bash
# 给脚本执行权限
chmod +x manage.sh

# 启动所有服务
./manage.sh start-all
```

### 手动启动

#### 1. 克隆项目
```bash
git clone <repository-url>
cd CheckInApp
```

#### 2. 后端设置
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt

# 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 文件设置 SECRET_KEY 等

# 启动后端
python run.py
```

后端服务将在 http://localhost:8000 启动

#### 3. 前端设置（可选）
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将在 http://localhost:3000 启动

### 4. 创建管理员账户

首次使用需要创建管理员账户:

```bash
# Windows
venv\Scripts\python backend\scripts\create_admin.py

# Linux/Mac
python backend/scripts/create_admin.py
```

按提示输入 alias(用户名) 并通过 QQ 扫码完成管理员创建。

## 📖 使用指南

### 访问地址

- **前端应用**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 登录流程

1. 打开前端应用
2. 输入您的 alias(用户别名)
3. 点击"QQ 扫码登录"
4. 使用手机 QQ 扫描弹出的二维码
5. 扫码成功后自动登录系统

### 用户功能

- 查看 Token 状态和过期时间
- 查看和管理自己的打卡任务
- 创建新的打卡任务
- 手动触发单个任务打卡
- 启用/禁用任务
- 查看任务的打卡记录
- 查看个人信息

### 管理员功能

- 用户管理（创建、编辑、删除）
- 查看所有用户的任务
- 批量启用/禁用任务
- 批量触发打卡
- 查看所有打卡记录
- 查看系统日志
- 系统统计信息（用户数、任务数、打卡统计）

## ⚙️ 配置说明

### 环境变量 (`.env`)

```env
# JWT 密钥（生产环境必须修改）
SECRET_KEY=your-secret-key-change-in-production

# 管理员默认别名
ADMIN_ALIAS=admin

# 数据库 URL（可选）
DATABASE_URL=sqlite:///./data/checkin.db

# CORS 允许的域名
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# 定时打卡时间
CHECKIN_SCHEDULE_HOUR=20
CHECKIN_SCHEDULE_MINUTE=0

# Token 过期检查间隔（分钟）
TOKEN_CHECK_INTERVAL_MINUTES=30

# 会话文件清理间隔（小时）
SESSION_CLEANUP_INTERVAL_HOURS=24
```

### 邮件配置 (`config.ini`)

```ini
[Email]
smtpserver = smtp.example.com
smtpport = 465
senderemail = your-email@example.com
senderpassword = your-password
```

## 📂 项目结构

```
CheckInApp/
├── backend/                # FastAPI 后端
│   ├── main.py            # 应用入口
│   ├── config.py          # 配置管理
│   ├── dependencies.py    # 认证中间件
│   ├── models/            # 数据库模型
│   │   ├── user.py       # User 模型
│   │   ├── check_in_task.py  # CheckInTask 模型 (V2 新增)
│   │   └── check_in_record.py # CheckInRecord 模型
│   ├── schemas/           # Pydantic Schema
│   │   ├── user.py
│   │   ├── task.py       # (V2 新增)
│   │   ├── auth.py
│   │   └── check_in.py
│   ├── api/               # API 路由
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── tasks.py      # (V2 新增)
│   │   ├── check_in.py
│   │   └── admin.py
│   ├── services/          # 业务逻辑
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── task_service.py  # (V2 新增)
│   │   ├── check_in_service.py
│   │   └── scheduler_service.py
│   ├── workers/           # Selenium 工作模块
│   │   ├── token_refresher.py
│   │   ├── check_in_worker.py
│   │   └── email_notifier.py
│   └── scripts/           # 工具脚本
│       └── create_admin.py
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── api/          # API 调用
│   │   ├── components/   # 组件
│   │   ├── views/        # 页面
│   │   ├── stores/       # Pinia 状态
│   │   └── router/       # 路由配置
│   └── package.json
├── data/                  # 数据库文件
├── logs/                  # 日志文件
│   └── backend.log       # 后端日志 (V2 更名)
├── sessions/              # 会话临时文件
├── venv/                  # Python 虚拟环境
├── run.py                 # 后端启动脚本
├── manage.bat/sh          # 进程管理脚本 (V2 增强)
├── ARCHITECTURE_V2.md     # V2 架构文档 (新增)
└── config.ini             # 邮件配置
```

## 📊 API 端点

系统提供 **29 个 RESTful API 端点**:

### 认证 (`/api/auth`)
- `POST /api/auth/request_qrcode` - 请求 QQ 扫码
- `GET /api/auth/qrcode_status/{session_id}` - 查询扫码状态
- `POST /api/auth/verify_token` - 验证 Token

### 用户 (`/api/users`)
- `POST /api/users` - 创建用户（管理员）
- `GET /api/users/me` - 获取当前用户
- `GET /api/users/me/token_status` - Token 状态
- `GET /api/users/me/tasks` - 获取当前用户任务列表 **(V2 新增)**
- `GET /api/users` - 用户列表（管理员）
- `GET /api/users/{user_id}` - 获取指定用户
- `PUT /api/users/{user_id}` - 更新用户
- `DELETE /api/users/{user_id}` - 删除用户（管理员）

### 任务 (`/api/tasks`) **(V2 新增模块)**
- `POST /api/tasks` - 创建任务
- `GET /api/tasks` - 获取当前用户任务
- `GET /api/tasks/{task_id}` - 获取任务详情
- `PUT /api/tasks/{task_id}` - 更新任务
- `DELETE /api/tasks/{task_id}` - 删除任务
- `POST /api/tasks/{task_id}/toggle` - 切换任务状态

### 打卡 (`/api/check_in`)
- `POST /api/check_in/manual/{task_id}` - 手动触发任务打卡
- `GET /api/check_in/task/{task_id}/records` - 获取任务打卡记录
- `GET /api/check_in/records` - 所有记录（管理员）
- `GET /api/check_in/records/count` - 记录统计（管理员）

### 管理员 (`/api/admin`)
- `POST /api/admin/batch_toggle_tasks` - 批量启用/禁用任务
- `POST /api/admin/batch_check_in` - 批量打卡
- `GET /api/admin/logs` - 系统日志
- `GET /api/admin/stats` - 系统统计

详细 API 文档请访问: http://localhost:8000/docs

## ⏰ 自动化任务

系统自动执行以下定时任务:

1. **定时打卡**: 每天 20:00 为所有启用的任务执行打卡
2. **Token 检查**: 每 30 分钟检查一次,即将过期时发送邮件到任务的邮箱
3. **会话清理**: 每 24 小时清理过期的会话文件

## 🔧 进程管理

使用内置的进程管理脚本可以方便地管理服务:

**Windows:**
```cmd
manage.bat start-backend   # 启动后端服务
manage.bat start-frontend  # 启动前端服务
manage.bat start-all       # 启动所有服务
manage.bat stop-backend    # 停止后端
manage.bat stop-frontend   # 停止前端
manage.bat stop-all        # 停止所有服务
manage.bat status          # 查看状态
manage.bat logs-backend    # 查看后端日志
manage.bat logs-frontend   # 查看前端日志
```

**Linux/Mac:**
```bash
./manage.sh start-backend
./manage.sh start-frontend
./manage.sh start-all
./manage.sh stop-backend
./manage.sh stop-frontend
./manage.sh stop-all
./manage.sh status
./manage.sh logs-backend
./manage.sh logs-frontend
```

## 🐛 故障排查

### 端口被占用
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

### 查看日志
```bash
# 后端日志
cat logs/backend.log

# 使用管理脚本查看
manage.bat logs-backend  # Windows
./manage.sh logs-backend  # Linux/Mac
```

### Selenium 问题

确保 Chrome 和 ChromeDriver 已正确配置。相关路径在 `backend/workers/` 中定义。

## 📚 文档

- [快速入门指南](QUICKSTART.md)
- [V2 架构文档](ARCHITECTURE_V2.md) **(推荐阅读)**
- [后端详细文档](backend/README.md)
- [后端开发总结](BACKEND_SUMMARY.md)
- [V1 旧版文档](v1/README.md)

## 🔒 安全建议

1. **生产环境务必修改 SECRET_KEY**
2. 不要将 `.env` 文件提交到版本控制
3. 定期更新依赖包
4. 使用 HTTPS 部署生产环境
5. 限制管理员账户数量
6. 定期备份数据库

## 🚀 部署

### Docker 部署（推荐）
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

### 传统部署
1. 使用 Gunicorn 运行后端
2. 构建前端并使用 Nginx 托管
3. 配置反向代理

详见部署文档。

## 📝 V2 更新日志

### 架构改进
- ✅ 实现用户-任务分离架构
- ✅ 新增 CheckInTask 数据模型
- ✅ 引入三层身份体系 (jwt_sub + alias + signature)
- ✅ 全局 Token 刷新机制

### 新增功能
- ✅ 任务管理 API (6个端点)
- ✅ 任务所有权验证
- ✅ 用户任务列表查询
- ✅ 任务级别的邮箱配置
- ✅ 任务级别的启用/禁用

### 功能优化
- ✅ API 端点从 18 个增加到 29 个
- ✅ 改进的权限控制系统
- ✅ 更清晰的代码结构
- ✅ UTF-8 编码全面支持
- ✅ 增强的日志系统
- ✅ 改进的进程管理脚本

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

[MIT License](LICENSE)

## 🙏 致谢

感谢所有开源项目的贡献者!

---

**版本**: V2.0.0
**状态**: ✅ 生产就绪
**最后更新**: 2025-12-31

## 🏗️ 技术架构

### 后端
- **Web 框架**: FastAPI 0.109+
- **服务器**: Uvicorn (ASGI)
- **ORM**: SQLAlchemy 2.0+
- **数据库**: SQLite (可迁移到 PostgreSQL)
- **任务调度**: APScheduler 3.10+
- **自动化**: Selenium 4.16+
- **认证**: JWT (python-jose)

### 前端
- **框架**: Vue 3.5+
- **构建工具**: Vite 7+
- **UI 组件**: Element Plus 2.13+
- **状态管理**: Pinia 3.0+
- **路由**: Vue Router 4.6+
- **HTTP 客户端**: Axios 1.13+

## 📦 快速开始

### 前置要求

- Python 3.9+
- Node.js 16+ (仅前端需要)
- Chrome 浏览器
- ChromeDriver

### 一键启动（推荐）

**Windows:**
```cmd
# 启动所有服务（后端 + 前端）
start_all.bat
```

**Linux/Mac:**
```bash
# 给脚本执行权限
chmod +x start_all.sh

# 启动所有服务
./start_all.sh
```

### 手动启动

#### 1. 克隆项目
```bash
git clone <repository-url>
cd CheckInApp
```

#### 2. 后端设置
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt

# 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 文件设置 SECRET_KEY 等

# 启动后端
python run.py
```

后端服务将在 http://localhost:8000 启动

#### 3. 前端设置（可选）
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将在 http://localhost:3000 启动

### 4. 创建管理员账户

首次使用需要创建管理员账户：

```bash
# Windows
venv\Scripts\python backend\scripts\create_admin.py

# Linux/Mac
python backend/scripts/create_admin.py
```

按提示输入 Signature 并通过 QQ 扫码完成管理员创建。

## 📖 使用指南

### 访问地址

- **前端应用**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 登录流程

1. 打开前端应用
2. 输入您的 Signature（唯一标识）
3. 点击"QQ 扫码登录"
4. 使用手机 QQ 扫描弹出的二维码
5. 扫码成功后自动登录系统

### 用户功能

- 查看 Token 状态和过期时间
- 手动触发打卡
- 查看自己的打卡记录
- 查看个人信息

### 管理员功能

- 用户管理（创建、编辑、删除）
- 批量启用/禁用用户
- 批量触发打卡
- 查看所有打卡记录
- 查看系统日志
- 系统统计信息

## ⚙️ 配置说明

### 环境变量 (`.env`)

```env
# JWT 密钥（生产环境必须修改）
SECRET_KEY=your-secret-key-change-in-production

# 管理员默认标识
ADMIN_SIGNATURE=admin

# 数据库 URL（可选）
DATABASE_URL=sqlite:///./data/checkin.db

# CORS 允许的域名
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# 定时打卡时间
CHECKIN_SCHEDULE_HOUR=20
CHECKIN_SCHEDULE_MINUTE=0
```

### 邮件配置 (`config.ini`)

```ini
[Email]
smtpserver = smtp.example.com
smtpport = 465
senderemail = your-email@example.com
senderpassword = your-password
```

## 📂 项目结构

```
CheckInApp/
├── backend/                # FastAPI 后端
│   ├── main.py            # 应用入口
│   ├── config.py          # 配置管理
│   ├── dependencies.py    # 认证中间件
│   ├── models/            # 数据库模型
│   ├── schemas/           # Pydantic Schema
│   ├── api/               # API 路由
│   ├── services/          # 业务逻辑
│   ├── workers/           # Selenium 工作模块
│   └── scripts/           # 工具脚本
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── api/          # API 调用
│   │   ├── components/   # 组件
│   │   ├── views/        # 页面
│   │   ├── stores/       # Pinia 状态
│   │   └── router/       # 路由配置
│   └── package.json
├── data/                  # 数据库文件
├── logs/                  # 日志文件
├── sessions/              # 会话临时文件
├── venv/                  # Python 虚拟环境
├── run.py                 # 后端启动脚本
├── manage.bat/sh          # 进程管理脚本
├── start_all.bat/sh       # 一键启动脚本
└── config.ini             # 邮件配置
```

## 📊 API 端点

系统提供 18 个 RESTful API 端点：

### 认证 (`/api/auth`)
- `POST /api/auth/request_qrcode` - 请求 QQ 扫码
- `GET /api/auth/qrcode_status/{session_id}` - 查询扫码状态
- `POST /api/auth/verify_token` - 验证 Token

### 用户 (`/api/users`)
- `POST /api/users` - 创建用户
- `GET /api/users/me` - 获取当前用户
- `GET /api/users/me/token_status` - Token 状态
- `GET /api/users` - 用户列表
- `PUT /api/users/{user_id}` - 更新用户
- `DELETE /api/users/{user_id}` - 删除用户

### 打卡 (`/api/check_in`)
- `POST /api/check_in/manual` - 手动打卡
- `GET /api/check_in/my_records` - 我的记录
- `GET /api/check_in/records` - 所有记录
- `GET /api/check_in/records/count` - 记录统计

### 管理员 (`/api/admin`)
- `POST /api/admin/batch_toggle_active` - 批量启用/禁用
- `POST /api/admin/batch_check_in` - 批量打卡
- `GET /api/admin/logs` - 系统日志
- `GET /api/admin/stats` - 系统统计

详细 API 文档请访问: http://localhost:8000/docs

## ⏰ 自动化任务

系统自动执行以下定时任务：

1. **定时打卡**: 每天 20:00 为所有启用的用户执行打卡
2. **Token 检查**: 每 30 分钟检查一次，即将过期时发送邮件
3. **会话清理**: 每 24 小时清理过期的会话文件

## 🔧 进程管理

使用内置的进程管理脚本可以方便地管理后端服务：

**Windows:**
```cmd
manage.bat start    # 启动服务（后台运行）
manage.bat stop     # 停止服务
manage.bat restart  # 重启服务
manage.bat status   # 查看状态
```

**Linux/Mac:**
```bash
./manage.sh start
./manage.sh stop
./manage.sh restart
./manage.sh status
```

## 🐛 故障排查

### 端口被占用
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

### 查看日志
```bash
# 后端日志
cat logs/CheckIn.log

# 使用管理脚本查看
./manage.sh status
```

### Selenium 问题

确保 Chrome 和 ChromeDriver 已正确配置。相关路径在 `backend/workers/` 中定义。

## 📚 文档

- [快速入门指南](QUICKSTART.md)
- [后端详细文档](backend/README.md)
- [后端开发总结](BACKEND_SUMMARY.md)
- [V1 旧版文档](v1/README.md)

## 🔒 安全建议

1. **生产环境务必修改 SECRET_KEY**
2. 不要将 `.env` 文件提交到版本控制
3. 定期更新依赖包
4. 使用 HTTPS 部署生产环境
5. 限制管理员账户数量

## 🚀 部署

### Docker 部署（推荐）
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

### 传统部署
1. 使用 Gunicorn 运行后端
2. 构建前端并使用 Nginx 托管
3. 配置反向代理

详见部署文档。

## 📝 开发计划

- [x] 后端 API 开发
- [x] 前端基础框架
- [x] 用户认证系统
- [x] 管理员功能
- [ ] 批量导入用户
- [ ] 数据导出功能
- [ ] Docker 镜像优化
- [ ] 单元测试覆盖

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[MIT License](LICENSE)

## 🙏 致谢

感谢所有开源项目的贡献者！

---

**版本**: V2.0.0
**状态**: ✅ 生产就绪
**最后更新**: 2025-12-31
