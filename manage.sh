#!/bin/bash
# ==============================================================================
# CheckIn App V2 - Unified Process Manager (Linux/Mac)
# Usage: ./manage.sh {start|stop|restart|status|log} [backend|frontend|all]
# ==============================================================================

set -e

# Get script directory
APP_DIR=$(cd "$(dirname "$0")" && pwd)

# Configuration
VENV_DIR="$APP_DIR/venv"
BACKEND_PID_FILE="$APP_DIR/backend.pid"
FRONTEND_PID_FILE="$APP_DIR/frontend.pid"
BACKEND_LOG_FILE="$APP_DIR/logs/backend.log"
FRONTEND_LOG_FILE="$APP_DIR/logs/frontend.log"
PYTHON_EXE="$VENV_DIR/bin/python"

# Parse command and target
COMMAND=$1
TARGET=${2:-all}

# Color codes for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# ============================================
# START COMMAND
# ============================================
start_command() {
    case $TARGET in
        backend)
            echo "========================================"
            echo "CheckIn App V2 - Starting Backend"
            echo "========================================"
            echo ""
            start_backend
            ;;
        frontend)
            echo "========================================"
            echo "CheckIn App V2 - Starting Frontend"
            echo "========================================"
            echo ""
            start_frontend
            ;;
        all)
            echo "========================================"
            echo "CheckIn App V2 - Starting All Services"
            echo "========================================"
            echo ""
            start_backend
            echo ""
            start_frontend
            echo ""
            echo "========================================"
            echo "All Services Started!"
            echo "========================================"
            echo ""
            echo "Backend API:  http://localhost:8000"
            echo "API Docs:     http://localhost:8000/docs"
            echo "Frontend App: http://localhost:3000"
            echo ""
            ;;
        *)
            log_error "Invalid target: $TARGET"
            usage
            ;;
    esac
}

