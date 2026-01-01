# Deployment Files

This directory contains configuration files and scripts for deploying CheckIn App V2 to a production server.

## Files

- **`nginx.conf.example`** - Nginx reverse proxy configuration
- **`checkin-app.service.example`** - Systemd service file
- **`deploy.sh`** - Automated deployment script
- **`DEPLOYMENT.md`** - Comprehensive deployment guide

## Quick Start

### Option 1: Automated Deployment (Recommended)

```bash
# Make script executable
chmod +x deployment/deploy.sh

# Run installation
sudo deployment/deploy.sh install
```

### Option 2: Manual Deployment

Follow the step-by-step guide in [DEPLOYMENT.md](./DEPLOYMENT.md).

## Deployment Script Usage

The `deploy.sh` script provides three main commands:

### 1. Install (First-time deployment)

```bash
sudo deployment/deploy.sh install
```

This will:
- Check system dependencies
- Create application user
- Setup virtual environment
- Install Python dependencies
- Build frontend
- Configure systemd service
- Configure Nginx
- Start all services

### 2. Update (Update existing installation)

```bash
sudo deployment/deploy.sh update
```

This will:
- Backup database
- Pull latest changes (if using git)
- Update Python dependencies
- Rebuild frontend
- Restart services

### 3. Rollback (Revert to previous version)

```bash
sudo deployment/deploy.sh rollback
```

This will:
- Stop services
- Restore database from latest backup
- Restart services

## Configuration Files

### Nginx Configuration

Edit `/etc/nginx/sites-available/checkin-app` and update:

- `server_name` - Your domain name
- `ssl_certificate` and `ssl_certificate_key` - SSL certificate paths
- `root` - Frontend build directory path (usually `/opt/checkin-app/frontend/dist`)

### Systemd Service

Edit `/etc/systemd/system/checkin-app.service` and update:

- `User` and `Group` - Application user (default: `checkin`)
- `WorkingDirectory` - Application directory (default: `/opt/checkin-app`)
- `ExecStart` - Path to Python executable and run script

### Environment Variables

Create and configure `.env` file in the application root:

```bash
sudo nano /opt/checkin-app/.env
```

Required variables:
```env
# Database
DATABASE_URL=sqlite:///./data/checkin.db

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=https://your-domain.com

# QQ Login
QQ_APPID=your-appid
QQ_APPSECRET=your-appsecret
```

## SSL Certificate Setup

### Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

### Manual Certificate

If you have your own SSL certificate:

1. Copy certificate files to `/etc/nginx/ssl/`
2. Update Nginx configuration with correct paths
3. Reload Nginx: `sudo systemctl reload nginx`

## Service Management

### Start Service

```bash
sudo systemctl start checkin-app
```

### Stop Service

```bash
sudo systemctl stop checkin-app
```

### Restart Service

```bash
sudo systemctl restart checkin-app
```

### Check Status

```bash
sudo systemctl status checkin-app
```

### View Logs

```bash
# Application logs
sudo journalctl -u checkin-app -f

# Nginx access logs
sudo tail -f /var/log/nginx/checkin-app-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/checkin-app-error.log
```

## Directory Structure

After deployment, the application structure should look like:

```
/opt/checkin-app/
├── backend/              # Backend Python code
│   ├── api/
│   ├── models/
│   ├── services/
│   └── ...
├── frontend/             # Frontend source code
│   ├── src/
│   ├── dist/            # Built static files (served by Nginx)
│   └── ...
├── venv/                # Python virtual environment
├── data/                # SQLite database
├── logs/                # Application logs
├── sessions/            # Session data
├── deployment/          # Deployment files (this directory)
├── .env                 # Environment variables
└── run_daemon.py        # Application entry point
```

## Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u checkin-app -xe

# Verify configuration
sudo -u checkin /opt/checkin-app/venv/bin/python /opt/checkin-app/run_daemon.py
```

### Nginx configuration errors

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log
```

### Database locked

```bash
# Check what's using the database
sudo fuser /opt/checkin-app/data/checkin.db

# Kill the process if needed
sudo fuser -k /opt/checkin-app/data/checkin.db
```

### Permission issues

```bash
# Fix ownership
sudo chown -R checkin:www-data /opt/checkin-app

# Fix permissions
sudo chmod -R 755 /opt/checkin-app
sudo chmod -R 775 /opt/checkin-app/{data,logs,sessions}
```

## Security Best Practices

1. **Keep system updated**
   ```bash
   sudo apt update && sudo apt upgrade
   ```

2. **Use firewall**
   ```bash
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw enable
   ```

3. **Regular backups**
   ```bash
   # Backup database
   sudo -u checkin cp /opt/checkin-app/data/checkin.db /backup/checkin-$(date +%Y%m%d).db
   ```

4. **Monitor logs**
   ```bash
   # Setup log rotation
   sudo nano /etc/logrotate.d/checkin-app
   ```

5. **Use strong passwords** and **secure SECRET_KEY**

## Performance Tuning

### Nginx

- Enable gzip compression (already configured)
- Configure caching headers (already configured)
- Adjust worker processes based on CPU cores

### Backend

- Increase uvicorn workers in service file:
  ```
  ExecStart=/opt/checkin-app/venv/bin/uvicorn backend.main:app --workers 4
  ```

- Consider using Gunicorn with uvicorn workers for production

### Database

- For high traffic, consider switching to PostgreSQL
- Regular VACUUM for SQLite

## Monitoring

Consider setting up monitoring tools:

- **Uptime monitoring**: Uptime Kuma, UptimeRobot
- **Log aggregation**: Loki, ELK Stack
- **Metrics**: Prometheus + Grafana
- **Error tracking**: Sentry

## Support

For detailed deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md).

For issues or questions:
- Check application logs
- Review troubleshooting section
- Open an issue on GitHub
