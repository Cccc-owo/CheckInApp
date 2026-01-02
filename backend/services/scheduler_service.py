import logging
import os
import time
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from filelock import FileLock
from sqlalchemy.orm import Session
from croniter import croniter

from backend.config import settings
from backend.models import get_db, User, CheckInTask
from backend.services.check_in_service import CheckInService
from backend.services.admin_service import AdminService

logger = logging.getLogger(__name__)

# 全局调度器实例
scheduler = None
scheduler_lock = None


def load_scheduled_tasks(db: Session, scheduler_instance):
    """
    从数据库加载所有启用的定时任务并添加到 APScheduler

    只加载满足以下条件的任务：
    - is_active = True
    - cron_expression IS NOT NULL

    Args:
        db: 数据库会话
        scheduler_instance: APScheduler BackgroundScheduler 实例

    Returns:
        包含统计信息的字典
    """
    logger.info("正在从数据库加载定时任务...")

    # 移除所有现有的动态任务（保留系统任务）
    for job in scheduler_instance.get_jobs():
        if job.id.startswith('task_'):
            scheduler_instance.remove_job(job.id)

    # 查询所有启用且有 cron 表达式的任务
    tasks = db.query(CheckInTask).filter(
        CheckInTask.is_active == True,
        CheckInTask.cron_expression.isnot(None)
    ).all()

    loaded_count = 0
    skipped_count = 0
    error_count = 0

    for task in tasks:
        try:
            # 验证 cron 表达式
            cron_str = str(task.cron_expression) if task.cron_expression else None
            if not cron_str or not croniter.is_valid(cron_str):
                logger.warning(f"跳过任务 {task.id}: 无效的 cron 表达式 '{task.cron_expression}'")
                skipped_count += 1
                continue

            # 创建任务 ID
            job_id = f"task_{task.id}"

            # 检查任务是否已存在
            if scheduler_instance.get_job(job_id):
                logger.debug(f"任务 {task.id} 已存在，跳过")
                continue

            # 添加任务到调度器
            scheduler_instance.add_job(
                func=scheduled_check_in_task,
                trigger=CronTrigger.from_crontab(cron_str),
                id=job_id,
                name=f"CheckIn-Task-{task.id}",
                args=[task.id],
                replace_existing=True
            )

            logger.info(f"✅ 加载任务 {task.id}: {task.name} (Cron: {task.cron_expression})")
            loaded_count += 1

        except Exception as e:
            logger.error(f"❌ 加载任务 {task.id} 时出错: {str(e)}")
            error_count += 1

    result = {
        "loaded": loaded_count,
        "skipped": skipped_count,
        "errors": error_count,
        "total": len(tasks)
    }

    logger.info(f"任务加载完成: {result}")
    return result


def scheduled_check_in_task(task_id: int):
    """
    执行指定任务的定时打卡

    这是由 APScheduler 在 cron 触发器触发时调用的函数
    使用与批量打卡相同的逻辑
    """
    from backend.models.database import SessionLocal

    db = SessionLocal()
    try:
        task = db.query(CheckInTask).filter(CheckInTask.id == task_id).first()
        if not task:
            logger.error(f"任务 {task_id} 不存在")
            return

        if not task.is_scheduled_enabled:
            logger.info(f"任务 {task_id} 未启用定时打卡 (is_active={task.is_active}, cron={task.cron_expression})")
            return

        logger.info(f"🤖 执行定时打卡任务 {task_id}")

        # 开始异步打卡
        CheckInService.start_async_check_in(task, "scheduled", db)

    except Exception as e:
        logger.error(f"执行定时打卡任务 {task_id} 时出错: {str(e)}", exc_info=True)
    finally:
        db.close()


def cleanup_expired_pending_users():
    """定时清理过期未审批用户（24小时未审批）"""
    logger.info("Scheduler: 正在清理过期未审批用户...")

    try:
        # 创建数据库会话
        db = next(get_db())

        try:
            count = AdminService.delete_expired_pending_users(db)
            logger.info(f"Scheduler: 已删除 {count} 个过期未审批用户")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Scheduler: 清理过期用户任务发生错误: {e}", exc_info=True)


def check_token_expiration():
    """
    检查 Token 是否即将过期，并发送邮件提醒

    检查所有用户的 Token，如果在 30 分钟内过期，发送提醒邮件
    注意：现在需要检查用户的任务，因为邮箱地址在任务中
    """
    logger.info("Scheduler: 正在执行 Token 过期检查...")

    try:
        # 创建数据库会话
        db = next(get_db())

        try:
            # 获取所有用户
            users = db.query(User).all()
            current_timestamp = int(datetime.now().timestamp())

            notified_count = 0

            for user in users:
                if not user.jwt_exp or user.jwt_exp == "0":
                    continue

                try:
                    exp_timestamp = int(user.jwt_exp)

                    # 检查是否在 30 分钟内过期（0 < 剩余时间 < 1800秒）
                    time_until_expiry = exp_timestamp - current_timestamp

                    if 0 < time_until_expiry < 1800:  # 30分钟 = 1800秒
                        # 使用用户账户的邮箱发送通知
                        if user.email:
                            logger.info(f"用户 {user.alias} 的 Token 即将过期，发送邮件提醒到 {user.email}...")
                            from backend.services.email_service import EmailService
                            jwt_exp_value = user.jwt_exp
                            jwt_exp_str = str(jwt_exp_value) if jwt_exp_value is not None else "0"
                            EmailService.notify_token_expiring(user, jwt_exp_str)
                            notified_count += 1

                except ValueError:
                    logger.warning(f"用户 {user.alias} 的 jwt_exp 格式不正确: {user.jwt_exp}")
                    continue

            logger.info(f"Scheduler: Token 过期检查完成，共发送 {notified_count} 封提醒邮件")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Scheduler: Token 过期检查任务发生错误: {e}", exc_info=True)


