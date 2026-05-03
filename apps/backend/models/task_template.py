from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.models.database import Base


class TaskTemplate(Base):
    """打卡任务模板"""
    __tablename__ = "task_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(Text, nullable=True, comment="模板描述")

    # 父模板 ID（用于继承）
    parent_id = Column(Integer, ForeignKey("task_templates.id", ondelete="SET NULL"), nullable=True, comment="父模板 ID")

    # 字段配置（JSON 格式）
    field_config = Column(Text, nullable=False, comment="字段配置（JSON）")

    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    # 自引用关系：父模板和子模板
    parent = relationship("TaskTemplate", remote_side=[id], backref="children")

    def __repr__(self):
        return f"<TaskTemplate(id={self.id}, name='{self.name}', is_active={self.is_active})>"
