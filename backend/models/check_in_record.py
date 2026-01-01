from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.models.database import Base


class CheckInRecord(Base):
    """打卡记录模型"""

    __tablename__ = "check_in_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("check_in_tasks.id", ondelete="CASCADE"), nullable=False, index=True, comment="任务 ID")
    status = Column(String(20), nullable=False, index=True, comment="状态: success/failure/out_of_time/unknown/pending")
    response_text = Column(Text, default="", comment="响应文本")
    error_message = Column(Text, default="", comment="错误信息")
    location = Column(Text, default="{}", comment="位置信息 JSON")
    trigger_type = Column(String(50), default="scheduled", comment="触发类型: scheduled/manual/admin")
    check_in_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, comment="打卡时间（UTC）")

    # 关联任务
    task = relationship("CheckInTask", back_populates="check_in_records")

    # 添加复合索引：加速常见查询
    __table_args__ = (
        Index('ix_record_task_time', 'task_id', 'check_in_time'),  # 获取任务的打卡记录(按时间排序)
        Index('ix_record_status_time', 'status', 'check_in_time'),  # 按状态和时间查询
    )

    def __repr__(self):
        return f"<CheckInRecord(id={self.id}, task_id={self.task_id}, status={self.status})>"
