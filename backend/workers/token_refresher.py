import os
import logging
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from filelock import FileLock

from backend.config import settings

logger = logging.getLogger(__name__)

# Chrome 配置路径
BASE_DIR = settings.BASE_DIR

# 调试文件路径
DEBUG_SCREENSHOT_PATH = os.path.join(BASE_DIR, "debug_screenshot.png")
DEBUG_PAGE_SOURCE_PATH = os.path.join(BASE_DIR, "debug_page_source.html")


def get_chrome_config():
    """获取 Chrome 配置（从 settings 读取）"""
    return {
        "chrome_binary": settings.CHROME_BINARY_PATH,
        "chromedriver": settings.CHROMEDRIVER_PATH
    }



def update_session_file(session_id: str, data: dict) -> None:
    """线程安全地写入会话文件"""
    filepath = settings.SESSION_DIR / f"{session_id}.json"
    lock_path = settings.SESSION_DIR / f"{session_id}.json.lock"

    try:
        with FileLock(lock_path, timeout=5):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"写入会话文件 {filepath} 失败: {e}")


def get_session_status(session_id: str) -> str:
    """安全地读取会话文件的状态"""
    filepath = settings.SESSION_DIR / f"{session_id}.json"
    lock_path = settings.SESSION_DIR / f"{session_id}.json.lock"

    if not filepath.exists():
        return None

    try:
        with FileLock(lock_path, timeout=5):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content:
                    return None
                data = json.loads(content)
        return data.get('status')
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"读取会话文件 {filepath} 失败: {e}")
        return None


def get_session_data(session_id: str) -> dict:
    """读取完整的会话数据"""
    filepath = settings.SESSION_DIR / f"{session_id}.json"
    lock_path = settings.SESSION_DIR / f"{session_id}.json.lock"

    if not filepath.exists():
        return None

    try:
        with FileLock(lock_path, timeout=5):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content:
                    return None
                return json.loads(content)
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"读取会话文件 {filepath} 失败: {e}")
        return None


def cancel_session(session_id: str) -> bool:
    """
    取消登录会话

    Args:
        session_id: 会话 ID

    Returns:
        是否成功取消
    """
    filepath = settings.SESSION_DIR / f"{session_id}.json"
    lock_path = settings.SESSION_DIR / f"{session_id}.json.lock"

    if not filepath.exists():
        logger.warning(f"尝试取消不存在的会话: {session_id}")
        return False

    try:
        with FileLock(lock_path, timeout=5):
            # 读取当前会话数据
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content:
                    return False
                data = json.loads(content)

            # 如果已经成功,不允许取消
            if data.get('status') == 'success':
                logger.info(f"会话 {session_id} 已成功,无法取消")
                return False

            # 标记为已取消
            data['status'] = 'cancelled'
            data['message'] = '用户取消登录'

            # 写回文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 会话 {session_id} 已取消")
        return True

    except Exception as e:
        logger.error(f"取消会话 {session_id} 失败: {e}")
        return False


