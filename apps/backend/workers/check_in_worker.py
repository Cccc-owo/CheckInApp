from __future__ import annotations

import json
import logging
import requests
import time
from typing import Dict, Any

from playwright.sync_api import sync_playwright

from backend.config import settings
from backend.workers.browser_automation import (
    PlaywrightLaunchConfig,
    extract_payload_header,
    save_page_debug_artifacts,
)

logger = logging.getLogger(__name__)

BASE_DIR = settings.BASE_DIR
DEBUG_SCREENSHOT_PATH = BASE_DIR / "payload_debug.png"
DEBUG_PAGE_SOURCE_PATH = BASE_DIR / "payload_debug_page_source.html"


def get_browser_config() -> PlaywrightLaunchConfig:
    """获取 Playwright 浏览器配置（从 settings 读取）"""
    return PlaywrightLaunchConfig(executable_path=settings.BROWSER_EXECUTABLE_PATH)


def get_live_x_api_payload(auth_token: str) -> str | None:
    """
    启动一个临时的无头浏览器会话，获取新鲜的 x-api-request-payload

    Args:
        auth_token: 用户的 Authorization Token

    Returns:
        x-api-request-payload 值，失败返回 None
    """
    logger.info("正在启动临时 Playwright 会话以监听网络请求...")

    browser = None
    context = None
    page = None
    payload_signature = None

    playwright = None
    try:
        browser_config = get_browser_config()

        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(**browser_config.to_launch_kwargs())
        context = browser.new_context(**browser_config.to_context_kwargs())
        page = context.new_page()

        def on_request(request) -> None:
            nonlocal payload_signature
            if payload_signature:
                return

            payload = extract_payload_header(request.headers)
            if payload:
                payload_signature = payload
                logger.info("成功通过 Playwright 捕获到现场的 x-api-request-payload！")

        page.on("request", on_request)

        page.goto("https://i.jielong.com/my-class", wait_until="domcontentloaded", timeout=60000)
        context.add_cookies(
            [
                {
                    "name": "token",
                    "value": auth_token,
                    "domain": ".jielong.com",
                    "path": "/",
                }
            ]
        )

        page.goto("https://i.jielong.com/my-form", wait_until="domcontentloaded", timeout=60000)

        max_wait_time = 20
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            if payload_signature:
                break
            page.wait_for_timeout(500)

        if not payload_signature:
            raise Exception(
                f"在 {max_wait_time} 秒内未能通过网络请求捕获到 x-api-request-payload。"
            )

    except Exception as e:
        logger.error(f"获取现场 x-api-request-payload 时失败: {e}")
        try:
            if page:
                save_page_debug_artifacts(page, DEBUG_SCREENSHOT_PATH, DEBUG_PAGE_SOURCE_PATH)
        except Exception as screenshot_error:
            logger.warning(f"保存调试截图失败: {screenshot_error}")

    finally:
        if page:
            try:
                page.close()
            except Exception:
                pass
        if context:
            try:
                context.close()
            except Exception:
                pass
        if browser:
            try:
                browser.close()
            except Exception as e:
                logger.warning(f"关闭 Playwright 浏览器时出现警告: {e}")
        if playwright:
            try:
                playwright.stop()
            except Exception as e:
                logger.warning(f"关闭 Playwright runtime 时出现警告: {e}")

    return payload_signature


