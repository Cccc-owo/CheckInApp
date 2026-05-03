import requests
import json
import time
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from typing import Dict, Any

from backend.config import settings

logger = logging.getLogger(__name__)

# Chrome 配置路径 - 从设置中读取
CHROME_BINARY_PATH = settings.CHROME_BINARY_PATH
CHROMEDRIVER_PATH = settings.CHROMEDRIVER_PATH


def get_live_x_api_payload(auth_token: str) -> str:
    """
    启动一个临时的无头浏览器会话，获取新鲜的 x-api-request-payload

    Args:
        auth_token: 用户的 Authorization Token

    Returns:
        x-api-request-payload 值，失败返回 None
    """
    logger.info("正在启动临时浏览器会话以监听网络日志...")

    # 根据配置创建 Service
    if CHROMEDRIVER_PATH:
        service = Service(executable_path=CHROMEDRIVER_PATH)
    else:
        service = Service()  # 使用 Selenium Manager 自动管理

    chrome_options = Options()

    # 如果配置了 Chrome 路径，则使用配置的路径
    if CHROME_BINARY_PATH:
        chrome_options.binary_location = CHROME_BINARY_PATH

    # 开启性能日志记录功能
    logging_prefs = {"performance": "ALL"}
    chrome_options.set_capability("goog:loggingPrefs", logging_prefs)

    # Headless 模式配置
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Chrome(service=service, options=chrome_options)

    payload_signature = None
    try:
        # 导航到同源空白页，用于设置 Cookie
        driver.get("https://i.jielong.com/my-class")

        # 注入长期 Token
        driver.add_cookie({"name": "token", "value": auth_token, "domain": ".jielong.com"})

        # 导航到触发 API 的页面
        driver.get("https://i.jielong.com/my-form")

        # 等待并捕获 x-api-request-payload
        max_wait_time = 20  # 最多等待20秒
        start_time = time.time()
        found = False

        while time.time() - start_time < max_wait_time:
            logs = driver.get_log("performance")
            for entry in logs:
                log = json.loads(entry["message"])["message"]
                if log["method"] == "Network.requestWillBeSent":
                    headers = log.get("params", {}).get("request", {}).get("headers", {})
                    headers_lower = {k.lower(): v for k, v in headers.items()}
                    if "x-api-request-payload" in headers_lower:
                        payload_signature = headers_lower["x-api-request-payload"]
                        logger.info("成功通过网络日志捕获到现场的 x-api-request-payload！")
                        found = True
                        break
            if found:
                break
            time.sleep(1)

        if not payload_signature:
            raise Exception(
                f"在 {max_wait_time} 秒内未能通过网络日志捕获到 x-api-request-payload。"
            )

    except Exception as e:
        logger.error(f"获取现场 x-api-request-payload 时失败: {e}")
        try:
            debug_screenshot = os.path.join(settings.BASE_DIR, "payload_debug.png")
            driver.save_screenshot(debug_screenshot)
        except Exception as screenshot_error:
            logger.warning(f"保存调试截图失败: {screenshot_error}")

    finally:
        # 优雅关闭 WebDriver，避免 Windows asyncio ConnectionResetError
        try:
            driver.quit()
        except Exception as e:
            # 忽略 WebDriver 关闭时的连接错误（Windows 平台常见问题）
            if "WinError 10054" not in str(e) and "ConnectionResetError" not in str(e):
                logger.warning(f"关闭 WebDriver 时出现警告: {e}")

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
    # 从 payload_config 中提取 Signature 用于日志
    from backend.utils.json_helpers import safe_parse_payload, extract_signature

    payload_dict = safe_parse_payload(task.payload_config)
    signature = extract_signature(task.payload_config) or "Unknown"

    logger.info(f"Selenium打卡: 正在为任务 ID: {task.id} (Signature: {signature}) 执行打卡...")

    if not user_token:
        error_msg = f"任务 ID: {task.id} (Signature: {signature}) 的 Token 为空，跳过。"
        logger.error(error_msg)
        return {
            "success": False,
            "status": "failure",
            "response_text": "",
            "error_message": error_msg,
        }

    # 获取 x-api-request-payload
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
        # 使用任务的 payload_config（从模板生成的完整配置，包含 ThreadId）
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

        # 打印请求详情用于调试
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

        # 判断响应内容（参考 V1 实现逻辑）
        # 情况1: 明确包含"打卡成功" → 成功
        if "打卡成功" in response_text:
            logger.info(f"✅ 检测到成功关键字 '打卡成功'，打卡成功")
            # 发送成功邮件通知
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

        # 情况2: 已经提交过了（重复提交）→ 视为成功，但不发送邮件
        # 匹配 "已被提交" 或 "已经打卡"
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

        # 情况3: 不在打卡时间范围 → 标记为时间范围外
        # 匹配 Data 或 Description 中的内容
        elif "不在打卡时间范围" in response_text or "不在打卡时间" in response_text:
            logger.warning(f"⏰ 检测到'不在打卡时间范围'，打卡时间不符")
            return {
                "success": False,
                "status": "out_of_time",
                "response_text": response_text,
                "error_message": "不在打卡时间范围内",
            }

        # 情况4: Token 失效的特征标识 → 失败
        # 扩展检测条件：检测多种 Token 失效的响应特征
        elif (
            "登录" in response_text
            or "授权" in response_text
            or "未登录" in response_text
            or "token" in response_text.lower()
            or "Unauthorized" in response_text
            or response.status_code == 401
        ):
            logger.warning(f"⚠️ 检测到Token失效特征，Token 可能已失效")
            # 发送打卡失败邮件通知（邮件内容已包含Token失效提醒和刷新指引）
            if task.user and task.user.email:
                try:
                    from backend.services.email_service import EmailService
                    from backend.utils.json_helpers import build_task_info

                    # 使用辅助函数构建 task_info（从 task 对象提取信息）
                    task_info = build_task_info(task)

                    # 只发送打卡失败通知（内容已说明Token失效）
                    EmailService.notify_check_in_result(
                        task.user, task_info, False, "Token 已失效，需要重新授权"
                    )
                except Exception as e:
                    logger.error(f"发送打卡失败邮件失败: {e}")

            return {
                "success": False,
                "status": "token_expired",  # 特殊状态，用于标识 Token 过期
                "response_text": response_text,
                "error_message": "Token 已失效，需要重新授权",
            }

        # 情况5: 其他响应 → 需要人工确认（标记为异常）
        else:
            logger.warning(f"⚠️ 未识别的响应内容，请检查: {response_text[:200]}...")
            # 标记为未知状态，记录完整响应供后续分析
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
