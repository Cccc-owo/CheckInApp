from apscheduler.schedulers.background import BackgroundScheduler
import configparser
import csv
from datetime import datetime, timezone
from filelock import FileLock, Timeout
from flask import Flask, render_template, request, jsonify
import json
import jwt
import logging
from logging.handlers import RotatingFileHandler
import os
import threading
import time
from urllib.parse import unquote
import atexit

# 导入其他模块
from shared_config import (
    CONFIG_PATH, LOG_PATH, SCHEDULER_LOCK, SESSIONS_DIR, CONFIG_INI_PATH,
    CONFIG_FILE_LOCK, CSV_FIELDNAMES, CHECKIN_HOUR, CHECKIN_MIN
)
from token_refresher import get_token_headless
from email_notifier import notification_worker_loop
from check_in_worker import perform_check_in

# --- Flask App 设置 ---
app = Flask(__name__)

# 1. 定义日志格式和处理器
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
log_handler = RotatingFileHandler(LOG_PATH, mode='a', maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
log_handler.setFormatter(log_formatter)

# 2. 获取并配置根记录器 (root logger)
# 这是关键：所有模块通过 getLogger(__name__) 创建的子记录器，都会将日志传递给根记录器
root_logger = logging.getLogger()
root_logger.addHandler(log_handler)
root_logger.setLevel(logging.INFO)

# 3. 移除Flask默认的handler，防止日志重复
app.logger.handlers.clear()
app.logger.propagate = True # 确保app.logger也将日志传递给根记录器

# 4. 将werkzeug的日志也重定向到我们的文件
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.propagate = True # 确保werkzeug日志也传递给根记录器

# --- 辅助函数 ---
def read_configs():
    """加固后的读取函数，增加日志，处理空文件和不存在的情况"""
    with CONFIG_FILE_LOCK:
        if not os.path.exists(CONFIG_PATH):
            app.logger.warning(f"配置文件 {CONFIG_PATH} 不存在，将返回空列表。")
            return []
        try:
            with open(CONFIG_PATH, mode='r', encoding='utf-8-sig') as file:
                content = file.read().strip()
                if not content:
                    app.logger.warning(f"配置文件 {CONFIG_PATH} 为空，返回空列表。")
                    return []
                file.seek(0)
                reader = csv.DictReader(file)
                rows = list(reader)
                app.logger.info(f"成功从 {CONFIG_PATH} 读取 {len(rows)} 条配置。")
                return rows
        except Exception as e:
            app.logger.error(f"读取config.csv时出错: {e}")
            return []

def write_configs(rows):
    """加固后的写入函数，始终使用全局列名"""
    with CONFIG_FILE_LOCK:
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8-sig', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=CSV_FIELDNAMES)
                writer.writeheader()
                writer.writerows(rows)
            app.logger.info(f"成功将 {len(rows)} 条配置写入到 {CONFIG_PATH}。")
        except Exception as e:
            app.logger.error(f"写入config.csv时出错: {e}")

def append_new_config(new_row_dict):
    """只在文件末尾追加一行新配置，更安全"""
    with CONFIG_FILE_LOCK:
        # 检查文件是否存在或为空，如果为空，则先写入标题行
        file_exists = os.path.exists(CONFIG_PATH)
        is_empty = not file_exists or os.path.getsize(CONFIG_PATH) == 0

        try:
            with open(CONFIG_PATH, 'a', encoding='utf-8-sig', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=CSV_FIELDNAMES)
                if is_empty:
                    writer.writeheader()
                writer.writerow(new_row_dict)
            app.logger.info(f"成功追加新配置到 {CONFIG_PATH}。")
        except Exception as e:
            app.logger.error(f"追加新配置到 {CONFIG_PATH} 时失败: {e}")

def is_token_expired(exp_timestamp):
    if not exp_timestamp or not exp_timestamp.isdigit(): return True
    return datetime.now(timezone.utc).timestamp() > int(exp_timestamp)

def cleanup_stale_sessions():
    """后台任务：清理超过10分钟未完成的刷新会话，运行一次后退出。"""
    # 使用 app.logger 来记录日志
    app.logger.info("Scheduler: 正在执行过期会话清理任务...")
    try:
        now = time.time()
        cleared_count = 0
        for filename in os.listdir(SESSIONS_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(SESSIONS_DIR, filename)
                file_time = os.path.getmtime(filepath)
                if now - file_time > 600: # 超过10分钟
                    os.remove(filepath)
                    cleared_count += 1
        if cleared_count > 0:
            app.logger.info(f"Scheduler: 成功清理了 {cleared_count} 个过期的会话文件。")
    except Exception as e:
        app.logger.error(f"Scheduler: 清理会话文件时出错: {e}")

def run_all_checkins(triggered_by="Scheduler"):
    try:
        app.logger.info(f"开始执行一轮打卡任务 (触发源: {triggered_by})...")
        configs = read_configs()
        if not configs:
            app.logger.warning("配置文件为空，跳过本轮打卡。")
            return
        
        email_settings = None
        if os.path.exists(CONFIG_INI_PATH):
            config_parser = configparser.ConfigParser()
            config_parser.read(CONFIG_INI_PATH)
            if 'Email' in config_parser:
                email_settings = config_parser['Email']
                
        for config in configs:
            auth_token = config.get('Authorization')
            if auth_token:
                perform_check_in(config) 
            else:
                signature = config.get('Signature', '未知用户')
                app.logger.warning(f"用户 {signature} 的 'Authorization' Token 为空，已跳过打卡。")
                app.logger.debug(f"    该用户的完整配置为: {config}")

        app.logger.info(f"本轮打卡任务已全部提交。")
    except Exception as e:
        # --- 这是关键的顶层异常捕获 ---
        app.logger.critical(f"执行 'run_all_checkins' 时发生未捕获的严重错误: {e}", exc_info=True)

# --- 路由 / API ---
@app.route('/')
def index():
    configs = read_configs()
    for config in configs:
        config['show_qrcode'] = is_token_expired(config.get('jwt_exp'))
    return render_template('index.html', configs=configs)

@app.route('/request_qrcode', methods=['POST'])
def request_qrcode():
    # 1. 从POST请求的JSON body中获取signature
    data = request.json
    signature = data.get('signature')
    if not signature:
        return jsonify({'status': 'error', 'message': 'Signature is required'}), 400

    # 2. 使用 signature 构建 session_id，以确保唯一性
    session_id = f"{signature}_{int(time.time())}"
    
    # 启动线程时，只传递 session_id，这与你的 token_refresher.py 匹配
    threading.Thread(target=get_token_headless, args=(session_id,)).start()
    return jsonify({'status': 'success', 'session_id': session_id})

@app.route('/get_qrcode_image/<session_id>')
def get_qrcode_image(session_id):
    session_filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    for _ in range(30):
        if os.path.exists(session_filepath):
            try:
                with open(session_filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data.get('qr_image_data'):
                    return jsonify({'status': 'success', 'image_data': data['qr_image_data']})
            except (json.JSONDecodeError, IOError) as e:
                app.logger.error(f"读取会话文件 {session_filepath} 失败: {e}")
        time.sleep(1)
    return jsonify({'status': 'error', 'message': '获取二维码超时'}), 408

@app.route('/check_refresh_status/<session_id>')
def check_refresh_status(session_id):
    session_filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(session_filepath):
        return jsonify({'status': 'waiting'})

    try:
        with open(session_filepath, 'r', encoding='utf-8') as f:
            session = json.load(f)
        status = session.get('status')

        if status == 'success':
            signature_to_update = session_id.split('_')[0]

            raw_token_value = session['token']
            pure_jwt = unquote(raw_token_value)
            if pure_jwt.lower().startswith('bearer '):
                pure_jwt = pure_jwt[7:]

            new_exp, new_sub = '0', ''
            try:
                decoded = jwt.decode(pure_jwt, options={"verify_signature": False})
                new_exp, new_sub = decoded.get('exp', '0'), decoded.get('sub', '')
                app.logger.info(f"成功解码JWT for sub {new_sub}, exp: {new_exp}")
            except Exception as e:
                app.logger.error(f"解码新的JWT时失败: {e}")

            rows = read_configs()
            is_updated = False
            for row in rows:
                # 使用 signature 来查找要更新的行
                if row['Signature'] == signature_to_update:
                    row['Authorization'], row['jwt_exp'], row['jwt_sub'] = pure_jwt, new_exp, new_sub
                    is_updated = True
                    # 找到并更新后，可以跳出循环，提高效率
                    break 

            if not is_updated:
                 app.logger.error(f"严重错误：在更新Token时，未在config.csv中找到Signature {signature_to_update}")

            write_configs(rows)

            os.remove(session_filepath) # 成功后删除临时文件
            return jsonify({'status': 'success'})

        elif status == 'error':
            message = session.get('message', '未知错误')
            os.remove(session_filepath) # 失败后也删除
            return jsonify({'status': 'error', 'message': message})
            
        return jsonify({'status': status}) # e.g., 'waiting_scan'
    
    except Exception as e:
        app.logger.error(f"检查状态时出错 {session_filepath}: {e}")
        return jsonify({'status': 'error', 'message': '读取状态文件失败'})

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.json
    rows = read_configs() # 读取所有现有用户
    
    # 1. 使用 Signature 检查用户是否已存在
    for row in rows:
        if row['Signature'] == data['Signature']:
            app.logger.warning(f"尝试添加已存在的用户: Signature {data['Signature']}")
            # 如果用户已存在，直接为他请求二维码，而不是重复添加
            # 这需要模拟 request_qrcode 的逻辑
            signature = data['Signature']
            session_id = f"{signature}_{int(time.time())}"
            threading.Thread(target=get_token_headless, args=(session_id,)).start()
            return jsonify({'status': 'success', 'session_id': session_id})

    # 创建一个完整的新行
    new_row = {field: '' for field in CSV_FIELDNAMES}
    new_row.update({
        'ThreadId': data['ThreadId'],
        'Signature': data['Signature'],
        'Texts': data['Texts'],
        'Values': data['Values'],
        'email': data['Email'],
        'jwt_exp': '0'
    })
    append_new_config(new_row)
    
    signature = data['Signature']
    session_id = f"{signature}_{int(time.time())}"
    threading.Thread(target=get_token_headless, args=(session_id,)).start()
    return jsonify({'status': 'success', 'session_id': session_id})

@app.route('/api/checkin_all', methods=['POST'])
def trigger_checkin_all():
    """API端点，用于手动触发所有用户的打卡"""
    try:
        # 在后台线程中运行，以防用户数量多时导致请求超时
        # 我们传递 "Manual Trigger" 来区分日志来源
        threading.Thread(target=run_all_checkins, args=("Manual Trigger",)).start()
        return jsonify({'status': 'success', 'message': '已成功触发全部重新打卡，请稍后在日志中查看结果。'})
    except Exception as e:
        app.logger.error(f"手动触发全部打卡时失败: {e}")
        return jsonify({'status': 'error', 'message': '触发失败，请查看服务器日志。'}), 500

# --------------------------------------------------------------------------
#  APScheduler 后台任务调度
# --------------------------------------------------------------------------

# 创建一个锁文件路径
# 确保这个文件位于一个所有 worker 都能访问到的地方
lock = FileLock(SCHEDULER_LOCK, timeout=5) # 设置5秒超时

try:
    # 尝试非阻塞地获取锁
    lock.acquire()

    # --- 只有成功获取锁的进程才能执行以下代码 ---
    app.logger.info("Scheduler lock acquired by this process. Initializing scheduler...")

    # 1. 初始化调度器
    scheduler = BackgroundScheduler(daemon=True, timezone='Asia/Shanghai')

    # 2. 添加你的后台任务
    scheduler.add_job(
        func=run_all_checkins,
        trigger='cron',
        hour=CHECKIN_HOUR,
        minute=CHECKIN_MIN,
        id='daily_check_in_job',
        name='执行每日打卡任务',
        replace_existing=True
    )
    app.logger.info(f"已添加每日打卡任务，将在每天 {CHECKIN_HOUR}:{CHECKIN_MIN:02d} 执行。")

    scheduler.add_job(
        func=cleanup_stale_sessions,
        trigger='interval',
        hours=24,
        id='cleanup_sessions_job',
        name='清理过期的会话文件',
        replace_existing=True
    )
    app.logger.info("已添加定期清理会话任务，每 24 小时执行一次。")
    
    scheduler.add_job(
        func=notification_worker_loop,
        trigger='interval',
        minutes=30,
        id='token_expiry_notification_job',
        name='检查Token过期并发送邮件',
        replace_existing=True
    )
    app.logger.info("已添加Token过期检查任务，每 30 分钟执行一次。")

    # 3. 启动调度器
    scheduler.start()
    app.logger.info("APScheduler 已成功启动。")

    # 4. 注册一个应用退出时的回调函数，确保调度器被安全关闭
    #    这个也只在持有锁的进程中注册
    atexit.register(lambda: scheduler.shutdown())

except Timeout:
    # 如果获取锁超时，说明另一个进程已经启动了调度器
    app.logger.info("Could not acquire scheduler lock, another process is handling scheduling.")
finally:
    # 确保在进程退出时释放锁 (尽管 with 语句通常能处理好)
    # lock.release() # 在这个场景下，锁应该由持有它的进程一直持有，所以不需要手动释放
    pass

if __name__ == '__main__':
    # 确保sessions目录存在
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR)
    
    app.run(debug=False, host='0.0.0.0', port=5000)