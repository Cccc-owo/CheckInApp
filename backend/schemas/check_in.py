from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ManualCheckInRequest(BaseModel):
    """手动打卡请求 Schema（已废弃，现在使用路径参数 task_id）"""
    task_id: Optional[int] = Field(None, description="任务 ID")


class BatchCheckInRequest(BaseModel):
    """批量打卡请求 Schema"""
    task_ids: list[int] = Field(..., description="任务 ID 列表")


class CheckInRecordResponse(BaseModel):
    """打卡记录响应 Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    status: str
    response_text: str
    error_message: str
    location: str
    trigger_type: str
    check_in_time: datetime  # Pydantic v2 自动序列化为 ISO 8601 格式

    # 新增字段：用户和任务信息（用于管理员查看）
    user_id: Optional[int] = Field(None, description="用户 ID")
    user_email: Optional[str] = Field(None, description="用户邮箱")
    task_name: Optional[str] = Field(None, description="任务名称")
    thread_id: Optional[str] = Field(None, description="接龙 ID")


class CheckInRecordWithTaskInfo(CheckInRecordResponse):
    """带任务信息的打卡记录响应 Schema"""
    task_name: str
    task_signature: str
    user_alias: str


class CheckInResultResponse(BaseModel):
    """打卡结果响应 Schema"""
    success: bool
    message: str
    record_id: Optional[int] = None
    error: Optional[str] = None
