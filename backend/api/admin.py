from typing import List
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.models import get_db, User, CheckInTask
from backend.schemas.check_in import BatchCheckInRequest
from backend.schemas.user import UserResponse
from backend.services.check_in_service import CheckInService
from backend.services.admin_service import AdminService
from backend.dependencies import get_current_admin_user
from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class BatchToggleTasksRequest(BaseModel):
    """批量启用/禁用任务请求"""
    task_ids: List[int]
    is_active: bool


@router.post("/batch_toggle_tasks", summary="批量启用/禁用任务")
async def batch_toggle_tasks(
    request: BatchToggleTasksRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    批量启用或禁用任务的自动打卡功能（需要管理员权限）

    - **task_ids**: 任务 ID 列表
    - **is_active**: true 为启用，false 为禁用
    """
    try:
        count = 0
        for task_id in request.task_ids:
            task = db.query(CheckInTask).filter(CheckInTask.id == task_id).first()
            if task:
                task.is_active = request.is_active
                count += 1

        db.commit()

        return {
            "success": True,
            "message": f"已{'启用' if request.is_active else '禁用'} {count} 个任务",
            "count": count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量操作失败: {str(e)}"
        )


@router.post("/batch_check_in", summary="批量触发打卡")
async def batch_check_in(
    request: BatchCheckInRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    批量触发任务打卡（需要管理员权限）

    - **task_ids**: 任务 ID 列表

    返回每个任务的打卡结果
    """
    try:
        result = CheckInService.batch_check_in_tasks(request.task_ids, db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量打卡失败: {str(e)}"
        )


@router.get("/logs", summary="获取系统日志")
async def get_system_logs(
    lines: int = Query(200, ge=1, le=2000, description="读取的日志行数"),
    current_user: User = Depends(get_current_admin_user)
):
    """
    获取系统日志（需要管理员权限）

    - **lines**: 读取最后 N 行日志

    返回日志内容（字符串格式）
    """
    try:
        log_file = settings.LOG_FILE

        if not log_file.exists():
            return {
                "success": True,
                "message": "日志文件不存在",
                "logs": "日志文件不存在"
            }

        # 使用 deque 高效读取最后 N 行，避免将整个文件加载到内存
        from collections import deque

        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            # 使用 deque 保持最后 N 行，内存占用固定
            last_lines = deque(f, maxlen=lines)

        # 返回字符串格式（不是数组）
        log_content = ''.join(last_lines)

        return {
            "success": True,
            "message": f"读取了最后 {len(last_lines)} 行日志",
            "logs": log_content
        }

    except Exception as e:
        logger.error(f"读取日志失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"读取日志失败: {str(e)}"
        )


@router.get("/stats", summary="获取系统统计")
async def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    获取系统统计信息（需要管理员权限）

    返回用户数、任务数、打卡记录数等统计信息
    """
    try:
        from backend.models import CheckInRecord
        from datetime import datetime, timedelta

        # 总用户数
        total_users = db.query(User).count()

        # 管理员用户数
        admin_users = db.query(User).filter(User.role == "admin").count()

        # 已审批的用户数（is_approved=True的用户）
        approved_users = db.query(User).filter(User.is_approved == True).count()

        # 总任务数
        total_tasks = db.query(CheckInTask).count()

        # 启用的任务数
        active_tasks = db.query(CheckInTask).filter(CheckInTask.is_active == True).count()

        # 总打卡记录数
        total_records = db.query(CheckInRecord).count()

        # 今日打卡记录数
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_records = db.query(CheckInRecord).filter(
            CheckInRecord.check_in_time >= today_start
        ).count()

        # 今日成功打卡数
        today_success = db.query(CheckInRecord).filter(
            CheckInRecord.check_in_time >= today_start,
            CheckInRecord.status == "success"
        ).count()

        # 今日失败打卡数
        today_failure = db.query(CheckInRecord).filter(
            CheckInRecord.check_in_time >= today_start,
            CheckInRecord.status == "failure"
        ).count()

        # 今日时间范围外打卡数
        today_out_of_time = db.query(CheckInRecord).filter(
            CheckInRecord.check_in_time >= today_start,
            CheckInRecord.status == "out_of_time"
        ).count()

        # 今日异常打卡数
        today_unknown = db.query(CheckInRecord).filter(
            CheckInRecord.check_in_time >= today_start,
            CheckInRecord.status == "unknown"
        ).count()

        # Token 即将过期的用户数（7天内）
        from backend.services.auth_service import AuthService

        current_timestamp = int(datetime.now().timestamp())
        expiring_soon_timestamp = current_timestamp + (7 * 24 * 60 * 60)  # 7天后

        expiring_users = 0
        for user in db.query(User).all():
            # 使用统一的验证方法
            result = AuthService.verify_checkin_authorization(user)

            if result["is_valid"]:
                exp_timestamp = result.get("expires_at")
                if exp_timestamp and current_timestamp < exp_timestamp < expiring_soon_timestamp:
                    expiring_users += 1

        return {
            "users": {
                "total": total_users,
                "admin": admin_users,
                "regular": total_users - admin_users,
                "active": approved_users  # 使用已审批用户数
            },
            "tasks": {
                "total": total_tasks,
                "active": active_tasks,
                "inactive": total_tasks - active_tasks
            },
            "check_in_records": {
                "total": total_records,
                "today": today_records,
                "today_success": today_success,
                "today_failure": today_failure,
                "today_out_of_time": today_out_of_time,
                "today_unknown": today_unknown
            },
            "tokens": {
                "expiring_soon": expiring_users
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计失败: {str(e)}"
        )


@router.get("/users/pending", response_model=List[UserResponse], summary="获取待审批用户")
async def get_pending_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    获取所有待审批的用户（需要管理员权限）
    """
    try:
        users = AdminService.get_pending_users(db)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取待审批用户失败: {str(e)}"
        )


@router.post("/users/{user_id}/approve", response_model=dict, summary="审批通过用户")
async def approve_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    审批通过指定用户（需要管理员权限）
    """
    try:
        result = AdminService.approve_user(user_id, db)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"审批用户失败: {str(e)}"
        )


@router.delete("/users/{user_id}/reject", response_model=dict, summary="拒绝用户")
async def reject_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    拒绝并删除指定用户（需要管理员权限）
    """
    try:
        result = AdminService.reject_user(user_id, db)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"拒绝用户失败: {str(e)}"
        )
