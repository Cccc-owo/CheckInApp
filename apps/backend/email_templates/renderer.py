from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from html import escape
from pathlib import Path
from string import Template
from typing import Any


class EmailTemplateRenderError(RuntimeError):
    pass


class SafeHtml(str):
    pass


class EmailTemplate(StrEnum):
    NEW_USER_REGISTRATION = "new-user-registration"
    USER_APPROVED = "user-approved"
    USER_REJECTED = "user-rejected"
    TOKEN_EXPIRING = "token-expiring"
    TOKEN_EXPIRED = "token-expired"
    CHECK_IN_RESULT = "check-in-result"


TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


TEMPLATE_META = {
    EmailTemplate.NEW_USER_REGISTRATION: {
        "title": "新用户注册通知",
        "subtitle": "请及时审批新注册账户",
        "header_background": "#4f46e5",
    },
    EmailTemplate.USER_APPROVED: {
        "title": "账户审批通过",
        "subtitle": "您现在可以使用接龙自动打卡系统",
        "header_background": "#15803d",
    },
    EmailTemplate.USER_REJECTED: {
        "title": "账户审批结果通知",
        "subtitle": "您的注册申请未通过审批",
        "header_background": "#b91c1c",
    },
    EmailTemplate.TOKEN_EXPIRING: {
        "title": "登录凭证即将过期",
        "subtitle": "请尽快刷新 QQ 登录凭证",
        "header_background": "#c2410c",
    },
    EmailTemplate.TOKEN_EXPIRED: {
        "title": "登录凭证已过期",
        "subtitle": "自动打卡任务已无法继续执行",
        "header_background": "#b91c1c",
    },
    EmailTemplate.CHECK_IN_RESULT: {
        "title": "打卡结果通知",
        "subtitle": "自动打卡任务执行结果",
        "header_background": "#2563eb",
    },
}


def _load_template(template_name: str) -> Template:
    template_path = TEMPLATE_DIR / f"{template_name}.html"
    if not template_path.exists():
        raise EmailTemplateRenderError(f"email template file missing: {template_name}")
    return Template(template_path.read_text(encoding="utf-8"))


def _escape_context(context: dict[str, Any]) -> dict[str, str]:
    escaped: dict[str, str] = {}
    for key, value in context.items():
        if isinstance(value, SafeHtml):
            escaped[key] = str(value)
        elif value is None:
            escaped[key] = ""
        else:
            escaped[key] = escape(str(value), quote=True)
    return escaped


def _substitute(template_obj: Template, context: dict[str, Any]) -> str:
    try:
        return template_obj.substitute(context)
    except KeyError as exc:
        missing_key = exc.args[0]
        raise EmailTemplateRenderError(
            f"missing required email template context: {missing_key}"
        ) from exc


def render_email_template(template: EmailTemplate, context: dict[str, Any]) -> str:
    escaped_context = _escape_context(context)
    body = _substitute(_load_template(template.value), escaped_context)
    meta = TEMPLATE_META[template]
    footer_year = context.get("year") or datetime.now().year
    return _substitute(
        _load_template("base"),
        {
            "title": meta["title"],
            "subtitle": meta["subtitle"],
            "header_background": meta["header_background"],
            "body": body,
            "year": str(footer_year),
        },
    )
