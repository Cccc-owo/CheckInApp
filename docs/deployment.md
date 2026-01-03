# 部署指南

## 环境准备

### 系统要求

- Ubuntu 20.04+ / CentOS 7+ / Windows Server
- Python 3.9+
- Node.js 16+
- Chrome / Chromium
- 2GB+ RAM

### 依赖安装

```bash
# Ubuntu
sudo apt update
sudo apt install -y python3 nodejs npm chromium-browser

# CentOS
sudo yum install -y python3 nodejs npm chromium
```

## 生产部署

### 方式一：传统部署

#### 1. 后端部署

```bash
# 克隆项目
git clone <repository>
cd CheckInApp

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt

# 生产环境额外依赖
pip install gunicorn

# 配置环境变量
cp .env.example .env
vim .env  # 修改环境变量
```

#### 2. 前端部署

```bash
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 输出在 dist/ 目录
```

**使用 Nginx 托管**:

[示例文件](../nginx.conf.example)

#### 3. 使用 Systemd 管理

[示例文件](../checkin-app.service.example)

### 方式二：Docker 部署（推荐）

TODO(Maybe never)

## 配置优化

### 生产环境变量

[示例文件](../.env.example)

### 数据库迁移到 PostgreSQL

```bash
# 安装 PostgreSQL
sudo apt install postgresql postgresql-contrib

# 创建数据库
sudo -u postgres createdb checkin
sudo -u postgres createuser checkin_user
sudo -u postgres psql -c "ALTER USER checkin_user WITH PASSWORD 'password';"

# 修改 .env
DATABASE_URL=postgresql://checkin_user:password@localhost/checkin
```

## 安全加固

### 1. 防火墙配置

```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 2. SSL 证书（Let's Encrypt）

```bash
sudo apt install certbot python3-certbot-nginx

sudo certbot --nginx -d your-domain.com

# 自动续期
sudo systemctl enable certbot.timer
```

### 3. 限制访问

- 修改 `.env` 中的 `CORS_ORIGINS` 为实际域名
- 在 Nginx 中配置 rate limiting
- 使用 fail2ban 防止暴力破解

## 监控维护

### 日志管理

```bash
# 查看后端日志
tail -f logs/backend.log
```

### 数据库备份

```bash
# SQLite 备份
cp data/checkin.db data/checkin.db.backup

# PostgreSQL 备份
pg_dump checkin > backup.sql

# 定时备份（crontab）
0 2 * * * /path/to/backup.sh
```

### 性能监控

使用工具：

- Prometheus + Grafana
- New Relic
- Sentry（错误追踪）

## 扩展部署

### 负载均衡

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

```python
# 安装 redis
pip install redis

# 配置会话存储
REDIS_URL=redis://localhost:6379/0
```

## 故障排查

### 端口占用

```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

### Selenium 问题

```bash
# 检查 Chrome 版本
chromium --version
chromedriver --version

# 确保版本匹配
```

### 权限问题

```bash
# 确保目录权限正确
sudo chown -R www-data:www-data /path/to/CheckInApp
sudo chmod -R 755 /path/to/CheckInApp
```

## 回滚策略

```bash
# 保存当前版本
git tag -a v2.0.0 -m "Production release"

# 回滚到上一版本
git checkout v1.9.0
docker-compose down
docker-compose up -d --build
```
