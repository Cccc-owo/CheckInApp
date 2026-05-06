from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import EmailNotificationSettings
from backend.models.database import SessionLocal
from backend.schemas.email_settings import (
    EmailNotificationSettingsResponse,
    EmailNotificationSettingsUpdate,
)

SETTINGS_ROW_ID = 1


@dataclass(frozen=True)
class EmailSettingsSnapshot:
    id: int
    smtp_server: str
    smtp_port: int
    smtp_sender_email: str
    smtp_sender_password: str
    smtp_use_ssl: bool
    notify_token_expiring: bool
    notify_check_in_success: bool
    require_admin_approval_for_registration: bool
    require_verified_email_for_approval: bool
    has_smtp_sender_password: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class EmailSettingsService:
    """读取和更新系统邮件配置。"""

    @staticmethod
    def _defaults() -> EmailNotificationSettings:
        return EmailNotificationSettings(
            id=SETTINGS_ROW_ID,
            smtp_server=settings.SMTP_SERVER,
            smtp_port=settings.SMTP_PORT,
            smtp_sender_email=settings.SMTP_SENDER_EMAIL,
            smtp_sender_password=settings.SMTP_SENDER_PASSWORD,
            smtp_use_ssl=settings.SMTP_USE_SSL,
            notify_token_expiring=True,
            notify_check_in_success=True,
            require_admin_approval_for_registration=True,
            require_verified_email_for_approval=True,
        )

    @staticmethod
    def _default_snapshot() -> EmailSettingsSnapshot:
        password = str(settings.SMTP_SENDER_PASSWORD or "")
        return EmailSettingsSnapshot(
            id=SETTINGS_ROW_ID,
            smtp_server=settings.SMTP_SERVER,
            smtp_port=settings.SMTP_PORT,
            smtp_sender_email=settings.SMTP_SENDER_EMAIL,
            smtp_sender_password=password,
            smtp_use_ssl=settings.SMTP_USE_SSL,
            notify_token_expiring=True,
            notify_check_in_success=True,
            require_admin_approval_for_registration=True,
            require_verified_email_for_approval=True,
            has_smtp_sender_password=bool(password),
            created_at=None,
            updated_at=None,
        )

    @staticmethod
    def _get_or_create(db: Session) -> EmailNotificationSettings:
        row = (
            db.query(EmailNotificationSettings)
            .filter(EmailNotificationSettings.id == SETTINGS_ROW_ID)
            .first()
        )
        if row:
            return row

        row = EmailSettingsService._defaults()
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def _to_snapshot(row: EmailNotificationSettings) -> EmailSettingsSnapshot:
        password = str(row.smtp_sender_password or "")
        return EmailSettingsSnapshot(
            id=row.id,
            smtp_server=str(row.smtp_server or ""),
            smtp_port=int(row.smtp_port or 0),
            smtp_sender_email=str(row.smtp_sender_email or ""),
            smtp_sender_password=password,
            smtp_use_ssl=bool(row.smtp_use_ssl),
            notify_token_expiring=bool(row.notify_token_expiring),
            notify_check_in_success=bool(row.notify_check_in_success),
            require_admin_approval_for_registration=bool(
                row.require_admin_approval_for_registration
            ),
            require_verified_email_for_approval=bool(row.require_verified_email_for_approval),
            has_smtp_sender_password=bool(password),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_response(snapshot: EmailSettingsSnapshot) -> EmailNotificationSettingsResponse:
        return EmailNotificationSettingsResponse(
            id=snapshot.id,
            smtp_server=snapshot.smtp_server,
            smtp_port=snapshot.smtp_port,
            smtp_sender_email=snapshot.smtp_sender_email,
            smtp_use_ssl=snapshot.smtp_use_ssl,
            notify_token_expiring=snapshot.notify_token_expiring,
            notify_check_in_success=snapshot.notify_check_in_success,
            require_admin_approval_for_registration=snapshot.require_admin_approval_for_registration,
            require_verified_email_for_approval=snapshot.require_verified_email_for_approval,
            has_smtp_sender_password=snapshot.has_smtp_sender_password,
            created_at=snapshot.created_at,
            updated_at=snapshot.updated_at,
        )

    @staticmethod
    def get_snapshot(db: Session) -> EmailSettingsSnapshot:
        return EmailSettingsService._to_snapshot(EmailSettingsService._get_or_create(db))

    @staticmethod
    def get_response(db: Session) -> EmailNotificationSettingsResponse:
        return EmailSettingsService._to_response(EmailSettingsService.get_snapshot(db))

    @staticmethod
    def update_settings(
        db: Session, payload: EmailNotificationSettingsUpdate
    ) -> EmailSettingsSnapshot:
        row = EmailSettingsService._get_or_create(db)
        row.smtp_server = payload.smtp_server
        row.smtp_port = payload.smtp_port
        row.smtp_sender_email = str(payload.smtp_sender_email)
        row.smtp_use_ssl = payload.smtp_use_ssl
        row.notify_token_expiring = payload.notify_token_expiring
        row.notify_check_in_success = payload.notify_check_in_success
        row.require_admin_approval_for_registration = (
            payload.require_admin_approval_for_registration
        )
        row.require_verified_email_for_approval = payload.require_verified_email_for_approval

        if payload.clear_smtp_sender_password:
            row.smtp_sender_password = ""
        elif payload.smtp_sender_password is not None:
            row.smtp_sender_password = payload.smtp_sender_password

        row.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
        return EmailSettingsService._to_snapshot(row)

    @staticmethod
    def update_response(
        db: Session, payload: EmailNotificationSettingsUpdate
    ) -> EmailNotificationSettingsResponse:
        return EmailSettingsService._to_response(EmailSettingsService.update_settings(db, payload))

    @staticmethod
    def get_smtp_config() -> dict[str, object] | None:
        db = SessionLocal()
        try:
            try:
                snapshot = EmailSettingsService.get_snapshot(db)
            except SQLAlchemyError:
                snapshot = EmailSettingsService._default_snapshot()
        finally:
            db.close()

        if not snapshot.smtp_server or not snapshot.smtp_sender_email or not snapshot.smtp_port:
            return None

        return {
            "smtp_server": snapshot.smtp_server,
            "smtp_port": snapshot.smtp_port,
            "sender_email": snapshot.smtp_sender_email,
            "sender_password": snapshot.smtp_sender_password,
            "use_ssl": snapshot.smtp_use_ssl,
        }

    @staticmethod
    def is_token_expiring_notification_enabled() -> bool:
        db = SessionLocal()
        try:
            try:
                return EmailSettingsService.get_snapshot(db).notify_token_expiring
            except SQLAlchemyError:
                return EmailSettingsService._default_snapshot().notify_token_expiring
        finally:
            db.close()

    @staticmethod
    def is_check_in_success_notification_enabled() -> bool:
        db = SessionLocal()
        try:
            try:
                return EmailSettingsService.get_snapshot(db).notify_check_in_success
            except SQLAlchemyError:
                return EmailSettingsService._default_snapshot().notify_check_in_success
        finally:
            db.close()

    @staticmethod
    def is_registration_approval_required() -> bool:
        db = SessionLocal()
        try:
            try:
                return EmailSettingsService.get_snapshot(db).require_admin_approval_for_registration
            except SQLAlchemyError:
                return (
                    EmailSettingsService._default_snapshot().require_admin_approval_for_registration
                )
        finally:
            db.close()

    @staticmethod
    def is_verified_email_required_for_approval() -> bool:
        db = SessionLocal()
        try:
            try:
                return EmailSettingsService.get_snapshot(db).require_verified_email_for_approval
            except SQLAlchemyError:
                return EmailSettingsService._default_snapshot().require_verified_email_for_approval
        finally:
            db.close()
