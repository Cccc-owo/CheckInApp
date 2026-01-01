from datetime import datetime
from typing import Optional
import json
from pydantic import BaseModel, Field, field_validator


class TaskBase(BaseModel):
    """打卡任务基础 Schema"""
    payload_config: str = Field(..., description="完整的 payload 配置 JSON（包含 ThreadId 和所有字段）")
    name: Optional[str] = Field("", max_length=100, description="任务名称（用户自定义）")
    is_active: Optional[bool] = Field(True, description="是否启用自动打卡")

    @field_validator('payload_config')
    @classmethod
    def validate_payload_config(cls, v: str) -> str:
        """
        验证 payload_config 是否为有效的 JSON，并且包含必需的 ThreadId 字段
        """
        if not v or not v.strip():
            raise ValueError("payload_config 不能为空")

        try:
            payload = json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"payload_config 必须是有效的 JSON 格式: {str(e)}")

        # 检查是否为字典类型
        if not isinstance(payload, dict):
            raise ValueError("payload_config 必须是 JSON 对象（字典）")

        # 检查必需字段 ThreadId
        if 'ThreadId' not in payload:
            raise ValueError("payload_config 必须包含 ThreadId 字段")

        thread_id = payload.get('ThreadId')
        if not thread_id or not str(thread_id).strip():
            raise ValueError("ThreadId 不能为空")

        return v


class TaskCreate(TaskBase):
    """创建打卡任务 Schema"""
    cron_expression: Optional[str] = Field(
        None,
        max_length=100,
        description="Crontab 表达式（例如 '0 20 * * *' 表示每天 20:00）。NULL 表示禁用定时打卡"
    )

    @field_validator('cron_expression')
    @classmethod
    def validate_cron_expression(cls, v: Optional[str]) -> Optional[str]:
        """验证 Crontab 表达式格式"""
        if v is None:
            return v  # NULL 允许（表示禁用定时打卡）

        if not v.strip():
            raise ValueError("cron_expression 不能为空字符串，应该使用 NULL")

        try:
            from croniter import croniter
            if not croniter.is_valid(v):
                raise ValueError(f"无效的 Crontab 表达式: '{v}'")
        except Exception as e:
            raise ValueError(f"Crontab 表达式验证失败: {str(e)}")

        return v


class TaskUpdate(BaseModel):
    """更新打卡任务 Schema"""
    payload_config: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None
    cron_expression: Optional[str] = Field(
        None,
        max_length=100,
        description="Crontab 表达式。NULL 表示禁用定时打卡"
    )

    @field_validator('payload_config')
    @classmethod
    def validate_payload_config(cls, v: Optional[str]) -> Optional[str]:
        """
        验证 payload_config 是否为有效的 JSON（如果提供的话）
        """
        if v is None:
            return v

        if not v.strip():
            raise ValueError("payload_config 不能为空字符串")

        try:
            payload = json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"payload_config 必须是有效的 JSON 格式: {str(e)}")

        # 检查是否为字典类型
        if not isinstance(payload, dict):
            raise ValueError("payload_config 必须是 JSON 对象（字典）")

        # 检查必需字段 ThreadId
        if 'ThreadId' not in payload:
            raise ValueError("payload_config 必须包含 ThreadId 字段")

        thread_id = payload.get('ThreadId')
        if not thread_id or not str(thread_id).strip():
            raise ValueError("ThreadId 不能为空")

        return v

    @field_validator('cron_expression')
    @classmethod
    def validate_cron_expression(cls, v: Optional[str]) -> Optional[str]:
        """验证 Crontab 表达式（与 TaskCreate 相同）"""
        if v is None:
            return v

        if not v.strip():
            raise ValueError("cron_expression 不能为空字符串，应该使用 NULL")

        try:
            from croniter import croniter
            if not croniter.is_valid(v):
                raise ValueError(f"无效的 Crontab 表达式: '{v}'")
        except Exception as e:
            raise ValueError(f"Crontab 表达式验证失败: {str(e)}")

        return v


class TaskResponse(TaskBase):
    """打卡任务响应 Schema"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    cron_expression: Optional[str] = Field(
        None,
        description="当前 Crontab 表达式（NULL = 禁用定时打卡）"
    )
    is_scheduled_enabled: Optional[bool] = Field(
        None,
        description="是否启用了定时打卡"
    )

    # 新增字段：最后一次打卡信息
    last_check_in_time: Optional[datetime] = Field(None, description="最后一次打卡时间")
    last_check_in_status: Optional[str] = Field(None, description="最后一次打卡状态")
    thread_id: Optional[str] = Field(None, description="接龙 ID（从 payload_config 中提取）")

    class Config:
        from_attributes = True
