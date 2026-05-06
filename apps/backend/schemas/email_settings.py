from __future__ import annotations

from datetime import datetime

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EmailNotificationSettingsBase(BaseModel):
    smtp_server: str = Field("", max_length=255, description="SMTP 服务器地址")
    smtp_port: int = Field(465, ge=1, le=65535, description="SMTP 端口")
    smtp_sender_email: str = Field("", max_length=255, description="发件邮箱")
    smtp_use_ssl: bool = Field(True, description="是否使用 SMTP SSL")
    notify_token_expiring: bool = Field(True, description="是否通知 Token 即将过期")
    notify_check_in_success: bool = Field(True, description="是否通知打卡成功")
    require_admin_approval_for_registration: bool = Field(
        True, description="新注册是否需要管理员审批"
    )
    warn_unverified_email_before_approval: bool = Field(
        True, description="审批未验证邮箱用户时是否警告"
    )

    @field_validator("smtp_server", "smtp_sender_email", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("smtp_sender_email")
    @classmethod
    def validate_sender_email(cls, value: str) -> str:
        if value == "":
            return value
        try:
            return str(validate_email(value, check_deliverability=False).normalized)
        except EmailNotValidError as exc:
            raise ValueError("发件邮箱格式无效") from exc


class EmailNotificationSettingsUpdate(EmailNotificationSettingsBase):
    smtp_sender_password: str | None = Field(
        None,
        max_length=500,
        description="新 SMTP 密码；省略表示保留现有值",
    )
    clear_smtp_sender_password: bool = Field(False, description="是否清空 SMTP 密码")

    @field_validator("smtp_sender_password")
    @classmethod
    def normalize_password(cls, value: str | None) -> str | None:
        if value == "":
            return None
        return value


class EmailNotificationSettingsResponse(EmailNotificationSettingsBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    has_smtp_sender_password: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
