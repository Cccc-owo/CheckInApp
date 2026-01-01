#!/bin/bash
# ==============================================================================
# CheckIn App V2 - Unified Service Manager (Linux/macOS)
# ==============================================================================
# Description: Manages backend and frontend services with unified interface
# Usage: ./manage.sh COMMAND [TARGET]
# Commands: start, stop, restart, status, log, build
# Targets: backend, frontend, all (default)
# ==============================================================================

set -eu
# Enable pipefail if supported (bash 3+)
if set -o | grep -q pipefail; then
    set -o pipefail
fi

# ==============================================================================
# Configuration
# ==============================================================================
readonly SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
readonly APP_DIR="${SCRIPT_DIR}"
readonly VENV_DIR="${APP_DIR}/venv"
readonly PYTHON_BIN="${VENV_DIR}/bin/python"

readonly BACKEND_PID="${APP_DIR}/backend.pid"
readonly FRONTEND_PID="${APP_DIR}/frontend.pid"
readonly BACKEND_LOG="${APP_DIR}/logs/backend.log"
readonly FRONTEND_LOG="${APP_DIR}/logs/frontend.log"

readonly BACKEND_PORT=8000
readonly FRONTEND_PORT=3000

# Colors
readonly C_RESET='\033[0m'
readonly C_RED='\033[0;31m'
readonly C_GREEN='\033[0;32m'
readonly C_YELLOW='\033[1;33m'
readonly C_BLUE='\033[0;34m'
readonly C_CYAN='\033[0;36m'

# ==============================================================================
# Utility Functions
# ==============================================================================
print_header() {
    local text="$1"
    printf "\n"
    printf "${C_CYAN}========================================${C_RESET}\n"
    printf "${C_CYAN}%s${C_RESET}\n" "$text"
    printf "${C_CYAN}========================================${C_RESET}\n"
}

log_info() {
    printf "${C_GREEN}[INFO]${C_RESET} %s\n" "$1"
}

log_success() {
    printf "${C_GREEN}[OK]${C_RESET} %s\n" "$1"
}

log_warn() {
    printf "${C_YELLOW}[WARNING]${C_RESET} %s\n" "$1"
}

log_error() {
    printf "${C_RED}[ERROR]${C_RESET} %s\n" "$1"
}

log_debug() {
    printf "${C_BLUE}[DEBUG]${C_RESET} %s\n" "$1"
}

# Check if a process is running by PID
is_process_alive() {
    local pid="$1"
    kill -0 "$pid" 2>/dev/null
}

# Get PID from PID file if exists
get_pid_from_file() {
    local pid_file="$1"
    if [ -f "$pid_file" ]; then
        cat "$pid_file"
    else
        echo ""
    fi
}

# Get PID listening on a port
get_pid_by_port() {
    local port="$1"
    local pid=""

    # Try lsof first
    if command -v lsof >/dev/null 2>&1; then
        pid=$(lsof -ti ":$port" 2>/dev/null | head -n1)
        if [ -n "$pid" ]; then
            echo "$pid"
            return 0
        fi
    fi

    # Fall back to netstat + ps
    if command -v netstat >/dev/null 2>&1; then
        local line
        line=$(netstat -tlnp 2>/dev/null | grep ":$port " | head -n1)
        if [ -n "$line" ]; then
            pid=$(echo "$line" | awk '{print $NF}' | cut -d'/' -f1)
            if [ -n "$pid" ] && [ "$pid" != "-" ]; then
                echo "$pid"
                return 0
            fi
        fi
    fi

    echo ""
    return 1
}

# Check Node.js version (returns 0 for valid, 1 for invalid)
check_node_version() {
    local node_cmd="$1"
    local node_version
    node_version=$($node_cmd --version 2>/dev/null | sed 's/v//')
    local major_version
    major_version=$(echo "$node_version" | cut -d. -f1)

    # Vite requires Node.js 20.19+ or 22.12+
    if [ "$major_version" -lt 20 ]; then
        return 1
    fi
    return 0
}

# Detect Node.js binary
find_node() {
    local node_cmd=""

    if command -v node &>/dev/null; then
        node_cmd="node"
    elif [ -x /usr/bin/node ]; then
        node_cmd="/usr/bin/node"
    elif [ -x /usr/local/bin/node ]; then
        node_cmd="/usr/local/bin/node"
    else
        return 1
    fi

    echo "$node_cmd"
    return 0
}

