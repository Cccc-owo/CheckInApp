import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.models import User, CheckInTask, CheckInRecord
from backend.schemas.task import TaskCreate, TaskUpdate

logger = logging.getLogger(__name__)


class TaskService:
    """打卡任务服务"""

    @staticmethod
    def create_task(user_id: int, task_data: TaskCreate, db: Session) -> CheckInTask:
        """
        创建打卡任务

        Args:
            user_id: 用户 ID
            task_data: 任务数据
            db: 数据库会话

        Returns:
            创建的任务对象
        """
        import json

        # 1. 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"用户 ID {user_id} 不存在")

        # 2. 从 payload_config 中提取 ThreadId 用于唯一性校验
        from backend.utils.json_helpers import safe_parse_payload, extract_thread_id

        payload = safe_parse_payload(task_data.payload_config)
        thread_id = payload.get("ThreadId")
        if not thread_id:
            raise ValueError("payload_config 中缺少 ThreadId")

        # 3. 验证唯一性：同一用户在同一个接龙中不能有重复的任务
        existing_tasks = (
            db.query(CheckInTask.payload_config).filter(CheckInTask.user_id == user_id).all()
        )

        for (payload_config,) in existing_tasks:
            existing_thread_id = extract_thread_id(payload_config)
            # extract_thread_id 已处理异常，失败时返回 None
            if existing_thread_id and existing_thread_id == thread_id:
                logger.warning(
                    f"⚠️ 任务创建冲突 - User: {user.alias}({user_id}), ThreadId: {thread_id}"
                )
                raise ValueError(f"该接龙中已存在任务。ThreadId: {thread_id}")

        # 4. 记录日志
        task_name = task_data.name or f"接龙任务 {thread_id}"
        logger.info(f"📝 用户 {user.alias}({user_id}) 正在创建任务: {task_name}")

        # 5. 创建任务
        task = CheckInTask(
            user_id=user_id,
            payload_config=task_data.payload_config,
            name=task_data.name or task_name,
            is_active=task_data.is_active if task_data.is_active is not None else True,
        )

        try:
            db.add(task)
            db.commit()
            db.refresh(task)
            logger.info(
                f"✅ 任务创建成功 - ID: {task.id}, Name: {task.name}, ThreadId: {thread_id}"
            )

            # 如果任务启用且包含 cron_expression，立即添加到调度器
            if task.is_scheduled_enabled:
                TaskService._reload_scheduler_for_task(task, db)

            return task
        except Exception as e:
            db.rollback()
            logger.error(f"❌ 任务创建失败: {str(e)}")
            raise ValueError(f"任务创建失败: {str(e)}")

    @staticmethod
    def get_task(task_id: int, db: Session) -> Optional[CheckInTask]:
        """
        获取任务详情

        Args:
            task_id: 任务 ID
            db: 数据库会话

        Returns:
            任务对象或 None
        """
        return db.query(CheckInTask).filter(CheckInTask.id == task_id).first()

    @staticmethod
    def enrich_task_with_check_in_info(task: CheckInTask, db: Session) -> dict:
        """
        为任务添加最后一次打卡信息和 ThreadId

        Args:
            task: 任务对象
            db: 数据库会话

        Returns:
            包含额外信息的任务字典
        """
        from backend.utils.json_helpers import extract_thread_id

        # 获取最后一次打卡记录
        last_record = (
            db.query(CheckInRecord)
            .filter(CheckInRecord.task_id == task.id)
            .order_by(desc(CheckInRecord.check_in_time))
            .first()
        )

        # 从 payload_config 提取 ThreadId
        thread_id = extract_thread_id(task.payload_config)  # type: ignore

        # 转换为字典并添加额外字段
        task_dict = {
            "id": task.id,
            "user_id": task.user_id,
            "payload_config": task.payload_config,
            "name": task.name,
            "is_active": task.is_active,
            "cron_expression": task.cron_expression,
            "is_scheduled_enabled": task.is_scheduled_enabled,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "thread_id": thread_id,
            "last_check_in_time": last_record.check_in_time if last_record else None,
            "last_check_in_status": last_record.status if last_record else None,
        }

        return task_dict

    @staticmethod
    def get_user_tasks(
        user_id: int, db: Session, include_inactive: bool = True
    ) -> List[CheckInTask]:
        """
        获取用户的所有任务

        Args:
            user_id: 用户 ID
            db: 数据库会话
            include_inactive: 是否包含未启用的任务

        Returns:
            任务列表
        """
        query = db.query(CheckInTask).filter(CheckInTask.user_id == user_id)

        if not include_inactive:
            query = query.filter(CheckInTask.is_active == True)

        return query.order_by(desc(CheckInTask.created_at)).all()

    @staticmethod
    def get_all_active_tasks(db: Session) -> List[CheckInTask]:
        """
        获取所有启用的任务（用于定时打卡）

        Args:
            db: 数据库会话

        Returns:
            启用的任务列表
        """
        return db.query(CheckInTask).filter(CheckInTask.is_active == True).all()

    @staticmethod
    def update_task(task_id: int, task_data: TaskUpdate, db: Session) -> Optional[CheckInTask]:
        """
        更新任务

        Args:
            task_id: 任务 ID
            task_data: 更新数据
            db: 数据库会话

        Returns:
            更新后的任务对象或 None
        """
        task = db.query(CheckInTask).filter(CheckInTask.id == task_id).first()

        if not task:
            return None

        # 更新字段
        update_data = task_data.model_dump(exclude_unset=True)

        # 检查是否更新了 cron_expression 或 is_active
        cron_changed = "cron_expression" in update_data
        active_changed = "is_active" in update_data

        for field, value in update_data.items():
            setattr(task, field, value)

        db.commit()
        db.refresh(task)

        logger.info(f"任务 {task_id} 已更新")

        # 如果 cron_expression 或 is_active 发生变化，重新加载调度器
        if cron_changed or active_changed:
            TaskService._reload_scheduler_for_task(task, db)

        return task

    @staticmethod
    def delete_task(task_id: int, db: Session) -> bool:
        """
        删除任务

        Args:
            task_id: 任务 ID
            db: 数据库会话

        Returns:
            是否删除成功
        """
        task = db.query(CheckInTask).filter(CheckInTask.id == task_id).first()

        if not task:
            return False

        db.delete(task)
        db.commit()

        logger.info(f"任务 {task_id} 已删除")

        # 从调度器中移除该任务
        TaskService._remove_task_from_scheduler(task_id)

        return True

    @staticmethod
    def toggle_task(task_id: int, db: Session) -> Optional[CheckInTask]:
        """
        切换任务的启用状态

        Args:
            task_id: 任务 ID
            db: 数据库会话

        Returns:
            更新后的任务对象或 None
        """
        task = db.query(CheckInTask).filter(CheckInTask.id == task_id).first()

        if not task:
            return None

        task.is_active = not task.is_active
        db.commit()
        db.refresh(task)

        logger.info(f"任务 {task_id} 状态已切换为: {'启用' if task.is_active else '禁用'}")

        # 重新加载调度器
        TaskService._reload_scheduler_for_task(task, db)

        return task

    @staticmethod
    def get_task_records(task_id: int, db: Session, limit: int = 50) -> List[CheckInRecord]:
        """
        获取任务的打卡记录

        Args:
            task_id: 任务 ID
            db: 数据库会话
            limit: 返回记录数量限制

        Returns:
            打卡记录列表
        """
        return (
            db.query(CheckInRecord)
            .filter(CheckInRecord.task_id == task_id)
            .order_by(desc(CheckInRecord.check_in_time))
            .limit(limit)
            .all()
        )

    @staticmethod
    def verify_task_ownership(task_id: int, user_id: int, db: Session) -> bool:
        """
        验证任务是否属于指定用户

        Args:
            task_id: 任务 ID
            user_id: 用户 ID
            db: 数据库会话

        Returns:
            是否属于该用户
        """
        task = (
            db.query(CheckInTask)
            .filter(CheckInTask.id == task_id, CheckInTask.user_id == user_id)
            .first()
        )

        return task is not None

    @staticmethod
    def _reload_scheduler_for_task(task: CheckInTask, db: Session):
        """
        重新加载指定任务到调度器

        Args:
            task: 任务对象
            db: 数据库会话
        """
        try:
            from backend.services.scheduler_service import scheduler
            from apscheduler.triggers.cron import CronTrigger
            from croniter import croniter

            if not scheduler:
                logger.warning(f"调度器未启动，无法加载任务 {task.id}")
                return

            job_id = f"task_{task.id}"

            # 先移除旧的任务（如果存在）
            existing_job = scheduler.get_job(job_id)
            if existing_job:
                scheduler.remove_job(job_id)
                logger.info(f"从调度器移除旧任务: {job_id}")

            # 如果任务启用且有有效的 cron 表达式，添加新任务
            if task.is_scheduled_enabled:
                cron_str = str(task.cron_expression)
                if croniter.is_valid(cron_str):
                    from backend.services.scheduler_service import scheduled_check_in_task

                    scheduler.add_job(
                        func=scheduled_check_in_task,
                        trigger=CronTrigger.from_crontab(cron_str),
                        id=job_id,
                        name=f"CheckIn-Task-{task.id}",
                        args=[task.id],
                        replace_existing=True,
                    )
                    logger.info(f"✅ 任务 {task.id} 已重新加载到调度器: {cron_str}")
                else:
                    logger.warning(f"任务 {task.id} 的 cron 表达式无效: {cron_str}")
            else:
                logger.info(f"任务 {task.id} 未启用或无 cron 表达式，已从调度器移除")

        except Exception as e:
            logger.error(f"重新加载任务 {task.id} 到调度器失败: {str(e)}")

    @staticmethod
    def _remove_task_from_scheduler(task_id: int):
        """
        从调度器中移除指定任务

        Args:
            task_id: 任务 ID
        """
        try:
            from backend.services.scheduler_service import scheduler

            if not scheduler:
                return

            job_id = f"task_{task_id}"
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
                logger.info(f"✅ 任务 {task_id} 已从调度器移除")

        except Exception as e:
            logger.error(f"从调度器移除任务 {task_id} 失败: {str(e)}")
