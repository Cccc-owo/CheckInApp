from datetime import datetime
from typing import Optional
import logging
import jwt as pyjwt
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from backend.models import get_db, User
from backend.utils.jwt import JWTManager

logger = logging.getLogger(__name__)


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前用户（使用 JWT 认证）

    认证说明：
    1. 网站登录使用 JWT token（存储在前端，21天过期）
    2. 打卡业务使用 authorization token（存储在数据库 User.authorization）
    3. JWT 过期后需要重新登录，但打卡 token 过期不影响网站使用
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 移除 "Bearer " 前缀（如果存在）
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization

    try:
        # 验证 JWT token
        payload = JWTManager.verify_token(token)
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 格式错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 从数据库获取用户
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"认证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )


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