# Wait for port to be listening
wait_for_port() {
    local port="$1"
    local max_wait="${2:-10}"
    local count=0

    while [ $count -lt $max_wait ]; do
        local pid
        pid=$(get_pid_by_port "$port")
        if [ -n "$pid" ]; then
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    return 1
}

# ==============================================================================
# Backend Management
# ==============================================================================
start_backend() {
    log_info "Starting backend service..."

    # Check if already running
    local pid
    pid=$(get_pid_from_file "$BACKEND_PID")
    if [ -n "$pid" ] && is_process_alive "$pid"; then
        log_warn "Backend already running (PID: $pid)"
        return 0
    fi

    # Clean stale PID file
    [ -f "$BACKEND_PID" ] && rm -f "$BACKEND_PID"

    # Verify virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtual environment not found: $VENV_DIR"
        log_info "Create it with: python3 -m venv venv"
        return 1
    fi

    if [ ! -x "$PYTHON_BIN" ]; then
        log_error "Python executable not found: $PYTHON_BIN"
        return 1
    fi

    # Create required directories
    mkdir -p "${APP_DIR}/data" "${APP_DIR}/logs" "${APP_DIR}/sessions"

    # Start backend daemon
    log_info "Launching backend daemon..."
    nohup "$PYTHON_BIN" "${APP_DIR}/run_daemon.py" >"$BACKEND_LOG" 2>&1 &
    local daemon_pid=$!
    echo "$daemon_pid" >"$BACKEND_PID"

    # Wait for service to be ready
    log_info "Waiting for backend to be ready..."
    if wait_for_port "$BACKEND_PORT" 15; then
        # Update PID with actual process on port
        local actual_pid
        actual_pid=$(get_pid_by_port "$BACKEND_PORT")
        if [ -n "$actual_pid" ]; then
            echo "$actual_pid" >"$BACKEND_PID"
            log_success "Backend started (PID: $actual_pid)"
        else
            log_success "Backend started (PID: $daemon_pid)"
        fi
        printf "     ${C_BLUE}API:${C_RESET}      http://localhost:%d\n" "$BACKEND_PORT"
        printf "     ${C_BLUE}Docs:${C_RESET}     http://localhost:%d/docs\n" "$BACKEND_PORT"
        printf "     ${C_BLUE}Log:${C_RESET}      %s\n" "$BACKEND_LOG"
        return 0
    else
        log_error "Backend failed to start - port $BACKEND_PORT not listening"
        log_info "Check logs: tail -f $BACKEND_LOG"
        rm -f "$BACKEND_PID"
        return 1
    fi
}

stop_backend() {
    log_info "Stopping backend..."

    local stopped=false

    # Try to stop by port first
    local pid
    pid=$(get_pid_by_port "$BACKEND_PORT")
    if [ -n "$pid" ]; then
        if kill -TERM "$pid" 2>/dev/null; then
            log_success "Backend stopped (PID: $pid)"
            stopped=true
        fi
    fi

    # Try PID file if not stopped yet
    if [ "$stopped" = "false" ]; then
        pid=$(get_pid_from_file "$BACKEND_PID")
        if [ -n "$pid" ] && is_process_alive "$pid"; then
            if kill -TERM "$pid" 2>/dev/null; then
                log_success "Backend stopped (PID: $pid)"
                stopped=true
            fi
        fi
    fi

    # Cleanup PID file
    rm -f "$BACKEND_PID"

    if [ "$stopped" = "false" ]; then
        log_warn "Backend not running"
    fi

    return 0
}

status_backend() {
    printf "\n${C_CYAN}[Backend Service]${C_RESET}\n"

    local pid
    pid=$(get_pid_from_file "$BACKEND_PID")

    if [ -z "$pid" ] || ! is_process_alive "$pid"; then
        printf "  Status: ${C_RED}NOT RUNNING${C_RESET}\n"
        rm -f "$BACKEND_PID"
        return 1
    fi

    printf "  Status: ${C_GREEN}RUNNING${C_RESET}\n"
    printf "  PID:    %s\n" "$pid"
    printf "  URL:    http://localhost:%d\n" "$BACKEND_PORT"
    printf "  Docs:   http://localhost:%d/docs\n" "$BACKEND_PORT"
    printf "  Log:    %s\n" "$BACKEND_LOG"

    # Show port info if lsof available
    if command -v lsof &>/dev/null; then
        local port_info
        port_info=$(lsof -i ":$BACKEND_PORT" 2>/dev/null | grep LISTEN || echo "N/A")
        printf "  Port:   %s\n" "$port_info"
    fi

    return 0
}

