import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import json
import threading

from backend.models import User, CheckInTask, CheckInRecord
from backend.workers.check_in_worker import perform_check_in

logger = logging.getLogger(__name__)


class CheckInService:
    """打卡服务"""

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
        logger.info(f"🎯 创建待处理打卡记录 - 任务: {task.name or f'Task-{task.id}'} (ID: {task.id})")

        # 创建一个 pending 状态的记录
        record = CheckInRecord(
            task_id=task.id,
            status="pending",
            response_text="",
            error_message="",
            location="{}",
            trigger_type=trigger_type
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
                    db.query(CheckInRecord).filter(CheckInRecord.id == record_id).update({
                        "status": "failure",
                        "error_message": "任务不存在"
                    })
                    db.commit()
                return

            # 执行打卡
            result = perform_check_in(task, user_token)

            # 更新记录
            db.query(CheckInRecord).filter(CheckInRecord.id == record_id).update({
                "status": result["status"],
                "response_text": result["response_text"],
                "error_message": result["error_message"]
            })
            db.commit()

            if result["success"]:
                logger.info(f"✅ 后台打卡成功 - Record ID: {record_id}")
            else:
                logger.error(f"❌ 后台打卡失败 - Record ID: {record_id}, 错误: {result['error_message']}")

        except Exception as e:
            logger.error(f"💥 后台打卡异常 - Task ID: {task_id}, Record ID: {record_id}, 错误: {str(e)}")
            # 更新记录状态
            try:
                db.query(CheckInRecord).filter(CheckInRecord.id == record_id).update({
                    "status": "failure",
                    "error_message": f"后台执行异常: {str(e)}"
                })
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

        # 获取用户的 Token
        user = task.user
        if not user or not user.authorization:
            error_msg = f"用户没有有效的 Token"
            logger.error(f"❌ {error_msg} - Task ID: {task.id}")

            # 创建失败记录
            record = CheckInRecord(
                task_id=task.id,
                status="failure",
                response_text="",
                error_message=error_msg,
                location="{}",
                trigger_type=trigger_type
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            return {
                "record_id": record.id,
                "status": "failure",
                "message": error_msg
            }

        # 检查 Token 是否过期
        if user.jwt_exp and user.jwt_exp != "0":
            try:
                exp_timestamp = int(user.jwt_exp)
                current_timestamp = int(datetime.now().timestamp())
                if current_timestamp > exp_timestamp:
                    error_msg = f"Token 已过期"
                    logger.warning(f"⏰ {error_msg} - Task ID: {task.id}")

                    record = CheckInRecord(
                        task_id=task.id,
                        status="failure",
                        response_text="",
                        error_message=f"{error_msg}，请重新扫码登录",
                        location="{}",
                        trigger_type=trigger_type
                    )
                    db.add(record)
                    db.commit()
                    db.refresh(record)

                    return {
                        "record_id": record.id,
                        "status": "failure",
                        "message": f"{error_msg}，请重新扫码登录"
                    }
            except ValueError:
                pass

        # 创建待处理记录
        record_id = CheckInService.create_pending_check_in_record(task, trigger_type, db)

        # 在后台线程中执行打卡
        import threading
        thread = threading.Thread(
            target=CheckInService.execute_check_in_async,
            args=(task.id, record_id, user.authorization),
            daemon=True
        )
        thread.start()

        logger.info(f"✅ 异步打卡任务已启动 - Record ID: {record_id}")

        return {
            "record_id": record_id,
            "status": "pending",
            "message": "打卡任务已启动，正在后台处理"
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
        logger.info(f"🎯 开始打卡 - 任务: {task.name or f'Task-{task.id}'} (ID: {task.id}), 触发: {trigger_type}")

        # 获取用户的 Token
        user = task.user
        if not user or not user.authorization:
            error_msg = f"用户没有有效的 Token"
            logger.error(f"❌ {error_msg} - Task ID: {task.id}, User ID: {user.id if user else 'None'}")

            # 记录失败
            record = CheckInRecord(
                task_id=task.id,
                status="failure",
                response_text="",
                error_message=error_msg,
                location="{}",
                trigger_type=trigger_type
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            return {
                "success": False,
                "message": error_msg,
                "record_id": record.id
            }

        # 检查 Token 是否过期
        if user.jwt_exp and user.jwt_exp != "0":
            try:
                exp_timestamp = int(user.jwt_exp)
                current_timestamp = int(datetime.now().timestamp())
                if current_timestamp > exp_timestamp:
                    error_msg = f"Token 已过期"
                    expires_at = datetime.fromtimestamp(exp_timestamp)
                    logger.warning(f"⏰ {error_msg} - 过期时间: {expires_at}, 用户: {user.alias}, Task ID: {task.id}")

                    # 记录失败
                    record = CheckInRecord(
                        task_id=task.id,
                        status="failure",
                        response_text="",
                        error_message=error_msg,
                        location="{}",
                        trigger_type=trigger_type
                    )
                    db.add(record)
                    db.commit()
                    db.refresh(record)

                    return {
                        "success": False,
                        "message": f"{error_msg}，请重新扫码登录",
                        "record_id": record.id
                    }
            except ValueError:
                pass

        # 执行打卡（传递 task 对象和用户 token）
        logger.info(f"🤖 调用 Selenium Worker 执行打卡...")
        result = perform_check_in(task, user.authorization)

        # 保存打卡记录
        record = CheckInRecord(
            task_id=task.id,
            status=result["status"],
            response_text=result["response_text"],
            error_message=result["error_message"],
            location="{}",
            trigger_type=trigger_type
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
            "record_id": record.id
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

        results = {
            "total": len(task_ids),
            "success": 0,
            "failure": 0,
            "skipped": 0,
            "details": []
        }

        # 优化：一次性查询所有任务，避免 N+1 查询
        tasks = db.query(CheckInTask).filter(CheckInTask.id.in_(task_ids)).all()
        tasks_dict = {task.id: task for task in tasks}

        for task_id in task_ids:
            try:
                task = tasks_dict.get(task_id)
                if not task:
                    logger.warning(f"⚠️ 任务 ID {task_id} 不存在，跳过")
                    results["skipped"] += 1
                    results["details"].append({
                        "task_id": task_id,
                        "success": False,
                        "message": "任务不存在"
                    })
                    continue

                # 执行打卡（移除 is_active 检查，允许手动打卡）
                result = CheckInService.perform_task_check_in(task, "admin", db)

                if result["success"]:
                    results["success"] += 1
                    logger.info(f"✅ 任务 {task_id} 批量打卡成功")
                else:
                    results["failure"] += 1
                    logger.error(f"❌ 任务 {task_id} 批量打卡失败: {result['message']}")

                results["details"].append({
                    "task_id": task_id,
                    "task_name": task.name or f'Task-{task.id}',
                    "success": result["success"],
                    "message": result["message"],
                    "record_id": result.get("record_id")
                })

            except Exception as e:
                logger.error(f"💥 任务 {task_id} 处理异常: {str(e)}")
                results["failure"] += 1
                results["details"].append({
                    "task_id": task_id,
                    "success": False,
                    "message": f"异常: {str(e)}"
                })

        logger.info(f"📊 批量打卡完成 - 成功: {results['success']}, 失败: {results['failure']}, 跳过: {results['skipped']}")
        return results

    @staticmethod
    def scheduled_check_in_all_active_tasks(db: Session) -> Dict[str, Any]:
        """
        定时任务：为所有启用的任务执行打卡

        Args:
            db: 数据库会话

        Returns:
            打卡结果统计
        """
        logger.info("开始执行定时打卡任务...")

        # 获取所有启用的任务（预加载用户信息）
        from sqlalchemy.orm import joinedload
        active_tasks = db.query(CheckInTask).options(
            joinedload(CheckInTask.user)
        ).filter(CheckInTask.is_active == True).all()

        logger.info(f"找到 {len(active_tasks)} 个启用的任务")

        results = {
            "total": len(active_tasks),
            "success": 0,
            "failure": 0,
            "skipped": 0,
            "details": []
        }

        for task in active_tasks:
            # 检查用户是否有 Token
            if not task.user or not task.user.authorization:
                logger.warning(f"任务 ID: {task.id} 的用户没有 Token，跳过")
                results["skipped"] += 1
                continue

            # 检查 Token 是否过期
            if task.user.jwt_exp and task.user.jwt_exp != "0":
                try:
                    exp_timestamp = int(task.user.jwt_exp)
                    current_timestamp = int(datetime.now().timestamp())
                    if current_timestamp > exp_timestamp:
                        logger.warning(f"任务 ID: {task.id} 的用户 Token 已过期，跳过")
                        results["skipped"] += 1
                        continue
                except ValueError:
                    pass

            # 执行打卡
            result = CheckInService.perform_task_check_in(task, "scheduled", db)

            if result["success"]:
                results["success"] += 1
            else:
                results["failure"] += 1

            results["details"].append({
                "task_id": task.id,
                "task_name": task.name or f'Task-{task.id}',
                "success": result["success"],
                "message": result["message"]
            })

        logger.info(f"定时打卡任务完成，成功: {results['success']}, 失败: {results['failure']}, 跳过: {results['skipped']}")
        return results

    @staticmethod
    def get_task_records(
        task_id: int,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        trigger_type: Optional[str] = None
    ) -> List[CheckInRecord]:
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
            打卡记录列表
        """
        query = db.query(CheckInRecord).filter(CheckInRecord.task_id == task_id)

        if status:
            query = query.filter(CheckInRecord.status == status)

        if trigger_type:
            query = query.filter(CheckInRecord.trigger_type == trigger_type)

        return query.order_by(
            CheckInRecord.check_in_time.desc()
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_user_records(
        user_id: int,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        trigger_type: Optional[str] = None
    ) -> List[CheckInRecord]:
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
            打卡记录列表
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

        return query.order_by(
            CheckInRecord.check_in_time.desc()
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_all_records(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        task_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[CheckInRecord]:
        """
        获取所有打卡记录（管理员）

        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 限制记录数
            task_id: 过滤任务 ID
            status: 过滤状态

        Returns:
            打卡记录列表
        """
        query = db.query(CheckInRecord)

        if task_id:
            query = query.filter(CheckInRecord.task_id == task_id)

        if status:
            query = query.filter(CheckInRecord.status == status)

        return query.order_by(
            CheckInRecord.check_in_time.desc()
        ).offset(skip).limit(limit).all()

    @staticmethod
    def enrich_record_with_user_task_info(record: CheckInRecord, db: Session) -> dict:
        """
        为打卡记录添加用户和任务信息

        Args:
            record: 打卡记录对象
            db: 数据库会话

        Returns:
            包含额外信息的记录字典
        """
        # 获取任务信息
        task = db.query(CheckInTask).filter(CheckInTask.id == record.task_id).first()

        # 获取用户信息
        user = None
        task_name = None
        thread_id = None

        if task:
            user = db.query(User).filter(User.id == task.user_id).first()
            task_name = task.name

            # 从 payload_config 提取 ThreadId
            try:
                payload = json.loads(str(task.payload_config))
                thread_id = payload.get('ThreadId')
            except:
                pass

        # 转换为字典并添加额外字段
        record_dict = {
            'id': record.id,
            'task_id': record.task_id,
            'status': record.status,
            'response_text': record.response_text,
            'error_message': record.error_message,
            'location': record.location,
            'trigger_type': record.trigger_type,
            'check_in_time': record.check_in_time,
            'user_id': user.id if user else None,
            'user_email': user.email if user else None,
            'task_name': task_name,
            'thread_id': thread_id,
        }

        return record_dict
