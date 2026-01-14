"""
时间处理辅助函数

提供统一的时间戳处理和格式化功能
"""
from datetime import datetime, timedelta
from typing import Optional


def now_timestamp() -> int:
    """
    获取当前时间戳（秒）

    Returns:
        当前时间戳
    """
    return int(datetime.now().timestamp())


def is_timestamp_expired(timestamp: int) -> bool:
    """
    检查时间戳是否已过期

    Args:
        timestamp: 时间戳（秒）

    Returns:
        是否已过期
    """
    return now_timestamp() > timestamp


def seconds_until_expiry(timestamp: int) -> int:
    """
    计算距离过期的秒数（负数表示已过期）

    Args:
        timestamp: 时间戳（秒）

    Returns:
        距离过期的秒数
    """
    return timestamp - now_timestamp()


def days_until_expiry(timestamp: int) -> int:
    """
    计算距离过期的天数（负数表示已过期）

    Args:
        timestamp: 时间戳（秒）

    Returns:
        距离过期的天数
    """
    seconds = seconds_until_expiry(timestamp)
    return seconds // 86400


def hours_until_expiry(timestamp: int) -> int:
    """
    计算距离过期的小时数（负数表示已过期）

    Args:
        timestamp: 时间戳（秒）

    Returns:
        距离过期的小时数
    """
    seconds = seconds_until_expiry(timestamp)
    return seconds // 3600


def minutes_until_expiry(timestamp: int) -> int:
    """
    计算距离过期的分钟数（负数表示已过期）

    Args:
        timestamp: 时间戳（秒）

    Returns:
        距离过期的分钟数
    """
    seconds = seconds_until_expiry(timestamp)
    return seconds // 60


def format_timestamp(timestamp: int, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    格式化时间戳为人类可读格式

    Args:
        timestamp: 时间戳（秒）
        format_str: 时间格式字符串

    Returns:
        格式化后的时间字符串
    """
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime(format_str)


def format_expiry_time(timestamp: int) -> str:
    """
    格式化过期时间为人类可读格式（带中文说明）

    Args:
        timestamp: 时间戳（秒）

    Returns:
        格式化后的时间字符串，如 "2024-01-01 12:00:00 (已过期 2 天)"
    """
    formatted_time = format_timestamp(timestamp)
    days = days_until_expiry(timestamp)

    if days > 0:
        return f"{formatted_time} (还剩 {days} 天)"
    elif days == 0:
        hours = hours_until_expiry(timestamp)
        if hours > 0:
            return f"{formatted_time} (还剩 {hours} 小时)"
        else:
            minutes = minutes_until_expiry(timestamp)
            if minutes > 0:
                return f"{formatted_time} (还剩 {minutes} 分钟)"
            else:
                return f"{formatted_time} (即将过期)"
    else:
        return f"{formatted_time} (已过期 {abs(days)} 天)"


def parse_jwt_exp(jwt_exp: Optional[str]) -> Optional[int]:
    """
    解析 jwt_exp 字段为时间戳

    Args:
        jwt_exp: jwt_exp 字符串（可能是 "0" 或数字字符串）

    Returns:
        时间戳，无效时返回 None
    """
    if not jwt_exp or jwt_exp == "0":
        return None

    try:
        return int(jwt_exp)
    except (ValueError, TypeError):
        return None