def get_token_headless(session_id: str, jwt_sub: str = None, alias: str = None, client_ip: str = "") -> None:
    """
    使用 Selenium 获取 QQ 扫码登录的 Token

    Args:
        session_id: 会话 ID
        jwt_sub: QQ 用户标识（老用户刷新 Token 时提供，新用户为 None）
        alias: 用户别名（用于新用户注册）
        client_ip: 客户端 IP 地址
    """
    driver = None
    current_step = "初始化"

    try:
        # 获取 Chrome 配置
        chrome_config = get_chrome_config()
        chrome_binary_path = chrome_config["chrome_binary"]
        chromedriver_path = chrome_config["chromedriver"]

        # 配置 Chrome 选项
        current_step = "配置 ChromeDriver"
        logger.info(f"Selenium ({session_id}): {current_step}...")

        chrome_options = Options()

        # 如果指定了自定义 Chrome 路径，则使用
        if chrome_binary_path:
            chrome_options.binary_location = chrome_binary_path
            logger.info(f"Selenium ({session_id}): 使用自定义 Chrome 路径: {chrome_binary_path}")
        else:
            logger.info(f"Selenium ({session_id}): 使用系统默认 Chrome")

        # Headless 模式配置
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        # 启动浏览器
        current_step = "启动 Chrome 浏览器"
        logger.info(f"Selenium ({session_id}): {current_step}...")

        # 如果指定了 ChromeDriver 路径，则使用 Service；否则让 Selenium 自动管理
        if chromedriver_path:
            service = Service(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info(f"Selenium ({session_id}): 使用自定义 ChromeDriver: {chromedriver_path}")
        else:
            driver = webdriver.Chrome(options=chrome_options)
            logger.info(f"Selenium ({session_id}): 使用 Selenium Manager 自动管理 ChromeDriver")

        logger.info(f"Selenium ({session_id}): Chrome 浏览器启动成功")
        current_step = "导航到登录页面"
        logger.info(f"Selenium ({session_id}): {current_step}...")
        driver.get("https://i.jielong.com/login?redirectTo=https%3A%2F%2Fi.jielong.com%2F")

        wait = WebDriverWait(driver, 60)

        # --- 步骤 1: 点击切换到 QQ 登录 ---
        current_step = "查找并点击切换按钮"
        toggle_button_selector = "div.login-wrap .toggle"
        logger.info(f"Selenium ({session_id}): {current_step} ({toggle_button_selector})...")
        toggle_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, toggle_button_selector)))
        toggle_button.click()

        # --- 步骤 2: 勾选同意服务协议 ---
        current_step = "勾选同意服务协议"
        checkbox_selector = "input.ant-checkbox-input[type='checkbox']"
        logger.info(f"Selenium ({session_id}): {current_step} ({checkbox_selector})...")
        checkbox = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, checkbox_selector)))
        if not checkbox.is_selected():
            checkbox.click()
            logger.info(f"Selenium ({session_id}): 已勾选服务协议")

        # --- 步骤 3: 点击"立即登录"按钮 ---
        current_step = "点击立即登录按钮"
        login_button_selector = "button.css-1wli0ry.ant-btn.ant-btn-default.login-btn"
        logger.info(f"Selenium ({session_id}): {current_step} ({login_button_selector})...")
        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, login_button_selector)))
        login_button.click()

        # --- 步骤 4: 等待二维码加载 ---
        import time
        time.sleep(3)  # 等待几秒让二维码刷新出来

        current_step = "等待QQ二维码图片加载"
        qq_qr_image_selector = "#login_container img"
        logger.info(f"Selenium ({session_id}): {current_step} ({qq_qr_image_selector})...")
        qr_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, qq_qr_image_selector)))

        logger.info(f"Selenium ({session_id}): 成功找到QQ二维码元素，正在截图...")
        qr_base64 = qr_element.screenshot_as_base64
        update_session_file(session_id, {
            'status': 'waiting_scan',
            'qr_image_data': qr_base64,
            'jwt_sub': jwt_sub,
            'alias': alias,  # 新增：保存 alias
            'client_ip': client_ip  # 新增：保存 IP
        })

        current_step = "等待用户扫描登录 (Cookie 'token' 出现)"
        cookie_name_to_find = "token"
        logger.info(f"Selenium ({session_id}): {current_step}...")

        # 自定义等待逻辑:每秒检查cookie和session状态
        max_wait_seconds = 120
        import time
        for i in range(max_wait_seconds):
            # 检查session是否被取消
            status = get_session_status(session_id)
            if status == 'cancelled':
                logger.info(f"Selenium ({session_id}): 用户取消了登录,终止会话")
                raise Exception("用户取消登录")

            # 检查cookie是否出现
            cookie = driver.get_cookie(cookie_name_to_find)
            if cookie:
                break

            time.sleep(1)
        else:
            # 超时未获取到cookie
            raise TimeoutException("等待扫码超时")

        cookie = driver.get_cookie(cookie_name_to_find)
        if cookie:
            logger.info(f"Selenium ({session_id}): 成功在Cookie中捕获到Token！")
            update_session_file(session_id, {
                'status': 'success',
                'token': cookie['value'],
                'alias': alias,  # 保存 alias
                'client_ip': client_ip  # 保存 IP
            })
        else:
            raise Exception("等待Cookie成功但获取失败")

    except TimeoutException:
        if get_session_status(session_id) == 'success':
            logger.warning(f"Selenium ({session_id}): 一个并发线程超时，但会话已成功，将忽略此超时。")
        else:
            # 释放预占的用户名
            if alias:
                from backend.services.registration_manager import registration_manager
                registration_manager.release_alias(alias, session_id)
                logger.info(f"超时释放用户名预占: {alias}")

            error_message = f"操作超时！卡在了步骤: '{current_step}'。请检查CSS选择器或网络。"
            logger.error(f"Selenium ({session_id}): {error_message}")

            # 保存调试信息（仅当 driver 已创建时）
            if driver:
                try:
                    driver.save_screenshot(DEBUG_SCREENSHOT_PATH)
                    with open(DEBUG_PAGE_SOURCE_PATH, 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    logger.error(f"Selenium ({session_id}): 调试截图和源码已保存。当前URL: {driver.current_url}")
                except Exception as debug_error:
                    logger.error(f"Selenium ({session_id}): 保存调试信息失败: {debug_error}")

            update_session_file(session_id, {
                'status': 'error',
                'message': error_message,
                'jwt_sub': jwt_sub
            })

    except Exception as e:
        if get_session_status(session_id) == 'success':
            logger.warning(f"Selenium ({session_id}): 一个并发线程出错 ({e})，但会话已成功，将忽略此错误。")
        else:
            # 释放预占的用户名
            if alias:
                from backend.services.registration_manager import registration_manager
                registration_manager.release_alias(alias, session_id)
                logger.info(f"异常释放用户名预占: {alias}")

            logger.error(f"Selenium ({session_id}): 发生未知错误: {e}", exc_info=True)
            update_session_file(session_id, {
                'status': 'error',
                'message': str(e),
                'jwt_sub': jwt_sub
            })

    finally:
        if driver:
            try:
                driver.quit()
                logger.info(f"Selenium ({session_id}): 浏览器已关闭")
            except Exception as quit_error:
                logger.error(f"Selenium ({session_id}): 关闭浏览器失败: {quit_error}")
