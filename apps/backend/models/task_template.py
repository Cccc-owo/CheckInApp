from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.models.database import Base


class TaskTemplate(Base):
    """打卡任务模板"""

    __tablename__ = "task_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="模板名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="模板描述")

    # 父模板 ID（用于继承）
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("task_templates.id", ondelete="SET NULL"),
        nullable=True,
        comment="父模板 ID",
    )

    # 字段配置（JSON 格式）
    field_config: Mapped[str] = mapped_column(Text, nullable=False, comment="字段配置（JSON）")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), comment="更新时间"
    )

    # 自引用关系：父模板和子模板
    parent: Mapped[TaskTemplate | None] = relationship(
        remote_side="TaskTemplate.id", back_populates="children"
    )
    children: Mapped[list[TaskTemplate]] = relationship(back_populates="parent")

    def __repr__(self):
        return f"<TaskTemplate(id={self.id}, name='{self.name}', is_active={self.is_active})>"
