# 部署指南

## 推荐方式：Docker Compose

Docker Compose 是当前推荐的生产部署方式。主机只需要 Docker Engine 和 Docker Compose，Python、Node.js、pnpm、Playwright Chromium 都由镜像构建和容器运行时负责。

### 系统要求

- Linux 服务器，建议 Ubuntu 20.04+ / Debian 11+ / CentOS 7+
- Docker Engine 24+
- Docker Compose v2
- 2GB+ RAM
- 可访问外网以构建镜像和下载依赖

### 首次部署

```bash
git clone <repository>
cd CheckInApp

cp deploy/compose.env.example .env
```

编辑 `.env`，至少修改：

- `SECRET_KEY`: 改成足够长的随机字符串。
- `CORS_ORIGINS`: 改成浏览器实际访问的站点，例如 `https://checkin.example.com`。
- `FRONTEND_URL`: 改成同一个公开站点，用于邮件里的链接。
- `CHECKIN_WEB_PORT`: 默认 `3090`，按服务器端口规划调整。
- SMTP 配置：需要邮件通知时填写真实 SMTP 参数。

启动：

```bash
docker compose up -d --build
```

默认访问：

- Web UI: `http://localhost:3090`
- API 健康检查: `http://localhost:3090/health`
- API 文档: `http://localhost:3090/docs`

### 运行结构

Compose 启动两个服务：

- `backend`: FastAPI、APScheduler、SQLAlchemy、Playwright Chromium。
- `web`: nginx，负责前端静态资源、SPA fallback，以及代理 `/api`、`/docs`、`/redoc`、`/openapi.json`、`/health` 到 backend。

持久化目录：

- `./data:/app/data`: SQLite 数据库，默认 `data/checkin.db`。
- `./sessions:/app/sessions`: Playwright 登录会话状态。
- `./logs:/app/logs`: 后端日志文件。

容器重建或镜像更新不会删除这些目录。

### 创建管理员

先让目标用户完成一次 QQ 扫码注册，然后在容器内运行管理员脚本：

```bash
docker compose exec backend uv run python apps/backend/scripts/create_admin.py
```

脚本会提示输入要升级的用户别名。

### 常用运维命令

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f backend
docker compose logs -f web

# 重启
docker compose restart

# 停止
docker compose down
```

### 更新

```bash
git pull
docker compose up -d --build
```

后端启动时会自动执行待迁移数据库脚本，并在迁移完成后才启动调度器。如果迁移失败，backend 服务会启动失败并在日志中标出失败的迁移 ID。

需要手动执行迁移时：

```bash
docker compose exec backend uv run python main.py backend-migrate
```

不要使用 `docker compose down -v`，否则会删除 Compose 管理的卷。当前默认使用项目目录 bind mount，仍应避免误删 `data/`、`sessions/`、`logs/`。

### 备份与恢复

备份 SQLite 和运行时状态：

```bash
mkdir -p backups
tar -czf backups/checkin-$(date +%Y%m%d-%H%M%S).tar.gz data sessions logs .env
```

恢复：

```bash
docker compose down
tar -xzf backups/<backup-file>.tar.gz
docker compose up -d
```

### 回滚

```bash
git checkout <previous-tag-or-commit>
docker compose up -d --build
```

回滚时复用同一份 `.env`、`data/`、`sessions/`、`logs/`。回滚到旧版本前，先确认当前版本已经执行的数据库迁移是否可被旧版本兼容读取。

### Compose 故障排查

端口占用：

```bash
sudo lsof -i :3090
```

修改 `.env` 中的 `CHECKIN_WEB_PORT` 后重新启动：

```bash
docker compose up -d
```

后端健康检查失败：

```bash
docker compose logs backend
docker compose exec backend uv run python main.py backend --check
```

Playwright 问题：

- Compose 部署不需要在主机安装 Chrome/Chromium。
- 如果 QQ 登录或 payload 捕获失败，先查看 `docker compose logs backend` 和 `logs/backend.log`。
- 重新构建镜像可刷新 Playwright 浏览器依赖：`docker compose build --no-cache backend`。

权限问题：

```bash
mkdir -p data sessions logs
chmod -R u+rwX data sessions logs
docker compose restart backend
```

## 备选方式：传统部署

传统部署适合已经有主机级 Python、Node.js、pnpm、Chromium、nginx 和 systemd 管理经验的环境。

### 系统要求

- Ubuntu 20.04+ / CentOS 7+ / Windows Server
- Python 3.12+
- uv
- Node.js 24+
- pnpm
- Chrome / Chromium
- 2GB+ RAM

### 依赖安装

```bash
# Ubuntu
sudo apt update
sudo apt install -y python3 nodejs npm chromium-browser
npm install -g pnpm
curl -LsSf https://astral.sh/uv/install.sh | sh

# CentOS
sudo yum install -y python3 nodejs npm chromium
npm install -g pnpm
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 后端部署

```bash
git clone <repository>
cd CheckInApp

uv sync
uv sync --extra production

cp .env.example .env
vim .env

uv run playwright install chromium
uv run python main.py backend --no-reload
```

### 前端部署

```bash
cd apps/frontend
pnpm install --frozen-lockfile
pnpm build
```

生产静态资源输出在 `apps/frontend/dist/`。

nginx 示例文件：[deploy/nginx/checkin-app.conf.example](../deploy/nginx/checkin-app.conf.example)

systemd 示例文件：[deploy/systemd/checkin-app.service.example](../deploy/systemd/checkin-app.service.example)

## 配置优化

### 生产环境变量

Compose 部署参考：[deploy/compose.env.example](../deploy/compose.env.example)

传统部署参考：[.env.example](../.env.example)

### 数据库迁移到 PostgreSQL

当前 Compose baseline 使用 SQLite 单后端部署。需要 PostgreSQL 时，先按传统方式准备数据库并修改 `DATABASE_URL`：

```bash
sudo apt install postgresql postgresql-contrib

sudo -u postgres createdb checkin
sudo -u postgres createuser checkin_user
sudo -u postgres psql -c "ALTER USER checkin_user WITH PASSWORD 'password';"

DATABASE_URL=postgresql://checkin_user:password@localhost/checkin
```

## 安全加固

### 防火墙配置

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

如果直接暴露 Compose web 端口，也需要允许 `CHECKIN_WEB_PORT` 对应端口。

### HTTPS

推荐在 Compose web 服务前放置外部反向代理或云厂商负载均衡来终止 TLS。传统 nginx 部署可以使用 Let's Encrypt：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
sudo systemctl enable certbot.timer
```

### 访问限制

- 生产环境必须修改默认 `SECRET_KEY`。
- 将 `CORS_ORIGINS` 和 `FRONTEND_URL` 设置为实际公开域名。
- 在外部反向代理中配置 rate limiting。
- 使用 fail2ban 防止暴力破解。

## 监控维护

### 日志

Compose：

```bash
docker compose logs -f backend
tail -f logs/backend.log
```

传统部署：

```bash
tail -f logs/backend.log
```

### 数据库备份

SQLite：

```bash
cp data/checkin.db data/checkin.db.backup
```

PostgreSQL：

```bash
pg_dump checkin > backup.sql
```

## 扩展部署

### 负载均衡

当前应用包含内置调度器，默认 Compose baseline 只运行一个 backend 服务。多 backend 实例需要先设计调度器互斥或外部调度机制。

传统 nginx upstream 示例：

```nginx
upstream backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    location /api {
        proxy_pass http://backend;
    }
}
```

### Redis 缓存

```bash
uv sync --extra redis
```

```env
REDIS_URL=redis://localhost:6379/0
```
