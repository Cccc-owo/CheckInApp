from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """用户基础 Schema"""

    alias: str = Field(..., min_length=2, max_length=50, description="用户别名（用于登录）")


class UserCreate(UserBase):
    """创建用户 Schema（管理员手动创建，只需要别名）"""

    role: Optional[str] = Field("user", description="角色: user/admin")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    password: Optional[str] = Field(None, min_length=6, description="初始密码（可选）")
    is_approved: Optional[bool] = Field(True, description="是否已审批（默认已审批）")


class UserUpdate(BaseModel):
    """更新用户 Schema（管理员编辑用户）"""

    alias: Optional[str] = Field(None, min_length=2, max_length=50, description="用户别名")
    role: Optional[str] = None
    is_approved: Optional[bool] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(
        None, min_length=6, description="新密码（可选，留空表示不修改）"
    )
    reset_password: Optional[bool] = Field(False, description="是否清空密码")
    allow_unverified_email: bool = Field(False, description="是否允许审批未验证邮箱用户")


class UserUpdateProfile(BaseModel):
    """用户更新个人信息 Schema"""

    alias: Optional[str] = Field(None, min_length=2, max_length=50, description="新别名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    current_password: Optional[str] = Field(
        None, min_length=6, description="当前密码（修改密码时必填）"
    )
    new_password: Optional[str] = Field(None, min_length=6, description="新密码")


class UserEmailUpdate(BaseModel):
    """用户设置邮箱并请求验证码 Schema"""

    email: EmailStr = Field(..., description="邮箱地址")


class UserEmailVerify(BaseModel):
    """用户邮箱验证码校验 Schema"""

    code: str = Field(..., min_length=4, max_length=12, description="邮箱验证码")


class AdminApprovalResponse(BaseModel):
    """管理员审批响应 Schema"""

    success: bool
    message: str
    user_id: Optional[int] = None
    requires_override: bool = False
    warning_code: Optional[str] = None


class UserResponse(BaseModel):
    """用户响应 Schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    alias: str
    role: str
    is_approved: bool
    jwt_exp: str
    email: Optional[EmailStr] = None
    email_verified: bool = False
    email_verified_at: Optional[datetime] = None
    has_password: bool = False  # 是否已设置密码
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserWithToken(UserResponse):
    """带 Token 的用户响应 Schema"""

    authorization: Optional[str] = None


class TokenStatus(BaseModel):
    """Token 状态 Schema"""

    is_valid: bool
    jwt_exp: str
    expires_at: Optional[int] = None  # Unix 时间戳（秒）
    days_until_expiry: Optional[int] = None
    expiring_soon: bool = False  # 是否即将过期（30分钟内）
