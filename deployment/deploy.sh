#!/bin/bash
# ==============================================================================
# CheckIn App V2 - Quick Deployment Script
# ==============================================================================
#
# This script automates the deployment process for CheckIn App V2
#
# Usage:
#   sudo ./deploy.sh [install|update|rollback]
#
# ==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="checkin-app"
APP_USER="checkin"
APP_DIR="/opt/checkin-app"
SERVICE_NAME="checkin-app.service"
NGINX_CONFIG="checkin-app"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_dependencies() {
    log_info "Checking dependencies..."

    local missing_deps=()

    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi

    # Check Node.js
    if ! command -v node &> /dev/null; then
        missing_deps+=("nodejs")
    fi

    # Check Nginx
    if ! command -v nginx &> /dev/null; then
        missing_deps+=("nginx")
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Please install them first:"
        log_info "  sudo apt install -y python3 python3-pip python3-venv nodejs nginx"
        exit 1
    fi

    log_info "All dependencies are installed"
}

create_user() {
    if id "$APP_USER" &>/dev/null; then
        log_info "User $APP_USER already exists"
    else
        log_info "Creating user $APP_USER..."
        useradd -r -m -s /bin/bash "$APP_USER"
        usermod -aG www-data "$APP_USER"
        log_info "User $APP_USER created"
    fi
}

create_directories() {
    log_info "Creating application directories..."

    mkdir -p "$APP_DIR"
    chown -R "$APP_USER:www-data" "$APP_DIR"

    sudo -u "$APP_USER" mkdir -p "$APP_DIR"/{data,logs,sessions}

    log_info "Directories created"
}

setup_backend() {
    log_info "Setting up backend..."

    cd "$APP_DIR"

    # Create virtual environment
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        sudo -u "$APP_USER" python3 -m venv venv
    fi

    # Install dependencies
    log_info "Installing Python dependencies..."
    sudo -u "$APP_USER" bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r backend/requirements.txt"

    # Create .env if not exists
    if [ ! -f ".env" ]; then
        log_warn ".env file not found, please create one from .env.example"
        if [ -f ".env.example" ]; then
            sudo -u "$APP_USER" cp .env.example .env
            log_info "Created .env from .env.example - please configure it"
        fi
    fi

    log_info "Backend setup complete"
}

build_frontend() {
    log_info "Building frontend..."

    cd "$APP_DIR/frontend"

    # Install dependencies
    if [ ! -d "node_modules" ]; then
        log_info "Installing Node.js dependencies..."
        sudo -u "$APP_USER" npm install
    fi

    # Build
    log_info "Building frontend for production..."
    sudo -u "$APP_USER" npm run build

    if [ -d "dist" ]; then
        log_info "Frontend built successfully"
    else
        log_error "Frontend build failed - dist directory not found"
        exit 1
    fi
}

setup_systemd() {
    log_info "Setting up systemd service..."

    if [ -f "$APP_DIR/deployment/checkin-app.service.example" ]; then
        # Copy service file
        cp "$APP_DIR/deployment/checkin-app.service.example" "/etc/systemd/system/$SERVICE_NAME"

        # Reload systemd
        systemctl daemon-reload

        # Enable service
        systemctl enable "$SERVICE_NAME"

        log_info "Systemd service configured"
    else
        log_error "Service file not found: $APP_DIR/deployment/checkin-app.service.example"
        exit 1
    fi
}

setup_nginx() {
    log_info "Setting up Nginx configuration..."

    if [ -f "$APP_DIR/deployment/nginx.conf.example" ]; then
        # Copy Nginx config
        cp "$APP_DIR/deployment/nginx.conf.example" "/etc/nginx/sites-available/$NGINX_CONFIG"

        # Create symlink
        if [ ! -L "/etc/nginx/sites-enabled/$NGINX_CONFIG" ]; then
            ln -s "/etc/nginx/sites-available/$NGINX_CONFIG" "/etc/nginx/sites-enabled/$NGINX_CONFIG"
        fi

        # Test Nginx config
        if nginx -t; then
            log_info "Nginx configuration is valid"
        else
            log_error "Nginx configuration test failed"
            exit 1
        fi

        log_warn "Please edit /etc/nginx/sites-available/$NGINX_CONFIG and configure your domain"
    else
        log_error "Nginx config file not found: $APP_DIR/deployment/nginx.conf.example"
        exit 1
    fi
}

