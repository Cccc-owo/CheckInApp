import uuid
import logging
import threading
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import unquote
from sqlalchemy.orm import Session

from backend.models import User
from backend.workers.token_refresher import get_token_headless, get_session_data
from backend.config import settings
from backend.utils.jwt import JWTManager

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务"""

    @staticmethod
    def request_qrcode(alias: str, client_ip: str, db: Session) -> Dict[str, Any]:
        """
        请求 QQ 扫码二维码（支持新用户注册）

        Args:
            alias: 用户别名
            client_ip: 客户端 IP 地址（用于会话标识）
            db: 数据库会话

        Returns:
            包含 session_id 和 qrcode_base64 的字典
        """
        from backend.services.registration_manager import registration_manager
        import time

        # 检查用户名是否已在数据库中存在
        existing_user = db.query(User).filter(User.alias == alias).first()

        # 生成唯一的会话 ID
        session_id = str(uuid.uuid4())

        if existing_user:
            # 检查是否为空 jwt_sub（测试账号）
            if not existing_user.jwt_sub:
                logger.warning(f"用户 {alias} 是测试账号（未绑定 QQ），禁止扫码登录")
                return {
                    "status": "error",
                    "message": "此账户为测试账号，暂未绑定 QQ，无法扫码登录"
                }

            # 老用户：刷新 Token
            logger.info(f"老用户 {alias} 请求刷新 Token，会话: {session_id}")

            # 在后台线程启动 Selenium，传入 jwt_sub
            thread = threading.Thread(
                target=get_token_headless,
                args=(session_id, existing_user.jwt_sub, alias, client_ip),
                daemon=True
            )
            thread.start()

        else:
            # 新用户：预占用户名
            if not registration_manager.reserve_alias(alias, session_id, timeout_seconds=120):
                logger.warning(f"用户名 {alias} 已被预占")
                return {
                    "status": "error",
                    "message": "该用户名正在被其他人注册，请稍后再试或更换用户名"
                }

            logger.info(f"新用户 {alias} 请求注册，会话: {session_id}，已预占用户名")

            # 在后台线程启动 Selenium，不传入 jwt_sub（新用户）
            thread = threading.Thread(
                target=get_token_headless,
                args=(session_id, None, alias, client_ip),
                daemon=True
            )
            thread.start()

        # 等待二维码生成（最多等待 30 秒）
        logger.info(f"等待会话 {session_id} 的二维码生成...")
        max_wait_time = 30
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            session_data = get_session_data(session_id)

            if session_data:
                status = session_data.get("status")

                # 二维码已生成
                if status == "waiting_scan":
                    qr_image_data = session_data.get("qr_image_data")
                    if qr_image_data:
                        logger.info(f"会话 {session_id} 的二维码已生成")
                        return {
                            "session_id": session_id,
                            "qrcode_base64": qr_image_data
                        }

                # 如果已经失败，直接返回错误
                elif status == "failed":
                    error_msg = session_data.get("message", "生成二维码失败")
                    logger.error(f"会话 {session_id} 生成二维码失败: {error_msg}")
                    return {
                        "status": "error",
                        "message": error_msg
                    }

            # 每 0.5 秒检查一次
            time.sleep(0.5)

        # 超时
        logger.error(f"会话 {session_id} 等待二维码生成超时（{max_wait_time}秒）")
        return {
            "status": "error",
            "message": f"生成二维码超时，请重试"
        }

    @staticmethod
    def get_qrcode_status(session_id: str, db: Session) -> Dict[str, Any]:
        """
        检查二维码扫描状态

        Args:
            session_id: 会话 ID
            db: 数据库会话

        Returns:
            包含状态信息的字典
        """
        session_data = get_session_data(session_id)

        if not session_data:
            return {
                "status": "pending",
                "message": "会话不存在或正在初始化"
            }

        status = session_data.get("status")
        jwt_sub = session_data.get("jwt_sub")  # 使用 jwt_sub 而非 signature

        if status == "waiting_scan":
            return {
                "status": "waiting_scan",
                "message": "请使用手机 QQ 扫描二维码",
                "qrcode_image": session_data.get("qr_image_data")
            }

        elif status == "success":
            token = session_data.get("token")
            alias = session_data.get("alias")  # 新增：从 session 中获取 alias

            # 解析 JWT Token 获取 jwt_exp 和 jwt_sub
            jwt_exp = "0"
            jwt_sub = ""

            if not token:
                logger.error("Token 为空")
                return {
                    "status": "error",
                    "message": "Token 为空"
                }

            try:
                # 清洗 Token：URL 解码 + 去除 Bearer 前缀（参考 v1 实现）
                pure_token = unquote(token)  # URL 解码
                if pure_token.lower().startswith('bearer '):
                    pure_token = pure_token[7:]  # 去除 "Bearer " 前缀

                decoded = jwt.decode(pure_token, options={"verify_signature": False})
                jwt_exp = str(decoded.get("exp", 0))
                jwt_sub = decoded.get("sub", "")
                logger.info(f"成功解析 JWT for sub={jwt_sub}, exp={jwt_exp}")
            except Exception as e:
                logger.error(f"解析 JWT Token 失败: {e}")
                return {
                    "status": "error",
                    "message": f"Token 解析失败: {str(e)}"
                }

            # 查找用户（通过 jwt_sub）
            user = db.query(User).filter(User.jwt_sub == jwt_sub).first()

            if user:
                # 老用户：更新 Token（存储清理后的 token）
                # 注意：如果通过别名登录，需要验证 jwt_sub 是否匹配
                if alias and alias == user.alias:
                    # 用户使用别名登录，验证 jwt_sub 是否一致
                    # 如果用户之前的 jwt_sub 不为空且与当前不一致，说明QQ号被换绑了
                    existing_jwt_sub = getattr(user, 'jwt_sub', '')
                    if isinstance(existing_jwt_sub, str) and existing_jwt_sub.strip() and existing_jwt_sub != jwt_sub:
                        logger.warning(f"⚠️ 用户 {user.alias} 的 jwt_sub 不匹配！数据库: {existing_jwt_sub}, 当前: {jwt_sub}")
                        return {
                            "status": "error",
                            "message": "QQ账号不匹配，请使用正确的QQ号扫码登录"
                        }

                user.authorization = pure_token  # 存储清理后的 token
                user.jwt_exp = jwt_exp
                user.token_expiring_notified = False  # 重置"即将过期"提醒标志
                user.token_expired_notified = False  # 重置"已过期"提醒标志
                user.updated_at = datetime.now()
                db.commit()
                db.refresh(user)

                logger.info(f"更新老用户 {user.alias} 的 Token")

                # 生成 JWT access token（用于网站登录）
                access_token = JWTManager.create_access_token(user.id, user.alias)

                return {
                    "status": "success",
                    "message": "登录成功",
                    "token": access_token,  # 返回 JWT token（用于网站登录）
                    "user": {
                        "id": user.id,
                        "alias": user.alias,
                        "role": user.role,
                        "is_approved": user.is_approved,
                        "jwt_sub": user.jwt_sub
                    },
                    "is_new_user": False
                }

            else:
                # 新用户：创建账户
                from backend.services.registration_manager import registration_manager

                # 验证用户名是否被预占
                if not alias or not registration_manager.is_alias_reserved(alias):
                    logger.error(f"新用户注册失败：用户名 {alias} 未预占或已过期")
                    return {
                        "status": "error",
                        "message": "注册失败：会话已过期，请重新扫码"
                    }

                # 检查用户名是否已被其他人注册（防止竞态）
                existing_user_by_alias = db.query(User).filter(User.alias == alias).first()
                if existing_user_by_alias:
                    registration_manager.release_alias(alias)
                    logger.error(f"新用户注册失败：用户名 {alias} 已被占用")
                    return {
                        "status": "error",
                        "message": "注册失败：用户名已被占用，请更换用户名"
                    }

                # 创建新用户（待审批状态）
                new_user = User(
                    jwt_sub=jwt_sub,
                    alias=alias,
                    authorization=pure_token,  # 存储清理后的 token
                    jwt_exp=jwt_exp,
                    role="user",
                    is_approved=False,  # 待审批
                )

                db.add(new_user)
                db.commit()
                db.refresh(new_user)

                # 释放用户名预占
                registration_manager.release_alias(alias)

                logger.info(f"✅ 新用户 {alias} 注册成功（待审批），ID: {new_user.id}")

                # 发送邮件通知管理员
                try:
                    from backend.services.email_service import EmailService
                    EmailService.notify_new_user_registration(new_user, db)
                except Exception as e:
                    logger.error(f"发送注册通知邮件失败: {e}")

                # 生成 JWT access token（用于网站登录）
                access_token = JWTManager.create_access_token(new_user.id, new_user.alias)

                return {
                    "status": "success",
                    "message": "注册成功，请等待管理员审批（24小时内）",
                    "token": access_token,  # 返回 JWT token（用于网站登录）
                    "user": {
                        "id": new_user.id,
                        "alias": new_user.alias,
                        "role": new_user.role,
                        "is_approved": new_user.is_approved,
                        "jwt_sub": new_user.jwt_sub
                    },
                    "is_new_user": True
                }

        elif status == "error":
            return {
                "status": "error",
                "message": session_data.get("message", "未知错误")
            }

        else:
            return {
                "status": "pending",
                "message": "正在初始化..."
            }

    @staticmethod
    def verify_token(authorization: str, db: Session) -> Dict[str, Any]:
        """
        验证 JWT Token 有效性

        Args:
            authorization: JWT Token（可带或不带 "Bearer " 前缀）
            db: 数据库会话

        Returns:
            包含验证结果的字典
        """
        from backend.utils.jwt import JWTManager

        # 移除 "Bearer " 前缀
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization

        try:
            # 验证 JWT token
            payload = JWTManager.verify_token(token)
            user_id = payload.get("user_id")

            if not user_id:
                return {
                    "is_valid": False,
                    "message": "Token 格式错误"
                }

            # 从数据库获取用户
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                return {
                    "is_valid": False,
                    "message": "用户不存在"
                }

            return {
                "is_valid": True,
                "message": "Token 有效",
                "user_id": user.id,
                "alias": user.alias,
                "role": user.role,
                "is_approved": user.is_approved
            }

        except pyjwt.ExpiredSignatureError:
            return {
                "is_valid": False,
                "message": "JWT Token 已过期"
            }
        except pyjwt.InvalidTokenError:
            return {
                "is_valid": False,
                "message": "JWT Token 无效"
            }
        except Exception as e:
            logger.error(f"验证 JWT Token 失败: {str(e)}")
            return {
                "is_valid": False,
                "message": "Token 验证失败"
            }

    @staticmethod
    def verify_checkin_authorization(user: User) -> Dict[str, Any]:
        """
        验证打卡业务 authorization token 的有效性

        注意：这与 JWT token 验证不同
        - JWT token 用于网站登录认证
        - authorization token 用于打卡业务操作（存储在 User.authorization）

        Args:
            user: 用户对象

        Returns:
            包含打卡 token 验证结果的字典
        """
        # 检查是否有 authorization token
        if not user.authorization or user.authorization == "":
            return {
                "is_valid": False,
                "message": "未设置打卡凭证",
                "reason": "no_token"
            }

        # 检查 Token 是否过期
        if not user.jwt_exp or user.jwt_exp == "0":
            return {
                "is_valid": False,
                "message": "打卡凭证无效",
                "reason": "invalid_expiry"
            }

        try:
            exp_timestamp = int(user.jwt_exp)
            current_timestamp = int(datetime.now().timestamp())

            if current_timestamp > exp_timestamp:
                days_expired = (current_timestamp - exp_timestamp) // 86400
                return {
                    "is_valid": False,
                    "message": f"打卡凭证已过期 {days_expired} 天",
                    "reason": "expired",
                    "days_expired": days_expired
                }

            # 计算剩余时间
            seconds_remaining = exp_timestamp - current_timestamp
            days_remaining = seconds_remaining // 86400
            minutes_remaining = seconds_remaining // 60

            # 判断是否即将过期（30分钟内）
            expiring_soon = minutes_remaining <= 30

            return {
                "is_valid": True,
                "message": "打卡凭证有效",
                "days_remaining": days_remaining,
                "minutes_remaining": minutes_remaining,
                "expiring_soon": expiring_soon,
                "expires_at": exp_timestamp
            }

        except ValueError:
            logger.error(f"用户 {user.id} 的 jwt_exp 格式不正确: {user.jwt_exp}")
            return {
                "is_valid": False,
                "message": "打卡凭证格式错误",
                "reason": "invalid_format"
            }

    @staticmethod
    def alias_login(alias: str, password: str, db: Session) -> Dict[str, Any]:
        """
        别名+密码登录

        Args:
            alias: 用户别名
            password: 密码
            db: 数据库会话

        Returns:
            包含登录结果的字典
        """
        # 查找用户
        user = db.query(User).filter(User.alias == alias).first()

        if not user:
            logger.warning(f"别名登录失败：用户 {alias} 不存在")
            return {
                "success": False,
                "message": "用户名或密码错误"
            }

        # 检查用户是否设置了密码
        if not user.password_hash:
            logger.warning(f"别名登录失败：用户 {alias} 未设置密码")
            return {
                "success": False,
                "message": "该用户未设置密码，请使用扫码登录"
            }

        # 验证密码
        try:
            password_bytes = password.encode('utf-8')
            hash_bytes = user.password_hash.encode('utf-8')

            if not bcrypt.checkpw(password_bytes, hash_bytes):
                logger.warning(f"别名登录失败：用户 {alias} 密码错误")
                return {
                    "success": False,
                    "message": "用户名或密码错误"
                }
        except Exception as e:
            logger.error(f"密码验证异常：{e}")
            return {
                "success": False,
                "message": "登录失败，请稍后重试"
            }

        # 检查 Token 状态（仅作提示，不阻止登录）
        token_warning = None

        if not user.authorization or user.jwt_exp == "0":
            logger.info(f"用户 {alias} Token 无效，允许密码登录但需提示用户更新")
            token_warning = "token_invalid"
        else:
            # 检查 Token 是否过期
            try:
                exp_timestamp = int(user.jwt_exp)
                current_timestamp = int(datetime.now().timestamp())

                if current_timestamp > exp_timestamp:
                    logger.info(f"用户 {alias} Token 已过期，允许密码登录但需提示用户更新")
                    token_warning = "token_expired"
            except ValueError:
                logger.error(f"用户 {user.id} 的 jwt_exp 格式不正确: {user.jwt_exp}")

        # 登录成功
        logger.info(f"✅ 用户 {alias} (ID: {user.id}) 别名登录成功")

        # 生成 JWT access token（用于网站登录）
        access_token = JWTManager.create_access_token(user.id, user.alias)

        result = {
            "success": True,
            "message": "登录成功",
            "token": access_token,  # 返回 JWT token（用于网站登录）
            "user": {
                "id": user.id,
                "alias": user.alias,
                "role": user.role,
                "is_approved": user.is_approved
            }
        }

        # 如果打卡 Token 有问题，添加警告信息（不影响网站使用）
        if token_warning:
            result["token_warning"] = token_warning
            if token_warning == "token_invalid":
                result["warning_message"] = "登录成功，但检测到打卡凭证无效，无法自动打卡，建议扫码更新"
            elif token_warning == "token_expired":
                result["warning_message"] = "登录成功，但检测到打卡凭证已过期，无法自动打卡，建议扫码更新"

        return result

    @staticmethod
    def hash_password(password: str) -> str:
        """
        使用 bcrypt 加密密码

        Args:
            password: 明文密码

        Returns:
            加密后的密码哈希
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hash_bytes = bcrypt.hashpw(password_bytes, salt)
        return hash_bytes.decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        验证密码

        Args:
            password: 明文密码
            password_hash: 密码哈希

        Returns:
            密码是否正确
        """
        try:
            password_bytes = password.encode('utf-8')
            hash_bytes = password_hash.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            logger.error(f"密码验证异常：{e}")
            return False

    @staticmethod
    def cancel_qrcode_session(session_id: str) -> Dict[str, Any]:
        """
        取消二维码登录会话

        Args:
            session_id: 会话 ID

        Returns:
            包含取消结果的字典
        """
        from backend.workers.token_refresher import cancel_session

        success = cancel_session(session_id)

        if success:
            return {
                "success": True,
                "message": "会话已取消"
            }
        else:
            return {
                "success": False,
                "message": "取消失败或会话不存在"
            }
