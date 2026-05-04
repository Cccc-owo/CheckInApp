import logging
import os
import time
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


def _task_job_id(task_id: int) -> str:
    return f"task_{task_id}"


def _remove_task_job(job_id: str, scheduler_instance=None) -> bool:
    active_scheduler = scheduler_instance or scheduler
    if not active_scheduler:
        return False

    existing_job = active_scheduler.get_job(job_id)
    if not existing_job:
        return False

    active_scheduler.remove_job(job_id)
    logger.info(f"✅ 已移除调度任务: {job_id}")
    return True


def remove_scheduled_task(task_id: int, scheduler_instance=None) -> bool:
    """从调度器移除指定任务。"""
    active_scheduler = scheduler_instance or scheduler
    if not active_scheduler:
        logger.warning(f"调度器未启动，无法移除任务 {task_id}")
        return False

    return _remove_task_job(_task_job_id(task_id), active_scheduler)


def sync_scheduled_task(task: CheckInTask, scheduler_instance=None) -> bool:
    """
    根据任务当前状态同步调度器中的对应 job。

    返回 True 表示任务已成功安排到调度器，False 表示未安排或调度器不可用。
    """
    active_scheduler = scheduler_instance or scheduler
    if not active_scheduler:
        logger.warning(f"调度器未启动，无法同步任务 {task.id}")
        return False

    job_id = _task_job_id(task.id)
    _remove_task_job(job_id, active_scheduler)

    if not task.is_scheduled_enabled:
        logger.info(f"任务 {task.id} 未启用或无 cron 表达式，已从调度器移除")
        return False

    cron_str = str(task.cron_expression or "").strip()
    if not cron_str or not croniter.is_valid(cron_str):
        logger.warning(f"任务 {task.id} 的 cron 表达式无效: {cron_str}")
        return False

    active_scheduler.add_job(
        func=scheduled_check_in_task,
        trigger=CronTrigger.from_crontab(cron_str),
        id=job_id,
        name=f"CheckIn-Task-{task.id}",
        args=[task.id],
        replace_existing=True,
    )

    logger.info(f"✅ 任务 {task.id} 已同步到调度器: {cron_str}")
    return True


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
        if job.id.startswith("task_"):
            scheduler_instance.remove_job(job.id)

    # 查询所有启用且有 cron 表达式的任务
    tasks = (
        db.query(CheckInTask)
        .filter(CheckInTask.is_active == True, CheckInTask.cron_expression.isnot(None))
        .all()
    )

    loaded_count = 0
    skipped_count = 0
    error_count = 0

    for task in tasks:
        try:
            if sync_scheduled_task(task, scheduler_instance):
                loaded_count += 1
            else:
                skipped_count += 1

        except Exception as e:
            logger.error(f"❌ 加载任务 {task.id} 时出错: {str(e)}")
            error_count += 1

    result = {
        "loaded": loaded_count,
        "skipped": skipped_count,
        "errors": error_count,
        "total": len(tasks),
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
            logger.info(
                f"任务 {task_id} 未启用定时打卡 (is_active={task.is_active}, cron={task.cron_expression})"
            )
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
    检查打卡 Token 是否即将过期，并发送邮件提醒

    检查所有用户的打卡 authorization token，如果在 30 分钟内过期，发送提醒邮件
    注意：检查的是打卡业务 token，不是网站登录 JWT token
    """
    from backend.utils.time_helpers import seconds_until_expiry, parse_jwt_exp

    logger.info("Scheduler: 正在执行打卡 Token 过期检查...")

    try:
        # 创建数据库会话
        db = next(get_db())

        try:
            # 获取所有用户
            users = db.query(User).all()
            notified_count = 0

            for user in users:
                # 跳过没有邮箱的用户
                user_email = user.email
                if not user_email:
                    logger.debug(f"用户 {user.alias} 未设置邮箱，跳过检查")
                    continue

                # 解析 jwt_exp
                jwt_exp_value = user.jwt_exp
                jwt_exp_str = str(jwt_exp_value) if jwt_exp_value is not None else "0"
                exp_timestamp = parse_jwt_exp(jwt_exp_str)
                if not exp_timestamp:
                    logger.debug(f"用户 {user.alias} 的 jwt_exp 无效，跳过检查")
                    continue

                # 计算剩余时间
                time_until_expiry = seconds_until_expiry(exp_timestamp)

                logger.debug(
                    f"用户 {user.alias}: 剩余 {time_until_expiry} 秒 (即将过期标志={user.token_expiring_notified}, 已过期标志={user.token_expired_notified})"
                )

                # 情况1：Token 即将过期（过期前 30 分钟内，且还未过期）
                if 0 < time_until_expiry < 1800:  # 30分钟 = 1800秒
                    # 检查是否已发送过提醒
                    expiring_notified = bool(user.token_expiring_notified)
                    if not expiring_notified:
                        logger.info(
                            f"用户 {user.alias} 的打卡 Token 即将过期，发送邮件提醒到 {user_email}..."
                        )
                        from backend.services.email_service import EmailService

                        # 发送"即将过期"邮件
                        success = EmailService.notify_token_expiring(user, jwt_exp_str)

                        if success:
                            user.token_expiring_notified = True
                            db.commit()
                            notified_count += 1
                            logger.info(f"用户 {user.alias} 的打卡 Token 即将过期邮件已发送并标记")
                        else:
                            logger.warning(f"用户 {user.alias} 的打卡 Token 即将过期邮件发送失败")

                # 情况2：Token 已过期
                # 修改逻辑：只要过期就发送提醒（不限制在30分钟内）
                # 但为了避免频繁发送，使用 token_expired_notified 标志
                elif time_until_expiry <= 0:  # Token 已过期
                    # 检查是否已发送过提醒
                    expired_notified = bool(user.token_expired_notified)
                    if not expired_notified:
                        logger.info(
                            f"用户 {user.alias} 的打卡 Token 已过期，发送邮件提醒到 {user_email}..."
                        )
                        from backend.services.email_service import EmailService

                        # 发送"已过期"邮件
                        success = EmailService.notify_token_expired(user)

                        if success:
                            user.token_expired_notified = True
                            db.commit()
                            notified_count += 1
                            logger.info(f"用户 {user.alias} 的打卡 Token 已过期邮件已发送并标记")
                        else:
                            logger.warning(f"用户 {user.alias} 的打卡 Token 已过期邮件发送失败")

                # 情况3：Token 正常（剩余时间 > 30 分钟），重置提醒标志
                elif time_until_expiry >= 1800:
                    expiring_notified = bool(user.token_expiring_notified)
                    expired_notified = bool(user.token_expired_notified)
                    if expiring_notified or expired_notified:
                        user.token_expiring_notified = False
                        user.token_expired_notified = False
                        db.commit()
                        logger.info(f"用户 {user.alias} 的打卡 Token 已刷新，重置所有提醒标志")

            logger.info(f"Scheduler: 打卡 Token 过期检查完成，共发送 {notified_count} 封提醒邮件")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Scheduler: Token 过期检查任务发生错误: {e}", exc_info=True)


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
            replace_existing=True,
        )
        logger.info(f"已添加 Token 过期检查任务: 每 {settings.TOKEN_CHECK_INTERVAL_MINUTES} 分钟")

        # 添加会话文件清理任务（每隔指定小时）
        scheduler.add_job(
            cleanup_old_sessions,
            trigger="interval",
            hours=settings.SESSION_CLEANUP_INTERVAL_HOURS,
            id="cleanup_old_sessions",
            name="清理旧会话文件任务",
            replace_existing=True,
        )
        logger.info(f"已添加会话清理任务: 每 {settings.SESSION_CLEANUP_INTERVAL_HOURS} 小时")

        # 添加清理过期未审批用户任务（每小时执行一次）
        scheduler.add_job(
            cleanup_expired_pending_users,
            trigger="interval",
            hours=1,
            id="cleanup_expired_pending_users",
            name="清理过期未审批用户任务",
            replace_existing=True,
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
