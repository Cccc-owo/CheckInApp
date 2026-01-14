from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.models import get_db, User, CheckInTask, CheckInRecord
from backend.schemas.check_in import (
    ManualCheckInRequest,
    CheckInRecordResponse,
    CheckInResultResponse,
    PaginatedResponse,
)
from backend.services.check_in_service import CheckInService
from backend.services.task_service import TaskService
from backend.dependencies import get_current_user, get_current_admin_user

router = APIRouter()


@router.post("/manual/{task_id}", summary="手动触发打卡（异步）")
async def manual_check_in(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    手动触发指定任务的打卡（异步方式，立即返回）

    - **task_id**: 任务 ID

    返回打卡记录 ID，可以通过 /record/{record_id}/status 查询打卡状态
    """
    # 验证任务归属
    if not TaskService.verify_task_ownership(task_id, current_user.id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此任务"
        )

    task = TaskService.get_task(task_id, db)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    try:
        result = CheckInService.start_async_check_in(task, "manual", db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动打卡任务失败: {str(e)}"
        )


@router.get("/record/{record_id}/status", summary="查询打卡记录状态")
async def get_check_in_record_status(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询指定打卡记录的状态

    - **record_id**: 打卡记录 ID

    返回状态：pending（进行中）、success（成功）、failure（失败）
    """
    from backend.utils.db_helpers import get_or_404

    # 获取打卡记录
    record = get_or_404(CheckInRecord, record_id, db, "打卡记录不存在")

    # 验证记录归属（通过任务归属）
    if not TaskService.verify_task_ownership(record.task_id, current_user.id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此记录"
        )

    return {
        "record_id": record.id,
        "task_id": record.task_id,
        "status": record.status,
        "response_text": record.response_text,
        "error_message": record.error_message,
        "trigger_type": record.trigger_type,
        "check_in_time": record.check_in_time
    }


@router.get("/task/{task_id}/records", response_model=PaginatedResponse[CheckInRecordResponse], summary="查看任务的打卡记录")
async def get_task_check_in_records(
    task_id: int,
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=500, description="限制记录数"),
    status_filter: Optional[str] = Query(None, alias="status", description="过滤状态 (success/failure)"),
    trigger_type: Optional[str] = Query(None, description="过滤触发类型 (scheduler/manual)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查看指定任务的打卡记录

    - **task_id**: 任务 ID
    - **skip**: 跳过记录数
    - **limit**: 限制记录数
    - **status**: 过滤状态 (success/failure)
    - **trigger_type**: 过滤触发类型 (scheduler/manual)

    用户只能查看自己的任务记录
    """
    # 验证任务归属
    if not TaskService.verify_task_ownership(task_id, current_user.id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此任务"
        )

    try:
        records, total = CheckInService.get_task_records(
            task_id, db, skip, limit, status_filter, trigger_type
        )
        return PaginatedResponse(
            records=records,
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取打卡记录失败: {str(e)}"
        )


@router.get("/my-records", response_model=PaginatedResponse[CheckInRecordResponse], summary="查看当前用户的所有打卡记录")
async def get_my_check_in_records(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=500, description="限制记录数"),
    status_filter: Optional[str] = Query(None, alias="status", description="过滤状态 (success/failure)"),
    trigger_type: Optional[str] = Query(None, description="过滤触发类型 (scheduler/manual)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查看当前用户所有任务的打卡记录

    - **skip**: 跳过记录数
    - **limit**: 限制记录数
    - **status**: 过滤状态 (success/failure)
    - **trigger_type**: 过滤触发类型 (scheduler/manual)
    """
    try:
        records, total = CheckInService.get_user_records(
            current_user.id, db, skip, limit, status_filter, trigger_type
        )
        return PaginatedResponse(
            records=records,
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取打卡记录失败: {str(e)}"
        )



@router.get("/records", response_model=PaginatedResponse[CheckInRecordResponse], summary="查看所有打卡记录（管理员）")
async def get_all_check_in_records(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=500, description="限制记录数"),
    task_id: Optional[int] = Query(None, description="过滤任务 ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="过滤状态 (success/failure)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    查看所有打卡记录（需要管理员权限）

    - **skip**: 跳过记录数
    - **limit**: 限制记录数
    - **task_id**: 过滤指定任务的记录
    - **status**: 过滤指定状态的记录
    """
    try:
        records, total = CheckInService.get_all_records(db, skip, limit, task_id, status_filter)
        # 为每条记录添加用户和任务信息
        enriched_records = [CheckInService.enrich_record_with_user_task_info(record, db) for record in records]
        return PaginatedResponse(
            records=enriched_records,
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取打卡记录失败: {str(e)}"
        )


@router.get("/records/count", summary="获取打卡记录统计（管理员）")
async def get_check_in_records_count(
    task_id: Optional[int] = Query(None, description="过滤任务 ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="过滤状态 (success/failure)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    获取打卡记录统计（需要管理员权限）

    返回符合条件的记录总数
    """
    try:
        query = db.query(CheckInRecord)

        if task_id:
            query = query.filter(CheckInRecord.task_id == task_id)

        if status_filter:
            query = query.filter(CheckInRecord.status == status_filter)

        total = query.count()

        return {"total": total}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计失败: {str(e)}"
        )