# Backend start logic
start_backend() {
    # Check if already running
    if [ -f "$BACKEND_PID_FILE" ]; then
        PID=$(cat "$BACKEND_PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            log_warn "Backend is already running (PID: $PID)"
            return 0
        else
            log_info "Backend PID file exists but process not running, cleaning up..."
            rm -f "$BACKEND_PID_FILE"
        fi
    fi

    # Check virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtual environment does not exist: $VENV_DIR"
        log_info "Please run first: python3 -m venv venv"
        exit 1
    fi

    # Check required directories
    mkdir -p data logs sessions

    log_info "Starting backend service in background..."

    # Start backend using run_daemon.py
    nohup "$PYTHON_EXE" "$APP_DIR/run_daemon.py" > "$BACKEND_LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$BACKEND_PID_FILE"

    log_info "Waiting for backend to start..."
    sleep 3

    # Check if port 8000 is listening
    SERVICE_RUNNING=0
    for i in {1..10}; do
        if lsof -i :8000 > /dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q :8000; then
            SERVICE_RUNNING=1
            break
        fi
        sleep 1
    done

    if [ $SERVICE_RUNNING -eq 1 ]; then
        # Get actual PID from port 8000
        ACTUAL_PID=$(lsof -ti :8000 2>/dev/null | head -n 1)
        if [ -n "$ACTUAL_PID" ]; then
            echo $ACTUAL_PID > "$BACKEND_PID_FILE"
            log_ok "Backend started successfully (PID: $ACTUAL_PID)"
            echo "     API Docs: http://localhost:8000/docs"
            echo "     Log: $BACKEND_LOG_FILE"
        else
            log_ok "Backend started successfully (PID: $PID)"
            echo "     API Docs: http://localhost:8000/docs"
            echo "     Log: $BACKEND_LOG_FILE"
        fi
    else
        log_error "Backend failed to start - port 8000 not listening"
        log_info "Check log: $BACKEND_LOG_FILE"
        echo ""
        echo "[DEBUG] Last 10 lines of log:"
        if [ -f "$BACKEND_LOG_FILE" ]; then
            tail -n 10 "$BACKEND_LOG_FILE"
        else
            echo "Log file not found"
        fi
        rm -f "$BACKEND_PID_FILE"
        exit 1
    fi
}

# Frontend start logic
start_frontend() {
    # Check if already running
    if [ -f "$FRONTEND_PID_FILE" ]; then
        PID=$(cat "$FRONTEND_PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            log_warn "Frontend is already running (PID: $PID)"
            return 0
        else
            log_info "Frontend PID file exists but process not running, cleaning up..."
            rm -f "$FRONTEND_PID_FILE"
        fi
    fi

    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js not found"
        log_info "Please install Node.js from https://nodejs.org/"
        exit 1
    fi

    # Check frontend directory
    if [ ! -d "frontend" ]; then
        log_error "Frontend directory not found"
        exit 1
    fi

    # Check node_modules
    if [ ! -d "frontend/node_modules" ]; then
        log_info "Installing frontend dependencies..."
        cd frontend
        npm install
        cd ..
    fi

    log_info "Starting frontend service in background..."

    # Start frontend in background
    cd frontend
    nohup npm run dev > "$FRONTEND_LOG_FILE" 2>&1 &
    PID=$!
    cd ..
    echo $PID > "$FRONTEND_PID_FILE"

    log_info "Waiting for frontend to start..."
    sleep 3

    # Check if port 3000 is listening
    SERVICE_RUNNING=0
    for i in {1..10}; do
        if lsof -i :3000 > /dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q :3000; then
            SERVICE_RUNNING=1
            break
        fi
        sleep 1
    done

    if [ $SERVICE_RUNNING -eq 1 ]; then
        # Get actual PID from port 3000
        ACTUAL_PID=$(lsof -ti :3000 2>/dev/null | head -n 1)
        if [ -n "$ACTUAL_PID" ]; then
            echo $ACTUAL_PID > "$FRONTEND_PID_FILE"
            log_ok "Frontend started successfully (PID: $ACTUAL_PID)"
            echo "     URL: http://localhost:3000"
            echo "     Log: $FRONTEND_LOG_FILE"
        else
            log_ok "Frontend started successfully (PID: $PID)"
            echo "     URL: http://localhost:3000"
            echo "     Log: $FRONTEND_LOG_FILE"
        fi
    else
        log_error "Frontend failed to start - port 3000 not listening"
        log_info "Check log: $FRONTEND_LOG_FILE"
        echo ""
        echo "[DEBUG] Last 10 lines of log:"
        if [ -f "$FRONTEND_LOG_FILE" ]; then
            tail -n 10 "$FRONTEND_LOG_FILE"
        else
            echo "Log file not found"
        fi
        rm -f "$FRONTEND_PID_FILE"
        exit 1
    fi
}

# ============================================
# STOP COMMAND
# ============================================
stop_command() {
    case $TARGET in
        backend)
            stop_backend
            ;;
        frontend)
            stop_frontend
            ;;
        all)
            echo "========================================"
            echo "CheckIn App V2 - Stopping All Services"
            echo "========================================"
            echo ""
            stop_backend
            echo ""
            stop_frontend
            ;;
        *)
            log_error "Invalid target: $TARGET"
            usage
            ;;
    esac
}

