# 接龙自动打卡系统 - 后端 API

FastAPI 后端服务，提供用户管理、QQ 扫码登录、自动打卡等功能。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境

创建 `.env` 文件（可选）：

```env
# 邮件通知配置（可选）
SMTP_SERVER=smtp.example.com
SMTP_PORT=465
SMTP_SENDER_EMAIL=your-email@example.com
SMTP_SENDER_PASSWORD=your-password-here

# Chrome 浏览器配置（可选）
CHROME_BINARY_PATH=
CHROMEDRIVER_PATH=
```

### 3. 初始化数据库

数据库会在首次启动时自动初始化。

### 4. 创建管理员用户

```bash
python backend/scripts/create_admin.py
```

按照提示输入管理员信息：
- Signature: 管理员标识（唯一）
- ThreadId: 接龙 ID
- 邮箱: 接收通知的邮箱

### 5. 启动服务

```bash
# 开发模式（支持热重载）
cd backend
python main.py

# 或者使用 uvicorn
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. 访问 API 文档

启动后访问: http://localhost:8000/docs

## 📁 项目结构

```
backend/
├── main.py                 # FastAPI 应用入口
├── config.py               # 配置管理
├── dependencies.py         # 认证中间件
├── requirements.txt        # Python 依赖
├── models/                 # 数据库模型
│   ├── database.py        # 数据库配置
│   ├── user.py            # User 模型
│   └── check_in_record.py # CheckInRecord 模型
├── schemas/                # Pydantic Schema
│   ├── user.py            # 用户相关 Schema
│   ├── auth.py            # 认证相关 Schema
│   └── check_in.py        # 打卡相关 Schema
├── api/                    # API 路由
│   ├── auth.py            # 认证 API
│   ├── users.py           # 用户管理 API
│   ├── check_in.py        # 打卡 API
│   └── admin.py           # 管理员 API
├── services/               # 业务逻辑层
│   ├── auth_service.py    # 认证服务
│   ├── user_service.py    # 用户服务
│   ├── check_in_service.py # 打卡服务
│   └── scheduler_service.py # 调度服务
├── workers/                # Selenium 工作模块
│   ├── token_refresher.py  # Token 刷新（QQ 扫码）
│   ├── check_in_worker.py  # 打卡执行
│   └── email_notifier.py   # 邮件通知
└── scripts/                # 工具脚本
    └── create_admin.py     # 创建管理员用户
```

## 🔌 API 端点

### 认证 API (`/api/auth`)

- `POST /api/auth/request_qrcode` - 请求 QQ 扫码二维码
- `GET /api/auth/qrcode_status/{session_id}` - 检查扫码状态
- `POST /api/auth/verify_token` - 验证 Token 有效性

### 用户 API (`/api/users`)

- `POST /api/users` - 创建用户（管理员）
- `GET /api/users/me` - 获取当前用户信息
- `GET /api/users/me/token_status` - 获取 Token 状态
- `GET /api/users` - 获取所有用户（管理员）
- `GET /api/users/{user_id}` - 获取指定用户
- `PUT /api/users/{user_id}` - 更新用户信息
- `DELETE /api/users/{user_id}` - 删除用户（管理员）

### 打卡 API (`/api/check_in`)

- `POST /api/check_in/manual` - 手动触发打卡
- `GET /api/check_in/my_records` - 查看自己的打卡记录
- `GET /api/check_in/records` - 查看所有打卡记录（管理员）
- `GET /api/check_in/records/count` - 获取打卡记录统计（管理员）

### 管理员 API (`/api/admin`)

- `POST /api/admin/batch_toggle_active` - 批量启用/禁用用户
- `POST /api/admin/batch_check_in` - 批量触发打卡
- `GET /api/admin/logs` - 获取系统日志
- `GET /api/admin/stats` - 获取系统统计

## ⚙️ 配置说明

### 邮件配置 (`config.ini`)

在项目根目录创建 `config.ini`：

```ini
[Email]
smtpserver = smtp.example.com
smtpport = 465
senderemail = your-email@example.com
senderpassword = your-password
```

### 定时任务配置

在 `backend/config.py` 中配置：

- `CHECKIN_SCHEDULE_HOUR`: 定时打卡小时（默认 20）
- `CHECKIN_SCHEDULE_MINUTE`: 定时打卡分钟（默认 0）
- `TOKEN_CHECK_INTERVAL_MINUTES`: Token 检查间隔（默认 30 分钟）
- `SESSION_CLEANUP_INTERVAL_HOURS`: 会话清理间隔（默认 24 小时）

## 🔐 认证流程

1. 用户输入 Signature 并请求二维码
2. 后端启动 Selenium 获取 QQ 登录二维码
3. 前端轮询检查扫码状态
4. 用户使用手机 QQ 扫码
5. 后端获取 Token 并解析 JWT
6. 用户后续请求使用 `Authorization: Bearer <token>` header

## 📊 定时任务

系统会自动执行以下定时任务：

1. **定时打卡**: 每天 20:00 为所有启用的用户执行打卡
2. **Token 过期检查**: 每 30 分钟检查一次，Token 在 30 分钟内过期时发送邮件提醒
3. **会话文件清理**: 每 24 小时清理超过 24 小时的旧会话文件

## 🛠️ 开发说明

### 添加新的 API 端点

1. 在 `backend/schemas/` 中定义请求/响应 Schema
2. 在 `backend/services/` 中实现业务逻辑
3. 在 `backend/api/` 中创建 API 路由
4. 在 `backend/main.py` 中注册路由

### 数据库迁移

如果修改了模型，删除 `data/checkin.db` 并重启服务即可重新创建数据库。

⚠️ 注意：生产环境建议使用 Alembic 进行数据库迁移。

## 🐛 故障排查

### 问题：无法启动 Selenium

确保已安装 Chrome 和 ChromeDriver：

```bash
# 检查路径配置
ls chrome-linux64/chrome
ls chromedriver
```

### 问题：Token 验证失败

检查数据库中用户的 `authorization` 字段是否有值。

### 问题：定时任务未执行

检查日志文件 `logs/CheckIn.log`，确认调度器是否成功启动。

### 问题：邮件发送失败

检查 `config.ini` 配置是否正确，SMTP 服务器是否可访问。

## 📝 环境变量

可选的环境变量：

- `DATABASE_URL`: 数据库 URL（默认使用 SQLite）
- `CORS_ORIGINS`: 允许的前端域名（默认 localhost:5173 和 localhost:3000）
- `SMTP_SERVER`: 邮件服务器地址（用于邮件通知，可选）
- `SMTP_SENDER_EMAIL`: 发件人邮箱（用于邮件通知，可选）
- `CHROME_BINARY_PATH`: Chrome 浏览器路径（可选，留空自动检测）
- `CHROMEDRIVER_PATH`: ChromeDriver 路径（可选，留空自动下载）

## 🚀 部署建议

### 使用 Gunicorn

```bash
pip install gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 使用 Systemd

创建 `/etc/systemd/system/checkin-api.service`：

```ini
[Unit]
Description=CheckIn API Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/CheckInApp
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl enable checkin-api
sudo systemctl start checkin-api
sudo systemctl status checkin-api
```

## 📄 许可证

本项目仅供学习和研究使用。
