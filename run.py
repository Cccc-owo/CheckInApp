"""
启动脚本 - 直接运行后端服务
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.chdir(BASE_DIR)

# 导入并运行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
