from __future__ import annotations

import base64
import json
import logging
import time

from filelock import FileLock
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from backend.config import settings
from backend.services.registration_manager import registration_manager
from backend.workers.browser_automation import (
    PlaywrightLaunchConfig,
    extract_cookie_value,
    save_page_debug_artifacts,
)

logger = logging.getLogger(__name__)

BASE_DIR = settings.BASE_DIR
DEBUG_SCREENSHOT_PATH = BASE_DIR / "debug_screenshot.png"
DEBUG_PAGE_SOURCE_PATH = BASE_DIR / "debug_page_source.html"


def get_browser_config() -> PlaywrightLaunchConfig:
    """获取 Playwright 浏览器配置（从 settings 读取）"""
    return PlaywrightLaunchConfig(executable_path=settings.BROWSER_EXECUTABLE_PATH)


def update_session_file(session_id: str, data: dict) -> None:
    """线程安全地写入会话文件"""
    filepath = settings.SESSION_DIR / f"{session_id}.json"
    lock_path = settings.SESSION_DIR / f"{session_id}.json.lock"

    try:
        with FileLock(lock_path, timeout=5):
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"写入会话文件 {filepath} 失败: {e}")


def get_session_status(session_id: str) -> str | None:
    """安全地读取会话文件的状态"""
    filepath = settings.SESSION_DIR / f"{session_id}.json"
    lock_path = settings.SESSION_DIR / f"{session_id}.json.lock"

    if not filepath.exists():
        return None

    try:
        with FileLock(lock_path, timeout=5):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                if not content:
                    return None
                from backend.utils.json_helpers import safe_parse_json

                data = safe_parse_json(content, {})
        return data.get("status")
    except IOError as e:
        logger.error(f"读取会话文件 {filepath} 失败: {e}")
        return None


def get_session_data(session_id: str) -> dict | None:
    """读取完整的会话数据"""
    filepath = settings.SESSION_DIR / f"{session_id}.json"
    lock_path = settings.SESSION_DIR / f"{session_id}.json.lock"

    if not filepath.exists():
        return None

    try:
        with FileLock(lock_path, timeout=5):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                if not content:
                    return None
                from backend.utils.json_helpers import safe_parse_json

                return safe_parse_json(content, {})
    except IOError as e:
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
            from backend.utils.json_helpers import safe_parse_json

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                if not content:
                    return False
                data = safe_parse_json(content, {})

            if data.get("status") == "success":
                logger.info(f"会话 {session_id} 已成功,无法取消")
                return False

            data["status"] = "cancelled"
            data["message"] = "用户取消登录"

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 会话 {session_id} 已取消")
        return True

    except Exception as e:
        logger.error(f"取消会话 {session_id} 失败: {e}")
        return False


def _close_quietly(resource, label: str) -> None:
    if not resource:
        return

    try:
        resource.close()
    except Exception as e:
        logger.warning(f"关闭 {label} 时出现警告: {e}")


def _release_alias_if_needed(alias: str | None, session_id: str) -> None:
    if not alias:
        return

    registration_manager.release_alias(alias, session_id)
    logger.info(f"释放用户名预占: {alias}")