# ==============================================================================
# Frontend Management
# ==============================================================================
start_frontend() {
    log_info "Starting frontend service..."

    # Check if already running
    local pid
    pid=$(get_pid_from_file "$FRONTEND_PID")
    if [ -n "$pid" ] && is_process_alive "$pid"; then
        log_warn "Frontend already running (PID: $pid)"
        return 0
    fi

    # Clean stale PID file
    [ -f "$FRONTEND_PID" ] && rm -f "$FRONTEND_PID"

    # Verify Node.js exists
    local node_bin
    node_bin=$(find_node)
    if [ $? -ne 0 ]; then
        log_error "Node.js not found"
        log_info "Install from: https://nodejs.org/"
        return 1
    fi

    # Check Node.js version
    if ! check_node_version "$node_bin"; then
        local node_version
        node_version=$($node_bin --version 2>/dev/null)
        log_error "Node.js version $node_version is too old"
        log_error "Vite requires Node.js 20.19+ or 22.12+"
        log_info "Upgrade: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
        log_info "Then: sudo apt-get install -y nodejs"
        return 1
    fi

    # Verify frontend directory
    if [ ! -d "${APP_DIR}/frontend" ]; then
        log_error "Frontend directory not found"
        return 1
    fi

    # Install dependencies if needed
    if [ ! -d "${APP_DIR}/frontend/node_modules" ]; then
        log_info "Installing frontend dependencies..."
        (cd "${APP_DIR}/frontend" && npm install)
    fi

    # Start frontend dev server
    log_info "Launching frontend dev server..."
    (cd "${APP_DIR}/frontend" && nohup npm run dev >"$FRONTEND_LOG" 2>&1 & echo $! >&3) 3>"$FRONTEND_PID"

    # Read PID from file
    local npm_pid
    npm_pid=$(cat "$FRONTEND_PID" 2>/dev/null || echo "unknown")

    # Wait for service to be ready
    log_info "Waiting for frontend to be ready..."
    if wait_for_port "$FRONTEND_PORT" 15; then
        # Update PID with actual process on port
        local actual_pid
        actual_pid=$(get_pid_by_port "$FRONTEND_PORT")
        if [ -n "$actual_pid" ]; then
            echo "$actual_pid" >"$FRONTEND_PID"
            log_success "Frontend started (PID: $actual_pid)"
        else
            log_success "Frontend started (PID: $npm_pid)"
        fi
        printf "     ${C_BLUE}URL:${C_RESET}      http://localhost:%d\n" "$FRONTEND_PORT"
        printf "     ${C_BLUE}Log:${C_RESET}      %s\n" "$FRONTEND_LOG"
        return 0
    else
        log_error "Frontend failed to start - port $FRONTEND_PORT not listening"

        # Show last 10 lines of log for debugging
        if [ -f "$FRONTEND_LOG" ]; then
            echo ""
            log_warn "Last 10 lines from log:"
            echo "----------------------------------------"
            tail -n 10 "$FRONTEND_LOG"
            echo "----------------------------------------"
        fi

        log_info "Full log: tail -f $FRONTEND_LOG"
        rm -f "$FRONTEND_PID"
        return 1
    fi
}

stop_frontend() {
    log_info "Stopping frontend..."

    local stopped=false

    # Try common Vite ports (3000-3010)
    for port in $(seq 3000 3010); do
        local pid
        pid=$(get_pid_by_port "$port")
        if [ -n "$pid" ]; then
            # Verify it's a node process
            if ps -p "$pid" -o comm= 2>/dev/null | grep -q node; then
                if kill -TERM "$pid" 2>/dev/null; then
                    log_success "Frontend stopped (PID: $pid, Port: $port)"
                    stopped=true
                fi
            fi
        fi
    done

    # Try PID file if not stopped yet
    if [ "$stopped" = "false" ]; then
        local pid
        pid=$(get_pid_from_file "$FRONTEND_PID")
        if [ -n "$pid" ] && is_process_alive "$pid"; then
            if kill -TERM "$pid" 2>/dev/null; then
                log_success "Frontend stopped (PID: $pid)"
                stopped=true
            fi
        fi
    fi

    # Cleanup PID file
    rm -f "$FRONTEND_PID"

    if [ "$stopped" = "false" ]; then
        log_warn "Frontend not running"
    fi

    return 0
}