def perform_check_in(task, user_token: str) -> Dict[str, Any]:
    """
    执行打卡任务

    Args:
        task: CheckInTask 对象，包含打卡任务配置
        user_token: 用户的 Authorization Token（从 task.user.authorization 获取）

    Returns:
        打卡结果字典:
            - success: 是否成功
            - status: 状态 (success/failure)
            - response_text: 响应文本
            - error_message: 错误信息
    """
    from backend.utils.json_helpers import safe_parse_payload, extract_signature

    payload_dict = safe_parse_payload(task.payload_config)
    signature = extract_signature(task.payload_config) or "Unknown"

    logger.info(f"Playwright打卡: 正在为任务 ID: {task.id} (Signature: {signature}) 执行打卡...")

    if not user_token:
        error_msg = f"任务 ID: {task.id} (Signature: {signature}) 的 Token 为空，跳过。"
        logger.error(error_msg)
        return {
            "success": False,
            "status": "failure",
            "response_text": "",
            "error_message": error_msg,
        }

    payload_signature = get_live_x_api_payload(user_token)
    if not payload_signature:
        error_msg = f"任务 ID: {task.id} (Signature: {signature}) 未能获取到现场签名，打卡中止。"
        logger.error(error_msg)
        return {
            "success": False,
            "status": "failure",
            "response_text": "",
            "error_message": error_msg,
        }

    try:
        from backend.utils.json_helpers import safe_parse_payload, extract_thread_id

        payload = safe_parse_payload(task.payload_config)
        thread_id = extract_thread_id(task.payload_config)

        if not thread_id:
            error_msg = f"任务 ID: {task.id} 的 payload_config 缺少 ThreadId"
            logger.error(error_msg)
            return {
                "success": False,
                "status": "failure",
                "response_text": "",
                "error_message": error_msg,
            }

        headers = {
            "User-Agent": "Mozilla%2f5.0+(Linux%3b+Android+16%3b+wv)+AppleWebKit%2f537.36+(KHTML%2c+like+Gecko)+Chrome%2f142.0.0.0+Safari%2f537.36+QQ%2f9.2.30.31620+QQ%2fMiniApp",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json",
            "authorization": f"Bearer {user_token}",
            "x-api-request-referer": "https://appservice.qq.com/1110276759",
            "x-api-request-payload": payload_signature,
            "referer": "https://appservice.qq.com/1110276759/8.10.1.7/page-frame.html",
            "platform": "qq",
            "x-api-request-mode": "cors",
        }

        url = "https://api.jielong.com/api/CheckIn/EditRecord"

        payload_json = json.dumps(payload, ensure_ascii=False)
        logger.info(f"📤 打卡请求详情 - 任务 ID: {task.id} (Signature: {signature})")
        logger.info(f"📍 URL: {url}")
        logger.info(f"📦 Payload: {payload_json}")
        logger.info(f"🔑 x-api-request-payload: {payload_signature[:50]}...")

        response = requests.post(url, data=payload_json, headers=headers)
        response.raise_for_status()
        response_text = response.text

        logger.info(
            f"✉️ 任务 ID: {task.id} (Signature: {signature}) 打卡请求完成！响应: {response_text}"
        )

        if "打卡成功" in response_text:
            logger.info(f"✅ 检测到成功关键字 '打卡成功'，打卡成功")
            if task.user and task.user.email:
                try:
                    from backend.services.email_service import EmailService

                    task_info = {
                        "thread_id": payload.get("ThreadId", "未知"),
                        "name": getattr(task, "name", "打卡任务"),
                    }
                    EmailService.notify_check_in_result(task.user, task_info, True, "打卡成功")
                except Exception as e:
                    logger.error(f"发送打卡成功邮件失败: {e}")

            return {
                "success": True,
                "status": "success",
                "response_text": response_text,
                "error_message": "",
            }

        elif (
            "已被提交" in response_text
            or "已经打卡" in response_text
            or "重复提交" in response_text
        ):
            logger.info(f"✅ 检测到'已被提交'，本次打卡已完成（重复提交，不发送邮件）")
            return {
                "success": True,
                "status": "success",
                "response_text": response_text,
                "error_message": "",
            }

        elif "不在打卡时间范围" in response_text or "不在打卡时间" in response_text:
            logger.warning(f"⏰ 检测到'不在打卡时间范围'，打卡时间不符")
            return {
                "success": False,
                "status": "out_of_time",
                "response_text": response_text,
                "error_message": "不在打卡时间范围内",
            }

        elif (
            "登录" in response_text
            or "授权" in response_text
            or "未登录" in response_text
            or "token" in response_text.lower()
            or "Unauthorized" in response_text
            or response.status_code == 401
        ):
            logger.warning(f"⚠️ 检测到Token失效特征，Token 可能已失效")
            if task.user and task.user.email:
                try:
                    from backend.services.email_service import EmailService
                    from backend.utils.json_helpers import build_task_info

                    task_info = build_task_info(task)

                    EmailService.notify_check_in_result(
                        task.user, task_info, False, "Token 已失效，需要重新授权"
                    )
                except Exception as e:
                    logger.error(f"发送打卡失败邮件失败: {e}")

            return {
                "success": False,
                "status": "token_expired",
                "response_text": response_text,
                "error_message": "Token 已失效，需要重新授权",
            }

        else:
            logger.warning(f"⚠️ 未识别的响应内容，请检查: {response_text[:200]}...")
            return {
                "success": False,
                "status": "unknown",
                "response_text": response_text,
                "error_message": "未识别的响应，请人工确认",
            }

    except requests.exceptions.RequestException as e:
        error_msg = f"为任务 ID: {task.id} (Signature: {signature}) 打卡时请求失败: {e}"
        logger.error(error_msg)

        response_text = ""
        if e.response is not None:
            response_text = e.response.text
            logger.error(f"响应状态码: {e.response.status_code}, 响应内容: {response_text}")

        return {
            "success": False,
            "status": "failure",
            "response_text": response_text,
            "error_message": str(e),
        }

    except Exception as e:
        error_msg = f"为任务 ID: {task.id} (Signature: {signature}) 打卡时发生未知错误: {e}"
        logger.error(error_msg)
        return {"success": False, "status": "failure", "response_text": "", "error_message": str(e)}
