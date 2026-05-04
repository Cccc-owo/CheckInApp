from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.models.database import Base

if TYPE_CHECKING:
    from backend.models.check_in_task import CheckInTask


class User(Base):
    """用户模型 - 账户信息"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    jwt_sub: Mapped[str | None] = mapped_column(
        String(200),
        unique=True,
        nullable=True,
        index=True,
        comment="QQ 扫码登录的唯一用户标识（注册时为空）",
    )
    alias: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="用户别名（用于登录）"
    )
    email: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="用户邮箱（用于接收通知）"
    )
    password_hash: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="密码哈希（bcrypt加密）"
    )
    authorization: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="当前有效的 QQ Token"
    )
    jwt_exp: Mapped[str] = mapped_column(String(20), default="0", comment="Token 过期时间戳")
    token_expiring_notified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Token 即将过期提醒是否已发送（过期前30分钟）",
    )
    token_expired_notified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Token 已过期提醒是否已发送（过期后30分钟内）",
    )
    role: Mapped[str] = mapped_column(
        String(20), default="user", index=True, comment="角色: user/admin"
    )
    is_approved: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, comment="是否已通过管理员审批"
    )

    # 账户锁定相关字段
    failed_login_attempts: Mapped[int] = mapped_column(
        default=0, nullable=False, comment="连续登录失败次数"
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="账户锁定到期时间"
    )
    last_failed_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最后一次登录失败时间"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), comment="更新时间"
    )

    # 关联打卡任务
    tasks: Mapped[list["CheckInTask"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    # 添加复合索引：加速审批管理查询
    __table_args__ = (
        Index("ix_user_role_approved", "role", "is_approved"),  # 管理员查询待审批用户
    )

    def __repr__(self):
        return f"<User(id={self.id}, alias={self.alias}, jwt_sub={self.jwt_sub}, role={self.role})>"

    @property
    def is_admin(self) -> bool:
        """判断是否为管理员"""
        return self.role == "admin"