status_frontend() {
    printf "\n${C_CYAN}[Frontend Service]${C_RESET}\n"

    local pid
    pid=$(get_pid_from_file "$FRONTEND_PID")

    if [ -z "$pid" ] || ! is_process_alive "$pid"; then
        printf "  Status: ${C_RED}NOT RUNNING${C_RESET}\n"
        rm -f "$FRONTEND_PID"
        return 1
    fi

    printf "  Status: ${C_GREEN}RUNNING${C_RESET}\n"
    printf "  PID:    %s\n" "$pid"
    printf "  URL:    http://localhost:%d\n" "$FRONTEND_PORT"
    printf "  Log:    %s\n" "$FRONTEND_LOG"

    # Show port info if lsof available
    if command -v lsof &>/dev/null; then
        local port_info
        port_info=$(lsof -i ":$FRONTEND_PORT" 2>/dev/null | grep LISTEN || echo "N/A")
        printf "  Port:   %s\n" "$port_info"
    fi

    return 0
}

# ==============================================================================
# Build Command
# ==============================================================================
build_frontend() {
    print_header "CheckIn App V2 - Building Frontend"

    # Verify Node.js exists
    local node_bin
    node_bin=$(find_node)
    if [ $? -ne 0 ]; then
        log_error "Node.js not found"
        log_info "Install from: https://nodejs.org/"
        return 1
    fi

    # Check Node.js version
    if ! check_node_version "$node_bin"; then
        local node_version
        node_version=$($node_bin --version 2>/dev/null)
        log_error "Node.js version $node_version is too old"
        log_error "Vite requires Node.js 20.19+ or 22.12+"
        log_info "Upgrade: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
        log_info "Then: sudo apt-get install -y nodejs"
        return 1
    fi

    # Verify frontend directory
    if [ ! -d "${APP_DIR}/frontend" ]; then
        log_error "Frontend directory not found"
        return 1
    fi

    # Install dependencies if needed
    if [ ! -d "${APP_DIR}/frontend/node_modules" ]; then
        log_info "Installing dependencies first..."
        (cd "${APP_DIR}/frontend" && npm install) || {
            log_error "Failed to install dependencies"
            return 1
        }
        echo
    fi

    log_info "Building frontend for production..."
    echo

    # Build
    (cd "${APP_DIR}/frontend" && npm run build)
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo
        log_success "Frontend built successfully!"

        # Show build info
        if [ -d "${APP_DIR}/frontend/dist" ]; then
            local dist_size
            dist_size=$(du -sh "${APP_DIR}/frontend/dist" 2>/dev/null | cut -f1 || echo "unknown")

            echo
            printf "${C_CYAN}Build Output:${C_RESET}\n"
            printf "  Location: %s/frontend/dist\n" "$APP_DIR"
            printf "  Size:     %s\n" "$dist_size"
            echo
            printf "${C_CYAN}File Structure:${C_RESET}\n"
            ls -lh "${APP_DIR}/frontend/dist/" 2>/dev/null || echo "  (unable to list files)"
            echo
            log_info "Deploy 'frontend/dist' to your web server"
        else
            log_warn "Build succeeded but dist directory not found"
        fi
        return 0
    else
        echo
        log_error "Frontend build failed"
        log_info "Check output above for details"
        return 1
    fi
}

# ==============================================================================
# Command Handlers
# ==============================================================================
cmd_start() {
    local target="${1:-all}"

    case "$target" in
        backend)
            print_header "CheckIn App V2 - Starting Backend"
            start_backend
            ;;
        frontend)
            print_header "CheckIn App V2 - Starting Frontend"
            start_frontend
            ;;
        all)
            print_header "CheckIn App V2 - Starting All Services"
            echo
            start_backend
            echo
            start_frontend
            echo
            printf "${C_GREEN}========================================${C_RESET}\n"
            printf "${C_GREEN}All Services Started!${C_RESET}\n"
            printf "${C_GREEN}========================================${C_RESET}\n"
            echo
            printf "Backend API:  http://localhost:%d\n" "$BACKEND_PORT"
            printf "API Docs:     http://localhost:%d/docs\n" "$BACKEND_PORT"
            printf "Frontend App: http://localhost:%d\n" "$FRONTEND_PORT"
            echo
            ;;
        *)
            log_error "Invalid target: $target"
            show_usage
            return 1
            ;;
    esac
}

