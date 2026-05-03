from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.models.database import Base


class User(Base):
    """用户模型 - 账户信息"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    jwt_sub = Column(String(200), unique=True, nullable=True, index=True, comment="QQ 扫码登录的唯一用户标识（注册时为空）")
    alias = Column(String(50), unique=True, nullable=False, index=True, comment="用户别名（用于登录）")
    email = Column(String(100), nullable=True, comment="用户邮箱（用于接收通知）")
    password_hash = Column(String(200), nullable=True, comment="密码哈希（bcrypt加密）")
    authorization = Column(Text, nullable=True, comment="当前有效的 QQ Token")
    jwt_exp = Column(String(20), default="0", comment="Token 过期时间戳")
    token_expiring_notified = Column(Boolean, default=False, nullable=False, comment="Token 即将过期提醒是否已发送（过期前30分钟）")
    token_expired_notified = Column(Boolean, default=False, nullable=False, comment="Token 已过期提醒是否已发送（过期后30分钟内）")
    role = Column(String(20), default="user", index=True, comment="角色: user/admin")
    is_approved = Column(Boolean, default=False, index=True, comment="是否已通过管理员审批")

    # 账户锁定相关字段
    failed_login_attempts = Column(Integer, default=0, nullable=False, comment="连续登录失败次数")
    locked_until = Column(DateTime(timezone=True), nullable=True, comment="账户锁定到期时间")
    last_failed_login = Column(DateTime(timezone=True), nullable=True, comment="最后一次登录失败时间")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    # 关联打卡任务
    tasks = relationship("CheckInTask", back_populates="user", cascade="all, delete-orphan")

    # 添加复合索引：加速审批管理查询
    __table_args__ = (
        Index('ix_user_role_approved', 'role', 'is_approved'),  # 管理员查询待审批用户
    )

    def __repr__(self):
        return f"<User(id={self.id}, alias={self.alias}, jwt_sub={self.jwt_sub}, role={self.role})>"

    @property
    def is_admin(self) -> bool:
        """判断是否为管理员"""
        return self.role == "admin"
