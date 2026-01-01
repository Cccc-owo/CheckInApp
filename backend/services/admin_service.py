import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from backend.models import User

logger = logging.getLogger(__name__)


class AdminService:
    """管理员服务"""

    @staticmethod
    def get_pending_users(db: Session) -> List[User]:
        """获取待审批用户列表"""
        users = db.query(User).filter(
            User.is_approved == False,
            User.role == "user"
        ).order_by(User.created_at.desc()).all()

        return users

    @staticmethod
    def approve_user(user_id: int, db: Session) -> Dict[str, Any]:
        """审批通过用户"""
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return {"success": False, "message": "用户不存在"}

        if user.is_approved:
            return {"success": False, "message": "用户已经通过审批"}

        user.is_approved = True
        user.updated_at = datetime.now()
        db.commit()

        logger.info(f"管理员审批通过用户: {user.alias} (ID: {user.id})")

        return {
            "success": True,
            "message": "审批成功",
            "user_id": user.id
        }

    @staticmethod
    def reject_user(user_id: int, db: Session) -> Dict[str, Any]:
        """拒绝并删除用户"""
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return {"success": False, "message": "用户不存在"}

        alias = user.alias
        db.delete(user)
        db.commit()

        logger.info(f"管理员拒绝用户: {alias} (ID: {user_id})")

        return {
            "success": True,
            "message": "已拒绝并删除用户"
        }

    @staticmethod
    def delete_expired_pending_users(db: Session) -> int:
        """删除24小时未审批的用户"""
        cutoff_time = datetime.now() - timedelta(hours=24)

        expired_users = db.query(User).filter(
            User.is_approved == False,
            User.role == "user",
            User.created_at < cutoff_time
        ).all()

        count = len(expired_users)

        for user in expired_users:
            logger.info(f"删除过期未审批用户: {user.alias} (ID: {user.id})")
            db.delete(user)

        db.commit()

        return count
