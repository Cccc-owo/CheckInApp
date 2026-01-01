#!/usr/bin/env python3
"""
创建管理员用户的脚本

使用方法:
    python backend/scripts/create_admin.py

或使用虚拟环境:
    ./venv/Scripts/python.exe backend/scripts/create_admin.py
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.models import init_db, User
from backend.models.database import SessionLocal
from backend.services.auth_service import AuthService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_user(alias: str):
    """
    将现有用户升级为管理员（或创建管理员占位符）

    Args:
        alias: 用户别名
    """
    # 初始化数据库
    init_db()

    # 创建数据库会话
    db = SessionLocal()

    try:
        # 检查别名是否已存在
        existing_user = db.query(User).filter(User.alias == alias).first()

        if existing_user:
            print(f"[OK] 找到用户：{alias}")
            print(f"   用户 ID: {existing_user.id}")
            print(f"   QQ 标识 (jwt_sub): {existing_user.jwt_sub}")
            print(f"   当前角色: {existing_user.role}")
            print(f"   审批状态: {existing_user.is_approved}")

            # 如果已经是管理员
            if existing_user.role == "admin":
                print("\n该用户已经是管理员")
                return

            # 升级为管理员
            response = input("\n是否将该用户升级为管理员？(y/n): ")
            if response.lower() == 'y':
                existing_user.role = "admin"
                existing_user.is_approved = True  # 确保已审批
                db.commit()

                print("\n" + "=" * 60)
                print("[成功] 用户已升级为管理员！")
                print("=" * 60)
                print(f"   用户 ID: {existing_user.id}")
                print(f"   别名: {existing_user.alias}")
                print(f"   QQ 标识: {existing_user.jwt_sub}")
                print(f"   角色: admin")
                print("=" * 60)
            else:
                print("操作已取消")
        else:
            print(f"\n[错误] 未找到别名为 '{alias}' 的用户")
            print("\n请先使用该别名进行 QQ 扫码注册，然后再运行此脚本升级为管理员")

    except Exception as e:
        logger.error(f"[错误] 操作失败: {e}")
        db.rollback()
        raise

    finally:
        db.close()


def main():
    """主函数"""
    print("=" * 60)
    print("接龙自动打卡系统 - 设置管理员")
    print("=" * 60)
    print()
    print("[说明]")
    print("   此脚本将已注册的用户升级为管理员")
    print("   请先使用别名进行 QQ 扫码注册，然后运行此脚本")
    print()

    # 获取用户别名
    alias = input("请输入要设置为管理员的用户别名 [admin]: ").strip() or "admin"

    print()
    print("=" * 60)
    print(f"准备将用户 '{alias}' 设置为管理员")
    print("=" * 60)
    print()

    create_admin_user(alias)


if __name__ == "__main__":
    main()
