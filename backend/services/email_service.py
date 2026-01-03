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
from typing import List
from sqlalchemy.orm import Session

from backend.models import User
from backend.workers.email_notifier import EmailNotifier
from backend.config import settings

logger = logging.getLogger(__name__)


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
        # 查询所有管理员邮箱
        admins = db.query(User).filter(User.role == "admin", User.email.isnot(None)).all()
        # 使用 str() 转换避免类型检查问题，并过滤空值
        admin_emails: List[str] = []
        for admin in admins:
            email_value = admin.email
            if email_value is not None:  # 使用 is not None 避免布尔转换
                admin_emails.append(str(email_value))

        if not admin_emails:
            logger.warning("没有找到管理员邮箱，无法发送通知")
            return False

        # 构建邮件内容
        subject = f"【接龙自动打卡系统】新用户注册通知 - {user.alias}"

        # 安全获取创建时间
        created_at_value = user.created_at
        created_time = created_at_value.strftime('%Y-%m-%d %H:%M:%S') if created_at_value is not None else '未知'

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
                            <td>{created_time}</td>
                        </tr>
                    </table>

                    <div class="warning">
                        <strong>⚠️ 重要提示：</strong>
                        <p>该用户需要在 24 小时内通过审批，否则账户将被自动删除。</p>
                        <p>请登录管理后台进行审批操作。</p>
                    </div>

                    <p>登录地址：<a href="{settings.FRONTEND_URL}/admin/users">{settings.FRONTEND_URL}/admin/users</a></p>
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

        # 构建邮件内容
        subject = f"【接龙自动打卡系统】账户审批通过 - {user.alias}"

        # 安全获取创建时间
        user_created_at = user.created_at
        created_time = user_created_at.strftime('%Y-%m-%d %H:%M:%S') if user_created_at is not None else '未知'

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
                    background-color: #28a745;
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
                .success-box {{
                    background-color: #d4edda;
                    border-left: 4px solid #28a745;
                    padding: 15px;
                    margin: 15px 0;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🎉 恭喜！账户审批通过</h2>
                </div>
                <div class="content">
                    <p>您好，{user.alias}！</p>
                    <p>恭喜您的账户已通过管理员审批，现在可以使用所有功能了。</p>

                    <div class="success-box">
                        <strong>✅ 审批结果：</strong> 已通过
                        <br>
                        <strong>审批时间：</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </div>

                    <table class="info-table">
                        <tr>
                            <td>用户名</td>
                            <td>{user.alias}</td>
                        </tr>
                        <tr>
                            <td>账户角色</td>
                            <td>{user.role}</td>
                        </tr>
                        <tr>
                            <td>注册时间</td>
                            <td>{created_time}</td>
                        </tr>
                    </table>

                    <p><strong>接下来您可以：</strong></p>
                    <ul>
                        <li>登录系统创建自动打卡任务</li>
                        <li>配置打卡时间和内容</li>
                        <li>查看打卡记录和统计</li>
                    </ul>

                    <p style="text-align: center;">
                        <a href="{settings.FRONTEND_URL}/login" class="btn">立即登录</a>
                    </p>

                    <p style="color: #666; font-size: 14px;">
                        💡 <strong>温馨提示：</strong>如果您还没有设置密码，建议在个人设置中设置密码，方便后续登录。
                    </p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿直接回复。</p>
                    <p>接龙自动打卡系统 © {datetime.now().year}</p>
                </div>
            </div>
        </body>
        </html>
        """

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

        # 构建邮件内容
        subject = f"【接龙自动打卡系统】账户审批结果 - {user.alias}"

        reason_html = f"<p><strong>拒绝原因：</strong>{reason}</p>" if reason else ""

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
                    background-color: #dc3545;
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
                .footer {{
                    margin-top: 20px;
                    text-align: center;
                    color: #999;
                    font-size: 12px;
                }}
                .error-box {{
                    background-color: #f8d7da;
                    border-left: 4px solid #dc3545;
                    padding: 15px;
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>账户审批结果通知</h2>
                </div>
                <div class="content">
                    <p>您好，{user.alias}！</p>
                    <p>很遗憾，您的账户注册申请未能通过审批。</p>

                    <div class="error-box">
                        <strong>❌ 审批结果：</strong> 未通过
                        <br>
                        <strong>处理时间：</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </div>

                    {reason_html}

                    <p>如有疑问，请联系系统管理员。</p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿直接回复。</p>
                    <p>接龙自动打卡系统 © {datetime.now().year}</p>
                </div>
            </div>
        </body>
        </html>
        """

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
        user_email = user.email
        if user_email is None:
            logger.info(f"用户 {user.alias} 未设置邮箱，跳过 Token 过期通知")
            return False

        # 计算剩余时间
        try:
            exp_timestamp = int(jwt_exp)
            current_timestamp = int(datetime.now().timestamp())
            minutes_left = (exp_timestamp - current_timestamp) // 60
        except ValueError:
            minutes_left = 0

        # 构建邮件内容
        subject = f"【接龙自动打卡系统】登录凭证即将过期 - {user.alias}"

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
                    background-color: #ff9800;
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
                .warning-box {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ff9800;
                    padding: 15px;
                    margin: 15px 0;
                }}
                .footer {{
                    margin-top: 20px;
                    text-align: center;
                    color: #999;
                    font-size: 12px;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>⚠️ 登录凭证即将过期</h2>
                </div>
                <div class="content">
                    <p>您好，{user.alias}！</p>
                    <p>您的 QQ 登录凭证即将在 <strong>{minutes_left} 分钟</strong>后过期。</p>

                    <div class="warning-box">
                        <strong>⚠️ 重要提示：</strong>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>登录凭证过期后，系统将无法自动执行您的打卡任务</li>
                            <li>建议尽快登录系统刷新凭证</li>
                            <li>如果您已设置密码，可以使用密码登录后扫码刷新凭证</li>
                        </ul>
                    </div>

                    <p><strong>如何刷新凭证：</strong></p>
                    <ol style="margin: 10px 0; padding-left: 20px;">
                        <li>登录系统（扫码或密码登录）</li>
                        <li>在个人设置旁的按钮中进行刷新 Token</li>
                        <li>使用手机 QQ 扫描二维码完成刷新</li>
                    </ol>

                    <p style="text-align: center;">
                        <a href="{settings.FRONTEND_URL}/login" class="btn">立即登录刷新</a>
                    </p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿直接回复。</p>
                    <p>接龙自动打卡系统 © {datetime.now().year}</p>
                </div>
            </div>
        </body>
        </html>
        """

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

        # 构建邮件内容
        subject = f"【接龙自动打卡系统】登录凭证已过期 - {user.alias}"

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
                    background-color: #dc3545;
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
                .error-box {{
                    background-color: #f8d7da;
                    border-left: 4px solid #dc3545;
                    padding: 15px;
                    margin: 15px 0;
                }}
                .footer {{
                    margin-top: 20px;
                    text-align: center;
                    color: #999;
                    font-size: 12px;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>❌ 登录凭证已过期</h2>
                </div>
                <div class="content">
                    <p>您好，{user.alias}！</p>
                    <p>您的 QQ 登录凭证已过期，系统已无法自动执行打卡任务。</p>

                    <div class="error-box">
                        <strong>⚠️ 重要提示：</strong>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>登录凭证已过期，所有自动打卡任务已暂停</li>
                            <li>请尽快登录系统刷新凭证以恢复服务</li>
                            <li>如果您已设置密码，可以使用密码登录后扫码刷新凭证</li>
                        </ul>
                    </div>

                    <p><strong>如何刷新 Token：</strong></p>
                    <ol style="margin: 10px 0; padding-left: 20px;">
                        <li>登录系统（扫码或密码登录）</li>
                        <li>在个人设置旁的按钮中进行刷新 Token</li>
                        <li>使用手机 QQ 扫描二维码完成刷新</li>
                    </ol>

                    <p style="text-align: center;">
                        <a href="{settings.FRONTEND_URL}/login" class="btn">立即登录刷新</a>
                    </p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿直接回复。</p>
                    <p>接龙自动打卡系统 © {datetime.now().year}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return EmailService.send_email([str(user_email)], subject, body_html)

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
        user_email = user.email
        if user_email is None:
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

        return EmailService.send_email([str(user_email)], subject, body_html)
