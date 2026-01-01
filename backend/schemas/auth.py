from typing import Optional
from pydantic import BaseModel, Field


class QRCodeRequest(BaseModel):
    """请求二维码 Schema"""
    alias: str = Field(..., description="用户别名")


class QRCodeResponse(BaseModel):
    """二维码响应 Schema"""
    session_id: str = Field(..., description="会话 ID")
    qrcode_image: str = Field(..., description="二维码 Base64 图片")


class QRCodeStatusResponse(BaseModel):
    """二维码状态响应 Schema"""
    status: str = Field(..., description="状态: pending/waiting_scan/success/error")
    message: Optional[str] = Field(None, description="状态消息")
    user_id: Optional[int] = Field(None, description="用户 ID (扫码成功时返回)")
    authorization: Optional[str] = Field(None, description="Token (扫码成功时返回)")
    qrcode_image: Optional[str] = Field(None, description="二维码 Base64 图片（等待扫描时返回）")


class TokenVerifyRequest(BaseModel):
    """Token 验证请求 Schema"""
    authorization: str = Field(..., description="Token")


class TokenVerifyResponse(BaseModel):
    """Token 验证响应 Schema"""
    is_valid: bool = Field(..., description="Token 是否有效")
    message: str = Field(..., description="验证消息")
    user_id: Optional[int] = Field(None, description="用户 ID")


class AliasLoginRequest(BaseModel):
    """别名+密码登录请求 Schema"""
    alias: str = Field(..., min_length=2, max_length=50, description="用户别名")
    password: str = Field(..., min_length=6, description="密码")


class AliasLoginResponse(BaseModel):
    """别名+密码登录响应 Schema"""
    success: bool = Field(..., description="登录是否成功")
    message: str = Field(..., description="登录消息")
    user_id: Optional[int] = Field(None, description="用户 ID")
    authorization: Optional[str] = Field(None, description="Token")
    alias: Optional[str] = Field(None, description="用户别名")
