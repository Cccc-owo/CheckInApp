"""
添加 payload_config 字段到 check_in_tasks 表的迁移脚本

运行方式：
    python backend/scripts/migrate_add_payload_config.py
    或
    .venv/Scripts/python.exe backend/scripts/migrate_add_payload_config.py
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.models.database import engine


def migrate():
    """执行迁移"""
    print("开始迁移：添加 payload_config 字段...")

    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("PRAGMA table_info(check_in_tasks)"))
        columns = [row[1] for row in result]

        if 'payload_config' in columns:
            print("[OK] payload_config 字段已存在，跳过迁移")
            return

        # 添加 payload_config 字段（JSON 文本，存储完整的 payload 配置）
        print("添加 payload_config 字段...")
        conn.execute(text("""
            ALTER TABLE check_in_tasks
            ADD COLUMN payload_config TEXT DEFAULT '{}' NOT NULL
        """))
        conn.commit()

        print("[OK] payload_config 字段添加成功")
        print("\n注意：现有任务的 payload_config 默认为空 JSON {}，")
        print("      Worker 将使用默认的固定字段值。")
        print("      新创建的任务将从模板继承完整的 payload 配置。")


if __name__ == "__main__":
    try:
        migrate()
        print("\n[SUCCESS] 迁移完成！")
    except Exception as e:
        print(f"\n[ERROR] 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
