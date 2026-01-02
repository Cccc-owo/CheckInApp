from datetime import datetime
from typing import Optional
import logging
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from backend.models import get_db, User

logger = logging.getLogger(__name__)


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前用户
    支持两种认证方式：
    1. Token 认证（QQ 扫码登录）
    2. User ID 认证（密码登录，格式：user_id:xxx）
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 移除 "Bearer " 前缀（如果存在）
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization

    # 检查是否为 user_id 格式的认证（用于密码登录）
    if token.startswith("user_id:"):
        user_id_str = token.replace("user_id:", "")
        try:
            user_id = int(user_id_str)
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 用户ID认证成功，检查是否设置了密码
            has_password = bool(user.password_hash)
            if not has_password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="该账户未设置密码，请使用扫码登录",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 密码登录的用户可以访问，无需检查 Token
            return user

        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的用户ID格式",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Token 认证（原有逻辑）
    # 从数据库查询用户
    user = db.query(User).filter(User.authorization == token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查 Token 是否过期
    if user.jwt_exp and user.jwt_exp != "0":
        try:
            exp_timestamp = int(user.jwt_exp)
            current_timestamp = int(datetime.now().timestamp())
            if current_timestamp > exp_timestamp:
                # 如果用户设置了密码，允许继续使用（Token 过期但不强制退出）
                has_password = bool(user.password_hash)
                if has_password:
                    # Token 过期但有密码，允许访问，但在响应头中添加警告
                    # 注意：这里不抛出异常，让用户继续使用
                    pass
                else:
                    # 没有密码的用户，Token 过期必须重新扫码登录
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token 已过期，请重新扫码登录",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
        except ValueError as e:
            # jwt_exp 格式不正确，记录警告后跳过 Token 过期验证
            logger.warning(f"用户 {user.id} ({user.alias}) 的 jwt_exp 格式不正确: {user.jwt_exp}, 错误: {e}")

    return user


async def require_approved_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    要求用户已通过审批
    """
    if not current_user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您的账户正在等待管理员审批，请耐心等待（24小时内）"
        )

    return current_user


async def get_current_admin_user(
    current_user: User = Depends(require_approved_user)
) -> User:
    """
    获取当前管理员用户
    验证用户是否具有管理员权限
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    return current_user


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    可选的用户认证
    如果提供了 Token 则返回用户，否则返回 None
    """
    if not authorization:
        return None

    try:
        return await get_current_user(authorization, db)
    except HTTPException:
        return None