cmd_stop() {
    local target="${1:-all}"

    case "$target" in
        backend)
            print_header "CheckIn App V2 - Stopping Backend"
            stop_backend
            ;;
        frontend)
            print_header "CheckIn App V2 - Stopping Frontend"
            stop_frontend
            ;;
        all)
            print_header "CheckIn App V2 - Stopping All Services"
            echo
            stop_backend
            echo
            stop_frontend
            ;;
        *)
            log_error "Invalid target: $target"
            show_usage
            return 1
            ;;
    esac
}

cmd_restart() {
    local target="${1:-all}"

    log_info "Restarting $target..."
    echo
    cmd_stop "$target"
    sleep 2
    cmd_start "$target"
}

cmd_status() {
    local target="${1:-all}"

    print_header "CheckIn App V2 - Service Status"

    case "$target" in
        backend)
            status_backend || true
            ;;
        frontend)
            status_frontend || true
            ;;
        all)
            status_backend || true
            status_frontend || true
            ;;
        *)
            log_error "Invalid target: $target"
            show_usage
            return 1
            ;;
    esac
    echo
}

cmd_log() {
    local target="${1:-}"

    if [ -z "$target" ] || [ "$target" = "all" ]; then
        log_error "Cannot tail multiple logs simultaneously"
        log_info "Use: $0 log backend  OR  $0 log frontend"
        return 1
    fi

    case "$target" in
        backend)
            if [ ! -f "$BACKEND_LOG" ]; then
                log_error "Log file not found: $BACKEND_LOG"
                return 1
            fi
            print_header "Backend Real-time Logs (Press Ctrl+C to exit)"
            echo
            tail -f "$BACKEND_LOG"
            ;;
        frontend)
            if [ ! -f "$FRONTEND_LOG" ]; then
                log_error "Log file not found: $FRONTEND_LOG"
                return 1
            fi
            print_header "Frontend Real-time Logs (Press Ctrl+C to exit)"
            echo
            tail -f "$FRONTEND_LOG"
            ;;
        *)
            log_error "Invalid target: $target"
            log_info "Use: backend or frontend"
            return 1
            ;;
    esac
}

# ==============================================================================
# Help and Usage
# ==============================================================================
show_usage() {
    echo
    printf "${C_CYAN}CheckIn App V2 - Unified Service Manager${C_RESET}\n"
    echo
    printf "${C_YELLOW}USAGE:${C_RESET}\n"
    echo "    \$0 COMMAND [TARGET]"
    echo
    printf "${C_YELLOW}COMMANDS:${C_RESET}\n"
    echo "    start [TARGET]   - Start service(s)"
    echo "    stop [TARGET]    - Stop service(s)"
    echo "    restart [TARGET] - Restart service(s)"
    echo "    status [TARGET]  - View service status"
    echo "    log TARGET       - View real-time logs (backend or frontend)"
    echo "    build            - Build frontend for production"
    echo
    printf "${C_YELLOW}TARGETS:${C_RESET}\n"
    echo "    backend          - Backend API service (port $BACKEND_PORT)"
    echo "    frontend         - Frontend dev server (port $FRONTEND_PORT)"
    echo "    all              - Both services (default)"
    echo
    printf "${C_YELLOW}EXAMPLES:${C_RESET}\n"
    echo "    \$0 start              # Start both services"
    echo "    \$0 start backend      # Start backend only"
    echo "    \$0 stop all           # Stop all services"
    echo "    \$0 status             # View all service status"
    echo "    \$0 log backend        # View backend logs"
    echo "    \$0 build              # Build frontend static files"
    echo "    \$0 restart frontend   # Restart frontend"
    echo
}

# ==============================================================================
# Main Entry Point
# ==============================================================================
main() {
    local command="${1:-}"
    local target="${2:-all}"

    if [ -z "$command" ]; then
        show_usage
        exit 1
    fi

    case "$command" in
        start)
            cmd_start "$target"
            ;;
        stop)
            cmd_stop "$target"
            ;;
        restart)
            cmd_restart "$target"
            ;;
        status)
            cmd_status "$target"
            ;;
        log)
            cmd_log "$target"
            ;;
        build)
            build_frontend
            ;;
        help|--help|-h)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