def get_token_headless(
    session_id: str, jwt_sub: str = None, alias: str = None, client_ip: str = ""
) -> None:
    """
    使用 Playwright 获取 QQ 扫码登录的 Token

    Args:
        session_id: 会话 ID
        jwt_sub: QQ 用户标识（老用户刷新 Token 时提供，新用户为 None）
        alias: 用户别名（用于新用户注册）
        client_ip: 客户端 IP 地址
    """
    current_step = "初始化"
    browser = None
    context = None
    page = None

    playwright = None
    try:
        browser_config = get_browser_config()
        logger.info(f"Playwright ({session_id}): {current_step}...")

        playwright = sync_playwright().start()
        current_step = "启动浏览器"
        logger.info(f"Playwright ({session_id}): {current_step}...")
        browser = playwright.chromium.launch(**browser_config.to_launch_kwargs())
        logger.info(f"Playwright ({session_id}): 浏览器启动成功")

        current_step = "创建上下文"
        context = browser.new_context(**browser_config.to_context_kwargs())
        page = context.new_page()

        current_step = "导航到登录页面"
        logger.info(f"Playwright ({session_id}): {current_step}...")
        page.goto(
            "https://i.jielong.com/login?redirectTo=https%3A%2F%2Fi.jielong.com%2F",
            wait_until="domcontentloaded",
            timeout=60000,
        )

        current_step = "查找并点击切换按钮"
        toggle_button = page.locator("div.login-wrap .toggle")
        logger.info(f"Playwright ({session_id}): {current_step}...")
        toggle_button.click(timeout=60000)

        current_step = "勾选同意服务协议"
        checkbox = page.locator("input.ant-checkbox-input[type='checkbox']")
        logger.info(f"Playwright ({session_id}): {current_step}...")
        if not checkbox.is_checked():
            checkbox.click(timeout=60000)
            logger.info(f"Playwright ({session_id}): 已勾选服务协议")

        current_step = "点击立即登录按钮"
        login_button = page.locator("button.css-1wli0ry.ant-btn.ant-btn-default.login-btn")
        logger.info(f"Playwright ({session_id}): {current_step}...")
        login_button.click(timeout=60000)

        current_step = "等待二维码刷新"
        page.wait_for_timeout(3000)

        current_step = "等待QQ二维码图片加载"
        qr_locator = page.locator("#login_container img").first
        logger.info(f"Playwright ({session_id}): {current_step}...")
        qr_locator.wait_for(state="visible", timeout=60000)

        logger.info(f"Playwright ({session_id}): 成功找到QQ二维码元素，正在截图...")
        qr_base64 = base64.b64encode(qr_locator.screenshot(timeout=60000)).decode("ascii")
        update_session_file(
            session_id,
            {
                "status": "waiting_scan",
                "qr_image_data": qr_base64,
                "jwt_sub": jwt_sub,
                "alias": alias,
                "client_ip": client_ip,
            },
        )

        current_step = "等待用户扫描登录 (Cookie 'token' 出现)"
        logger.info(f"Playwright ({session_id}): {current_step}...")

        max_wait_seconds = 120
        for _ in range(max_wait_seconds):
            status = get_session_status(session_id)
            if status == "cancelled":
                logger.info(f"Playwright ({session_id}): 用户取消了登录,终止会话")
                _release_alias_if_needed(alias, session_id)
                return

            token = extract_cookie_value(context.cookies(), "token")
            if token:
                logger.info(f"Playwright ({session_id}): 成功在Cookie中捕获到Token！")
                update_session_file(
                    session_id,
                    {
                        "status": "success",
                        "token": token,
                        "alias": alias,
                        "client_ip": client_ip,
                    },
                )
                return

            time.sleep(1)

        raise PlaywrightTimeoutError("等待扫码超时")

    except PlaywrightTimeoutError:
        if get_session_status(session_id) == "success":
            logger.warning(
                f"Playwright ({session_id}): 一个并发线程超时，但会话已成功，将忽略此超时。"
            )
        else:
            _release_alias_if_needed(alias, session_id)
            error_message = f"操作超时！卡在了步骤: '{current_step}'。请检查页面选择器或网络。"
            logger.error(f"Playwright ({session_id}): {error_message}")

            if page:
                try:
                    save_page_debug_artifacts(page, DEBUG_SCREENSHOT_PATH, DEBUG_PAGE_SOURCE_PATH)
                    logger.error(
                        f"Playwright ({session_id}): 调试截图和源码已保存。当前URL: {page.url}"
                    )
                except Exception as debug_error:
                    logger.error(f"Playwright ({session_id}): 保存调试信息失败: {debug_error}")

            update_session_file(
                session_id, {"status": "error", "message": error_message, "jwt_sub": jwt_sub}
            )

    except Exception as e:
        if get_session_status(session_id) == "success":
            logger.warning(
                f"Playwright ({session_id}): 一个并发线程出错 ({e})，但会话已成功，将忽略此错误。"
            )
        else:
            _release_alias_if_needed(alias, session_id)
            logger.error(f"Playwright ({session_id}): 发生未知错误: {e}", exc_info=True)

            if page:
                try:
                    save_page_debug_artifacts(page, DEBUG_SCREENSHOT_PATH, DEBUG_PAGE_SOURCE_PATH)
                except Exception as debug_error:
                    logger.error(f"Playwright ({session_id}): 保存调试信息失败: {debug_error}")

            update_session_file(
                session_id, {"status": "error", "message": str(e), "jwt_sub": jwt_sub}
            )

    finally:
        _close_quietly(page, "页面")
        _close_quietly(context, "浏览器上下文")
        _close_quietly(browser, "浏览器")
        if playwright:
            try:
                playwright.stop()
            except Exception as e:
                logger.warning(f"关闭 Playwright runtime 时出现警告: {e}")
        logger.info(f"Playwright ({session_id}): 浏览器已关闭")
