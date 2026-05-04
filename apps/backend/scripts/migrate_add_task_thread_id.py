"""
数据库迁移脚本：添加打卡任务 thread_id 字段并回填。

运行方式：
    uv run python -m backend.scripts.migrate_add_task_thread_id
"""

import json
import logging
import sys
from pathlib import Path

APPS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(APPS_DIR))

from sqlalchemy import text

from backend.models.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _extract_thread_id(payload_config: str | None) -> str | None:
    if not payload_config:
        return None
    try:
        payload = json.loads(payload_config)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    thread_id = payload.get("ThreadId")
    value = str(thread_id).strip() if thread_id is not None else ""
    return value or None


def migrate() -> None:
    """执行迁移。"""
    logger.info("开始迁移：添加 check_in_tasks.thread_id 字段...")

    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(check_in_tasks)"))
        columns = [row[1] for row in result]

        if "thread_id" not in columns:
            logger.info("添加 thread_id 字段...")
            conn.execute(text("ALTER TABLE check_in_tasks ADD COLUMN thread_id VARCHAR(100)"))
            conn.commit()
            logger.info("✓ thread_id 字段添加成功")
        else:
            logger.info("✓ thread_id 字段已存在，跳过")

        rows = conn.execute(text("SELECT id, payload_config FROM check_in_tasks")).fetchall()
        invalid_ids: list[int] = []
        seen: dict[tuple[int, str], int] = {}
        duplicate_ids: list[int] = []

        full_rows = conn.execute(
            text("SELECT id, user_id, payload_config FROM check_in_tasks")
        ).fetchall()
        for row in full_rows:
            thread_id = _extract_thread_id(row.payload_config)
            if not thread_id:
                invalid_ids.append(row.id)
                continue
            key = (row.user_id, thread_id)
            if key in seen:
                duplicate_ids.append(row.id)
            else:
                seen[key] = row.id

        if invalid_ids or duplicate_ids:
            messages = []
            if invalid_ids:
                messages.append(f"payload_config 缺少有效 ThreadId 的任务: {invalid_ids}")
            if duplicate_ids:
                messages.append(f"同用户 ThreadId 重复的任务: {duplicate_ids}")
            raise RuntimeError("；".join(messages))

        for row in rows:
            thread_id = _extract_thread_id(row.payload_config)
            if thread_id:
                conn.execute(
                    text("UPDATE check_in_tasks SET thread_id = :thread_id WHERE id = :id"),
                    {"thread_id": thread_id, "id": row.id},
                )
        conn.commit()

        indexes = conn.execute(text("PRAGMA index_list(check_in_tasks)")).fetchall()
        index_names = [row[1] for row in indexes]
        if "ix_task_user_thread_id_unique" not in index_names:
            logger.info("添加用户级 thread_id 唯一索引...")
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX ix_task_user_thread_id_unique "
                    "ON check_in_tasks (user_id, thread_id)"
                )
            )
            conn.commit()
            logger.info("✓ 用户级 thread_id 唯一索引添加成功")
        else:
            logger.info("✓ 用户级 thread_id 唯一索引已存在，跳过")

    logger.info("✅ 迁移完成！任务 thread_id 身份字段已启用")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        sys.exit(1)
