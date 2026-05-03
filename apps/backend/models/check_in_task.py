from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.models.database import Base


class CheckInTask(Base):
    """打卡任务模型"""

    __tablename__ = "check_in_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户 ID")
    payload_config = Column(Text, default="{}", nullable=False, comment="完整的 payload 配置 JSON（从模板生成，包含 ThreadId 和所有字段）")
    name = Column(String(100), default="", comment="任务名称（用户自定义）")
    is_active = Column(Boolean, default=True, comment="是否启用自动打卡（不影响手动打卡）")
    cron_expression = Column(String(100), default="0 20 * * *", nullable=True, comment="Crontab 表达式（NULL 表示禁用自动打卡，否则按表达式执行）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    # 关联用户
    user = relationship("User", back_populates="tasks")

    # 关联打卡记录
    check_in_records = relationship("CheckInRecord", back_populates="task", cascade="all, delete-orphan")

    # 添加索引：加速查询
    __table_args__ = (
        Index('ix_task_user_active', 'user_id', 'is_active'),
        Index('ix_task_cron', 'cron_expression'),  # 加速查询启用了定时打卡的任务
    )

    def __repr__(self):
        return f"<CheckInTask(id={self.id}, user_id={self.user_id}, name={self.name}, cron={self.cron_expression})>"

    @property
    def is_scheduled_enabled(self) -> bool:
        """判断是否启用了自动打卡（is_active 为 True 且 cron_expression 不为空）"""
        return bool(self.is_active) and bool(self.cron_expression)
