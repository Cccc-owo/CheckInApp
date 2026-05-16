# 架构设计

## 系统概述

CheckIn App V2 是一个接龙自动打卡系统，采用同仓库的前后端分离架构：

- 后端提供 FastAPI API、数据库访问、调度器、邮件通知和 Playwright 自动化能力。
- 前端提供 Vue 3 单页应用，负责登录、审批状态、任务、记录、模板和管理员后台。
- SQLite 是当前默认持久化层，运行数据集中在仓库根目录的 `data/`、`logs/` 和 `sessions/`。
- 生产部署推荐使用 Docker Compose，由 nginx 托管前端静态文件并反向代理后端 API。

系统的核心边界是“网站登录身份”和“打卡业务授权”分离：

- 网站登录使用应用自己签发的 JWT，前端保存在 localStorage，用于访问 `/api/*`。
- 打卡业务使用 QQ 扫码得到的接龙 authorization token，后端保存在 `users.authorization`，仅在执行打卡和 Token 监控时使用。

## 运行时视图

```text
Browser (Vue SPA)
    |
    | fetch /api/*
    v
FastAPI app (apps/backend/main.py)
    |
    +-- API routers (auth/users/tasks/templates/check_in/admin)
    |       |
    |       v
    |   Services (业务规则、权限辅助、邮件、调度同步)
    |       |
    |       v
    |   SQLAlchemy models -> SQLite data/checkin.db
    |
    +-- APScheduler (动态任务 + 系统维护任务)
    |
    +-- Worker threads
            |
            +-- Playwright token refresh / QR login
            +-- Playwright check-in payload capture
            +-- requests 调用接龙 API
```

后端启动生命周期由 `apps/backend/main.py` 的 FastAPI lifespan 管理：

1. 初始化数据库表。
2. 执行待处理数据库迁移。
3. 确保 `data/`、`logs/`、`sessions/` 存在。
4. 启动 APScheduler，并加载启用的动态打卡任务。
5. 应用关闭时停止调度器。

根目录 `main.py` 是本地开发和部署辅助入口，负责启动后端、前端、守护进程、迁移、构建和状态查询。

## 代码分层

### 后端

```text
apps/backend/
├── main.py              # FastAPI app、生命周期、CORS、异常处理、路由注册
├── config.py            # pydantic-settings 配置与 .env 读取
├── dependencies.py      # JWT 当前用户、审批用户、管理员依赖
├── exceptions.py        # 结构化业务异常
├── limiter.py           # slowapi 限流器
├── migrations.py        # 内置迁移编排和 schema_migrations 表
├── api/                 # HTTP 路由层，只做请求解析、权限依赖、服务调用
├── services/            # 业务规则和跨模块协调
├── models/              # SQLAlchemy ORM 模型和数据库会话
├── schemas/             # Pydantic 请求/响应结构
├── workers/             # Playwright 与打卡执行器
├── email_templates/     # Jinja 风格邮件模板渲染
├── migration_steps/     # 单个迁移步骤
└── scripts/             # 管理和迁移脚本
```

主要约束：

- 路由层不直接承载复杂业务规则，核心规则放在 `services/`。
- 所有数据库会话通过 `get_db()` 或后台线程内独立 `SessionLocal()` 创建。
- 后台线程不能复用请求线程的 SQLAlchemy session。
- 业务可预期错误使用 `BaseAPIException` 派生类，统一返回 `{ "error": { "code", "message", "field" } }` 风格。
- SQLite datetime 读取后会被规范化为 UTC timezone-aware，避免 naive datetime 在业务层扩散。

### 前端

```text
apps/frontend/src/
├── main.ts              # Vue 应用入口
├── App.vue              # 根组件和当前 route 渲染
├── app/
│   ├── auth.ts          # 登录态、当前用户、localStorage 同步
│   ├── router.ts        # 轻量前端路由和守卫
│   └── theme.ts         # 主题偏好
├── api/
│   ├── client.ts        # fetch 封装、Bearer token、错误归一化
│   ├── index.ts         # 按业务域拆分 API helper
│   └── types.ts         # 前端 API 类型
├── views/               # 用户页面
├── views/admin/         # 管理员页面
├── components/          # 应用组件和 UI primitive
└── utils/               # 格式化 helper
```

前端没有引入 Vue Router，而是在 `app/router.ts` 中维护路由表、路径匹配和守卫。守卫规则：

