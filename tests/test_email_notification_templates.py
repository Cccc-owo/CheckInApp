from __future__ import annotations

from datetime import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import Base, User
from backend.services.email_service import EmailService
from backend.services.email_templates import (
    EmailTemplate,
    EmailTemplateRenderError,
    SafeHtml,
    render_email_template,
)


def test_registration_template_escapes_dynamic_values_and_uses_shared_layout() -> None:
    html = render_email_template(
        EmailTemplate.NEW_USER_REGISTRATION,
        {
            "user_alias": "<Alice>",
            "user_id": "42",
            "created_time": "2026-05-05 10:00:00",
            "admin_url": "https://example.test/admin/users?x=1&y=2",
        },
    )

    assert '<div class="email-shell"' in html
    assert "新用户注册通知" in html
    assert "&lt;Alice&gt;" in html
    assert "<Alice>" not in html
    assert "https://example.test/admin/users?x=1&amp;y=2" in html


def test_template_renderer_fails_clearly_when_context_is_missing() -> None:
    with pytest.raises(EmailTemplateRenderError, match="created_time"):
        render_email_template(
            EmailTemplate.NEW_USER_REGISTRATION,
            {
                "user_alias": "Alice",
                "user_id": "42",
                "admin_url": "https://example.test/admin/users",
            },
        )


def test_template_renderer_allows_trusted_html_snippets() -> None:
    html = render_email_template(
        EmailTemplate.USER_REJECTED,
        {
            "user_alias": "Alice",
            "processed_time": "2026-05-05 10:00:00",
            "reason_section": SafeHtml("<p><strong>拒绝原因：</strong>资料不完整</p>"),
        },
    )

    assert "<strong>拒绝原因：</strong>资料不完整" in html


def test_template_renderer_defaults_footer_year_to_current_year() -> None:
    html = render_email_template(
        EmailTemplate.TOKEN_EXPIRED,
        {
            "user_alias": "Alice",
            "login_url": "https://example.test/login",
        },
    )

    assert str(datetime.now().year) in html


@pytest.mark.parametrize(
    ("template", "context", "expected"),
    [
        (
            EmailTemplate.USER_APPROVED,
            {
                "user_alias": "Alice",
                "user_role": "user",
                "created_time": "2026-05-01 09:00:00",
                "approved_time": "2026-05-05 10:00:00",
                "login_url": "https://example.test/login",
            },
            "账户审批通过",
        ),
        (
            EmailTemplate.USER_REJECTED,
            {
                "user_alias": "Alice",
                "processed_time": "2026-05-05 10:00:00",
                "reason_section": "<p><strong>拒绝原因：</strong>资料不完整</p>",
            },
            "未通过",
        ),
        (
            EmailTemplate.TOKEN_EXPIRING,
            {
                "user_alias": "Alice",
                "minutes_left": "25",
            },
            "25 分钟",
        ),
        (
            EmailTemplate.TOKEN_EXPIRED,
            {
                "user_alias": "Alice",
                "login_url": "https://example.test/login",
            },
            "登录凭证已过期",
        ),
        (
            EmailTemplate.CHECK_IN_RESULT,
            {
                "user_alias": "Alice",
                "executed_time": "2026-05-05 10:00:00",
                "thread_id": "thread-1",
                "status_text": "失败",
                "status_color": "#b91c1c",
                "message_row": "<tr><td>失败原因</td><td>Token 失效</td></tr>",
                "guidance_section": "<p>请刷新 Token。</p>",
            },
            "thread-1",
        ),
    ],
)
def test_supported_notification_templates_render_shared_layout(
    template: EmailTemplate, context: dict[str, str], expected: str
) -> None:
    html = render_email_template(template, context)

    assert '<div class="email-shell"' in html
    assert expected in html
    assert "接龙自动打卡系统" in html


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def add_user(db_session, alias: str, email: str | None = None, role: str = "user") -> User:
    user = User(alias=alias, email=email, role=role)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_new_user_registration_notification_uses_template_and_admin_recipients(
    db_session, monkeypatch
) -> None:
    admin = add_user(db_session, "admin", "admin@example.test", "admin")
    user = add_user(db_session, "<Alice>", "alice@example.test")
    sent: dict[str, object] = {}

    def fake_send(to_emails: list[str], subject: str, body_html: str) -> bool:
        sent["to_emails"] = to_emails
        sent["subject"] = subject
        sent["body_html"] = body_html
        return True

    monkeypatch.setattr(EmailService, "send_email", fake_send)

    assert EmailService.notify_new_user_registration(user, db_session) is True

    assert sent["to_emails"] == [admin.email]
    assert "新用户注册通知" in str(sent["subject"])
    assert "&lt;Alice&gt;" in str(sent["body_html"])
    assert "<Alice>" not in str(sent["body_html"])
    assert "/admin/users" in str(sent["body_html"])


