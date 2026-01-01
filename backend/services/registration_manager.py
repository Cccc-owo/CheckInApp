"""
用户名预占和注册限流管理器
"""
import time
import threading
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RegistrationManager:
    """用户注册管理器 - 处理用户名预占和注册限流"""

    def __init__(self):
        # 用户名预占记录: {alias: {session_id: str, expire_time: float}}
        self._reserved_aliases: Dict[str, Dict] = {}

        # Cookie 注册限流记录: {cookie_value: expire_time}
        self._registration_cookies: Dict[str, float] = {}

        # 线程锁
        self._lock = threading.RLock()

        # 启动清理线程
        self._start_cleanup_thread()

    def reserve_alias(self, alias: str, session_id: str, timeout_seconds: int = 120) -> bool:
        """
        预占用户名

        Args:
            alias: 用户名
            session_id: 会话 ID
            timeout_seconds: 超时时间（秒），默认 120 秒（2 分钟）

        Returns:
            是否预占成功
        """
        with self._lock:
            current_time = time.time()
            expire_time = current_time + timeout_seconds

            # 检查用户名是否已被预占
            if alias in self._reserved_aliases:
                reservation = self._reserved_aliases[alias]

                # 检查是否过期
                if reservation['expire_time'] > current_time:
                    # 未过期，检查是否是同一个 session
                    if reservation['session_id'] == session_id:
                        # 同一个 session，更新过期时间
                        reservation['expire_time'] = expire_time
                        logger.info(f"用户名 {alias} 预占时间已更新（session: {session_id}）")
                        return True
                    else:
                        # 不同 session，预占失败
                        logger.warning(f"用户名 {alias} 已被占用（session: {reservation['session_id']}）")
                        return False

            # 预占用户名
            self._reserved_aliases[alias] = {
                'session_id': session_id,
                'expire_time': expire_time
            }
            logger.info(f"用户名 {alias} 已预占（session: {session_id}, 超时: {timeout_seconds}s）")
            return True

    def release_alias(self, alias: str, session_id: Optional[str] = None) -> bool:
        """
        释放用户名预占

        Args:
            alias: 用户名
            session_id: 会话 ID（可选，如果提供则只释放匹配的 session）

        Returns:
            是否释放成功
        """
        with self._lock:
            if alias not in self._reserved_aliases:
                return False

            reservation = self._reserved_aliases[alias]

            # 如果指定了 session_id，则只释放匹配的
            if session_id and reservation['session_id'] != session_id:
                logger.warning(f"尝试释放用户名 {alias}，但 session 不匹配")
                return False

            del self._reserved_aliases[alias]
            logger.info(f"用户名 {alias} 预占已释放")
            return True

    def is_alias_reserved(self, alias: str) -> bool:
        """
        检查用户名是否被预占

        Args:
            alias: 用户名

        Returns:
            是否被预占
        """
        with self._lock:
            if alias not in self._reserved_aliases:
                return False

            reservation = self._reserved_aliases[alias]
            current_time = time.time()

            # 检查是否过期
            if reservation['expire_time'] <= current_time:
                # 已过期，自动释放
                del self._reserved_aliases[alias]
                return False

            return True

    def check_registration_cookie(self, cookie_value: str) -> bool:
        """
        检查 Cookie 是否在限流期内

        Args:
            cookie_value: Cookie 值

        Returns:
            True 表示可以注册，False 表示在限流期内
        """
        with self._lock:
            current_time = time.time()

            # 检查 Cookie 是否存在
            if cookie_value in self._registration_cookies:
                expire_time = self._registration_cookies[cookie_value]

                # 检查是否过期
                if expire_time > current_time:
                    remaining = int(expire_time - current_time)
                    logger.warning(f"Cookie {cookie_value[:8]}... 在限流期内（剩余 {remaining} 秒）")
                    return False
                else:
                    # 已过期，移除记录
                    del self._registration_cookies[cookie_value]

            return True

    def record_registration(self, cookie_value: str, cooldown_seconds: int = 600) -> None:
        """
        记录注册操作（10 分钟冷却）

        Args:
            cookie_value: Cookie 值
            cooldown_seconds: 冷却时间（秒），默认 600 秒（10 分钟）
        """
        with self._lock:
            current_time = time.time()
            expire_time = current_time + cooldown_seconds

            self._registration_cookies[cookie_value] = expire_time
            logger.info(f"Cookie {cookie_value[:8]}... 已记录注册（冷却 {cooldown_seconds} 秒）")

    def _cleanup_expired_records(self) -> None:
        """清理过期的预占记录和限流记录"""
        with self._lock:
            current_time = time.time()

            # 清理过期的用户名预占
            expired_aliases = [
                alias for alias, reservation in self._reserved_aliases.items()
                if reservation['expire_time'] <= current_time
            ]

            for alias in expired_aliases:
                del self._reserved_aliases[alias]
                logger.debug(f"用户名 {alias} 预占已过期，自动释放")

            # 清理过期的注册限流记录
            expired_cookies = [
                cookie for cookie, expire_time in self._registration_cookies.items()
                if expire_time <= current_time
            ]

            for cookie in expired_cookies:
                del self._registration_cookies[cookie]
                logger.debug(f"Cookie {cookie[:8]}... 限流记录已过期，自动清理")

            if expired_aliases or expired_cookies:
                logger.info(f"清理完成：{len(expired_aliases)} 个用户名，{len(expired_cookies)} 个 Cookie")

    def _start_cleanup_thread(self) -> None:
        """启动定期清理线程"""
        def cleanup_loop():
            while True:
                try:
                    time.sleep(60)  # 每 60 秒清理一次
                    self._cleanup_expired_records()
                except Exception as e:
                    logger.error(f"清理线程异常: {e}")

        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
        logger.info("注册管理器清理线程已启动")

    def get_stats(self) -> Dict:
        """获取当前状态统计"""
        with self._lock:
            return {
                'reserved_aliases_count': len(self._reserved_aliases),
                'rate_limited_cookies_count': len(self._registration_cookies),
                'reserved_aliases': list(self._reserved_aliases.keys()),
            }


# 全局单例
registration_manager = RegistrationManager()