- 未登录用户访问受保护页面会跳转 `/login`。
- 已登录但未审批用户只能进入 `/pending-approval`。
- 已审批用户访问 `/pending-approval` 会跳转 `/dashboard`。
- 管理员页面要求 `role === "admin"`。
- 已登录已审批用户访问 `/login` 会跳转 `/dashboard`。

API 访问统一走 `api/client.ts`。它会：

- 从 localStorage 读取应用 JWT 并附加 `Authorization: Bearer <token>`。
- 将结构化错误、FastAPI `detail` 和网络错误统一成前端 `ApiError`。
- 在 401 时清理本地登录态。
- 通过 `VITE_API_BASE_URL` 支持前后端不同源部署。

## API 边界

后端统一挂载在 `settings.API_PREFIX`，当前默认是 `/api`：

- `/api/auth`：扫码登录/注册、二维码状态、取消扫码会话、JWT 验证、别名密码登录。
- `/api/users`：当前用户、邮箱验证、个人资料、用户管理、用户任务列表。
- `/api/tasks`：当前用户任务列表、详情、更新、删除、启停、cron 校验。
- `/api/templates`：模板列表/预览、管理员模板管理、从模板创建任务。
- `/api/check_in`：手动打卡、打卡状态、用户记录、任务记录、管理员全部记录。
- `/api/admin`：待审批用户、审批/拒绝、统计、日志、批量任务操作、邮件与通知策略。

权限分层：

- `get_current_user` 只验证应用 JWT，不要求审批通过。
- `require_approved_user` 要求用户已通过审批。
- `get_current_admin_user` 要求已审批且角色为 admin。
- 路由内的任务和记录访问必须通过任务归属校验，普通用户只能操作自己的任务与记录。

## 数据模型

### User

用户账户、登录凭证、审批和通知状态。

关键字段：

- `jwt_sub`：QQ 扫码登录得到的唯一用户标识；管理员手动创建的测试/预置用户可为空。
- `alias`：站内登录名，唯一。
- `email`、`email_verified_at`、`email_verification_code_hash`、`email_verification_expires_at`：邮箱验证流程。
- `password_hash`：别名+密码登录使用的 bcrypt 哈希。
- `authorization`：接龙业务 authorization token。
- `jwt_exp`：接龙业务 token 的过期时间戳字符串。
- `token_expiring_notified`、`token_expired_notified`：Token 提醒去重标志。
- `role`：`user` 或 `admin`。
- `is_approved`：管理员审批状态。
- `failed_login_attempts`、`locked_until`、`last_failed_login`：密码登录锁定状态。

关系：

- 一个用户拥有多个 `CheckInTask`。
- 删除用户会级联删除其任务和打卡记录。

### CheckInTask

用户的单个接龙打卡任务。

关键字段：

- `user_id`：所属用户。
- `thread_id`：接龙项目 ID，和用户组成唯一约束。
- `payload_config`：完整打卡 payload JSON。
- `name`：任务显示名。
- `is_active`：是否启用自动调度，不影响手动打卡。
- `cron_expression`：五段 crontab 表达式；为空表示不调度。

约束：

- `(user_id, thread_id)` 唯一，防止同一用户重复创建同一接龙任务。
- 调度启用条件是 `is_active == true` 且 `cron_expression` 非空且合法。

### CheckInRecord

一次打卡执行的结果。

关键字段：

- `task_id`：所属任务。
- `status`：`pending`、`success`、`failure`、`out_of_time`、`unknown`、`token_expired` 等。
- `response_text`：接龙 API 响应文本。
- `error_message`：失败信息。
- `location`：位置信息 JSON。
- `trigger_type`：`scheduled`、`manual` 或 `admin`。
- `check_in_time`：UTC 时间。

### TaskTemplate

管理员维护的任务模板，用于快速创建任务 payload。

关键字段：

- `name`、`description`：模板展示信息。
- `parent_id`：父模板，可多层继承。
- `field_config`：字段配置 JSON。
- `is_active`：是否对普通用户可用。

模板服务会递归合并父模板配置，子模板字段覆盖父模板字段；从模板创建任务时会把用户输入字段转换成完整 payload，并写入任务的 `payload_config` 和 `thread_id`。

### EmailNotificationSettings

管理员可配置的邮件和审批策略。

关键字段：

- SMTP：`smtp_server`、`smtp_port`、`smtp_sender_email`、`smtp_sender_password`、`smtp_use_ssl`。
- 通知开关：`notify_token_expiring`、`notify_check_in_success`。
- 注册审批策略：`require_admin_approval_for_registration`、`require_verified_email_for_approval`。

