import requests
import configparser
import csv
import json
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from shared_config import (
    CONFIG_INI_PATH, CONFIG_PATH, CONFIG_FILE_LOCK, get_logger,
    CHROME_BINARY_PATH, CHROMEDRIVER_PATH
)
from email_notifier import send_success_notification, send_failure_notification

logger = get_logger(__name__)

def read_configs():
    """线程安全地读取配置文件"""
    with CONFIG_FILE_LOCK:
        if not os.path.exists(CONFIG_PATH):
            return []
        with open(CONFIG_PATH, mode='r', encoding='utf-8-sig') as file:
            return list(csv.DictReader(file))

def get_live_x_api_payload(auth_token):
    """
    启动一个临时的无头浏览器会话，只为了获取新鲜的 x-api-request-payload。
    """
    logger.info("正在启动临时浏览器会话以监听网络日志...")
    
    service = Service(executable_path=CHROMEDRIVER_PATH) if CHROMEDRIVER_PATH else Service()
    chrome_options = Options()
    chrome_options.binary_location = CHROME_BINARY_PATH
    
    # --- 1. (最关键) 开启性能日志记录功能 ---
    # 这会让浏览器记录下所有的网络事件
    logging_prefs = {'performance': 'ALL'}
    chrome_options.set_capability('goog:loggingPrefs', logging_prefs)

    # --- Headless模式配置 ---
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    payload_signature = None
    try:
        # 1. 导航到一个同源空白页，用于设置Cookie
        driver.get("https://i.jielong.com/my-class")
        
        # 3. 注入我们的长期Token
        driver.add_cookie({
            'name': 'token',
            'value': auth_token,
            'domain': '.jielong.com'
        })

        # 4. 导航到触发API的页面，这将产生网络日志
        driver.get("https://i.jielong.com/my-form")
        
        # 5. 等待几秒，确保页面有足够的时间加载并发起API请求
        max_wait_time = 20  # 最多等待20秒
        start_time = time.time()
        found = False
        while time.time() - start_time < max_wait_time:
            logs = driver.get_log('performance')
            for entry in logs:
                log = json.loads(entry['message'])['message']
                if log['method'] == 'Network.requestWillBeSent':
                    headers = log.get('params', {}).get('request', {}).get('headers', {})
                    headers_lower = {k.lower(): v for k, v in headers.items()}
                    if 'x-api-request-payload' in headers_lower:
                        payload_signature = headers_lower['x-api-request-payload']
                        logger.info("成功通过网络日志捕获到现场的 x-api-request-payload！")
                        found = True
                        break
            if found:
                break
            time.sleep(1) # 每次轮询间隔1秒
        
        if not payload_signature:
            raise Exception(f"在 {max_wait_time} 秒内未能通过网络日志捕获到 x-api-request-payload。")
    
    except Exception as e:
        logger.error(f"获取现场 x-api-request-payload 时失败: {e}")
        driver.save_screenshot(os.path.join(os.path.dirname(__file__), 'payload_debug.png'))
    finally:
        driver.quit()
        
    return payload_signature

def perform_check_in(config):
    logger.info(f"Selenium打卡: 正在为 Signature: {config['Signature']} 执行打卡...")
    
    auth_token = config.get('Authorization')
    if not auth_token:
        logger.error(f"Signature: {config['Signature']} 的长期Token为空，跳过。")
        return
    
    payload_signature = get_live_x_api_payload(auth_token)
    if not payload_signature:
        logger.error(f"Signature: {config['Signature']} 未能获取到现场签名，打卡中止。")
        return

    email_settings = None
    if config.get('email'):
        if os.path.exists(CONFIG_INI_PATH):
            config_parser = configparser.ConfigParser()
            config_parser.read(CONFIG_INI_PATH)
            # 使用 .get() 安全访问
            if 'Email' in config_parser:
                email_settings = config_parser['Email']
            else:
                 logger.warning("在 config.ini 中找不到 [Email] 配置段，无法发送邮件。")
        else:
            logger.warning("找不到 config.ini，无法发送邮件通知。")

    try:
        payload = {
            "Id": 0,
            "ThreadId": config['ThreadId'],
            "Number": "",
            "Signature": config['Signature'],
            "RecordValues": [{
                "FieldId": 1,
                "Values": [config['Values']],
                "Texts": [config['Texts']],
                "HasValue": True,
                "Scores": [],
                "Files": [],
                "MatrixValues": [],
                "CustomTableValues": [],
                "FillInMatrixFieldValues": [],
                "MatrixFormValues": []
            }],
            "DateTarget": "",
            "IsNeedManualAudit": False,
            "MinuteTarget": -1,
            "IsNameNumberComfirm": False
        }
        
        headers = {
            'User-Agent': "Mozilla%2f5.0+(Linux%3b+Android+16%3b+wv)+AppleWebKit%2f537.36+(KHTML%2c+like+Gecko)+Chrome%2f142.0.0.0+Safari%2f537.36+QQ%2f9.2.30.31620+QQ%2fMiniApp",
            'Accept-Encoding': "gzip",
            'Content-Type': "application/json",
            'authorization': f"Bearer {auth_token}",
            'x-api-request-referer': "https://appservice.qq.com/1110276759",
            'x-api-request-payload': payload_signature,
            'referer': "https://appservice.qq.com/1110276759/8.10.1.7/page-frame.html",
            'platform': "qq",
            'x-api-request-mode': "cors",
        }
        
        url = "https://api.jielong.com/api/CheckIn/EditRecord"
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        response_text = response.text
        logger.info(f"Signature: {config['Signature']} 打卡请求完成！响应: {response_text}")
        # logger.info(f"payload = {payload}")
        # logger.info(f"headers = {headers}")
        # logger.info(f"url = {url}")
        
        # 判断响应内容
        if email_settings:
            if "打卡成功" in response_text:
                logger.info(f"检测到成功关键字，为 {config['Signature']} 发送成功邮件...")
                send_success_notification(config, email_settings)
            elif ("QSfqFrHF0jbMZcd3DVuvf6k5HceMjOlDwzX1b/SJ4agLnRkO" in response_text or
                  "请先授权登录小程序" in response_text): # 打卡失败附带的Data 或 授权失效
                logger.warning(f"检测到登录失败关键字，为 {config['Signature']} 发送失败提醒邮件...")
                send_failure_notification(config, email_settings)
        
        # 检查HTTP状态码，如果需要的话
        response.raise_for_status()
        return response.text

    except requests.exceptions.RequestException as e:
        logger.error(f"为 Signature: {config['Signature']} 打卡时请求失败: {e}")
        if e.response is not None:
            logger.error(f"    响应状态码: {e.response.status_code}, 响应内容: {e.response.text}")
            return e.response.text # 同样返回响应文本
        return None # 请求彻底失败
    except Exception as e:
        logger.error(f"为 Signature: {config['Signature']} 打卡时发生未知错误: {e}")
        return None
