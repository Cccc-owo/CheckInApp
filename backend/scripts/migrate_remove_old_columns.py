"""
删除 check_in_tasks 表中不再需要的旧列的迁移脚本

删除的列：
- signature (VARCHAR) - 已在 payload_config 中
- texts (VARCHAR) - 已在 payload_config 中
- values (TEXT) - 已在 payload_config 中
- thread_id (VARCHAR) - 已在 payload_config 的 ThreadId 中
- email (VARCHAR) - 从 user 表的 email 字段获取

新架构只保留：
- id, user_id, payload_config, name, is_active, created_at, updated_at

运行方式：
    python backend/scripts/migrate_remove_old_columns.py
    或
    venv/Scripts/python.exe backend/scripts/migrate_remove_old_columns.py
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from backend.models.database import engine


def migrate():
    """执行迁移：删除旧列"""
    print("开始迁移：删除 check_in_tasks 表中的旧列...")
    print("将删除的列: signature, texts, values, thread_id, email")
    print("=" * 60)

    with engine.connect() as conn:
        # 检查表结构
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('check_in_tasks')]

        print(f"\n当前表列: {', '.join(columns)}")

        old_columns = ['signature', 'texts', 'values', 'thread_id', 'email']
        columns_to_remove = [col for col in old_columns if col in columns]

        if not columns_to_remove:
            print("\n[OK] 旧列已被删除，跳过迁移")
            return

        print(f"\n需要删除的列: {', '.join(columns_to_remove)}")

        # SQLite 不支持直接 DROP COLUMN，需要重建表
        # 步骤：
        # 1. 创建新表（只包含需要的列）
        # 2. 复制数据
        # 3. 删除旧表
        # 4. 重命名新表

        print("\n正在重建表结构...")

        # 1. 创建新表
        conn.execute(text("""
            CREATE TABLE check_in_tasks_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                payload_config TEXT NOT NULL DEFAULT '{}',
                name VARCHAR(100) DEFAULT '',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        print("  [OK] 创建新表结构")

        # 2. 复制数据（只复制保留的列）
        conn.execute(text("""
            INSERT INTO check_in_tasks_new
                (id, user_id, payload_config, name, is_active, created_at, updated_at)
            SELECT
                id, user_id, payload_config, name, is_active, created_at, updated_at
            FROM check_in_tasks
        """))
        print("  [OK] 复制数据到新表")

        # 3. 删除旧表
        conn.execute(text("DROP TABLE check_in_tasks"))
        print("  [OK] 删除旧表")

        # 4. 重命名新表
        conn.execute(text("ALTER TABLE check_in_tasks_new RENAME TO check_in_tasks"))
        print("  [OK] 重命名新表")

        # 5. 重建索引
        conn.execute(text("""
            CREATE INDEX ix_check_in_tasks_user_id ON check_in_tasks(user_id)
        """))
        conn.execute(text("""
            CREATE INDEX ix_check_in_tasks_id ON check_in_tasks(id)
        """))
        conn.execute(text("""
            CREATE INDEX ix_task_user_active ON check_in_tasks(user_id, is_active)
        """))
        print("  [OK] 重建索引")

        conn.commit()

        print("\n[SUCCESS] 表结构迁移成功！")
        print("\n新的表结构：")
        inspector = inspect(engine)
        new_columns = [col['name'] for col in inspector.get_columns('check_in_tasks')]
        print(f"  列: {', '.join(new_columns)}")


if __name__ == "__main__":
    try:
        migrate()
        print("\n" + "=" * 60)
        print("[完成] 迁移成功完成！")
        print("\n数据库已更新为新架构：")
        print("  - 删除了 signature, texts, values, thread_id, email 列")
        print("  - 保留了 payload_config 列（存储完整的 JSON payload）")
        print("  - ThreadId 现在存储在 payload_config 中")
        print("  - Email 现在从 user 表获取")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
