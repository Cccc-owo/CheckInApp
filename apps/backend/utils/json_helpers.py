"""
JSON 处理辅助函数

提供安全的 JSON 解析和数据提取功能
"""
import json
import logging
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)


def safe_parse_json(
    json_str: Optional[str],
    default: Any = None,
    log_error: bool = True
) -> Any:
    """
    安全解析 JSON 字符串，失败时返回默认值

    Args:
        json_str: JSON 字符串
        default: 解析失败时的默认值
        log_error: 是否记录解析错误日志

    Returns:
        解析后的对象，失败时返回 default
    """
    if not json_str:
        return default

    try:
        return json.loads(str(json_str))
    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        if log_error:
            logger.debug(f"JSON 解析失败: {str(e)}, 原始数据: {json_str[:100]}...")
        return default


def safe_parse_payload(
    payload_config: Optional[str],
    default: Optional[Dict] = None
) -> Dict:
    """
    安全解析 payload_config，失败时返回默认字典

    Args:
        payload_config: payload 配置字符串
        default: 解析失败时的默认值

    Returns:
        解析后的字典
    """
    result = safe_parse_json(payload_config, default or {})
    # 确保返回值是字典类型
    if not isinstance(result, dict):
        logger.warning(f"payload_config 不是字典类型: {type(result)}")
        return default or {}
    return result


def extract_thread_id(payload_config: Optional[str]) -> Optional[str]:
    """
    从 payload_config 中提取 ThreadId

    Args:
        payload_config: payload 配置字符串

    Returns:
        ThreadId 或 None
    """
    payload = safe_parse_payload(payload_config)
    return payload.get('ThreadId')


def extract_signature(payload_config: Optional[str]) -> Optional[str]:
    """
    从 payload_config 中提取 Signature

    Args:
        payload_config: payload 配置字符串

    Returns:
        Signature 或 None
    """
    payload = safe_parse_payload(payload_config)
    return payload.get('Signature')


def build_task_info(task) -> Dict[str, str]:
    """
    从 task 对象构建 task_info 字典（用于邮件通知等场景）

    Args:
        task: CheckInTask 对象

    Returns:
        包含 thread_id 和 name 的字典
    """
    return {
        'thread_id': extract_thread_id(getattr(task, 'payload_config', None)) or '未知',
        'name': getattr(task, 'name', None) or f'Task-{getattr(task, "id", "Unknown")}'
    }
