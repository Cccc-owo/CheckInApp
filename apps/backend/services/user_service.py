import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import bcrypt
from email_validator import validate_email, EmailNotValidError
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.models import User
from backend.schemas.user import UserCreate, UserUpdate, UserUpdateProfile

logger = logging.getLogger(__name__)


def escape_like_pattern(text: str) -> str:
    """
    转义 LIKE 查询中的特殊字符

    Args:
        text: 原始搜索文本

    Returns:
        转义后的文本
    """
    return text.replace("%", r"\%").replace("_", r"\_")


class UserService:
    """用户服务"""

    @staticmethod
    def _clear_email_verification(user: User) -> None:
        user.email_verified_at = None
        user.email_verification_code_hash = None
        user.email_verification_expires_at = None

    @staticmethod
    def _normalize_email(email: str) -> str:
        try:
            return str(validate_email(email.strip(), check_deliverability=False).normalized)
        except EmailNotValidError as exc:
            raise ValueError("邮箱格式无效") from exc

    @staticmethod
    def create_user(user_data: UserCreate, db: Session) -> User:
        """
        创建用户（管理员手动创建）

        Args:
            user_data: 用户创建数据（包括 alias, role, email, password 等）
            db: 数据库会话

        Returns:
            创建的用户对象
        """
        # 检查 alias 是否已存在
        existing_alias = db.query(User).filter(User.alias == user_data.alias).first()
        if existing_alias:
            raise ValueError(f"用户别名 {user_data.alias} 已存在")

        # 创建用户（管理员创建的用户没有 jwt_sub，需要后续扫码绑定）
        user = User(
            jwt_sub=None,  # NULL 表示未绑定 QQ
            alias=user_data.alias,
            email=str(user_data.email) if user_data.email is not None else None,
            role=user_data.role or "user",
            is_approved=user_data.is_approved
            if user_data.is_approved is not None
            else True,  # 使用请求中的值，默认已审批
            jwt_exp="0",
            authorization=None,
        )

        # 如果提供了密码，则设置密码
        if user_data.password:
            import bcrypt

            password_hash = bcrypt.hashpw(user_data.password.encode("utf-8"), bcrypt.gensalt())
            setattr(user, "password_hash", password_hash.decode("utf-8"))

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(
            f"管理员创建用户成功: {user.alias} (ID: {user.id}, 角色: {user.role}, 密码: {'已设置' if user_data.password else '未设置'})"
        )
        return user

    @staticmethod
    def get_user_by_id(user_id: int, db: Session) -> Optional[User]:
        """
        根据 ID 获取用户

        Args:
            user_id: 用户 ID
            db: 数据库会话

        Returns:
            用户对象或 None
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_alias(alias: str, db: Session) -> Optional[User]:
        """
        根据 alias 获取用户

        Args:
            alias: 用户别名
            db: 数据库会话

        Returns:
            用户对象或 None
        """
        return db.query(User).filter(User.alias == alias).first()

    @staticmethod
    def get_user_by_jwt_sub(jwt_sub: str, db: Session) -> Optional[User]:
        """
        根据 jwt_sub 获取用户

        Args:
            jwt_sub: QQ 用户标识
            db: 数据库会话

        Returns:
            用户对象或 None
        """
        return db.query(User).filter(User.jwt_sub == jwt_sub).first()

    @staticmethod
    def get_all_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role: Optional[str] = None,
    ) -> List[User]:
        """
        获取所有用户

        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 限制记录数
            search: 搜索关键词（alias 或 jwt_sub）
            role: 过滤角色（user/admin）

        Returns:
            用户列表
        """
        query = db.query(User)

        # 搜索过滤
        if search:
            # 转义 LIKE 特殊字符，防止通配符滥用
            escaped_search = escape_like_pattern(search)
            # 注意：jwt_sub 可能为 NULL，需要处理
            search_conditions = [User.alias.ilike(f"%{escaped_search}%")]
            # 只有当 jwt_sub 不为空时才搜索
            search_conditions.append(User.jwt_sub.ilike(f"%{escaped_search}%"))
            query = query.filter(or_(*search_conditions))

        # 角色过滤
        if role:
            query = query.filter(User.role == role)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_user(user_id: int, user_data: UserUpdate, db: Session) -> User:
        """
        更新用户信息（管理员操作）

        Args:
            user_id: 用户 ID
            user_data: 用户更新数据
            db: 数据库会话

        Returns:
            更新后的用户对象
        """
        from backend.services.auth_service import AuthService

        user = UserService.get_user_by_id(user_id, db)
        if not user:
            raise ValueError(f"用户 ID {user_id} 不存在")

        # 更新字段
        update_data = user_data.model_dump(exclude_unset=True)

        # 如果更新 alias，检查是否重复
        if "alias" in update_data and update_data["alias"] != user.alias:
            existing_user = db.query(User).filter(User.alias == update_data["alias"]).first()
            if existing_user:
                raise ValueError(f"用户别名 {update_data['alias']} 已存在")

        # 处理密码重置
        if update_data.get("reset_password"):
            user.password_hash = None
            logger.info(f"管理员重置用户 {user.alias} (ID: {user_id}) 的密码")

        # 处理密码修改
        elif "password" in update_data and update_data["password"]:
            user.password_hash = AuthService.hash_password(update_data["password"])
            logger.info(f"管理员修改用户 {user.alias} (ID: {user_id}) 的密码")

        # 更新其他字段（排除密码相关字段）
        excluded_fields = {"password", "reset_password", "allow_unverified_email"}
        if "email" in update_data:
            next_email = update_data["email"]
            next_email = str(next_email) if next_email is not None else None
            if next_email != user.email:
                UserService._clear_email_verification(user)
            update_data["email"] = next_email

        for key, value in update_data.items():
            if key not in excluded_fields:
                setattr(user, key, value)

        user.updated_at = datetime.now()
        db.commit()
        db.refresh(user)

        logger.info(f"更新用户成功: {user.alias} (ID: {user.id})")
        return user

    @staticmethod
    def update_user_profile(user_id: int, profile_data: UserUpdateProfile, db: Session) -> User:
        """
        更新用户个人信息（别名、邮箱和密码）

        Args:
            user_id: 用户 ID
            profile_data: 个人信息更新数据
            db: 数据库会话

        Returns:
            更新后的用户对象
        """
        from backend.services.auth_service import AuthService

        user = UserService.get_user_by_id(user_id, db)
        if not user:
            raise ValueError(f"用户 ID {user_id} 不存在")

        update_data = profile_data.model_dump(exclude_unset=True)

        # 更新别名
        if "alias" in update_data and update_data["alias"] != user.alias:
            existing_user = db.query(User).filter(User.alias == update_data["alias"]).first()
            if existing_user:
                raise ValueError(f"用户别名 {update_data['alias']} 已存在")
            user.alias = update_data["alias"]
            logger.info(f"用户 ID {user_id} 别名更新: {user.alias}")

        # 邮箱必须走 /users/me/email 的验证码流程，不能从普通资料保存绕过。
        if "email" in update_data:
            next_email = str(update_data["email"]) if update_data["email"] is not None else None
            if next_email != user.email:
                raise ValueError("邮箱修改需要先完成验证码验证")

        # 更新密码
        if "new_password" in update_data and update_data["new_password"]:
            # 如果用户已设置密码，需要验证当前密码
            if user.password_hash:
                if "current_password" not in update_data or not update_data["current_password"]:
                    raise ValueError("修改密码时必须提供当前密码")

                # 验证当前密码
                if not AuthService.verify_password(
                    update_data["current_password"], user.password_hash
                ):
                    raise ValueError("当前密码错误")

            # 设置新密码
            user.password_hash = AuthService.hash_password(update_data["new_password"])
            logger.info(f"用户 ID {user_id} 密码已更新")

        user.updated_at = datetime.now()
        db.commit()
        db.refresh(user)

        logger.info(f"✅ 更新用户个人信息成功: {user.alias} (ID: {user.id})")
        return user

    @staticmethod
    def set_email_for_verification(user_id: int, email: str, db: Session) -> User:
        from backend.services.email_service import EmailService

        user = UserService.get_user_by_id(user_id, db)
        if not user:
            raise ValueError(f"用户 ID {user_id} 不存在")

        normalized_email = UserService._normalize_email(email)
        if normalized_email != user.email:
            user.email = normalized_email
            UserService._clear_email_verification(user)

        code = f"{secrets.randbelow(1_000_000):06d}"
        code_hash = bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user.email_verification_code_hash = code_hash
        user.email_verification_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        user.updated_at = datetime.now(timezone.utc)

        sent = EmailService.send_email_verification_code(normalized_email, user.alias, code)
        if not sent:
            db.rollback()
            raise ValueError("验证码邮件发送失败，请检查邮件配置后重试")

        db.commit()
        db.refresh(user)
        logger.info("用户 ID %s 已请求邮箱验证码: %s", user_id, normalized_email)
        return user

    @staticmethod
    def verify_email_code(user_id: int, code: str, db: Session) -> User:
        user = UserService.get_user_by_id(user_id, db)
        if not user:
            raise ValueError(f"用户 ID {user_id} 不存在")

        code_hash = user.email_verification_code_hash
        expires_at = user.email_verification_expires_at
        now = datetime.now(timezone.utc)
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if not code_hash or not expires_at or expires_at <= now:
            raise ValueError("验证码无效或已过期")

        if not bcrypt.checkpw(code.encode("utf-8"), code_hash.encode("utf-8")):
            raise ValueError("验证码无效或已过期")

        user.email_verified_at = now
        user.email_verification_code_hash = None
        user.email_verification_expires_at = None
        user.updated_at = now
        db.commit()
        db.refresh(user)
        logger.info("用户 ID %s 邮箱验证成功: %s", user_id, user.email)
        return user

    @staticmethod
    def delete_user(user_id: int, db: Session) -> bool:
        """
        删除用户

        Args:
            user_id: 用户 ID
            db: 数据库会话

        Returns:
            是否删除成功
        """
        user = UserService.get_user_by_id(user_id, db)
        if not user:
            raise ValueError(f"用户 ID {user_id} 不存在")

        alias = user.alias
        db.delete(user)
        db.commit()

        logger.info(f"删除用户成功: {alias} (ID: {user_id})")
        return True

    @staticmethod
    def get_users_by_role(role: str, db: Session) -> List[User]:
        """
        获取指定角色的用户

        Args:
            role: 角色（user/admin）
            db: 数据库会话

        Returns:
            用户列表
        """
        return db.query(User).filter(User.role == role).all()

    @staticmethod
    def count_users(db: Session, role: Optional[str] = None) -> int:
        """
        统计用户数量

        Args:
            db: 数据库会话
            role: 角色过滤（可选）

        Returns:
            用户数量
        """
        query = db.query(User)
        if role:
            query = query.filter(User.role == role)
        return query.count()
