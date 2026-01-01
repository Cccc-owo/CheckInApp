import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import logging

from backend.config import settings

logger = logging.getLogger(__name__)

# --- 邮件模板 ---

EXPIRATION_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Token 到期提醒</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            max-width: 600px;
            margin: 40px auto;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #f44336 0%, #e91e63 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .content {{
            padding: 30px 40px;
        }}
        .alert-box {{
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 16px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .info-item {{
            margin: 16px 0;
            padding: 12px;
            background-color: #f9f9f9;
            border-radius: 6px;
        }}
        .info-item strong {{
            color: #333;
            display: inline-block;
            min-width: 100px;
        }}
        .highlight {{
            color: #f44336;
            font-weight: 600;
        }}
        .action-button {{
            display: inline-block;
            margin: 20px 0;
            padding: 12px 32px;
            background: linear-gradient(135deg, #f44336 0%, #e91e63 100%);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
        }}
        .footer {{
            background-color: #fafafa;
            padding: 20px;
            text-align: center;
            color: #999;
            font-size: 12px;
            border-top: 1px solid #eeeeee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ Token 即将到期提醒</h1>
        </div>
        <div class="content">
            <p>您好，</p>
            <div class="alert-box">
                <p>您的接龙打卡系统 <span class="highlight">Token 即将到期</span>，为避免影响自动打卡功能，请尽快刷新您的 Token。</p>
            </div>
            <div class="info-item">
                <strong>到期时间：</strong><span class="highlight">{exp_time}</span>
            </div>
            <div class="info-item">
                <strong>通知时间：</strong>{send_time}
            </div>
            <p style="margin-top: 20px; color: #666;">
                请登录系统，前往 <strong>用户设置</strong> 页面刷新您的 Token，以确保自动打卡功能正常运行。
            </p>
        </div>
        <div class="footer">
            <p>此邮件由接龙自动打卡系统自动发送，请勿直接回复</p>
            <p>CheckIn App V2 © 2026</p>
        </div>
    </div>
</body>
</html>
"""

SUCCESS_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>打卡成功通知</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            max-width: 600px;
            margin: 40px auto;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .content {{
            padding: 30px 40px;
        }}
        .success-icon {{
            text-align: center;
            font-size: 64px;
            margin: 20px 0;
        }}
        .success-box {{
            background-color: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 16px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .info-item {{
            margin: 16px 0;
            padding: 12px;
            background-color: #f9f9f9;
            border-radius: 6px;
        }}
        .info-item strong {{
            color: #333;
            display: inline-block;
            min-width: 100px;
        }}
        .highlight {{
            color: #4caf50;
            font-weight: 600;
        }}
        .footer {{
            background-color: #fafafa;
            padding: 20px;
            text-align: center;
            color: #999;
            font-size: 12px;
            border-top: 1px solid #eeeeee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ 打卡成功</h1>
        </div>
        <div class="content">
            <div class="success-icon">🎉</div>
            <p>您好，</p>
            <div class="success-box">
                <p><strong>自动打卡已成功完成！</strong></p>
            </div>
            <div class="info-item">
                <strong>打卡时间：</strong><span class="highlight">{send_time}</span>
            </div>
            <div class="info-item">
                <strong>打卡状态：</strong><span class="highlight">成功 ✓</span>
            </div>
            <p style="margin-top: 20px; color: #666;">
                您无需进行任何操作，系统已自动为您完成打卡。此邮件仅作通知。
            </p>
        </div>
        <div class="footer">
            <p>此邮件由接龙自动打卡系统自动发送，请勿直接回复</p>
            <p>CheckIn App V2 © 2026</p>
        </div>
    </div>
</body>
</html>
"""

FAILURE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>打卡失败通知</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            max-width: 600px;
            margin: 40px auto;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #f44336 0%, #e91e63 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .content {{
            padding: 30px 40px;
        }}
        .error-icon {{
            text-align: center;
            font-size: 64px;
            margin: 20px 0;
        }}
        .error-box {{
            background-color: #ffebee;
            border-left: 4px solid #f44336;
            padding: 16px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .info-item {{
            margin: 16px 0;
            padding: 12px;
            background-color: #f9f9f9;
            border-radius: 6px;
        }}
        .info-item strong {{
            color: #333;
            display: inline-block;
            min-width: 100px;
        }}
        .highlight {{
            color: #f44336;
            font-weight: 600;
        }}
        .action-box {{
            background-color: #fff3e0;
            padding: 16px;
            margin: 20px 0;
            border-radius: 6px;
            border: 1px solid #ffb74d;
        }}
        .action-box h3 {{
            margin: 0 0 12px 0;
            color: #ff6f00;
            font-size: 16px;
        }}
        .action-box ul {{
            margin: 8px 0;
            padding-left: 20px;
        }}
        .action-box li {{
            margin: 6px 0;
            color: #666;
        }}
        .footer {{
            background-color: #fafafa;
            padding: 20px;
            text-align: center;
            color: #999;
            font-size: 12px;
            border-top: 1px solid #eeeeee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>❌ 打卡失败通知</h1>
        </div>
        <div class="content">
            <div class="error-icon">⚠️</div>
            <p>您好，</p>
            <div class="error-box">
                <p><strong>自动打卡失败，需要您的关注！</strong></p>
            </div>
            <div class="info-item">
                <strong>失败时间：</strong>{send_time}
            </div>
            <div class="info-item">
                <strong>失败原因：</strong><span class="highlight">Token 已失效（需要登录）</span>
            </div>
            <div class="action-box">
                <h3>📋 需要您执行以下操作：</h3>
                <ul>
                    <li>登录接龙自动打卡系统</li>
                    <li>刷新您的 Authorization Token</li>
                    <li>确认 Token 更新成功</li>
                </ul>
            </div>
            <p style="margin-top: 20px; color: #666;">
                Token 失效是正常现象，通常在一段时间后会自动过期。刷新 Token 后，系统将恢复自动打卡功能。
            </p>
        </div>
        <div class="footer">
            <p>此邮件由接龙自动打卡系统自动发送，请勿直接回复</p>
            <p>CheckIn App V2 © 2026</p>
        </div>
    </div>
</body>
</html>
"""


def get_email_settings():
    """
    从环境变量读取邮件配置

    如果 SMTP_SERVER、SMTP_PORT 或 SMTP_SENDER_EMAIL 有任一为空，则禁用邮件功能

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
        'smtpserver': settings.SMTP_SERVER,
        'smtpport': settings.SMTP_PORT,
        'senderemail': settings.SMTP_SENDER_EMAIL,
        'senderpassword': settings.SMTP_SENDER_PASSWORD,
        'use_ssl': settings.SMTP_USE_SSL
    }


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

        # 根据配置选择使用 SSL 或普通 SMTP
        if email_settings.get('use_ssl', True):
            with smtplib.SMTP_SSL(email_settings['smtpserver'], int(email_settings['smtpport'])) as server:
                server.login(email_settings['senderemail'], email_settings['senderpassword'])
                server.sendmail(msg["From"], msg["To"], msg.as_string())
        else:
            with smtplib.SMTP(email_settings['smtpserver'], int(email_settings['smtpport'])) as server:
                server.starttls()
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
