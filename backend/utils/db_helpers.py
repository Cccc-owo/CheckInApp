"""
数据库操作辅助函数

提供统一的资源查询、权限验证等通用功能
"""
from typing import TypeVar, Type, Optional, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

T = TypeVar('T')


def get_or_404(
    model: Type[T],
    model_id: int,
    db: Session,
    error_message: Optional[str] = None
) -> T:
    """
    查询资源，不存在则抛出 404

    Args:
        model: SQLAlchemy 模型类
        model_id: 资源 ID
        db: 数据库会话
        error_message: 自定义错误消息

    Returns:
        查询到的资源对象

    Raises:
        HTTPException: 404 资源不存在
    """
    obj = db.query(model).filter(model.id == model_id).first()
    if not obj:
        default_message = f"{model.__name__}不存在"
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_message or default_message
        )
    return obj


def get_owned_or_403(
    model: Type[T],
    model_id: int,
    user_id: int,
    db: Session,
    error_message: Optional[str] = None
) -> T:
    """
    查询资源并验证归属，否则抛出 403

    Args:
        model: SQLAlchemy 模型类（必须有 user_id 字段）
        model_id: 资源 ID
        user_id: 当前用户 ID
        db: 数据库会话
        error_message: 自定义错误消息

    Returns:
        查询到的资源对象

    Raises:
        HTTPException: 403 无权访问此资源
    """
    obj = db.query(model).filter(
        model.id == model_id,
        model.user_id == user_id
    ).first()

    if not obj:
        # 先检查资源是否存在
        exists = db.query(model).filter(model.id == model_id).first()
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__}不存在"
            )
        # 资源存在但不属于当前用户
        default_message = f"无权访问此{model.__name__}"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_message or default_message
        )

    return obj


def get_by_field_or_404(
    model: Type[T],
    field_name: str,
    field_value: Any,
    db: Session,
    error_message: Optional[str] = None
) -> T:
    """
    根据字段查询资源，不存在则抛出 404

    Args:
        model: SQLAlchemy 模型类
        field_name: 字段名
        field_value: 字段值
        db: 数据库会话
        error_message: 自定义错误消息

    Returns:
        查询到的资源对象

    Raises:
        HTTPException: 404 资源不存在
    """
    obj = db.query(model).filter(
        getattr(model, field_name) == field_value
    ).first()

    if not obj:
        default_message = f"{model.__name__}不存在"
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_message or default_message
        )
    return obj
