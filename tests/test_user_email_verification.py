from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api import users as users_api
from backend.dependencies import get_current_user, get_db
from backend.models import Base, User
from backend.schemas.email_settings import EmailNotificationSettingsUpdate
from backend.schemas.user import UserUpdate
from backend.services import email_settings_service
from backend.services.admin_service import AdminService
from backend.services.email_service import EmailService
from backend.services.email_settings_service import EmailSettingsService
from backend.services.user_service import UserService


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    return engine, session_factory, session


def add_user(session, alias: str = "Alice", email: str | None = None) -> User:
    user = User(alias=alias, email=email, role="user", is_approved=False, jwt_exp="0")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_current_user_can_set_and_verify_email(monkeypatch) -> None:
    engine, _, session = make_session()
    user = add_user(session)
    sent: dict[str, object] = {}

    def fake_send_verification_code(to_email: str, alias: str, code: str) -> bool:
        sent["to_email"] = to_email
        sent["alias"] = alias
        sent["code"] = code
        return True

    monkeypatch.setattr(EmailService, "send_email_verification_code", fake_send_verification_code)

    result = UserService.set_email_for_verification(user.id, " Alice@Example.COM ", session)

    assert result.email == "Alice@example.com"
    assert result.email_verified is False
    assert sent["to_email"] == "Alice@example.com"
    assert isinstance(sent["code"], str)
    assert sent["code"] != ""

    verified = UserService.verify_email_code(user.id, str(sent["code"]), session)

    assert verified.email_verified is True
    assert verified.email_verified_at is not None
    refreshed = session.get(User, user.id)
    assert refreshed is not None
    assert refreshed.email_verification_code_hash is None
    assert refreshed.email_verification_expires_at is None
    session.close()
    engine.dispose()


def test_email_verification_rejects_wrong_or_expired_code(monkeypatch) -> None:
    engine, _, session = make_session()
    user = add_user(session)
    sent: dict[str, str] = {}

    monkeypatch.setattr(
        EmailService,
        "send_email_verification_code",
        lambda to_email, alias, code: sent.setdefault("code", code) or True,
    )

    UserService.set_email_for_verification(user.id, "alice@example.com", session)

    with pytest.raises(ValueError, match="验证码"):
        UserService.verify_email_code(user.id, "000000", session)

    refreshed = session.get(User, user.id)
    assert refreshed is not None
    refreshed.email_verification_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    session.commit()

    with pytest.raises(ValueError, match="验证码"):
        UserService.verify_email_code(user.id, sent["code"], session)

    session.close()
    engine.dispose()


def test_changing_email_clears_verification_state(monkeypatch) -> None:
    engine, _, session = make_session()
    user = add_user(session, email="old@example.com")
    user.email_verified_at = datetime.now(timezone.utc)
    session.commit()

    monkeypatch.setattr(EmailService, "send_email_verification_code", lambda *args: True)

    result = UserService.set_email_for_verification(user.id, "new@example.com", session)

    assert result.email == "new@example.com"
    assert result.email_verified is False
    refreshed = session.get(User, user.id)
    assert refreshed is not None
    assert refreshed.email_verified_at is None
    session.close()
    engine.dispose()


def test_approval_requires_warning_then_allows_override(monkeypatch) -> None:
    engine, session_factory, session = make_session()
    monkeypatch.setattr(email_settings_service, "SessionLocal", session_factory)
    user = add_user(session)

    first = AdminService.approve_user(user.id, session)
    assert first["success"] is False
    assert first["requires_override"] is True
    assert first["warning_code"] == "UNVERIFIED_EMAIL"

    second = AdminService.approve_user(user.id, session, allow_unverified_email=True)
    assert second["success"] is True
    assert second["warning_code"] == "UNVERIFIED_EMAIL"
    assert session.get(User, user.id).is_approved is True
    session.close()
    engine.dispose()


def test_approval_warning_can_be_disabled(monkeypatch) -> None:
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
            notify_check_in_success=True,
            require_admin_approval_for_registration=True,
            warn_unverified_email_before_approval=False,
        ),
    )
    user = add_user(session)

    result = AdminService.approve_user(user.id, session)

    assert result["success"] is True
    assert "requires_override" not in result
    session.close()
    engine.dispose()


def test_approval_notification_requires_verified_email(monkeypatch) -> None:
    sent: dict[str, object] = {}

    def fake_send(to_emails: list[str], subject: str, body_html: str) -> bool:
        sent["to_emails"] = to_emails
        return True

    monkeypatch.setattr(EmailService, "send_email", fake_send)

    unverified = User(alias="Alice", email="alice@example.com")
    assert EmailService.notify_user_approved(unverified) is False
    assert sent == {}

    verified = User(alias="Bob", email="bob@example.com")
    verified.email_verified_at = datetime.now(timezone.utc)
    assert EmailService.notify_user_approved(verified) is True
    assert sent["to_emails"] == ["bob@example.com"]


def test_registration_approval_policy_controls_new_user_approval(monkeypatch) -> None:
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
            notify_check_in_success=True,
            require_admin_approval_for_registration=False,
            warn_unverified_email_before_approval=True,
        ),
    )

    assert EmailSettingsService.is_registration_approval_required() is False
    session.close()
    engine.dispose()


def test_admin_update_warns_when_approval_changes_email_before_approval(monkeypatch) -> None:
    engine, session_factory, session = make_session()
    monkeypatch.setattr(email_settings_service, "SessionLocal", session_factory)
    user = add_user(session, email="old@example.com")
    user.email_verified_at = datetime.now(timezone.utc)
    session.commit()

    warning = AdminService.approval_warning_for_user(
        user,
        allow_unverified_email=False,
        next_email="new@example.com",
    )

    assert warning is not None
    assert warning["requires_override"] is True

    UserService.update_user(
        user.id,
        UserUpdate(email="new@example.com", is_approved=True, allow_unverified_email=True),
        session,
    )

    refreshed = session.get(User, user.id)
    assert refreshed is not None
    assert refreshed.email == "new@example.com"
    assert refreshed.email_verified is False
    session.close()
    engine.dispose()


def test_admin_update_route_returns_unverified_email_warning(monkeypatch) -> None:
    engine, session_factory, session = make_session()
    monkeypatch.setattr(email_settings_service, "SessionLocal", session_factory)
    admin = User(alias="Admin", role="admin", is_approved=True, jwt_exp="0")
    user = User(alias="Alice", role="user", is_approved=False, jwt_exp="0")
    session.add_all([admin, user])
    session.commit()
    session.refresh(admin)
    session.refresh(user)

    app = FastAPI()
    app.include_router(users_api.router, prefix="/api/users")

    def override_get_db():
        yield session

    async def override_get_current_user() -> User:
        return admin

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)
    response = client.put(f"/api/users/{user.id}", json={"is_approved": True})

    assert response.status_code == 200
    assert response.json() == {
        "success": False,
        "message": "用户邮箱未验证，确认后仍可继续审批",
        "user_id": None,
        "requires_override": True,
        "warning_code": "UNVERIFIED_EMAIL",
    }
    assert session.get(User, user.id).is_approved is False
    session.close()
    engine.dispose()
