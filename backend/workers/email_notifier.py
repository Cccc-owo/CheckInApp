"""
邮件发送引擎 (底层)

职能：提供基础的 SMTP 邮件发送功能
- SMTP 服务器连接
- 邮件发送
- 配置管理
- 不包含业务逻辑
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import List, Optional

from backend.config import settings

logger = logging.getLogger(__name__)


class EmailNotifier:
    """邮件发送引擎（底层服务）"""

    @staticmethod
    def get_email_config() -> Optional[dict]:
        """
        从环境变量读取邮件配置

        Returns:
            dict: 邮件配置，如果配置不完整则返回 None
        """
        # 检查必要的邮件配置是否存在
        if not settings.SMTP_SERVER or not settings.SMTP_SENDER_EMAIL:
            logger.debug("邮件配置未完成（SMTP_SERVER 或 SMTP_SENDER_EMAIL 为空），邮件发送功能已禁用")
            return None

        if not settings.SMTP_PORT:
            logger.debug("邮件配置未完成（SMTP_PORT 为空），邮件发送功能已禁用")
            return None

        # 返回配置字典
        return {
            'smtp_server': settings.SMTP_SERVER,
            'smtp_port': settings.SMTP_PORT,
            'sender_email': settings.SMTP_SENDER_EMAIL,
            'sender_password': settings.SMTP_SENDER_PASSWORD,
            'use_ssl': settings.SMTP_USE_SSL
        }

    @staticmethod
    def send_email(
        to_emails: List[str],
        subject: str,
        html_content: str,
        from_email: Optional[str] = None
    ) -> bool:
        """
        发送邮件（底层方法）

        Args:
            to_emails: 收件人邮箱列表
            subject: 邮件主题
            html_content: HTML 邮件内容
            from_email: 发件人邮箱（可选，默认使用配置中的发件人）

        Returns:
            是否发送成功
        """
        email_config = EmailNotifier.get_email_config()
        if not email_config:
            logger.warning("邮件配置不完整，跳过发送邮件")
            return False

        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['From'] = from_email or email_config['sender_email']
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject

            # 添加 HTML 正文
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # 连接 SMTP 服务器并发送
            if email_config.get('use_ssl', True):
                server = smtplib.SMTP_SSL(
                    email_config['smtp_server'],
                    int(email_config['smtp_port'])
                )
            else:
                server = smtplib.SMTP(
                    email_config['smtp_server'],
                    int(email_config['smtp_port'])
                )
                server.starttls()

            server.login(email_config['sender_email'], email_config['sender_password'])
            server.sendmail(msg['From'], to_emails, msg.as_string())
            server.quit()

            logger.info(f"邮件发送成功: {subject} -> {', '.join(to_emails)}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False

    @staticmethod
    def is_email_enabled() -> bool:
        """
        检查邮件功能是否启用

        Returns:
            邮件功能是否可用
        """
        return EmailNotifier.get_email_config() is not None

