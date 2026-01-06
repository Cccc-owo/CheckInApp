"""
数据库迁移脚本：添加账户锁定相关字段

添加字段：
- failed_login_attempts: 连续登录失败次数
- locked_until: 账户锁定到期时间
- last_failed_login: 最后一次登录失败时间

运行方式：
    python -m backend.scripts.migrate_add_account_lockout
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.models.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """执行迁移"""
    logger.info("开始迁移：添加账户锁定相关字段...")

    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]

        # 添加 failed_login_attempts 字段
        if 'failed_login_attempts' not in columns:
            logger.info("添加 failed_login_attempts 字段...")
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0 NOT NULL"
            ))
            conn.commit()
            logger.info("✓ failed_login_attempts 字段添加成功")
        else:
            logger.info("✓ failed_login_attempts 字段已存在，跳过")

        # 添加 locked_until 字段
        if 'locked_until' not in columns:
            logger.info("添加 locked_until 字段...")
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN locked_until DATETIME"
            ))
            conn.commit()
            logger.info("✓ locked_until 字段添加成功")
        else:
            logger.info("✓ locked_until 字段已存在，跳过")

        # 添加 last_failed_login 字段
        if 'last_failed_login' not in columns:
            logger.info("添加 last_failed_login 字段...")
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN last_failed_login DATETIME"
            ))
            conn.commit()
            logger.info("✓ last_failed_login 字段添加成功")
        else:
            logger.info("✓ last_failed_login 字段已存在，跳过")

    logger.info("✅ 迁移完成！账户锁定功能已启用")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        sys.exit(1)
