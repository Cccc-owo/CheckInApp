import os
import threading
import logging
from filelock import FileLock

# 1. 存放所有共享的路径常量
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.csv')
LOG_PATH = os.path.join(BASE_DIR, 'CheckIn.log')
SESSIONS_DIR = os.path.join(BASE_DIR, 'sessions')
CONFIG_INI_PATH = os.path.join(BASE_DIR, 'config.ini')

DEBUG_SCREENSHOT_PATH = os.path.join(BASE_DIR, 'debug_screenshot.png')
DEBUG_PAGE_SOURCE_PATH = os.path.join(BASE_DIR, 'debug_page_source.html')

CHROME_BINARY_PATH = os.path.join(BASE_DIR, "chrome-linux64/chrome")
CHROMEDRIVER_PATH = os.path.join(BASE_DIR, "chromedriver")

# 2. 存放所有共享的锁
CONFIG_LOCK_PATH = os.path.join(BASE_DIR, 'config.csv.lock')
CONFIG_FILE_LOCK = FileLock(CONFIG_LOCK_PATH, timeout=10) # 10秒超时
SCHEDULER_LOCK = os.path.join(BASE_DIR, "scheduler.lock")

# 3. 存放共享的CSV列名
CSV_FIELDNAMES = [
    'ThreadId', 'Signature', 'Texts', 'Values', 
    'jwt_sub', 'Authorization', 'jwt_exp', 'email'
]

CHECKIN_HOUR = 20  # 设置每天打卡的小时数 (24小时制, 8代表早上8点)
CHECKIN_MIN = 0    # 分钟

def get_logger(name):
    """
    只获取指定名称的logger实例。
    具体的配置（如Handler, Formatter）将由主应用 app.py 统一完成。
    """
    return logging.getLogger(name)