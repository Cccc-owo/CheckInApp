from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.models.database import Base

if TYPE_CHECKING:
    from backend.models.check_in_record import CheckInRecord
    from backend.models.user import User


class CheckInTask(Base):
    """打卡任务模型"""

    __tablename__ = "check_in_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        comment="用户 ID",
    )
    thread_id: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
        nullable=True,
        comment="接龙项目 ID",
    )
    payload_config: Mapped[str] = mapped_column(
        Text,
        default="{}",
        nullable=False,
        comment="完整的 payload 配置 JSON（从模板生成，包含 ThreadId 和所有字段）",
    )
    name: Mapped[str] = mapped_column(String(100), default="", comment="任务名称（用户自定义）")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否启用自动打卡（不影响手动打卡）"
    )
    cron_expression: Mapped[str | None] = mapped_column(
        String(100),
        default="0 20 * * *",
        nullable=True,
        comment="Crontab 表达式（NULL 表示禁用自动打卡，否则按表达式执行）",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), comment="更新时间"
    )

    # 关联用户
    user: Mapped["User"] = relationship(back_populates="tasks")

    # 关联打卡记录
    check_in_records: Mapped[list["CheckInRecord"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

    # 添加索引：加速查询
    __table_args__ = (
        Index("ix_task_user_active", "user_id", "is_active"),
        UniqueConstraint("user_id", "thread_id", name="uq_task_user_thread_id"),
        Index("ix_task_cron", "cron_expression"),  # 加速查询启用了定时打卡的任务
    )

    def __repr__(self):
        return f"<CheckInTask(id={self.id}, user_id={self.user_id}, name={self.name}, cron={self.cron_expression})>"

    @property
    def is_scheduled_enabled(self) -> bool:
        """判断是否启用了自动打卡（is_active 为 True 且 cron_expression 不为空）"""
        return bool(self.is_active) and bool(self.cron_expression)
