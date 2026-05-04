"""
数据库迁移脚本：添加账户锁定相关字段。

通常无需手动运行，后端启动时会自动执行待迁移项。需要单独执行时：
    uv run python -m backend.scripts.migrate_add_account_lockout
"""

from __future__ import annotations

import logging
import sys

from backend.migration_steps.account_lockout import apply as apply_account_lockout
from backend.models.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate() -> None:
    logger.info("开始迁移：添加账户锁定相关字段...")
    with engine.connect() as conn:
        apply_account_lockout(conn)
    logger.info("✅ 迁移完成！账户锁定功能已启用")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        logger.error("❌ 迁移失败: %s", e)
        sys.exit(1)
