"""
邮件业务服务 (高级)

职能：提供业务相关的邮件操作
- 新用户注册通知
- 用户审批通知
- 打卡结果通知
- Token 到期提醒
- 调用底层 EmailNotifier 发送邮件
"""

import logging
from datetime import datetime
from html import escape
from typing import Any, List

from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import User
from backend.services.email_settings_service import EmailSettingsService
from backend.services.email_templates import EmailTemplate, SafeHtml, render_email_template
from backend.utils.time_helpers import minutes_until_expiry, parse_jwt_exp
from backend.workers.email_notifier import EmailNotifier

logger = logging.getLogger(__name__)


def _format_datetime(value: Any) -> str:
    if value is None:
        return "未知"

    try:
        return value.strftime("%Y-%m-%d %H:%M:%S")
    except AttributeError:
        return str(value)


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _frontend_path(path: str) -> str:
    return f"{settings.FRONTEND_URL}{path}"


def _email_text(value: object) -> str:
    return escape(str(value), quote=True)


def _optional_reason_section(reason: str) -> SafeHtml:
    if not reason:
        return SafeHtml("")

    return SafeHtml(
        '<div class="status-box" style="--accent: #64748b; --surface: #f8fafc;">'
        '<p class="status-title">拒绝原因</p>'
        f"<p>{_email_text(reason)}</p>"
        "</div>"
    )


def _message_row(message: str) -> SafeHtml:
    if not message:
        return SafeHtml("")

    return SafeHtml(f'<tr><td class="info-label">失败原因</td><td>{_email_text(message)}</td></tr>')


def _check_in_guidance_section(success: bool, is_token_error: bool) -> SafeHtml:
    if success:
        return SafeHtml("<p>如有问题，请及时检查您的打卡配置。</p>")

    dashboard_url = _email_text(_frontend_path("/dashboard"))
    if is_token_error:
        status_html = (
            '<div class="status-box" style="--accent: #b91c1c; --surface: #fef2f2;">'
            '<p class="status-title">打卡凭证已过期</p>'
            "<p>打卡凭证已过期，无法自动打卡。所有自动打卡任务已暂停，请进入网页处理。</p>"
            "</div>"
        )
    else:
        status_html = "<p>请进入网页检查任务配置和最近记录。</p>"

    return SafeHtml(
        status_html + '<div class="action-wrap">'
        f'<a href="{dashboard_url}" class="action-link" style="--accent: #b91c1c;">立即登录刷新</a>'
        "</div>"
    )


def _is_token_error(success: bool, message: str) -> bool:
    if success or not message:
        return False

    return any(
        marker in message
        for marker in (
            "Token",
            "token",
            "失效",
            "授权",
            "登录",
        )
    )