def scheduled_check_in():
    """
    定时打卡任务：每天定时为所有启用的任务执行打卡
    """
    logger.info("Scheduler: 开始执行定时打卡任务...")

    try:
        # 创建数据库会话
        db = next(get_db())

        try:
            result = CheckInService.scheduled_check_in_all_active_tasks(db)

            logger.info(
                f"Scheduler: 定时打卡任务完成，"
                f"总计: {result['total']}, "
                f"成功: {result['success']}, "
                f"失败: {result['failure']}, "
                f"跳过: {result['skipped']}"
            )

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Scheduler: 定时打卡任务发生错误: {e}", exc_info=True)


def cleanup_old_sessions():
    """
    清理旧的会话文件

    删除超过指定时间的会话文件
    """
    logger.info("Scheduler: 开始清理旧会话文件...")

    try:
        session_dir = settings.SESSION_DIR

        if not session_dir.exists():
            logger.info("Scheduler: 会话目录不存在，跳过清理")
            return

        current_time = time.time()
        cleanup_threshold = settings.SESSION_CLEANUP_HOURS * 3600  # 转换为秒

        deleted_count = 0

        for file_path in session_dir.glob("*.json"):
            try:
                # 获取文件修改时间
                file_mtime = file_path.stat().st_mtime
                file_age = current_time - file_mtime

                # 如果文件超过阈值，删除它
                if file_age > cleanup_threshold:
                    # 同时删除对应的锁文件
                    lock_file = session_dir / f"{file_path.stem}.json.lock"

                    file_path.unlink()
                    if lock_file.exists():
                        lock_file.unlink()

                    deleted_count += 1
                    logger.debug(f"删除旧会话文件: {file_path.name}")

            except Exception as e:
                logger.error(f"删除会话文件 {file_path.name} 时出错: {e}")

        logger.info(f"Scheduler: 会话文件清理完成，共删除 {deleted_count} 个文件")

    except Exception as e:
        logger.error(f"Scheduler: 清理会话文件任务发生错误: {e}", exc_info=True)


def start_scheduler():
    """
    启动调度器

    使用文件锁确保在多进程部署时只有一个调度器运行
    """
    global scheduler, scheduler_lock

    # 创建调度器锁文件
    lock_file = settings.BASE_DIR / "scheduler.lock"
    scheduler_lock = FileLock(lock_file, timeout=1)

    try:
        # 尝试获取锁
        scheduler_lock.acquire(blocking=False)

        logger.info("成功获取调度器锁，启动调度器...")

        # 创建后台调度器
        scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

        # 添加 Token 过期检查任务（每隔指定分钟）
        scheduler.add_job(
            check_token_expiration,
            trigger="interval",
            minutes=settings.TOKEN_CHECK_INTERVAL_MINUTES,
            id="check_token_expiration",
            name="Token 过期检查任务",
            replace_existing=True
        )
        logger.info(
            f"已添加 Token 过期检查任务: 每 {settings.TOKEN_CHECK_INTERVAL_MINUTES} 分钟"
        )

        # 添加会话文件清理任务（每隔指定小时）
        scheduler.add_job(
            cleanup_old_sessions,
            trigger="interval",
            hours=settings.SESSION_CLEANUP_INTERVAL_HOURS,
            id="cleanup_old_sessions",
            name="清理旧会话文件任务",
            replace_existing=True
        )
        logger.info(
            f"已添加会话清理任务: 每 {settings.SESSION_CLEANUP_INTERVAL_HOURS} 小时"
        )

        # 添加清理过期未审批用户任务（每小时执行一次）
        scheduler.add_job(
            cleanup_expired_pending_users,
            trigger="interval",
            hours=1,
            id="cleanup_expired_pending_users",
            name="清理过期未审批用户任务",
            replace_existing=True
        )
        logger.info("已添加清理过期未审批用户任务: 每 1 小时")

        # 新增：从数据库加载动态任务
        db = next(get_db())
        try:
            load_scheduled_tasks(db, scheduler)
        finally:
            db.close()

        # 启动调度器
        scheduler.start()
        logger.info("调度器已启动")

    except Exception as e:
        logger.warning(f"无法获取调度器锁或启动失败: {e}")
        logger.info("可能其他进程已经在运行调度器，跳过启动")
        scheduler_lock = None


def stop_scheduler():
    """
    停止调度器并释放锁
    """
    global scheduler, scheduler_lock

    if scheduler:
        logger.info("正在停止调度器...")
        scheduler.shutdown()
        logger.info("调度器已停止")

    if scheduler_lock:
        try:
            scheduler_lock.release()
            logger.info("已释放调度器锁")
        except Exception as e:
            logger.warning(f"释放调度器锁时出错: {e}")
