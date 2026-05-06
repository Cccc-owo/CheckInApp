from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.models import get_db, User
from backend.schemas.user import (
    AdminApprovalResponse,
    UserCreate,
    UserUpdate,
    UserResponse,
    TokenStatus,
    UserUpdateProfile,
    UserEmailUpdate,
    UserEmailVerify,
)
from backend.schemas.task import TaskResponse
from backend.services.user_service import UserService
from backend.services.task_service import TaskService
from backend.services.admin_service import AdminService
from backend.dependencies import get_current_user, get_current_admin_user
from backend.exceptions import (
    AuthorizationError,
    BaseAPIException,
    ResourceNotFoundError,
    ValidationError,
)

router = APIRouter()
EXPECTED_API_EXCEPTIONS = (BaseAPIException, HTTPException)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户（管理员）",
)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    创建用户（需要管理员权限）

    - **alias**: 用户别名（用于登录）
    - **role**: 角色（可选，默认 "user"）
    - **email**: 邮箱地址（可选）
    """
    try:
        user = UserService.create_user(user_data, db)
        return user
    except ValueError as e:
        raise ValidationError(str(e))
    except EXPECTED_API_EXCEPTIONS:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建用户失败: {str(e)}"
        )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户的信息
    """
    # 创建响应对象，手动添加 has_password 字段
    user_dict = {
        "id": current_user.id,
        "alias": current_user.alias,
        "role": current_user.role,
        "is_approved": current_user.is_approved,
        "jwt_exp": current_user.jwt_exp,
        "email": current_user.email,
        "email_verified": current_user.email_verified,
        "email_verified_at": current_user.email_verified_at,
        "has_password": bool(current_user.password_hash),
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
    }
    return user_dict


@router.get("/me/status", response_model=dict, summary="获取当前用户审批状态")
async def get_user_status(current_user: User = Depends(get_current_user)):
    """
    获取用户审批状态（不要求审批通过）
    """
    return {
        "user_id": current_user.id,
        "alias": current_user.alias,
        "is_approved": current_user.is_approved,
        "email": current_user.email,
        "email_verified": current_user.email_verified,
        "email_verified_at": current_user.email_verified_at.isoformat()
        if current_user.email_verified_at
        else None,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }


@router.put("/me/email", response_model=UserResponse, summary="设置邮箱并发送验证码")
async def set_current_user_email(
    email_data: UserEmailUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    设置当前用户邮箱并发送验证码（不要求账户已审批）。
    """
    try:
        return UserService.set_email_for_verification(current_user.id, str(email_data.email), db)
    except ValueError as e:
        raise ValidationError(str(e))
    except EXPECTED_API_EXCEPTIONS:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"设置邮箱失败: {str(e)}"
        )


@router.post("/me/email/verify", response_model=UserResponse, summary="验证当前用户邮箱")
async def verify_current_user_email(
    verify_data: UserEmailVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    校验当前用户邮箱验证码（不要求账户已审批）。
    """
    try:
        return UserService.verify_email_code(current_user.id, verify_data.code, db)
    except ValueError as e:
        raise ValidationError(str(e))
    except EXPECTED_API_EXCEPTIONS:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"验证邮箱失败: {str(e)}"
        )


@router.put("/me/profile", response_model=UserResponse, summary="更新个人信息")
async def update_current_user_profile(
    profile_data: UserUpdateProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新当前用户的个人信息

    - **alias**: 新别名（可选）
    - **current_password**: 当前密码（修改密码时必填）
    - **new_password**: 新密码（可选）

    注意：
    - 修改密码时必须提供 current_password 和 new_password
    - 首次设置密码时不需要 current_password
    """
    try:
        user = UserService.update_user_profile(current_user.id, profile_data, db)
        return user
    except ValueError as e:
        raise ValidationError(str(e))
    except EXPECTED_API_EXCEPTIONS:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新个人信息失败: {str(e)}"
        )


@router.get("/me/token_status", response_model=TokenStatus, summary="获取当前用户打卡 Token 状态")
async def get_current_user_token_status(current_user: User = Depends(get_current_user)):
    """
    获取当前用户的打卡 Token 状态（authorization token，非 JWT）

    注意：此接口检查的是打卡业务 token，不是网站登录 JWT token
    """
    from backend.services.auth_service import AuthService

    # 使用统一的验证方法
    result = AuthService.verify_checkin_authorization(current_user)

    return {
        "is_valid": result["is_valid"],
        "jwt_exp": current_user.jwt_exp,
        "expires_at": result.get("expires_at"),
        "days_until_expiry": result.get("days_remaining"),
        "expiring_soon": result.get("expiring_soon", False),
    }


@router.get("/me/tasks", response_model=List[TaskResponse], summary="获取当前用户的任务列表")
async def get_current_user_tasks(
    include_inactive: bool = Query(True, description="是否包含未启用的任务"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前登录用户的所有打卡任务

    - **include_inactive**: 是否包含未启用的任务（默认 True）
    """
    try:
        tasks = TaskService.get_user_tasks(current_user.id, db, include_inactive)
        return tasks
    except EXPECTED_API_EXCEPTIONS:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取任务列表失败: {str(e)}"
        )