## 核心业务流程

### QQ 扫码登录和注册

1. 前端调用 `/api/auth/request_qrcode`，提交 alias。
2. 后端做注册频率限制和 alias 预占，创建 `session_id`。
3. 后台线程调用 Playwright 打开接龙登录页并生成二维码。
4. 前端轮询 `/api/auth/qrcode_status/{session_id}`。
5. 扫码成功后，后端解析接龙 token 中的 `sub` 和 `exp`。
6. 如果 `jwt_sub` 已存在，更新该用户的 `authorization`、`jwt_exp` 和通知标志。
7. 如果是新用户，创建 `User`，审批状态取决于邮件设置中的注册审批策略。
8. 后端签发应用 JWT 返回前端，前端保存后进入审批或业务页面。

扫码得到的是打卡业务 token；返回给前端的是应用 JWT。两者不能混用。

### 别名密码登录

1. 前端调用 `/api/auth/alias_login`。
2. 后端按 alias 查找用户并检查账户锁定状态。
3. 使用 bcrypt 验证 `password_hash`。
4. 登录成功后签发应用 JWT。
5. 如果打卡业务 token 过期，登录仍可成功，但前端应提示用户刷新授权。

### 邮箱验证和审批

1. 已登录用户可在未审批状态下调用 `/api/users/me/email` 设置邮箱。
2. 后端规范化邮箱、生成 6 位验证码、保存 bcrypt 哈希和 10 分钟过期时间。
3. 邮件服务发送验证码；发送失败则回滚邮箱更新。
4. 用户调用 `/api/users/me/email/verify` 校验验证码。
5. 管理员审批时，审批策略可要求邮箱已验证；需要绕过时必须显式提交 `allow_unverified_email`。
6. 审批通过或拒绝会触发相应邮件通知。

### 从模板创建任务

1. 普通用户读取启用模板，管理员可管理所有模板。
2. 用户选择模板、填写 `thread_id` 和字段值。
3. `TemplateService` 合并父模板配置并生成完整 payload。
4. `TaskService` 创建 `CheckInTask`，提取并持久化 `thread_id`。
5. 如果同一用户已存在相同 `thread_id`，返回结构化 409 冲突。
6. 任务创建或更新后同步 APScheduler 中的动态任务。

### 手动打卡

1. 前端调用 `/api/check_in/manual/{task_id}`。
2. 后端验证任务归属。
3. `CheckInService.start_async_check_in()` 创建 `pending` 记录。
4. 后台线程使用独立数据库 session 执行打卡。
5. Worker 使用任务 payload 和用户 `authorization` 调用接龙接口。
6. 后台线程更新记录状态、响应文本和错误信息。
7. 前端轮询 `/api/check_in/record/{record_id}/status` 获取结果。

### 定时打卡

1. 后端启动时 `start_scheduler()` 获取 `scheduler.lock`，确保多进程部署中只有一个调度器。
2. APScheduler 添加系统维护任务。
3. `load_scheduled_tasks()` 加载所有启用且有 cron 的任务。
4. 每个任务以 `task_{id}` 注册动态 job。
5. job 触发后调用 `scheduled_check_in_task()`，再走异步打卡流程。
6. 任务启停、cron 更新或删除时需要同步对应 job。

### Token 监控和邮件通知

系统任务 `check_token_expiration` 按 `TOKEN_CHECK_INTERVAL_MINUTES` 执行：

- 跳过未配置邮箱或 `jwt_exp` 无效的用户。
- 打卡 token 过期前 30 分钟内发送即将过期提醒。
- 打卡 token 已过期且尚未通知时发送过期提醒。
- Token 被刷新且剩余时间恢复到 30 分钟以上时重置提醒标志。

打卡失败且识别为 token 过期时，也会走统一的过期通知逻辑。

## 后台任务和并发模型

当前后台执行模型是“进程内调度器 + 守护线程”：

- APScheduler 负责定时触发。
- 扫码登录和手动/定时打卡使用 Python daemon thread 执行耗时工作。
- Playwright 会话状态存储在 `sessions/*.json`，并通过文件锁保护。
- `scheduler.lock` 用于避免多个后端 worker 同时启动调度器。

这个模型适合单机或小规模部署。若未来扩展为多实例高可用，需要把调度器和异步执行迁移到外部队列，例如 Celery/RQ/Arq，并把会话状态放入共享存储。

## 迁移策略

项目没有使用 Alembic，而是使用内置迁移系统：

