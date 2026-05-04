import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import threading

from backend.models import User, CheckInTask, CheckInRecord
from backend.workers.check_in_worker import perform_check_in

logger = logging.getLogger(__name__)


class CheckInService:
    """打卡服务"""

    @staticmethod
    def handle_token_expired(user: User, task: CheckInTask, db: Session) -> None:
        """
        处理 Token 过期情况：发送邮件通知并标记标志位

        Args:
            user: 用户对象
            task: 打卡任务对象
            db: 数据库会话
        """
        if not user or not user.email:
            return

        # 检查是否已经发送过通知
        if user.token_expired_notified:
            logger.debug(f"用户 {user.alias} 已发送过 Token 过期通知，跳过")
            return

        try:
            from backend.services.email_service import EmailService
            from backend.utils.json_helpers import build_task_info

            # 使用辅助函数构建 task_info
            task_info = build_task_info(task)

            # 发送打卡失败通知（内容包含 Token 失效说明和刷新指引）
            EmailService.notify_check_in_result(
                user, task_info, False, "Token 已失效，需要重新授权"
            )
            logger.info(f"已发送 Token 过期邮件到 {user.email}")

            # 标记已发送 Token 过期通知
            user.token_expired_notified = True
            db.commit()
            logger.info(f"标记用户 {user.alias} 的 token_expired_notified 为 True")

        except Exception as e:
            logger.error(f"处理 Token 过期失败: {e}")

    @staticmethod
    def create_pending_check_in_record(task: CheckInTask, trigger_type: str, db: Session) -> int:
        """
        创建一个待处理的打卡记录并返回 record_id

        Args:
            task: 打卡任务对象
            trigger_type: 触发类型 (manual/scheduled/admin)
            db: 数据库会话

        Returns:
            打卡记录 ID
        """
        logger.info(
            f"🎯 创建待处理打卡记录 - 任务: {task.name or f'Task-{task.id}'} (ID: {task.id})"
        )

        # 创建一个 pending 状态的记录
        record = CheckInRecord(
            task_id=task.id,
            status="pending",
            response_text="",
            error_message="",
            location="{}",
            trigger_type=trigger_type,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        logger.info(f"✅ 创建待处理记录成功 - Record ID: {record.id}")
        return record.id

    @staticmethod
    def execute_check_in_async(task_id: int, record_id: int, user_token: str):
        """
        在后台线程中执行打卡操作

        Args:
            task_id: 任务 ID
            record_id: 打卡记录 ID
            user_token: 用户 Token
        """
        from backend.models.database import SessionLocal

        # 创建独立的数据库会话
        db = SessionLocal()

        try:
            logger.info(f"🤖 后台线程开始执行打卡 - Task ID: {task_id}, Record ID: {record_id}")

            # 获取任务对象
            task = db.query(CheckInTask).filter(CheckInTask.id == task_id).first()
            if not task:
                logger.error(f"❌ 任务不存在 - Task ID: {task_id}")
                # 更新记录状态为失败
                record = db.query(CheckInRecord).filter(CheckInRecord.id == record_id).first()
                if record:
                    db.query(CheckInRecord).filter(CheckInRecord.id == record_id).update(
                        {"status": "failure", "error_message": "任务不存在"}
                    )
                    db.commit()
                return

            # 执行打卡
            result = perform_check_in(task, user_token)

            # 如果是 Token 过期导致的失败，处理 Token 过期情况
            if result["status"] == "token_expired" and task.user:
                CheckInService.handle_token_expired(task.user, task, db)

            # 更新记录
            db.query(CheckInRecord).filter(CheckInRecord.id == record_id).update(
                {
                    "status": result["status"],
                    "response_text": result["response_text"],
                    "error_message": result["error_message"],
                }
            )
            db.commit()

            if result["success"]:
                logger.info(f"✅ 后台打卡成功 - Record ID: {record_id}")
            else:
                logger.error(
                    f"❌ 后台打卡失败 - Record ID: {record_id}, 错误: {result['error_message']}"
                )

        except Exception as e:
            logger.error(
                f"💥 后台打卡异常 - Task ID: {task_id}, Record ID: {record_id}, 错误: {str(e)}"
            )
            # 更新记录状态
            try:
                db.query(CheckInRecord).filter(CheckInRecord.id == record_id).update(
                    {"status": "failure", "error_message": f"后台执行异常: {str(e)}"}
                )
                db.commit()
            except Exception as inner_e:
                logger.error(f"💥 更新记录失败: {str(inner_e)}")
        finally:
            db.close()

    @staticmethod
    def start_async_check_in(task: CheckInTask, trigger_type: str, db: Session) -> Dict[str, Any]:
        """
        启动异步打卡任务

        Args:
            task: 打卡任务对象
            trigger_type: 触发类型 (manual/scheduled/admin)
            db: 数据库会话

        Returns:
            包含 record_id 的字典
        """
        logger.info(f"🚀 启动异步打卡 - 任务: {task.name or f'Task-{task.id}'} (ID: {task.id})")

        # 获取用户的打卡 Token
        user = task.user
        if not user or not user.authorization:
            error_msg = f"用户没有有效的打卡 Token"
            logger.error(f"❌ {error_msg} - Task ID: {task.id}")

            # 创建失败记录
            record = CheckInRecord(
                task_id=task.id,
                status="failure",
                response_text="",
                error_message=error_msg,
                location="{}",
                trigger_type=trigger_type,
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            return {"record_id": record.id, "status": "failure", "message": error_msg}

        # 不再提前验证 Token，交给统一的打卡逻辑处理
        # 这样可以确保所有错误（包括 Token 过期）都通过统一的流程处理

        # 创建待处理记录
        record_id = CheckInService.create_pending_check_in_record(task, trigger_type, db)

        # 在后台线程中执行打卡
        import threading

        thread = threading.Thread(
            target=CheckInService.execute_check_in_async,
            args=(task.id, record_id, user.authorization),
            daemon=True,
        )
        thread.start()

        logger.info(f"✅ 异步打卡任务已启动 - Record ID: {record_id}")

        return {
            "record_id": record_id,
            "status": "pending",
            "message": "打卡任务已启动，正在后台处理",
        }

    @staticmethod
    def perform_task_check_in(task: CheckInTask, trigger_type: str, db: Session) -> Dict[str, Any]:
        """
        执行单个任务的打卡

        Args:
            task: 打卡任务对象
            trigger_type: 触发类型 (manual/scheduled/admin)
            db: 数据库会话

        Returns:
            打卡结果字典
        """
        logger.info(
            f"🎯 开始打卡 - 任务: {task.name or f'Task-{task.id}'} (ID: {task.id}), 触发: {trigger_type}"
        )

        # 获取用户的打卡 Token
        user = task.user
        if not user or not user.authorization:
            error_msg = f"用户没有有效的打卡 Token"
            logger.error(
                f"❌ {error_msg} - Task ID: {task.id}, User ID: {user.id if user else 'None'}"
            )

            # 记录失败
            record = CheckInRecord(
                task_id=task.id,
                status="failure",
                response_text="",
                error_message=error_msg,
                location="{}",
                trigger_type=trigger_type,
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            return {"success": False, "message": error_msg, "record_id": record.id}

        # 使用统一的打卡 Token 验证方法
        from backend.services.auth_service import AuthService

        token_result = AuthService.verify_checkin_authorization(user)

        if not token_result["is_valid"]:
            error_msg = token_result["message"]
            logger.warning(f"⏰ {error_msg} - 用户: {user.alias}, Task ID: {task.id}")

            # 处理 Token 过期：发送邮件并标记
            CheckInService.handle_token_expired(user, task, db)

            # 记录失败
            record = CheckInRecord(
                task_id=task.id,
                status="token_expired",  # 使用统一的状态标识
                response_text="",
                error_message=error_msg,
                location="{}",
                trigger_type=trigger_type,
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            return {
                "success": False,
                "message": f"{error_msg}，请重新扫码登录",
                "record_id": record.id,
            }

        # 执行打卡（传递 task 对象和用户 token）
        logger.info(f"🤖 调用 Playwright Worker 执行打卡...")
        result = perform_check_in(task, user.authorization)

        # 如果是 Token 过期导致的失败，处理 Token 过期情况
        if result["status"] == "token_expired" and user:
            CheckInService.handle_token_expired(user, task, db)

        # 保存打卡记录
        record = CheckInRecord(
            task_id=task.id,
            status=result["status"],
            response_text=result["response_text"],
            error_message=result["error_message"],
            location="{}",
            trigger_type=trigger_type,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        if result["success"]:
            logger.info(f"✅ 打卡成功 - Record ID: {record.id}")
        else:
            logger.error(f"❌ 打卡失败 - {result['error_message']}")

        return {
            "success": result["success"],
            "message": "打卡成功" if result["success"] else f"打卡失败: {result['error_message']}",
            "record_id": record.id,
        }

    @staticmethod
    def batch_check_in_tasks(task_ids: List[int], db: Session) -> Dict[str, Any]:
        """
        批量打卡任务

        Args:
            task_ids: 任务 ID 列表
            db: 数据库会话

        Returns:
            批量打卡结果
        """
        logger.info(f"🚀 开始批量打卡，任务数量: {len(task_ids)}")

        results = {"total": len(task_ids), "success": 0, "failure": 0, "skipped": 0, "details": []}

        # 优化：一次性查询所有任务，避免 N+1 查询
        tasks = db.query(CheckInTask).filter(CheckInTask.id.in_(task_ids)).all()
        tasks_dict = {task.id: task for task in tasks}

        for task_id in task_ids:
            try:
                task = tasks_dict.get(task_id)
                if not task:
                    logger.warning(f"⚠️ 任务 ID {task_id} 不存在，跳过")
                    results["skipped"] += 1
                    results["details"].append(
                        {"task_id": task_id, "success": False, "message": "任务不存在"}
                    )
                    continue

                # 执行打卡（移除 is_active 检查，允许手动打卡）
                result = CheckInService.perform_task_check_in(task, "admin", db)

                if result["success"]:
                    results["success"] += 1
                    logger.info(f"✅ 任务 {task_id} 批量打卡成功")
                else:
                    results["failure"] += 1
                    logger.error(f"❌ 任务 {task_id} 批量打卡失败: {result['message']}")

                results["details"].append(
                    {
                        "task_id": task_id,
                        "task_name": task.name or f"Task-{task.id}",
                        "success": result["success"],
                        "message": result["message"],
                        "record_id": result.get("record_id"),
                    }
                )

            except Exception as e:
                logger.error(f"💥 任务 {task_id} 处理异常: {str(e)}")
                results["failure"] += 1
                results["details"].append(
                    {"task_id": task_id, "success": False, "message": f"异常: {str(e)}"}
                )

        logger.info(
            f"📊 批量打卡完成 - 成功: {results['success']}, 失败: {results['failure']}, 跳过: {results['skipped']}"
        )
        return results

    @staticmethod
    def get_task_records(
        task_id: int,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        trigger_type: Optional[str] = None,
    ) -> tuple[List[CheckInRecord], int]:
        """
        获取任务的打卡记录

        Args:
            task_id: 任务 ID
            db: 数据库会话
            skip: 跳过记录数
            limit: 限制记录数
            status: 过滤状态 (success/failure)
            trigger_type: 过滤触发类型 (scheduler/manual)

        Returns:
            (打卡记录列表, 总记录数)
        """
        query = db.query(CheckInRecord).filter(CheckInRecord.task_id == task_id)

        if status:
            query = query.filter(CheckInRecord.status == status)

        if trigger_type:
            query = query.filter(CheckInRecord.trigger_type == trigger_type)

        # 获取总数
        total = query.count()

        # 获取分页数据
        records = query.order_by(CheckInRecord.check_in_time.desc()).offset(skip).limit(limit).all()

        return records, total

    @staticmethod
    def get_user_records(
        user_id: int,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        trigger_type: Optional[str] = None,
    ) -> tuple[List[CheckInRecord], int]:
        """
        获取用户的所有打卡记录

        Args:
            user_id: 用户 ID
            db: 数据库会话
            skip: 跳过记录数
            limit: 限制记录数
            status: 过滤状态 (success/failure)
            trigger_type: 过滤触发类型 (scheduler/manual)

        Returns:
            (打卡记录列表, 总记录数)
        """
        # 获取用户的所有任务ID
        user_task_ids = db.query(CheckInTask.id).filter(CheckInTask.user_id == user_id).all()
        task_ids = [task_id for (task_id,) in user_task_ids]

        # 查询这些任务的打卡记录
        query = db.query(CheckInRecord).filter(CheckInRecord.task_id.in_(task_ids))

        if status:
            query = query.filter(CheckInRecord.status == status)

        if trigger_type:
            query = query.filter(CheckInRecord.trigger_type == trigger_type)

        # 获取总数
        total = query.count()

        # 获取分页数据
        records = query.order_by(CheckInRecord.check_in_time.desc()).offset(skip).limit(limit).all()

        return records, total

    @staticmethod
    def get_all_records(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        task_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> tuple[List[CheckInRecord], int]:
        """
        获取所有打卡记录（管理员）- 使用联表查询优化性能

        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 限制记录数
            task_id: 过滤任务 ID
            status: 过滤状态

        Returns:
            (打卡记录列表, 总记录数)
        """
        from sqlalchemy.orm import joinedload

        # 使用 joinedload 预加载关联的 task 和 user，避免 N+1 查询
        query = db.query(CheckInRecord).options(
            joinedload(CheckInRecord.task).joinedload(CheckInTask.user)
        )

        if task_id:
            query = query.filter(CheckInRecord.task_id == task_id)

        if status:
            query = query.filter(CheckInRecord.status == status)

        # 获取总数
        total = query.count()

        # 获取分页数据
        records = query.order_by(CheckInRecord.check_in_time.desc()).offset(skip).limit(limit).all()

        return records, total

    @staticmethod
    def enrich_record_with_user_task_info(record: CheckInRecord, db: Session) -> dict:
        """
        为打卡记录添加用户和任务信息

        注意：如果使用了 joinedload，task 和 user 已经预加载，不会产生额外查询

        Args:
            record: 打卡记录对象
            db: 数据库会话（可选，仅在未使用 joinedload 时使用）

        Returns:
            包含额外信息的记录字典
        """
        # 尝试使用已加载的关联对象，如果没有则查询
        task = (
            record.task
            if hasattr(record, "task") and record.task
            else db.query(CheckInTask).filter(CheckInTask.id == record.task_id).first()
        )

        # 获取用户信息
        user = None
        task_name = None
        thread_id = None

        if task:
            # 尝试使用已加载的 user，否则查询
            user = (
                task.user
                if hasattr(task, "user") and task.user
                else db.query(User).filter(User.id == task.user_id).first()
            )
            task_name = task.name

            # 从 payload_config 提取 ThreadId
            from backend.utils.json_helpers import extract_thread_id

            thread_id = extract_thread_id(task.payload_config)  # type: ignore

        # 转换为字典并添加额外字段
        record_dict = {
            "id": record.id,
            "task_id": record.task_id,
            "status": record.status,
            "response_text": record.response_text,
            "error_message": record.error_message,
            "location": record.location,
            "trigger_type": record.trigger_type,
            "check_in_time": record.check_in_time,
            "user_id": user.id if user else None,
            "user_email": user.email if user else None,
            "task_name": task_name,
            "thread_id": thread_id,
        }

        return record_dict