@router.get("", response_model=List[UserResponse], summary="获取所有用户（管理员）")
async def get_all_users(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=500, description="限制记录数"),
    search: Optional[str] = Query(None, description="搜索关键词（alias）"),
    role: Optional[str] = Query(None, description="过滤角色 (user/admin)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    获取所有用户列表（需要管理员权限）

    - **skip**: 跳过记录数
    - **limit**: 限制记录数
    - **search**: 搜索关键词（模糊匹配 alias）
    - **role**: 过滤角色（user/admin）
    """
    try:
        users = UserService.get_all_users(db, skip, limit, search, role)
        return users
    except EXPECTED_API_EXCEPTIONS:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取用户列表失败: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse, summary="获取指定用户")
async def get_user(
    user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    获取指定用户信息

    - 普通用户只能查看自己的信息
    - 管理员可以查看所有用户信息
    """
    # 检查权限
    if current_user.role != "admin" and current_user.id != user_id:
        raise AuthorizationError("权限不足，只能查看自己的信息")

    user = UserService.get_user_by_id(user_id, db)
    if not user:
        raise ResourceNotFoundError(f"用户 ID {user_id} 不存在")

    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse | AdminApprovalResponse,
    summary="更新用户信息",
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新用户信息

    - 普通用户只能更新自己的部分信息（不包括 role）
    - 管理员可以更新所有用户的所有信息
    """
    # 检查权限
    if current_user.role != "admin":
        if current_user.id != user_id:
            raise AuthorizationError("权限不足，只能更新自己的信息")
        # 普通用户不能修改 role
        if user_data.role is not None:
            raise AuthorizationError("普通用户不能修改角色")

    try:
        # 获取更新前的用户状态
        old_user = UserService.get_user_by_id(user_id, db)
        if not old_user:
            raise ResourceNotFoundError(f"用户 ID {user_id} 不存在")

        # 保存更新前的审批状态 (先读取后转换为 Python bool)
        old_approved_value = old_user.is_approved
        was_approved_before = True if old_approved_value else False
        is_admin = current_user.role == "admin"
        update_data = user_data.model_dump(exclude_unset=True)
        will_approve = (
            is_admin and (not was_approved_before) and update_data.get("is_approved") is True
        )
        if will_approve:
            approval_warning = AdminService.approval_warning_for_user(
                old_user,
                allow_unverified_email=user_data.allow_unverified_email,
                next_email=str(update_data["email"]) if "email" in update_data else None,
            )
            if approval_warning and approval_warning.get("requires_override"):
                return approval_warning

        # 更新用户信息
        user = UserService.update_user(user_id, user_data, db)

        # 检查是否需要发送审批通过邮件
        new_approved_value = user.is_approved
        is_approved_now = True if new_approved_value else False

        needs_notification = is_admin and (not was_approved_before) and is_approved_now

        if needs_notification:
            try:
                from backend.services.email_service import EmailService

                EmailService.notify_user_approved(user)
            except Exception as e:
                # 邮件发送失败不影响审批操作
                import logging

                logging.getLogger(__name__).error(f"发送审批通过邮件失败: {e}")

        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except EXPECTED_API_EXCEPTIONS:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新用户失败: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除用户（管理员）")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    删除用户（需要管理员权限）
    """
    try:
        UserService.delete_user(user_id, db)
        return None
    except ValueError as e:
        raise ResourceNotFoundError(str(e))
    except EXPECTED_API_EXCEPTIONS:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除用户失败: {str(e)}"
        )
