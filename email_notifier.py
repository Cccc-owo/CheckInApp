import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import csv
import os
import configparser

from shared_config import CONFIG_PATH, CONFIG_FILE_LOCK, get_logger, CONFIG_INI_PATH

logger = get_logger(__name__)

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
        <p>您的 <span class="important">token</span> 已经到期，请前往 <span class="important"><a href="http://localhost:5000">http://localhost:5000</a></span> 重新刷新您的 token，否则您的自动打卡功能将会失效。</p>
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
        h1 {{ color: #d9534f; }} /* 红色标题 */
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
        <p><strong>请您立即前往 <span class="important"><a href="http://localhost:5000">http://localhost:5000</a></span> 刷新您的 Token，以确保后续打卡能够成功。</strong></p>
    </div>
    <p class="footer">感谢您的使用！</p>
</body>
</html>
"""

def _send_email(to_email, subject, html_content, email_settings):
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
    except Exception as e:
        logger.error(f"向 {to_email} 发送邮件时失败: {e}")

def send_notification_email(user_config, email_settings):
    """发送Token到期提醒邮件"""
    html = EXPIRATION_HTML_TEMPLATE.format(
        name=user_config["email"],
        exp_time=time.strftime("%Y年%m月%d日 %H:%M:%S", time.localtime(float(user_config["jwt_exp"]))),
        send_time=time.strftime("%Y年%m月%d日 %H:%M:%S", time.localtime())
    )
    _send_email(user_config["email"], "接龙管家Token到期通知", html, email_settings)

def send_success_notification(user_config, email_settings):
    """发送打卡成功通知邮件"""
    html = SUCCESS_HTML_TEMPLATE.format(
        name=user_config["email"],
        send_time=time.strftime("%Y年%m月%d日 %H:%M:%S", time.localtime())
    )
    _send_email(user_config["email"], "自动打卡成功通知", html, email_settings)

def send_failure_notification(user_config, email_settings):
    """发送打卡失败通知邮件"""
    html = FAILURE_HTML_TEMPLATE.format(
        name=user_config["email"],
        send_time=time.strftime("%Y年%m月%d日 %H:%M:%S", time.localtime())
    )
    _send_email(user_config["email"], "【紧急】自动打卡失败 - 需要刷新Token", html, email_settings)

def notification_worker_loop():
    """后台任务：检查Token是否即将过期，并发送邮件提醒。单次运行。"""
    logger.info("Scheduler: 正在执行邮件过期通知检查...")
    config_ini_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    
    try:
        # 1. 读取邮件配置
        if not os.path.exists(config_ini_path):
            logger.warning("Scheduler: 找不到 config.ini，邮件通知功能将跳过。")
            return # 直接退出
            
        config_parser = configparser.ConfigParser()
        config_parser.read(config_ini_path)
        if 'Email' not in config_parser:
            logger.warning("Scheduler: config.ini 中缺少 [Email] 部分，跳过。")
            return
        email_settings = config_parser['Email']

        # 2. 线程安全地读取用户配置
        with CONFIG_FILE_LOCK:
            if not os.path.exists(CONFIG_PATH):
                configs = []
            else:
                with open(CONFIG_PATH, mode='r', encoding='utf-8-sig') as file:
                    configs = list(csv.DictReader(file))
        
        # 3. 检查每个用户的Token是否即将过期
        now = time.time()
        for user in configs:
            if not user.get('jwt_exp') or not user.get('email'):
                continue

            try:
                exp_time = float(user['jwt_exp'])
                # 检查是否在 30 分钟内过期，并且尚未发送过提醒（可选，防止重复发送）
                if 0 < (now - exp_time) < 1800:
                    logger.info(f"{user['Signature']} 的Token过期，准备发送邮件...")
                    send_notification_email(user, email_settings)
            except (ValueError, TypeError):
                logger.warning(f"Scheduler: 跳过用户 {user['Signature']}，因为jwt_exp格式不正确: {user['jwt_exp']}")
                continue
        logger.info("Scheduler: 邮件到期检查完成。")
    except Exception as e:
        logger.error(f"Scheduler: 邮件通知任务发生严重错误: {e}")
