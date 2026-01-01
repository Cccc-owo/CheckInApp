import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import logging
import configparser
from pathlib import Path

from backend.config import settings

logger = logging.getLogger(__name__)

# --- 邮件模板 ---

EXPIRATION_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>Token 到期通知</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; margin: 20px; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); }}
        h1 {{ color: #d9534f; }}
        .message {{ background-color: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 20px; }}
        .important {{ font-weight: bold; color: #d9534f; }}
        .footer {{ font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <h1>注意!</h1>
    <div class="message">
        <p>{name}，请注意!</p>
        <p>您的 <span class="important">token</span> 已经到期，请尽快重新刷新您的 token，否则您的自动打卡功能将会失效。</p>
        <p><strong>到期时间:</strong> {exp_time}</p>
    </div>
    <p class="footer">邮件发送时间: {send_time}</p>
</body>
</html>
"""

SUCCESS_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>打卡成功通知</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; margin: 20px; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); }}
        h1 {{ color: #5cb85c; }}
        .message {{ background-color: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 20px; }}
        .important {{ font-weight: bold; color: #5cb85c; }}
        .footer {{ font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <h1>打卡成功!</h1>
    <div class="message">
        <p>{name}，您好!</p>
        <p>系统已于 <span class="important">{send_time}</span> 成功为您完成自动打卡。</p>
        <p>您无需进行任何操作，此邮件仅作通知。</p>
    </div>
    <p class="footer">感谢您的使用！</p>
</body>
</html>
"""

FAILURE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>打卡失败通知</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; margin: 20px; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); }}
        h1 {{ color: #d9534f; }}
        .message {{ background-color: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 20px; }}
        .important {{ font-weight: bold; color: #d9534f; }}
        .footer {{ font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <h1>通知：自动打卡失败!</h1>
    <div class="message">
        <p>{name}，您好!</p>
        <p>系统于 <span class="important">{send_time}</span> 尝试为您自动打卡时失败。</p>
        <p><strong>失败原因:</strong> 服务器返回 "需要登录"，这通常意味着您的 <span class="important">Token 已失效</span>。</p>
        <p><strong>请您立即刷新您的 Token，以确保后续打卡能够成功。</strong></p>
    </div>
    <p class="footer">感谢您的使用！</p>
</body>
</html>
"""


def get_email_settings():
    """
    从 config.ini 读取邮件配置

    Returns:
        dict: 邮件配置，如果配置文件不存在则返回 None
    """
    if not settings.EMAIL_CONFIG_FILE.exists():
        logger.warning("找不到 config.ini，无法发送邮件")
        return None

    try:
        config_parser = configparser.ConfigParser()
        config_parser.read(settings.EMAIL_CONFIG_FILE, encoding='utf-8')

        if 'Email' not in config_parser:
            logger.warning("config.ini 中缺少 [Email] 配置段")
            return None

        return config_parser['Email']

    except Exception as e:
        logger.error(f"读取邮件配置失败: {e}")
        return None


def _send_email(to_email: str, subject: str, html_content: str, email_settings: dict) -> bool:
    """
    发送邮件

    Args:
        to_email: 收件人邮箱
        subject: 邮件主题
        html_content: HTML 邮件内容
        email_settings: 邮件配置

    Returns:
        是否发送成功
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = email_settings['senderemail']
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        with smtplib.SMTP_SSL(email_settings['smtpserver'], int(email_settings['smtpport'])) as server:
            server.login(email_settings['senderemail'], email_settings['senderpassword'])
            server.sendmail(msg["From"], msg["To"], msg.as_string())

        logger.info(f"已成功向 {to_email} 发送邮件，主题: {subject}")
        return True

    except Exception as e:
        logger.error(f"向 {to_email} 发送邮件时失败: {e}")
        return False


def send_expiration_notification(email: str, jwt_exp: str) -> bool:
    """
    发送 Token 到期提醒邮件

    Args:
        email: 收件人邮箱
        jwt_exp: Token 过期时间戳

    Returns:
        是否发送成功
    """
    email_settings = get_email_settings()
    if not email_settings:
        return False

    try:
        exp_time = time.strftime("%Y年%m月%d日 %H:%M:%S", time.localtime(float(jwt_exp)))
        send_time = time.strftime("%Y年%m月%d日 %H:%M:%S", time.localtime())

        html = EXPIRATION_HTML_TEMPLATE.format(
            name=email,
            exp_time=exp_time,
            send_time=send_time
        )

        return _send_email(email, "接龙管家Token到期通知", html, email_settings)

    except Exception as e:
        logger.error(f"发送过期通知邮件失败: {e}")
        return False


def send_success_notification(email: str) -> bool:
    """
    发送打卡成功通知邮件

    Args:
        email: 收件人邮箱

    Returns:
        是否发送成功
    """
    email_settings = get_email_settings()
    if not email_settings:
        return False

    try:
        send_time = time.strftime("%Y年%m月%d日 %H:%M:%S", time.localtime())

        html = SUCCESS_HTML_TEMPLATE.format(
            name=email,
            send_time=send_time
        )

        return _send_email(email, "自动打卡成功通知", html, email_settings)

    except Exception as e:
        logger.error(f"发送成功通知邮件失败: {e}")
        return False


def send_failure_notification(email: str) -> bool:
    """
    发送打卡失败通知邮件

    Args:
        email: 收件人邮箱

    Returns:
        是否发送成功
    """
    email_settings = get_email_settings()
    if not email_settings:
        return False

    try:
        send_time = time.strftime("%Y年%m月%d日 %H:%M:%S", time.localtime())

        html = FAILURE_HTML_TEMPLATE.format(
            name=email,
            send_time=send_time
        )

        return _send_email(email, "打卡失败 - 需要刷新Token", html, email_settings)

    except Exception as e:
        logger.error(f"发送失败通知邮件失败: {e}")
        return False
