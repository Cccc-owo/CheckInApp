"""
数据库迁移脚本：添加打卡任务 thread_id 字段并回填。

通常无需手动运行，后端启动时会自动执行待迁移项。需要单独执行时：
    uv run python -m backend.scripts.migrate_add_task_thread_id
"""

from __future__ import annotations

import logging
import sys

from backend.migration_steps.task_thread_id import apply as apply_task_thread_id
from backend.models.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate() -> None:
    logger.info("开始迁移：添加 check_in_tasks.thread_id 字段...")
    with engine.connect() as conn:
        apply_task_thread_id(conn)
    logger.info("✅ 迁移完成！任务 thread_id 身份字段已启用")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        logger.error("❌ 迁移失败: %s", e)
        sys.exit(1)