def test_user_rejection_notification_escapes_reason_and_skips_missing_email(monkeypatch) -> None:
    sent: dict[str, object] = {}

    def fake_send(to_emails: list[str], subject: str, body_html: str) -> bool:
        sent["to_emails"] = to_emails
        sent["subject"] = subject
        sent["body_html"] = body_html
        return True

    monkeypatch.setattr(EmailService, "send_email", fake_send)

    assert EmailService.notify_user_rejected(User(alias="NoMail"), "ignored") is False
    assert sent == {}

    user = User(alias="Bob", email="bob@example.test")
    assert EmailService.notify_user_rejected(user, "<script>alert(1)</script>") is True

    assert sent["to_emails"] == ["bob@example.test"]
    assert "账户审批结果" in str(sent["subject"])
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in str(sent["body_html"])
    assert "<script>" not in str(sent["body_html"])


def test_user_approval_notification_uses_template_login_link(monkeypatch) -> None:
    sent: dict[str, object] = {}

    def fake_send(to_emails: list[str], subject: str, body_html: str) -> bool:
        sent["to_emails"] = to_emails
        sent["subject"] = subject
        sent["body_html"] = body_html
        return True

    monkeypatch.setattr(EmailService, "send_email", fake_send)

    assert (
        EmailService.notify_user_approved(User(alias="Alice", email="alice@example.test")) is True
    )

    assert sent["to_emails"] == ["alice@example.test"]
    assert "账户审批通过" in str(sent["subject"])
    assert "立即登录" in str(sent["body_html"])
    assert "/login" in str(sent["body_html"])


def test_token_notifications_use_template_links(monkeypatch) -> None:
    sent_messages: list[dict[str, object]] = []

    def fake_send(to_emails: list[str], subject: str, body_html: str) -> bool:
        sent_messages.append(
            {
                "to_emails": to_emails,
                "subject": subject,
                "body_html": body_html,
            }
        )
        return True

    monkeypatch.setattr(EmailService, "send_email", fake_send)
    monkeypatch.setattr(
        "backend.services.email_service.parse_jwt_exp",
        lambda jwt_exp: 1000,
        raising=False,
    )
    monkeypatch.setattr(
        "backend.services.email_service.minutes_until_expiry",
        lambda exp_timestamp: 25,
        raising=False,
    )

    user = User(alias="Alice", email="alice@example.test")
    assert EmailService.notify_token_expiring(user, "1000") is True
    assert EmailService.notify_token_expired(user) is True

    assert len(sent_messages) == 2
    assert "登录凭证即将过期" in str(sent_messages[0]["subject"])
    assert "25 分钟" in str(sent_messages[0]["body_html"])
    assert "立即登录刷新" not in str(sent_messages[0]["body_html"])
    assert "登录凭证已过期" in str(sent_messages[1]["subject"])
    assert "立即登录刷新" in str(sent_messages[1]["body_html"])


def test_check_in_result_notification_preserves_token_error_guidance(monkeypatch) -> None:
    sent: dict[str, object] = {}

    def fake_send(to_emails: list[str], subject: str, body_html: str) -> bool:
        sent["to_emails"] = to_emails
        sent["subject"] = subject
        sent["body_html"] = body_html
        return True

    monkeypatch.setattr(EmailService, "send_email", fake_send)

    user = User(alias="Alice", email="alice@example.test")
    assert (
        EmailService.notify_check_in_result(
            user,
            {"thread_id": "thread-1<script>"},
            False,
            "Token <expired>",
        )
        is True
    )

    assert sent["to_emails"] == ["alice@example.test"]
    assert "打卡❌ 失败" in str(sent["subject"])
    assert "thread-1&lt;script&gt;" in str(sent["body_html"])
    assert "Token &lt;expired&gt;" in str(sent["body_html"])
    assert "打卡凭证已过期" in str(sent["body_html"])
    assert "立即登录刷新" in str(sent["body_html"])
    assert "/dashboard" in str(sent["body_html"])


def test_failed_check_in_notification_includes_dashboard_button(monkeypatch) -> None:
    sent: dict[str, object] = {}

    def fake_send(to_emails: list[str], subject: str, body_html: str) -> bool:
        sent["to_emails"] = to_emails
        sent["subject"] = subject
        sent["body_html"] = body_html
        return True

    monkeypatch.setattr(EmailService, "send_email", fake_send)

    assert (
        EmailService.notify_check_in_result(
            User(alias="Alice", email="alice@example.test"),
            {"thread_id": "thread-2"},
            False,
            "网络错误",
        )
        is True
    )

    assert "打卡❌ 失败" in str(sent["subject"])
    assert "立即登录刷新" in str(sent["body_html"])
    assert "/dashboard" in str(sent["body_html"])
