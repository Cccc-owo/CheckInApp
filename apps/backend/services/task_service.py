import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.exceptions import (
    InternalServerError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError as APIValidationError,
)
from backend.models import User, CheckInTask, CheckInRecord
from backend.schemas.task import TaskCreate, TaskUpdate

logger = logging.getLogger(__name__)


class TaskService:
    """打卡任务服务"""

    @staticmethod
    def _normalize_thread_id(thread_id: Any) -> str:
        value = str(thread_id).strip() if thread_id is not None else ""
        if not value:
            raise APIValidationError(
                "payload_config 必须包含有效的 ThreadId 字段",
                error_code="TASK_IDENTITY_INVALID",
            )
        return value

    @staticmethod
    def _extract_thread_id_from_payload(payload_config: str) -> str:
        from backend.utils.json_helpers import safe_parse_payload

        payload = safe_parse_payload(payload_config)
        return TaskService._normalize_thread_id(payload.get("ThreadId"))

    @staticmethod
    def _resolve_thread_id_for_task(task: CheckInTask) -> Optional[str]:
        thread_id = getattr(task, "thread_id", None)
        if thread_id is not None:
            value = str(thread_id).strip()
            if value:
                return value

        from backend.utils.json_helpers import extract_thread_id

        legacy_thread_id = extract_thread_id(task.payload_config)
        if legacy_thread_id is None:
            return None
        value = str(legacy_thread_id).strip()
        return value or None

    @staticmethod
    def _ensure_unique_thread_id(
        db: Session, user_id: int, thread_id: str, exclude_task_id: int | None = None
    ) -> None:
        query = db.query(CheckInTask.id).filter(
            CheckInTask.user_id == user_id, CheckInTask.thread_id == thread_id
        )
        if exclude_task_id is not None:
            query = query.filter(CheckInTask.id != exclude_task_id)

        conflict = query.first()
        if conflict:
            raise ResourceConflictError(
                f"该接龙中已存在任务。ThreadId: {thread_id}",
                error_code="TASK_IDENTITY_CONFLICT",
            )

    @staticmethod
    def _sync_scheduler_for_task(task: CheckInTask) -> None:
        from backend.services.scheduler_service import sync_scheduled_task

        sync_scheduled_task(task)

    @staticmethod
    def _remove_scheduler_for_task(task_id: int) -> None:
        from backend.services.scheduler_service import remove_scheduled_task

        remove_scheduled_task(task_id)

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
        # 1. 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ResourceNotFoundError(f"用户 ID {user_id} 不存在", error_code="USER_NOT_FOUND")

        # 2. 从 payload_config 中提取 ThreadId 用于唯一性校验
        thread_id = TaskService._extract_thread_id_from_payload(task_data.payload_config)

        # 3. 验证唯一性：同一用户在同一个接龙中不能有重复的任务
        TaskService._ensure_unique_thread_id(db, user_id, thread_id)

        # 4. 记录日志
        task_name = task_data.name or f"接龙任务 {thread_id}"
        logger.info(f"📝 用户 {user.alias}({user_id}) 正在创建任务: {task_name}")

        # 5. 创建任务
        task = CheckInTask(
            user_id=user_id,
            thread_id=thread_id,
            payload_config=task_data.payload_config,
            name=task_data.name or task_name,
            is_active=task_data.is_active if task_data.is_active is not None else True,
            cron_expression=task_data.cron_expression or "0 20 * * *",
        )

        try:
            db.add(task)
            db.commit()
            db.refresh(task)
            logger.info(
                f"✅ 任务创建成功 - ID: {task.id}, Name: {task.name}, ThreadId: {thread_id}"
            )

            # 如果任务启用且包含 cron_expression，立即添加到调度器
            TaskService._sync_scheduler_for_task(task)

            return task
        except APIValidationError:
            db.rollback()
            raise
        except ResourceConflictError:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"❌ 任务创建失败: {str(e)}")
            raise InternalServerError(f"任务创建失败: {str(e)}")

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
        # 获取最后一次打卡记录
        last_record = (
            db.query(CheckInRecord)
            .filter(CheckInRecord.task_id == task.id)
            .order_by(desc(CheckInRecord.check_in_time))
            .first()
        )

        # 优先使用持久化的 ThreadId，兼容旧数据时回退到 payload_config
        thread_id = TaskService._resolve_thread_id_for_task(task)

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
            raise ResourceNotFoundError("任务不存在", error_code="TASK_NOT_FOUND")

        # 更新字段
        update_data = task_data.model_dump(exclude_unset=True)

        # 检查是否更新了 cron_expression 或 is_active
        cron_changed = "cron_expression" in update_data
        active_changed = "is_active" in update_data

        if "payload_config" in update_data:
            new_thread_id = TaskService._extract_thread_id_from_payload(
                update_data["payload_config"]
            )
            TaskService._ensure_unique_thread_id(
                db, task.user_id, new_thread_id, exclude_task_id=task.id
            )
            task.thread_id = new_thread_id

        for field, value in update_data.items():
            setattr(task, field, value)

        try:
            db.commit()
            db.refresh(task)
        except ResourceConflictError:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"任务 {task_id} 更新失败: {str(e)}")
            raise InternalServerError(f"任务更新失败: {str(e)}")

        logger.info(f"任务 {task_id} 已更新")

        # 如果 cron_expression 或 is_active 发生变化，重新加载调度器
        if cron_changed or active_changed:
            TaskService._sync_scheduler_for_task(task)

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
            raise ResourceNotFoundError("任务不存在", error_code="TASK_NOT_FOUND")

        try:
            db.delete(task)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"任务 {task_id} 删除失败: {str(e)}")
            raise InternalServerError(f"任务删除失败: {str(e)}")

        logger.info(f"任务 {task_id} 已删除")

        # 从调度器中移除该任务
        TaskService._remove_scheduler_for_task(task_id)

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
            raise ResourceNotFoundError("任务不存在", error_code="TASK_NOT_FOUND")

        task.is_active = not task.is_active
        try:
            db.commit()
            db.refresh(task)
        except Exception as e:
            db.rollback()
            logger.error(f"任务 {task_id} 状态切换失败: {str(e)}")
            raise InternalServerError(f"任务状态切换失败: {str(e)}")

        logger.info(f"任务 {task_id} 状态已切换为: {'启用' if task.is_active else '禁用'}")

        # 重新加载调度器
        TaskService._sync_scheduler_for_task(task)

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
            TaskService._sync_scheduler_for_task(task)
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
            TaskService._remove_scheduler_for_task(task_id)
        except Exception as e:
            logger.error(f"从调度器移除任务 {task_id} 失败: {str(e)}")
