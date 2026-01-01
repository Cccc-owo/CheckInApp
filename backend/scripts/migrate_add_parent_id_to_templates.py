"""
数据库迁移脚本：为 task_templates 表添加 parent_id 字段

运行方法：
    python backend/scripts/migrate_add_parent_id_to_templates.py
"""
import sys
import os
from pathlib import Path

# 设置 UTF-8 编码输出（Windows 兼容）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.models.database import engine, SessionLocal


def migrate():
    """为 task_templates 表添加 parent_id 字段"""
    print("=" * 60)
    print("开始数据库迁移：添加 parent_id 字段到 task_templates 表")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 检查字段是否已存在
        result = db.execute(text(
            "SELECT COUNT(*) FROM pragma_table_info('task_templates') WHERE name='parent_id'"
        ))
        field_exists = result.fetchone()[0] > 0

        if field_exists:
            print("⚠️  parent_id 字段已存在，跳过迁移")
            return

        # 添加 parent_id 字段
        print("📝 正在添加 parent_id 字段...")
        db.execute(text(
            "ALTER TABLE task_templates ADD COLUMN parent_id INTEGER"
        ))
        db.commit()
        print("✅ parent_id 字段添加成功")

        # 创建外键约束（SQLite 不支持直接添加外键，需要重建表）
        print("\n📝 注意：SQLite 不支持直接添加外键约束")
        print("   如需外键约束，请重建表或在下次完整迁移时处理")

        print("\n" + "=" * 60)
        print("✅ 数据库迁移完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    migrate()
