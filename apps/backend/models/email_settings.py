from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.models.database import Base


class EmailNotificationSettings(Base):
    """系统邮件配置与通知策略设置。"""

    __tablename__ = "email_notification_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    smtp_server: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    smtp_port: Mapped[int] = mapped_column(Integer, default=465, nullable=False)
    smtp_sender_email: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    smtp_sender_password: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    smtp_use_ssl: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_token_expiring: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_check_in_success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), comment="更新时间"
    )
