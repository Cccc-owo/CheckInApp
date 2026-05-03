"""
JWT 认证工具模块

用于生成和验证网站登录的 JWT Token
注意：这与打卡业务的 authorization token 是分开的
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from backend.config import settings
import logging

logger = logging.getLogger(__name__)

# JWT 配置
JWT_SECRET_KEY = settings.SECRET_KEY  # 使用现有的 SECRET_KEY
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 21  # JWT 有效期：21天


class JWTManager:
    """JWT 管理器"""

    @staticmethod
    def create_access_token(user_id: int, user_alias: str) -> str:
        """
        创建访问令牌

        Args:
            user_id: 用户 ID
            user_alias: 用户别名

        Returns:
            JWT token 字符串
        """
        now = datetime.utcnow()
        exp = now + timedelta(days=JWT_EXPIRATION_DAYS)

        payload = {
            "user_id": user_id,
            "alias": user_alias,
            "iat": now,  # Issued At - 签发时间
            "exp": exp,  # Expiration Time - 过期时间
            "type": "access"  # Token 类型
        }

        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        logger.info(f"为用户 {user_alias}(ID: {user_id}) 创建 JWT，过期时间: {exp}")
        return token

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """
        验证并解码 JWT token

        Args:
            token: JWT token 字符串

        Returns:
            解码后的 payload 字典

        Raises:
            jwt.ExpiredSignatureError: Token 已过期
            jwt.InvalidTokenError: Token 无效
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

            # 验证 token 类型
            if payload.get("type") != "access":
                raise jwt.InvalidTokenError("Token 类型不正确")

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("JWT Token 已过期")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT Token 无效: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"验证 JWT Token 时发生错误: {str(e)}")
            raise jwt.InvalidTokenError(f"Token 验证失败: {str(e)}")

    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[int]:
        """
        从 JWT token 中提取用户 ID（不验证过期）

        Args:
            token: JWT token 字符串

        Returns:
            用户 ID 或 None
        """
        try:
            # decode 时设置 verify=False 跳过过期验证
            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
                options={"verify_exp": False}
            )
            return payload.get("user_id")
        except Exception as e:
            logger.error(f"从 Token 提取用户 ID 失败: {str(e)}")
            return None

    @staticmethod
    def is_token_expired(token: str) -> bool:
        """
        检查 token 是否过期（不抛出异常）

        Args:
            token: JWT token 字符串

        Returns:
            True 表示已过期，False 表示未过期
        """
        try:
            JWTManager.verify_token(token)
            return False
        except jwt.ExpiredSignatureError:
            return True
        except jwt.InvalidTokenError:
            return True
