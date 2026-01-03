"""
为 users 表添加 Token 过期提醒字段的迁移脚本

新增的列：
- token_expiring_notified (BOOLEAN) - Token 即将过期提醒是否已发送（过期前30分钟内）
- token_expired_notified (BOOLEAN) - Token 已过期提醒是否已发送（过期后30分钟内）

这两个字段用于实现两次 Token 过期提醒：
1. 过期前 30 分钟内：提醒用户 Token 即将过期
2. 过期后 30 分钟内：提醒用户 Token 已过期，需要刷新

运行方式：
    python backend/scripts/migrate_add_token_expiry_notified.py
    或
    venv/Scripts/python.exe backend/scripts/migrate_add_token_expiry_notified.py
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
    """执行迁移：添加 token_expiring_notified 和 token_expired_notified 列"""
    print("开始迁移：为 users 表添加 Token 过期提醒字段...")
    print("=" * 60)

    with engine.connect() as conn:
        # 检查表结构
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('users')]

        print(f"\n当前表列: {', '.join(columns)}")

        # 检查是否已存在新字段
        has_expiring = 'token_expiring_notified' in columns
        has_expired = 'token_expired_notified' in columns

        if has_expiring and has_expired:
            print("\n[OK] Token 过期提醒字段已存在，跳过迁移")
            return

        print(f"\n需要添加的列:")
        print(f"  - token_expiring_notified (BOOLEAN, DEFAULT False)")
        print(f"  - token_expired_notified (BOOLEAN, DEFAULT False)")

        # SQLite 不支持直接 ALTER TABLE ADD COLUMN with constraints，需要重建表
        # 步骤：
        # 1. 创建新表（包含两个新字段）
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
                token_expiring_notified BOOLEAN NOT NULL DEFAULT 0,
                token_expired_notified BOOLEAN NOT NULL DEFAULT 0,
                role VARCHAR(20) DEFAULT 'user',
                is_approved BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        """))
        print("  [OK] 创建新表结构")

        # 2. 复制数据（为旧数据设置两个字段都为 False）
        conn.execute(text("""
            INSERT INTO users_new
                (id, jwt_sub, alias, email, password_hash, authorization, jwt_exp,
                 token_expiring_notified, token_expired_notified,
                 role, is_approved, created_at, updated_at)
            SELECT
                id, jwt_sub, alias, email, password_hash, authorization, jwt_exp,
                0, 0,
                role, is_approved, created_at, updated_at
            FROM users
        """))
        print("  [OK] 复制数据到新表（所有用户的提醒字段默认为 False）")

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
        print("  - 添加了 token_expiring_notified 列（Token 即将过期提醒，过期前30分钟）")
        print("  - 添加了 token_expired_notified 列（Token 已过期提醒，过期后30分钟内）")
        print("  - 所有现有用户的提醒字段默认为 False")
        print("\n提醒逻辑：")
        print("  1. 过期前 30 分钟内：发送\"即将过期\"邮件，设置 token_expiring_notified = True")
        print("  2. 过期后 30 分钟内：发送\"已过期\"邮件，设置 token_expired_notified = True")
        print("  3. 用户刷新 Token 后：重置两个字段为 False")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
