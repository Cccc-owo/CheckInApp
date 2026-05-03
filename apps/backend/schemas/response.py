"""
统一的 API 响应 Schema
"""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel


T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """统一成功响应"""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None


class ErrorDetail(BaseModel):
    """错误详情"""
    code: str
    message: str
    field: Optional[str] = None  # 字段验证错误时使用


class ErrorResponse(BaseModel):
    """统一错误响应"""
    success: bool = False
    error: ErrorDetail
