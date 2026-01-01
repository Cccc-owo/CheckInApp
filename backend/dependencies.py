from datetime import datetime
from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from backend.models import get_db, User


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前用户
    从 Authorization header 中验证 Token 并返回用户
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 移除 "Bearer " 前缀（如果存在）
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization

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
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token 已过期，请重新登录",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except ValueError:
            pass  # jwt_exp 格式不正确，跳过验证

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
