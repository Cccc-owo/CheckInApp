"""
删除 users 表中 registered_ip 列的迁移脚本

删除的列：
- registered_ip (VARCHAR) - 注册IP地址，不再需要

新架构中移除该字段以保护用户隐私。

运行方式：
    python backend/scripts/migrate_remove_registered_ip.py
    或
    venv/Scripts/python.exe backend/scripts/migrate_remove_registered_ip.py
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
    """执行迁移：删除 registered_ip 列"""
    print("开始迁移：删除 users 表中的 registered_ip 列...")
    print("=" * 60)

    with engine.connect() as conn:
        # 检查表结构
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('users')]

        print(f"\n当前表列: {', '.join(columns)}")

        if 'registered_ip' not in columns:
            print("\n[OK] registered_ip 列已被删除，跳过迁移")
            return

        print(f"\n需要删除的列: registered_ip")

        # SQLite 不支持直接 DROP COLUMN，需要重建表
        # 步骤：
        # 1. 创建新表（不包含 registered_ip）
        # 2. 复制数据
        # 3. 删除旧表
        # 4. 重命名新表

        print("\n正在重建表结构...")

        # 1. 创建新表
        conn.execute(text("""
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jwt_sub VARCHAR(200) UNIQUE,
                alias VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100),
                password_hash VARCHAR(200),
                authorization TEXT,
                jwt_exp VARCHAR(20) DEFAULT '0',
                role VARCHAR(20) DEFAULT 'user',
                is_approved BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        """))
        print("  [OK] 创建新表结构")

        # 2. 复制数据（不包含 registered_ip）
        conn.execute(text("""
            INSERT INTO users_new
                (id, jwt_sub, alias, email, password_hash, authorization, jwt_exp,
                 role, is_approved, created_at, updated_at)
            SELECT
                id, jwt_sub, alias, email, password_hash, authorization, jwt_exp,
                role, is_approved, created_at, updated_at
            FROM users
        """))
        print("  [OK] 复制数据到新表")

        # 3. 删除旧表
        conn.execute(text("DROP TABLE users"))
        print("  [OK] 删除旧表")

        # 4. 重命名新表
        conn.execute(text("ALTER TABLE users_new RENAME TO users"))
        print("  [OK] 重命名新表")

        # 5. 重建索引
        conn.execute(text("""
            CREATE INDEX ix_users_jwt_sub ON users(jwt_sub)
        """))
        conn.execute(text("""
            CREATE INDEX ix_users_alias ON users(alias)
        """))
        conn.execute(text("""
            CREATE INDEX ix_users_role ON users(role)
        """))
        conn.execute(text("""
            CREATE INDEX ix_users_is_approved ON users(is_approved)
        """))
        conn.execute(text("""
            CREATE INDEX ix_users_id ON users(id)
        """))
        conn.execute(text("""
            CREATE INDEX ix_user_role_approved ON users(role, is_approved)
        """))
        print("  [OK] 重建索引")

        conn.commit()

        print("\n[SUCCESS] 表结构迁移成功！")
        print("\n新的表结构：")
        inspector = inspect(engine)
        new_columns = [col['name'] for col in inspector.get_columns('users')]
        print(f"  列: {', '.join(new_columns)}")


if __name__ == "__main__":
    try:
        migrate()
        print("\n" + "=" * 60)
        print("[完成] 迁移成功完成！")
        print("\n数据库已更新为新架构：")
        print("  - 删除了 registered_ip 列（保护用户隐私）")
        print("  - 保留了所有其他用户数据")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
