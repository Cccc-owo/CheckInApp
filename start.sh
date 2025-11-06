#!/bin/bash

# ==============================================================================
# CheckInApp 启动脚本
# ==============================================================================

# --- 配置 ---

# 项目的绝对路径
# $(dirname "$0") 会获取脚本文件所在的目录
# cd ... && pwd 会确保我们得到的是绝对路径
APP_DIR=$(cd "$(dirname "$0")" && pwd)

# 虚拟环境的路径
VENV_DIR="$APP_DIR/venv"

# Gunicorn的配置
WORKERS=4  # 工作进程数，可以根据你的CPU核心数调整 (2 * cores + 1)
BIND_ADDR="0.0.0.0:5000" # 绑定的地址和端口

# Gunicorn进程ID文件的存放位置
PID_FILE="$APP_DIR/gunicorn.pid"

# Flask应用的主文件和实例
# 格式为: <文件名>:<Flask实例名>
APP_MODULE="app:app"

# 日志文件（可选，Gunicorn会把输出重定向到这里）
LOG_FILE="$APP_DIR/gunicorn.log"

# --- 检查虚拟环境 ---
if [ ! -d "$VENV_DIR" ]; then
    echo "错误: 虚拟环境目录 '$VENV_DIR' 不存在。"
    echo "请先运行 'python3 -m venv venv' 来创建它。"
    exit 1
fi

# --- 激活虚拟环境 ---
# source命令必须在当前shell下执行，所以我们把所有操作放在这个脚本里
source "$VENV_DIR/bin/activate"
echo "虚拟环境已激活。"

# --- 脚本操作 (start|stop|restart) ---

case "$1" in
    start)
        echo "正在启动 CheckInApp..."
        # --daemon 参数让gunicorn在后台运行
        # --pid 参数指定了PID文件的位置，方便我们停止它
        # --access-logfile 和 --error-logfile 将日志输出到文件
        gunicorn --workers $WORKERS \
                 --bind $BIND_ADDR \
                 --pid $PID_FILE \
                 --access-logfile $LOG_FILE \
                 --error-logfile $LOG_FILE \
                 --daemon \
                 $APP_MODULE
        echo "CheckInApp 已启动。PID保存在 $PID_FILE, 日志输出到 $LOG_FILE"
        ;;
    stop)
        echo "正在停止 CheckInApp..."
        if [ -f "$PID_FILE" ]; then
            # 从PID文件中读取进程ID并杀死它
            kill $(cat "$PID_FILE")
            rm "$PID_FILE"
            echo "服务已停止。"
        else
            echo "错误: 找不到PID文件。服务可能没有在运行。"
        fi
        ;;
    restart)
        echo "正在重启 CheckInApp..."
        # 先执行stop，再执行start
        "$0" stop
        sleep 2 # 等待一下，确保进程已完全关闭
        "$0" start
        ;;
    status)
        echo "检查 CheckInApp 状态..."
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null; then
                echo "服务正在运行，PID: $PID"
            else
                echo "服务不在运行，但PID文件存在。可能已意外崩溃。"
            fi
        else
            echo "服务不在运行。"
        fi
        ;;
    log)
        echo "查看实时日志 (按 Ctrl+C 退出)..."
        tail -f "$LOG_FILE"
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|log}"
        exit 1
        ;;
esac

exit 0