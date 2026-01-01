import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import User

logger = logging.getLogger(__name__)


class EmailService:
    """邮件通知服务"""

    @staticmethod
    def send_email(to_emails: List[str], subject: str, body_html: str) -> bool:
        """
        发送邮件

        Args:
            to_emails: 收件人邮箱列表
            subject: 邮件主题
            body_html: 邮件正文（HTML 格式）

        Returns:
            是否发送成功
        """
        # 检查邮件配置
        if not all([settings.SMTP_SERVER, settings.SMTP_SENDER_EMAIL, settings.SMTP_SENDER_PASSWORD]):
            logger.warning("邮件配置不完整，跳过发送邮件")
            return False

        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['From'] = settings.SMTP_SENDER_EMAIL
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject

            # 添加 HTML 正文
            html_part = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(html_part)

            # 连接 SMTP 服务器并发送
            if settings.SMTP_USE_SSL:
                server = smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT)
            else:
                server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
                server.starttls()

            server.login(settings.SMTP_SENDER_EMAIL, settings.SMTP_SENDER_PASSWORD)
            server.sendmail(settings.SMTP_SENDER_EMAIL, to_emails, msg.as_string())
            server.quit()

            logger.info(f"邮件发送成功: {subject} -> {', '.join(to_emails)}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False

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
        # 查询所有管理员邮箱
        admins = db.query(User).filter(User.role == "admin", User.email.isnot(None)).all()
        admin_emails = [admin.email for admin in admins if admin.email]

        if not admin_emails:
            logger.warning("没有找到管理员邮箱，无法发送通知")
            return False

        # 构建邮件内容
        subject = f"【接龙自动打卡系统】新用户注册通知 - {user.alias}"

        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #667eea;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 0 0 5px 5px;
                }}
                .info-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                .info-table td {{
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                }}
                .info-table td:first-child {{
                    font-weight: bold;
                    width: 120px;
                }}
                .footer {{
                    margin-top: 20px;
                    text-align: center;
                    color: #999;
                    font-size: 12px;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 10px;
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🔔 新用户注册通知</h2>
                </div>
                <div class="content">
                    <p>尊敬的管理员，</p>
                    <p>有新用户注册了接龙自动打卡系统，请及时审批。</p>

                    <table class="info-table">
                        <tr>
                            <td>用户名</td>
                            <td>{user.alias}</td>
                        </tr>
                        <tr>
                            <td>用户 ID</td>
                            <td>{user.id}</td>
                        </tr>
                        <tr>
                            <td>注册时间</td>
                            <td>{user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '未知'}</td>
                        </tr>
                        <tr>
                            <td>注册 IP</td>
                            <td>{user.registered_ip or '未记录'}</td>
                        </tr>
                    </table>

                    <div class="warning">
                        <strong>⚠️ 重要提示：</strong>
                        <p>该用户需要在 24 小时内通过审批，否则账户将被自动删除。</p>
                        <p>请登录管理后台进行审批操作。</p>
                    </div>

                    <p>登录地址：<a href="http://localhost:5173/admin/users">http://localhost:5173/admin/users</a></p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿直接回复。</p>
                    <p>接龙自动打卡系统 © {datetime.now().year}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return EmailService.send_email(admin_emails, subject, body_html)

    @staticmethod
    def notify_check_in_result(user: User, task_info: dict, success: bool, message: str = "") -> bool:
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
        if not user.email:
            logger.info(f"用户 {user.alias} 未设置邮箱，跳过打卡通知")
            return False

        # 构建邮件内容
        status_text = "✅ 成功" if success else "❌ 失败"
        status_color = "#28a745" if success else "#dc3545"

        subject = f"【接龙自动打卡】打卡{status_text} - {user.alias}"

        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: {status_color};
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 0 0 5px 5px;
                }}
                .info-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                .info-table td {{
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                }}
                .info-table td:first-child {{
                    font-weight: bold;
                    width: 120px;
                }}
                .footer {{
                    margin-top: 20px;
                    text-align: center;
                    color: #999;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>打卡通知 {status_text}</h2>
                </div>
                <div class="content">
                    <p>您好，{user.alias}！</p>
                    <p>您的接龙自动打卡任务已执行。</p>

                    <table class="info-table">
                        <tr>
                            <td>执行时间</td>
                            <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                        </tr>
                        <tr>
                            <td>任务 ID</td>
                            <td>{task_info.get('thread_id', '未知')}</td>
                        </tr>
                        <tr>
                            <td>打卡状态</td>
                            <td><strong style="color: {status_color};">{status_text}</strong></td>
                        </tr>
                        {f'<tr><td>详细信息</td><td>{message}</td></tr>' if message else ''}
                    </table>

                    <p>如有问题，请及时检查您的打卡配置。</p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿直接回复。</p>
                    <p>接龙自动打卡系统 © {datetime.now().year}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return EmailService.send_email([user.email], subject, body_html)
