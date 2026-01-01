# CheckIn App V2 - Deployment Guide

This guide explains how to deploy CheckIn App V2 to a production server using Nginx and systemd.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Application Setup](#application-setup)
4. [Nginx Configuration](#nginx-configuration)
5. [Systemd Service Setup](#systemd-service-setup)
6. [SSL/TLS Certificate](#ssltls-certificate)
7. [Monitoring and Logs](#monitoring-and-logs)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- **Operating System**: Ubuntu 20.04+ or similar Linux distribution
- **Python**: 3.9 or higher
- **Node.js**: 16+ (for building frontend)
- **Nginx**: 1.18 or higher
- **Domain name** (optional but recommended for SSL)

### Install Required Packages

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and tools
sudo apt install -y python3 python3-pip python3-venv

# Install Node.js (using NodeSource)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Nginx
sudo apt install -y nginx

# Install other dependencies
sudo apt install -y git curl wget
```

---

## Server Setup

### 1. Create Application User

```bash
# Create a dedicated user for the application
sudo useradd -r -m -s /bin/bash checkin
sudo usermod -aG www-data checkin
```

### 2. Create Application Directory

```bash
# Create directory structure
sudo mkdir -p /opt/checkin-app
sudo chown -R checkin:www-data /opt/checkin-app

# Create required subdirectories
sudo -u checkin mkdir -p /opt/checkin-app/{data,logs,sessions}
```

---

## Application Setup

### 1. Clone Repository

```bash
# Switch to application user
sudo su - checkin

# Clone the repository
cd /opt/checkin-app
git clone https://github.com/your-repo/checkin-app.git .

# Or upload your files using scp/rsync
```

### 2. Setup Backend

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and configure your settings
nano .env
```

**Important Environment Variables:**

```env
# Database
DATABASE_URL=sqlite:///./data/checkin.db

# Security
SECRET_KEY=your-secret-key-here-change-this
ALLOWED_ORIGINS=https://your-domain.com

# QQ Login (if applicable)
QQ_APPID=your-qq-appid
QQ_APPSECRET=your-qq-appsecret

# Email notifications (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ADMIN_EMAIL=admin@your-domain.com
```

### 3. Initialize Database

```bash
# Run database migrations if needed
# Example:
# alembic upgrade head

# Or run initialization script
python backend/scripts/create_admin.py
```

### 4. Build Frontend

```bash
# Install frontend dependencies
cd frontend
npm install

# Build for production
npm run build

# Verify build output
ls -lh dist/
```

### 5. Set Permissions

```bash
# Exit from checkin user
exit

# Set proper permissions
sudo chown -R checkin:www-data /opt/checkin-app
sudo chmod -R 755 /opt/checkin-app
sudo chmod -R 775 /opt/checkin-app/{data,logs,sessions}
```

---

## Nginx Configuration

### 1. Copy Configuration

```bash
# Copy example configuration
sudo cp /opt/checkin-app/deployment/nginx.conf.example /etc/nginx/sites-available/checkin-app

# Edit configuration
sudo nano /etc/nginx/sites-available/checkin-app
```

### 2. Update Configuration

Replace the following placeholders:

- `your-domain.com` → Your actual domain name
- `/opt/checkin-app` → Your installation path (if different)

### 3. Enable Site

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/checkin-app /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## Systemd Service Setup

### 1. Copy Service File

```bash
# Copy example service file
sudo cp /opt/checkin-app/deployment/checkin-app.service.example /etc/systemd/system/checkin-app.service

# Edit service file
sudo nano /etc/systemd/system/checkin-app.service
```

### 2. Update Service File

Replace placeholders:

- `User=www-data` → `User=checkin` (if using dedicated user)
- `WorkingDirectory=/opt/checkin-app` → Your installation path
- Adjust paths in `ExecStart` if needed

### 3. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable checkin-app.service

# Start service
sudo systemctl start checkin-app.service

# Check status
sudo systemctl status checkin-app.service

# View logs
sudo journalctl -u checkin-app -f
```

---

## SSL/TLS Certificate

### Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Follow the prompts to configure SSL

# Test auto-renewal
sudo certbot renew --dry-run
```

The Certbot will automatically update your Nginx configuration with SSL settings.

### Manual Certificate Setup

If you have your own SSL certificate:

```bash
# Copy certificate files
sudo mkdir -p /etc/nginx/ssl
sudo cp your-cert.crt /etc/nginx/ssl/
sudo cp your-key.key /etc/nginx/ssl/

# Set permissions
sudo chmod 600 /etc/nginx/ssl/your-key.key

# Update Nginx configuration with certificate paths
```

---

## Monitoring and Logs

### Service Logs

```bash
# View service logs
sudo journalctl -u checkin-app -f

# View last 100 lines
sudo journalctl -u checkin-app -n 100

# View logs since yesterday
sudo journalctl -u checkin-app --since yesterday
```

### Application Logs

```bash
# Backend logs
tail -f /opt/checkin-app/logs/backend.log

# Nginx access logs
sudo tail -f /var/log/nginx/checkin-app-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/checkin-app-error.log
```

### Service Status

```bash
# Check service status
sudo systemctl status checkin-app

# Check if port is listening
sudo netstat -tlnp | grep :8000

# Check process
ps aux | grep python
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check service logs
sudo journalctl -u checkin-app -xe

# Check if port is already in use
sudo lsof -i :8000

# Verify permissions
ls -la /opt/checkin-app/

# Test manual start
sudo -u checkin /opt/checkin-app/venv/bin/python /opt/checkin-app/run_daemon.py
```

### Nginx Errors

```bash
# Test Nginx configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Verify backend is running
curl http://localhost:8000/health
```

### Database Issues

```bash
# Check database file permissions
ls -la /opt/checkin-app/data/

# Check if database is locked
fuser /opt/checkin-app/data/checkin.db

# Backup database
cp /opt/checkin-app/data/checkin.db /opt/checkin-app/data/checkin.db.backup
```

### Frontend Not Loading

```bash
# Verify build exists
ls -la /opt/checkin-app/frontend/dist/

# Check Nginx configuration for root path
grep -n "root" /etc/nginx/sites-available/checkin-app

# Clear browser cache or test with curl
curl -I https://your-domain.com/
```

---

## Updating the Application

### Update Backend

```bash
# Switch to application user
sudo su - checkin
cd /opt/checkin-app

# Pull latest changes
git pull

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -r backend/requirements.txt

# Run migrations if needed
# alembic upgrade head

# Exit and restart service
exit
sudo systemctl restart checkin-app
```

### Update Frontend

```bash
sudo su - checkin
cd /opt/checkin-app/frontend

# Pull latest changes
git pull

# Install dependencies
npm install

# Build
npm run build

# Exit
exit

# No need to restart - Nginx serves static files
```

---

## Security Recommendations

1. **Firewall**: Use `ufw` to restrict access
   ```bash
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw enable
   ```

2. **Regular Updates**: Keep system and packages updated
   ```bash
   sudo apt update && sudo apt upgrade
   ```

3. **Backup**: Regular backups of database and configuration
   ```bash
   # Create backup script
   sudo nano /opt/checkin-app/backup.sh
   ```

4. **Monitoring**: Consider using monitoring tools like Prometheus, Grafana, or Uptime Kuma

5. **Rate Limiting**: Configure Nginx rate limiting for API endpoints

---

## Additional Resources

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Systemd Documentation](https://www.freedesktop.org/software/systemd/man/)
- [Let's Encrypt](https://letsencrypt.org/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

## Support

For issues or questions, please:
- Check the logs first
- Review this guide carefully
- Open an issue on GitHub
- Contact system administrator
