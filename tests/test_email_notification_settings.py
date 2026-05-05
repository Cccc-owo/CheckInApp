from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api import admin as admin_api
from backend.dependencies import get_current_user, get_db
from backend.models import Base, User
from backend.schemas.email_settings import EmailNotificationSettingsUpdate
from backend.services import email_settings_service
from backend.services.email_service import EmailService
from backend.services.email_settings_service import EmailSettingsService


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    return engine, session_factory, session


def test_email_settings_default_row_uses_environment_defaults_and_masks_password(
    monkeypatch,
) -> None:
    engine, _, session = make_session()
    monkeypatch.setattr(email_settings_service.settings, "SMTP_SERVER", "smtp.example.test")
    monkeypatch.setattr(email_settings_service.settings, "SMTP_PORT", 2525)
    monkeypatch.setattr(email_settings_service.settings, "SMTP_SENDER_EMAIL", "mailer@example.com")
    monkeypatch.setattr(email_settings_service.settings, "SMTP_SENDER_PASSWORD", "secret")
    monkeypatch.setattr(email_settings_service.settings, "SMTP_USE_SSL", False)

    snapshot = EmailSettingsService.get_snapshot(session)

    assert snapshot.smtp_server == "smtp.example.test"
    assert snapshot.smtp_port == 2525
    assert snapshot.smtp_sender_email == "mailer@example.com"
    assert snapshot.smtp_sender_password == "secret"
    assert snapshot.has_smtp_sender_password is True
    session.close()
    engine.dispose()


def test_email_settings_update_preserves_and_clears_password(monkeypatch) -> None:
    engine, _, session = make_session()
    monkeypatch.setattr(email_settings_service.settings, "SMTP_SERVER", "smtp.example.test")
    monkeypatch.setattr(email_settings_service.settings, "SMTP_PORT", 2525)
    monkeypatch.setattr(email_settings_service.settings, "SMTP_SENDER_EMAIL", "mailer@example.com")
    monkeypatch.setattr(email_settings_service.settings, "SMTP_SENDER_PASSWORD", "")
    monkeypatch.setattr(email_settings_service.settings, "SMTP_USE_SSL", False)

    EmailSettingsService.get_snapshot(session)
    EmailSettingsService.update_settings(
        session,
        EmailNotificationSettingsUpdate(
            smtp_server="smtp.changed.test",
            smtp_port=587,
            smtp_sender_email="ops@example.com",
            smtp_use_ssl=True,
            notify_token_expiring=False,
            notify_check_in_success=False,
            smtp_sender_password="new-secret",
        ),
    )

    updated = EmailSettingsService.get_snapshot(session)
    assert updated.smtp_server == "smtp.changed.test"
    assert updated.smtp_port == 587
    assert updated.smtp_sender_email == "ops@example.com"
    assert updated.smtp_sender_password == "new-secret"
    assert updated.notify_token_expiring is False
    assert updated.notify_check_in_success is False

    EmailSettingsService.update_settings(
        session,
        EmailNotificationSettingsUpdate(
            smtp_server="smtp.changed.test",
            smtp_port=587,
            smtp_sender_email="ops@example.com",
            smtp_use_ssl=True,
            notify_token_expiring=False,
            notify_check_in_success=False,
            clear_smtp_sender_password=True,
        ),
    )

    cleared = EmailSettingsService.get_snapshot(session)
    assert cleared.smtp_sender_password in ("", None)
    assert cleared.has_smtp_sender_password is False
    session.close()
    engine.dispose()


def test_admin_email_settings_route_rejects_non_admin() -> None:
    engine, session_factory, session = make_session()
    app = FastAPI()
    app.include_router(admin_api.router, prefix="/api/admin")

    def override_get_db():
        yield session

    async def override_get_current_user() -> User:
        return User(id=1, alias="user", role="user", is_approved=True)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)
    response = client.get("/api/admin/email_settings")

    assert response.status_code == 403
    session.close()
    engine.dispose()


def test_token_expiring_notification_can_be_disabled(monkeypatch) -> None:
    engine, session_factory, session = make_session()
    monkeypatch.setattr(email_settings_service, "SessionLocal", session_factory)
    EmailSettingsService.update_settings(
        session,
        EmailNotificationSettingsUpdate(
            smtp_server="smtp.example.test",
            smtp_port=465,
            smtp_sender_email="mailer@example.com",
            smtp_use_ssl=True,
            notify_token_expiring=False,
            notify_check_in_success=True,
        ),
    )

    sent: dict[str, object] = {}

    def fake_send(*args, **kwargs) -> bool:
        sent["called"] = True
        return True

    monkeypatch.setattr(EmailService, "send_email", fake_send)

    user = User(alias="Alice", email="alice@example.com")
    assert EmailService.notify_token_expiring(user, "1000") is False
    assert sent == {}
    session.close()
    engine.dispose()


def test_success_check_in_notification_can_be_disabled(monkeypatch) -> None:
    engine, session_factory, session = make_session()
    monkeypatch.setattr(email_settings_service, "SessionLocal", session_factory)
    EmailSettingsService.update_settings(
        session,
        EmailNotificationSettingsUpdate(
            smtp_server="smtp.example.test",
            smtp_port=465,
            smtp_sender_email="mailer@example.com",
            smtp_use_ssl=True,
            notify_token_expiring=True,
            notify_check_in_success=False,
        ),
    )

    sent: dict[str, object] = {}

    def fake_send(*args, **kwargs) -> bool:
        sent["called"] = True
        return True

    monkeypatch.setattr(EmailService, "send_email", fake_send)

    user = User(alias="Alice", email="alice@example.com")
    assert (
        EmailService.notify_check_in_result(
            user,
            {"thread_id": "thread-1"},
            True,
            "打卡成功",
        )
        is False
    )
    assert sent == {}
    session.close()
    engine.dispose()


def test_email_settings_update_validates_sender_email() -> None:
    with pytest.raises(ValidationError):
        EmailNotificationSettingsUpdate(
            smtp_server="smtp.example.test",
            smtp_port=465,
            smtp_sender_email="not-an-email",
            smtp_use_ssl=True,
            notify_token_expiring=True,
            notify_check_in_success=True,
        )
