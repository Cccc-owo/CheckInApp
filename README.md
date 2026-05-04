# CheckIn App V2

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3.5+-brightgreen.svg)](https://vuejs.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)

接龙自动打卡系统，通过 QQ 登录实现每日自动考勤提交。

## 特性

- QQ 扫码登录
- 用户任务分离（一人多任务）
- 任务模板系统
- 定时自动打卡
- 邮件通知
- 用户审批机制
- 管理后台

## 技术栈

**后端**: FastAPI + SQLAlchemy + APScheduler + Selenium  
**前端**: Vue 3 + TypeScript + shadcn-vue + Tailwind  
**数据库**: SQLite  

## 快速开始

### 环境要求

- Python 3.9+
- uv
- Node.js 20+
- pnpm
- Chrome 浏览器

### 安装运行

```bash
# 后端
uv sync
uv run python main.py backend

# 前端
cd apps/frontend
pnpm install
pnpm dev

# 创建管理员
uv run python apps/backend/scripts/create_admin.py
```

### 访问地址

- 前端: <http://localhost:3000>
- API 文档: <http://localhost:8000/docs>

## 进程管理

```bash
uv run python main.py backend-daemon
python main.py frontend-daemon
python main.py status
python main.py stop [all|backend|frontend]
python main.py frontend-build
```

## 配置

复制 `.env.example` 到 `.env`

nginx 与 systemd 的配置文件参考已给出，见 `.example`

## 文档

- [架构设计](docs/architecture.md)
- [部署指南](docs/deployment.md)
- [开发指南](docs/development.md)
