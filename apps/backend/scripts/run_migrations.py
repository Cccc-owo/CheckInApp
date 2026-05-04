#!/usr/bin/env python3
"""
运行数据库迁移的脚本。

使用方法:
    uv run python -m backend.scripts.run_migrations
"""

from __future__ import annotations

import logging

from backend.migrations import MigrationExecutionError, run_pending_migrations
from backend.models import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> int:
    try:
        init_db()
        result = run_pending_migrations()
    except MigrationExecutionError as exc:
        logger.error("❌ 迁移失败: %s", exc)
        return 1

    logger.info("✅ 迁移完成：applied=%s skipped=%s", len(result.applied), len(result.skipped))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
