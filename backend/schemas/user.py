from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserBase(BaseModel):
    """用户基础 Schema"""
    alias: str = Field(..., min_length=2, max_length=50, description="用户别名（用于登录）")


class UserCreate(UserBase):
    """创建用户 Schema（管理员手动创建，只需要别名）"""
    role: Optional[str] = Field("user", description="角色: user/admin")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    is_approved: Optional[bool] = Field(True, description="是否已审批（默认已审批）")


class UserUpdate(BaseModel):
    """更新用户 Schema（管理员编辑用户）"""
    alias: Optional[str] = Field(None, min_length=2, max_length=50, description="用户别名")
    role: Optional[str] = None
    is_approved: Optional[bool] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6, description="新密码（可选，留空表示不修改）")
    reset_password: Optional[bool] = Field(False, description="是否清空密码")


class UserUpdateProfile(BaseModel):
    """用户更新个人信息 Schema"""
    alias: Optional[str] = Field(None, min_length=2, max_length=50, description="新别名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    current_password: Optional[str] = Field(None, min_length=6, description="当前密码（修改密码时必填）")
    new_password: Optional[str] = Field(None, min_length=6, description="新密码")


class UserResponse(BaseModel):
    """用户响应 Schema"""
    id: int
    alias: str
    role: str
    is_approved: bool
    jwt_exp: str
    email: Optional[EmailStr] = None
    has_password: bool = False  # 是否已设置密码
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


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
