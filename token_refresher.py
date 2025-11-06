import os
import logging
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from shared_config import CHROME_BINARY_PATH, CHROMEDRIVER_PATH, DEBUG_PAGE_SOURCE_PATH, DEBUG_SCREENSHOT_PATH, SESSIONS_DIR

logger = logging.getLogger(__name__)

def update_session_file(session_id, data):
    """线程安全地写入会话文件"""
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"写入会话文件 {filepath} 失败: {e}")

def get_session_status(session_id):
    """安全地读取会话文件的状态"""
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # 增加对空文件的判断
            content = f.read()
            if not content:
                return None
            data = json.loads(content)
        return data.get('status')
    except (IOError, json.JSONDecodeError):
        return None

def get_token_headless(session_id):
    service = Service(executable_path=CHROMEDRIVER_PATH)
    chrome_options = Options()
    chrome_options.binary_location = CHROME_BINARY_PATH
    
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
    
    try:
        current_step = "导航到登录页面"
        logger.info(f"Selenium: {current_step}...")
        driver.get("https://i.jielong.com/login?redirectTo=https%3A%2F%2Fi.jielong.com%2F")
        
        wait = WebDriverWait(driver, 60)

        # --- 智能等待流程 ---
        current_step = "查找并点击切换按钮"
        toggle_button_selector = "div.login-wrap .toggle"
        logger.info(f"Selenium: {current_step} ({toggle_button_selector})...")
        toggle_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, toggle_button_selector)))
        toggle_button.click()
        
        current_step = "等待QQ登录容器出现"
        qq_container_selector = "#login_container"
        logger.info(f"Selenium: {current_step} ({qq_container_selector})...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, qq_container_selector)))

        current_step = "等待QQ二维码图片加载"
        qq_qr_image_selector = "#login_container img"
        logger.info(f"Selenium: {current_step} ({qq_qr_image_selector})...")
        qr_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, qq_qr_image_selector)))
        
        logger.info("Selenium: 成功找到QQ二维码元素，正在截图...")
        qr_base64 = qr_element.screenshot_as_base64
        update_session_file(session_id, {'status': 'waiting_scan', 'qr_image_data': qr_base64})

        current_step = "等待用户扫描登录 (Cookie 'token' 出现)"
        cookie_name_to_find = "token"
        logger.info(f"Selenium: {current_step}...")
        WebDriverWait(driver, 300, 1).until(lambda d: d.get_cookie(cookie_name_to_find) is not None)
        
        cookie = driver.get_cookie(cookie_name_to_find)
        if cookie:
            logger.info("Selenium: 成功在Cookie中捕获到Token！")
            update_session_file(session_id, {'status': 'success', 'token': cookie['value']})
        else:
            raise Exception("等待Cookie成功但获取失败")

    except TimeoutException:
        if get_session_status(session_id) == 'success':
            logger.warning(f"Selenium ({session_id}): 一个并发线程超时，但会话已成功，将忽略此超时。")
        else:
            error_message = f"操作超时！卡在了步骤: '{current_step}'。请检查CSS选择器或网络。"
            logger.error(f"Selenium ({session_id}): {error_message}")
            driver.save_screenshot(DEBUG_SCREENSHOT_PATH)
            with open(DEBUG_PAGE_SOURCE_PATH, 'w', encoding='utf-8') as f: f.write(driver.page_source)
            logger.error(f"Selenium ({session_id}): 调试截图和源码已保存。当前URL: {driver.current_url}")
            update_session_file(session_id, {'status': 'error', 'message': error_message})

    except Exception as e:
        # --- 同样地，在其他异常中也加入检查 ---
        if get_session_status(session_id) == 'success':
            logger.warning(f"Selenium ({session_id}): 一个并发线程出错 ({e})，但会话已成功，将忽略此错误。")
        else:
            logger.error(f"Selenium ({session_id}): 发生未知错误: {e}", exc_info=True)
            update_session_file(session_id, {'status': 'error', 'message': str(e)})
            
    finally:
        driver.quit()