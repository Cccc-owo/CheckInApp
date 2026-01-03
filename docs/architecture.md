# 架构设计

## 系统概述

CheckIn App V2 采用用户-任务分离架构，一个用户可管理多个打卡任务，全局 Token 刷新，任务级别独立控制。

## 核心架构

### V2 关键改进

- **用户-任务分离**: User 和 CheckInTask 独立管理
- **全局 Token**: 用户级别的 authorization token，一次扫码更新所有任务
- **任务级控制**: 每个任务独立的启用状态和邮箱配置
- **任务模板**: TaskTemplate 系统，快速创建标准化任务

### 数据模型

#### User（用户）

```python
- id: 主键
- jwt_sub: QQ ID（唯一）
- alias: 用户名
- email: 邮箱
- password_hash: 密码（可选）
- authorization: QQ Token（全局）
- jwt_exp: Token 过期时间
- role: admin/user
- is_approved: 审批状态
```

#### CheckInTask（任务）

```python
- id: 主键
- user_id: 所属用户
- name: 任务名称
- payload_config: JSON 配置（包含打卡字段）
- cron_expression: 定时表达式（如 "0 20 * * *"）
- is_active: 是否启用
```

#### CheckInRecord（记录）

```python
- id: 主键
- task_id: 所属任务
- status: success/failed/already_submitted
- response_text: API 响应
- trigger_type: scheduled/manual/admin
- check_in_time: 打卡时间
```

#### TaskTemplate（模板）

```python
- id: 主键
- name: 模板名称
- field_config: JSON 字段配置
- parent_id: 父模板（可选）
- is_active: 是否启用
```

## 技术栈

### 后端

- **FastAPI**: Web 框架，自动生成 API 文档
- **SQLAlchemy**: ORM，支持多数据库
- **APScheduler**: 任务调度，动态加载 cron 任务
- **Selenium**: 浏览器自动化，获取 QQ Token 和打卡 payload
- **JWT**: 身份认证
- **SMTP**: 邮件通知

### 前端

- **Vue 3**: Composition API
- **Ant Design Vue**: UI 组件库
- **Pinia**: 状态管理
- **Axios**: HTTP 客户端，拦截器处理 Token

## 认证流程

### QQ 扫码登录

1. 用户输入 alias
2. 后端检查 alias 可用性和频率限制
3. Selenium 启动 headless Chrome，打开接龙登录页
4. 生成 QR code，返回给前端
5. 用户手机 QQ 扫码
6. Selenium 检测登录成功，提取 authorization token 和 jwt
7. 存储用户信息（待审批状态）
8. 管理员审批后用户可登录

### 密码登录

1. 用户设置密码后可使用 alias + password 登录
2. 后端验证密码，返回 JWT token

## 打卡流程

### 手动打卡

1. 用户点击任务的"立即打卡"按钮
2. 后端异步执行打卡任务
3. Selenium 获取最新 x-api-request-payload
4. 使用用户的 authorization token 调用接龙 API
5. 解析响应，存储记录
6. 返回结果

### 定时打卡

1. 系统启动时加载所有启用的任务
2. APScheduler 根据 cron_expression 调度
3. 到达时间后自动执行打卡流程
4. 发送邮件通知到任务配置的邮箱

## 调度任务

### Token 监控

- 间隔: 30 分钟（可配置）
- 功能: 检查 Token 过期时间
  - 30 分钟内过期: 发送预警邮件
  - 已过期 30 分钟内: 发送过期通知

### 会话清理

- 间隔: 24 小时
- 功能: 删除旧的 Selenium 会话文件

### 用户清理

- 间隔: 1 小时
- 功能: 删除 24 小时未审批的用户

## 权限控制

### 角色

- **admin**: 所有权限
- **user**: 仅操作自己的数据

### 验证机制

- 任务所有权验证: 确保用户只能操作自己的任务
- JWT 认证: 所有 API 需要有效 token
- 审批机制: 新用户需管理员审批

## 目录结构

### 后端分层

```
backend/
├── api/          # 路由层（29 个端点）
├── services/     # 业务逻辑层
├── models/       # 数据模型层
├── schemas/      # 请求响应模型
├── workers/      # Selenium 工作模块
└── scripts/      # 工具脚本
```

### 前端分层

```
frontend/src/
├── api/          # API 调用封装
├── views/        # 页面组件
├── components/   # 可复用组件
├── stores/       # Pinia 状态
├── router/       # 路由配置
└── composables/  # 组合式函数
```

## 扩展性

- 数据库可切换到 PostgreSQL/MySQL
- 调度任务可扩展到 Celery
- 前端可独立部署到 CDN
- 支持 Docker 容器化部署
