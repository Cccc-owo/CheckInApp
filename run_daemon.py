"""
Daemon mode startup script - For background service
后台服务启动脚本 - 用于守护进程模式
"""
import sys
import os
from pathlib import Path

# Add project root directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.chdir(BASE_DIR)

# Import and run in production mode
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload for daemon mode
        log_level="info",
        access_log=True,
    )