start_services() {
    log_info "Starting services..."

    # Start application
    systemctl start "$SERVICE_NAME"

    # Reload Nginx
    systemctl reload nginx

    # Check status
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_info "Application service started successfully"
    else
        log_error "Application service failed to start"
        systemctl status "$SERVICE_NAME"
        exit 1
    fi

    log_info "All services started"
}

install() {
    log_info "Starting installation..."

    check_root
    check_dependencies
    create_user
    create_directories
    setup_backend
    build_frontend
    setup_systemd
    setup_nginx

    # Set permissions
    chown -R "$APP_USER:www-data" "$APP_DIR"
    chmod -R 755 "$APP_DIR"
    chmod -R 775 "$APP_DIR"/{data,logs,sessions}

    start_services

    echo ""
    log_info "================================================"
    log_info "Installation complete!"
    log_info "================================================"
    echo ""
    log_info "Next steps:"
    log_info "1. Configure .env file: sudo nano $APP_DIR/.env"
    log_info "2. Configure Nginx: sudo nano /etc/nginx/sites-available/$NGINX_CONFIG"
    log_info "3. Set up SSL certificate: sudo certbot --nginx -d your-domain.com"
    log_info "4. Restart services: sudo systemctl restart $SERVICE_NAME nginx"
    echo ""
    log_info "Useful commands:"
    log_info "  Status:  sudo systemctl status $SERVICE_NAME"
    log_info "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
    log_info "  Restart: sudo systemctl restart $SERVICE_NAME"
    echo ""
}

update() {
    log_info "Updating application..."

    check_root

    cd "$APP_DIR"

    # Backup database
    if [ -f "data/checkin.db" ]; then
        log_info "Backing up database..."
        sudo -u "$APP_USER" cp data/checkin.db "data/checkin.db.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    # Pull latest changes (if using git)
    if [ -d ".git" ]; then
        log_info "Pulling latest changes..."
        sudo -u "$APP_USER" git pull
    fi

    # Update backend
    log_info "Updating backend dependencies..."
    sudo -u "$APP_USER" bash -c "source venv/bin/activate && pip install -r backend/requirements.txt"

    # Rebuild frontend
    build_frontend

    # Restart service
    log_info "Restarting service..."
    systemctl restart "$SERVICE_NAME"

    # Check status
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_info "Update completed successfully"
    else
        log_error "Service failed to start after update"
        systemctl status "$SERVICE_NAME"
        exit 1
    fi
}

rollback() {
    log_info "Rolling back to previous version..."

    check_root

    cd "$APP_DIR"

    # Find latest backup
    LATEST_BACKUP=$(ls -t data/checkin.db.backup.* 2>/dev/null | head -n 1)

    if [ -z "$LATEST_BACKUP" ]; then
        log_error "No database backup found"
        exit 1
    fi

    log_info "Found backup: $LATEST_BACKUP"

    # Stop service
    systemctl stop "$SERVICE_NAME"

    # Restore database
    log_info "Restoring database..."
    sudo -u "$APP_USER" cp "$LATEST_BACKUP" data/checkin.db

    # Rollback git (if using git)
    if [ -d ".git" ]; then
        log_warn "Please manually rollback git to the desired commit"
        log_info "Example: git reset --hard <commit-hash>"
    fi

    # Start service
    systemctl start "$SERVICE_NAME"

    log_info "Rollback completed"
}

# Main
case "${1:-}" in
    install)
        install
        ;;
    update)
        update
        ;;
    rollback)
        rollback
        ;;
    *)
        echo "CheckIn App V2 - Deployment Script"
        echo ""
        echo "Usage: $0 {install|update|rollback}"
        echo ""
        echo "Commands:"
        echo "  install  - Full installation (first time)"
        echo "  update   - Update existing installation"
        echo "  rollback - Rollback to previous version"
        echo ""
        exit 1
        ;;
esac

exit 0