class EmailService:
    """邮件业务服务（高级服务）"""

    @staticmethod
    def send_email(to_emails: List[str], subject: str, body_html: str) -> bool:
        """
        发送邮件（业务层方法，调用底层 EmailNotifier）

        Args:
            to_emails: 收件人邮箱列表
            subject: 邮件主题
            body_html: 邮件正文（HTML 格式）

        Returns:
            是否发送成功
        """
        return EmailNotifier.send_email(to_emails, subject, body_html)

    @staticmethod
    def notify_new_user_registration(user: User, db: Session) -> bool:
        """
        通知管理员有新用户注册

        Args:
            user: 新注册的用户
            db: 数据库会话

        Returns:
            是否发送成功
        """
        admins = db.query(User).filter(User.role == "admin", User.email.isnot(None)).all()
        admin_emails: List[str] = []
        for admin in admins:
            email_value = admin.email
            if email_value is not None:
                admin_emails.append(str(email_value))

        if not admin_emails:
            logger.warning("没有找到管理员邮箱，无法发送通知")
            return False

        subject = f"【接龙自动打卡系统】新用户注册通知 - {user.alias}"
        body_html = render_email_template(
            EmailTemplate.NEW_USER_REGISTRATION,
            {
                "user_alias": user.alias,
                "user_id": user.id,
                "created_time": _format_datetime(user.created_at),
                "admin_url": _frontend_path("/admin/users"),
            },
        )

        return EmailService.send_email(admin_emails, subject, body_html)

    @staticmethod
    def send_email_verification_code(to_email: str, alias: str, code: str) -> bool:
        subject = f"【接龙自动打卡系统】邮箱验证码 - {alias}"
        body_html = (
            "<p>您正在验证接龙自动打卡系统账号邮箱。</p>"
            f"<p>验证码：<strong>{_email_text(code)}</strong></p>"
            "<p>验证码 10 分钟内有效。如非本人操作，请忽略本邮件。</p>"
        )
        return EmailService.send_email([to_email], subject, body_html)

    @staticmethod
    def notify_user_approved(user: User) -> bool:
        """
        通知用户审批已通过

        Args:
            user: 已通过审批的用户

        Returns:
            是否发送成功
        """
        user_email = user.email
        if user_email is None:
            logger.info(f"用户 {user.alias} 未设置邮箱，跳过审批通知")
            return False
        if not user.email_verified_at:
            logger.info(f"用户 {user.alias} 邮箱未验证，跳过审批通知")
            return False

        subject = f"【接龙自动打卡系统】账户审批通过 - {user.alias}"
        body_html = render_email_template(
            EmailTemplate.USER_APPROVED,
            {
                "user_alias": user.alias,
                "user_role": user.role,
                "created_time": _format_datetime(user.created_at),
                "approved_time": _now_text(),
                "login_url": _frontend_path("/login"),
            },
        )

        return EmailService.send_email([str(user_email)], subject, body_html)

    @staticmethod
    def notify_user_rejected(user: User, reason: str = "") -> bool:
        """
        通知用户审批被拒绝

        Args:
            user: 被拒绝的用户
            reason: 拒绝原因（可选）

        Returns:
            是否发送成功
        """
        user_email = user.email
        if user_email is None:
            logger.info(f"用户 {user.alias} 未设置邮箱，跳过拒绝通知")
            return False

        subject = f"【接龙自动打卡系统】账户审批结果 - {user.alias}"
        body_html = render_email_template(
            EmailTemplate.USER_REJECTED,
            {
                "user_alias": user.alias,
                "processed_time": _now_text(),
                "reason_section": _optional_reason_section(reason),
            },
        )

        return EmailService.send_email([str(user_email)], subject, body_html)

    @staticmethod
    def notify_token_expiring(user: User, jwt_exp: str) -> bool:
        """
        通知用户 Token 即将过期

        Args:
            user: 用户对象
            jwt_exp: Token 过期时间戳

        Returns:
            是否发送成功
        """
        if not EmailSettingsService.is_token_expiring_notification_enabled():
            logger.info("Token 即将过期通知已关闭，跳过发送")
            return False

        user_email = user.email
        if user_email is None:
            logger.info(f"用户 {user.alias} 未设置邮箱，跳过 Token 过期通知")
            return False

        exp_timestamp = parse_jwt_exp(jwt_exp)
        minutes_left = minutes_until_expiry(exp_timestamp) if exp_timestamp else 0

        subject = f"【接龙自动打卡系统】登录凭证即将过期 - {user.alias}"
        body_html = render_email_template(
            EmailTemplate.TOKEN_EXPIRING,
            {
                "user_alias": user.alias,
                "minutes_left": minutes_left,
            },
        )

        return EmailService.send_email([str(user_email)], subject, body_html)

    @staticmethod
    def notify_token_expired(user: User) -> bool:
        """
        通知用户 Token 已过期

        Args:
            user: 用户对象

        Returns:
            是否发送成功
        """
        user_email = user.email
        if user_email is None:
            logger.info(f"用户 {user.alias} 未设置邮箱，跳过 Token 已过期通知")
            return False

        subject = f"【接龙自动打卡系统】登录凭证已过期 - {user.alias}"
        body_html = render_email_template(
            EmailTemplate.TOKEN_EXPIRED,
            {
                "user_alias": user.alias,
                "login_url": _frontend_path("/login"),
            },
        )

        return EmailService.send_email([str(user_email)], subject, body_html)

    @staticmethod
    def notify_check_in_result(
        user: User, task_info: dict, success: bool, message: str = ""
    ) -> bool:
        """
        通知用户打卡结果

        Args:
            user: 用户对象
            task_info: 打卡任务信息（包含 thread_id, texts, values 等）
            success: 打卡是否成功
            message: 额外消息

        Returns:
            是否发送成功
        """
        if success and not EmailSettingsService.is_check_in_success_notification_enabled():
            logger.info("打卡成功通知已关闭，跳过发送")
            return False

        user_email = user.email
        if user_email is None:
            logger.info(f"用户 {user.alias} 未设置邮箱，跳过打卡通知")
            return False

        status_text = "成功" if success else "失败"
        status_color = "#15803d" if success else "#b91c1c"
        subject = f"【接龙自动打卡】打卡{'✅ 成功' if success else '❌ 失败'} - {user.alias}"
        token_error = _is_token_error(success, message)

        body_html = render_email_template(
            EmailTemplate.CHECK_IN_RESULT,
            {
                "user_alias": user.alias,
                "executed_time": _now_text(),
                "thread_id": task_info.get("thread_id", "未知"),
                "status_text": status_text,
                "status_color": status_color,
                "message_row": _message_row(message),
                "guidance_section": _check_in_guidance_section(success, token_error),
            },
        )

        return EmailService.send_email([str(user_email)], subject, body_html)