# Backend stop logic
stop_backend() {
    log_info "Stopping backend..."

    # First try to kill by port
    BACKEND_KILLED=0
    PIDS=$(lsof -ti :8000 2>/dev/null)
    if [ -n "$PIDS" ]; then
        for pid in $PIDS; do
            kill -TERM $pid 2>/dev/null || kill -9 $pid 2>/dev/null
            if [ $? -eq 0 ]; then
                log_ok "Backend stopped (PID: $pid)"
                BACKEND_KILLED=1
            fi
        done
    fi

    # Then try PID file if port method didn't work
    if [ $BACKEND_KILLED -eq 0 ]; then
        if [ -f "$BACKEND_PID_FILE" ]; then
            PID=$(cat "$BACKEND_PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                kill -TERM $PID 2>/dev/null || kill -9 $PID 2>/dev/null
                if [ $? -eq 0 ]; then
                    log_ok "Backend stopped (PID: $PID)"
                fi
            else
                log_warn "Backend not running (process does not exist)"
            fi
        else
            log_warn "Backend not running (no process found)"
        fi
    fi

    # Clean up PID file
    rm -f "$BACKEND_PID_FILE"
}

# Frontend stop logic
stop_frontend() {
    log_info "Stopping frontend..."

    # First try to kill by port
    FRONTEND_KILLED=0

    # Check port 3000
    PIDS=$(lsof -ti :3000 2>/dev/null)
    if [ -n "$PIDS" ]; then
        for pid in $PIDS; do
            kill -TERM $pid 2>/dev/null || kill -9 $pid 2>/dev/null
            if [ $? -eq 0 ]; then
                log_ok "Frontend stopped (PID: $pid)"
                FRONTEND_KILLED=1
            fi
        done
    fi

    # Also check ports 3001-3010 (Vite fallback ports)
    if [ $FRONTEND_KILLED -eq 0 ]; then
        for port in {3001..3010}; do
            PIDS=$(lsof -ti :$port 2>/dev/null)
            if [ -n "$PIDS" ]; then
                for pid in $PIDS; do
                    # Check if it's a node process
                    if ps -p $pid -o comm= | grep -q node; then
                        kill -TERM $pid 2>/dev/null || kill -9 $pid 2>/dev/null
                        if [ $? -eq 0 ]; then
                            log_ok "Frontend stopped (PID: $pid, Port: $port)"
                            FRONTEND_KILLED=1
                        fi
                    fi
                done
            fi
        done
    fi

    # Then try PID file if port method didn't work
    if [ $FRONTEND_KILLED -eq 0 ]; then
        if [ -f "$FRONTEND_PID_FILE" ]; then
            PID=$(cat "$FRONTEND_PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                kill -TERM $PID 2>/dev/null || kill -9 $PID 2>/dev/null
                if [ $? -eq 0 ]; then
                    log_ok "Frontend stopped (PID: $PID)"
                fi
            else
                log_warn "Frontend not running (process does not exist)"
            fi
        else
            log_warn "Frontend not running (no process found)"
        fi
    fi

    # Clean up PID file
    rm -f "$FRONTEND_PID_FILE"
}

# ============================================
# RESTART COMMAND
# ============================================
restart_command() {
    log_info "Restarting $TARGET..."
    echo ""
    stop_command
    sleep 2
    start_command
}

# ============================================
# STATUS COMMAND
# ============================================
status_command() {
    echo "========================================"
    echo "CheckIn App V2 - Service Status"
    echo "========================================"
    echo ""

    case $TARGET in
        backend)
            status_backend
            ;;
        frontend)
            status_frontend
            ;;
        all)
            status_backend
            echo ""
            status_frontend
            ;;
        *)
            log_error "Invalid target: $TARGET"
            usage
            ;;
    esac
}