- 迁移定义在 `apps/backend/migrations.py` 的 `MIGRATIONS`。
- 每个迁移步骤位于 `apps/backend/migration_steps/`。
- 已执行迁移记录在数据库表 `schema_migrations`。
- 后端启动时自动执行 `run_pending_migrations()`。
- 也可以手动运行 `uv run python main.py backend-migrate`。

添加字段或回填数据时应新增 migration step，不应只依赖 `Base.metadata.create_all()`，因为后者不会修改已有表结构。

## 配置和运行数据

配置通过 `.env` 读取，核心配置在 `apps/backend/config.py`：

- `SECRET_KEY`：应用 JWT 签名密钥，生产必须替换。
- `DATABASE_URL`：默认 `sqlite:///data/checkin.db`。
- `CORS_ORIGINS`：允许访问 API 的前端源。
- `LOG_FILE`、`LOG_LEVEL`：日志路径和级别。
- `SESSION_DIR`：Playwright 扫码会话文件目录。
- `SMTP_*`：默认 SMTP 配置；运行时可被数据库中的邮件设置覆盖。
- `FRONTEND_URL`：邮件链接使用的前端地址。
- `TOKEN_CHECK_INTERVAL_MINUTES`、`SESSION_CLEANUP_INTERVAL_HOURS`：系统任务频率。
- `BROWSER_EXECUTABLE_PATH`：可指定 Playwright/Chromium 路径。

运行数据：

- `data/checkin.db`：SQLite 数据库。
- `logs/backend.log`、`logs/frontend.log`：本地进程日志。
- `sessions/`：二维码登录会话状态和锁文件。
- `backend.pid`、`frontend.pid`：本地 daemon 模式进程号。
- `scheduler.lock`：调度器单实例锁。

## 部署形态

### 本地开发

- 后端：`uv run python main.py backend`
- 迁移：`uv run python main.py backend-migrate`
- 前端：`cd apps/frontend && pnpm dev`
- 前端构建：`python main.py frontend-build`

默认端口：

- 后端 API：`http://localhost:8000`
- 前端 Vite：`http://localhost:3000`

### Docker Compose

生产推荐使用 `compose.yaml`：

- `backend` 镜像运行 FastAPI、迁移、调度器和 Playwright 相关能力。
- `web` 镜像构建并托管前端静态资源，通过 nginx 转发 `/api`、`/docs`、`/openapi.json` 和 `/health`。
- `checkin-data`、`checkin-logs`、`checkin-sessions` volume 保存运行数据。

部署配置样例位于：

- `deploy/compose.env.example`
- `deploy/docker/backend/Dockerfile`
- `deploy/docker/web/Dockerfile`
- `deploy/docker/web/nginx.conf`
- `deploy/nginx/checkin-app.conf.example`
- `deploy/systemd/checkin-app.service.example`

## 架构约束和测试护栏

项目已有若干测试用于约束架构边界：

- `tests/test_backend_structure_boundaries.py`：任务身份、重复冲突、调度同步、datetime 规范化和服务错误透传。
- `tests/test_frontend_architecture.py`：前端目录结构、用户/管理员路由、邮箱验证流程、扫码刷新对话框和 API 覆盖。
- `tests/test_backend_auto_migrations.py`、`tests/test_run_migrations_script.py`：迁移启动和脚本行为。
- 邮件相关测试覆盖通知设置、模板渲染和邮箱验证流程。
- 浏览器自动化测试覆盖关键 worker 行为。

新增功能时应保持以下边界：

- 新 HTTP 行为先放入对应 `api/*` 路由，再委托给 `services/*`。
- 任务归属和管理员权限必须在路由或依赖层显式校验。
- 后台线程必须创建自己的数据库 session。
- 任务调度状态变化必须调用 scheduler 同步入口。
- 新数据库列必须有 migration step 和测试。
- 前端新增 API 调用必须经过 `api/index.ts` 和 `api/client.ts`，不要在视图里散落裸 `fetch`。
- 前端新增页面必须加入 `app/router.ts` 并考虑登录、审批和管理员守卫。

## 可扩展方向

当前实现优先简单可靠的单机部署。未来可扩展点：

- 数据库从 SQLite 切换到 PostgreSQL/MySQL。
- 后台线程和 APScheduler 迁移到外部任务队列。
- Playwright 会话状态迁移到 Redis 或对象存储。
- 前端静态资源独立部署到 CDN，API 通过 `VITE_API_BASE_URL` 指向后端。
- 邮件发送抽象为可插拔 provider，支持队列重试和审计日志。