# Backend status
status_backend() {
    echo "[Backend Service]"

    if [ ! -f "$BACKEND_PID_FILE" ]; then
        echo "  Status: NOT RUNNING"
        return 0
    fi

    PID=$(cat "$BACKEND_PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "  Status: RUNNING"
        echo "  PID: $PID"
        echo "  URL: http://localhost:8000/docs"
        echo "  Log: $BACKEND_LOG_FILE"
        echo "  Port: $(lsof -i :8000 2>/dev/null | grep LISTEN || echo 'N/A')"
    else
        echo "  Status: NOT RUNNING"
        rm -f "$BACKEND_PID_FILE"
    fi
}

# Frontend status
status_frontend() {
    echo "[Frontend Service]"

    if [ ! -f "$FRONTEND_PID_FILE" ]; then
        echo "  Status: NOT RUNNING"
        return 0
    fi

    PID=$(cat "$FRONTEND_PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "  Status: RUNNING"
        echo "  PID: $PID"
        echo "  URL: http://localhost:3000"
        echo "  Log: $FRONTEND_LOG_FILE"
        echo "  Port: $(lsof -i :3000 2>/dev/null | grep LISTEN || echo 'N/A')"
    else
        echo "  Status: NOT RUNNING"
        rm -f "$FRONTEND_PID_FILE"
    fi
}

# ============================================
# BUILD COMMAND
# ============================================
build_command() {
    echo "========================================"
    echo "CheckIn App V2 - Building Frontend"
    echo "========================================"
    echo ""

    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js not found"
        log_info "Please install Node.js from https://nodejs.org/"
        exit 1
    fi

    # Check frontend directory
    if [ ! -d "frontend" ]; then
        log_error "Frontend directory not found"
        exit 1
    fi

    # Check node_modules
    if [ ! -d "frontend/node_modules" ]; then
        log_info "Installing frontend dependencies first..."
        cd frontend
        npm install
        if [ $? -ne 0 ]; then
            log_error "Failed to install dependencies"
            exit 1
        fi
        cd ..
        echo ""
    fi

    log_info "Building frontend for production..."
    echo ""

    # Build frontend
    cd frontend
    npm run build
    BUILD_EXIT_CODE=$?
    cd ..

    if [ $BUILD_EXIT_CODE -eq 0 ]; then
        echo ""
        log_ok "Frontend built successfully!"

        # Check if dist directory exists
        if [ -d "frontend/dist" ]; then
            DIST_SIZE=$(du -sh frontend/dist | cut -f1)
            echo ""
            echo "Build output:"
            echo "  Location: $APP_DIR/frontend/dist"
            echo "  Size: $DIST_SIZE"
            echo ""
            echo "File structure:"
            ls -lh frontend/dist/
            echo ""
            log_info "You can now deploy the 'frontend/dist' directory to your web server"
        else
            log_warn "Build succeeded but dist directory not found"
        fi
    else
        echo ""
        log_error "Frontend build failed"
        log_info "Check the output above for error details"
        exit 1
    fi
}

# ============================================
# LOG COMMAND
# ============================================
log_command() {
    case $TARGET in
        backend)
            echo "========================================"
            echo "Backend Real-time Logs (Press Ctrl+C to exit)"
            echo "========================================"
            echo ""

            if [ ! -f "$BACKEND_LOG_FILE" ]; then
                log_error "Log file does not exist: $BACKEND_LOG_FILE"
                exit 1
            fi

            tail -f "$BACKEND_LOG_FILE"
            ;;
        frontend)
            echo "========================================"
            echo "Frontend Real-time Logs (Press Ctrl+C to exit)"
            echo "========================================"
            echo ""

            if [ ! -f "$FRONTEND_LOG_FILE" ]; then
                log_error "Log file does not exist: $FRONTEND_LOG_FILE"
                exit 1
            fi

            tail -f "$FRONTEND_LOG_FILE"
            ;;
        all)
            log_error "Cannot tail multiple logs simultaneously"
            log_info "Use: ./manage.sh log backend OR ./manage.sh log frontend"
            usage
            ;;
        *)
            log_error "Invalid target: $TARGET"
            usage
            ;;
    esac
}

# ============================================
# USAGE
# ============================================
usage() {
    echo "CheckIn App V2 - Unified Process Manager"
    echo ""
    echo "Usage: $0 COMMAND [TARGET]"
    echo ""
    echo "Commands:"
    echo "  start [TARGET]   - Start service(s)"
    echo "  stop [TARGET]    - Stop service(s)"
    echo "  restart [TARGET] - Restart service(s)"
    echo "  status [TARGET]  - View service(s) status"
    echo "  log TARGET       - View real-time logs (backend or frontend only)"
    echo "  build            - Build frontend for production"
    echo ""
    echo "Targets:"
    echo "  backend  - Backend API service (default port: 8000)"
    echo "  frontend - Frontend dev server (default port: 3000)"
    echo "  all      - Both services (default)"
    echo ""
    echo "Examples:"
    echo "  $0 start              # Start both services"
    echo "  $0 start backend      # Start backend only"
    echo "  $0 stop all           # Stop all services"
    echo "  $0 status             # View all services status"
    echo "  $0 log backend        # View backend logs"
    echo "  $0 build              # Build frontend static files"
    echo "  $0 restart frontend   # Restart frontend"
    exit 1
}

# ============================================
# MAIN
# ============================================
if [ -z "$COMMAND" ]; then
    usage
fi

case $COMMAND in
    start)
        start_command
        ;;
    stop)
        stop_command
        ;;
    restart)
        restart_command
        ;;
    status)
        status_command
        ;;
    log)
        log_command
        ;;
    build)
        build_command
        ;;
    *)
        usage
        ;;
esac

exit 0
