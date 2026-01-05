from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from backend.models import get_db, User
from backend.schemas.task import TaskUpdate, TaskResponse
from backend.services.task_service import TaskService
from backend.dependencies import get_current_user

router = APIRouter()


class CronValidateRequest(BaseModel):
    """Cron 表达式验证请求"""
    cron_expression: str = Field(..., min_length=9, description="Crontab 表达式")

# create_task_from_template: 已在 templates.py 中定义

@router.get("/", response_model=List[TaskResponse], summary="获取当前用户的任务列表")
async def get_tasks(
    include_inactive: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的所有打卡任务

    - **include_inactive**: 是否包含未启用的任务（默认 true）
    """
    try:
        tasks = TaskService.get_user_tasks(current_user.id, db, include_inactive)
        # 为每个任务添加额外信息
        enriched_tasks = [TaskService.enrich_task_with_check_in_info(task, db) for task in tasks]
        return enriched_tasks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {str(e)}"
        )


@router.get("/{task_id}", response_model=TaskResponse, summary="获取任务详情")
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定任务的详情

    需要验证任务属于当前用户
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

    return task


@router.put("/{task_id}", response_model=TaskResponse, summary="更新任务")
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新指定任务的信息

    需要验证任务属于当前用户
    """
    # 验证任务归属
    if not TaskService.verify_task_ownership(task_id, current_user.id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此任务"
        )

    task = TaskService.update_task(task_id, task_data, db)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除任务")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除指定任务

    需要验证任务属于当前用户，删除后会同时删除所有关联的打卡记录
    """
    # 验证任务归属
    if not TaskService.verify_task_ownership(task_id, current_user.id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此任务"
        )

    success = TaskService.delete_task(task_id, db)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )


@router.post("/{task_id}/toggle", response_model=TaskResponse, summary="切换任务启用状态")
async def toggle_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    切换任务的启用/禁用状态

    需要验证任务属于当前用户
    """
    # 验证任务归属
    if not TaskService.verify_task_ownership(task_id, current_user.id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此任务"
        )

    task = TaskService.toggle_task(task_id, db)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    return task


@router.post("/validate-cron", summary="验证 Crontab 表达式")
async def validate_cron_expression(request: CronValidateRequest):
    """
    验证 Crontab 表达式并预览下一个执行时间

    请求体: {"cron_expression": "0 20 * * *"}

    返回:
    {
        "valid": true,
        "message": "有效的 Crontab 表达式",
        "next_times": [
            "2024-01-02 20:00:00",
            "2024-01-03 20:00:00",
            ...
        ],
        "description": "每天 20:00"
    }
    """
    cron_expr = request.cron_expression.strip()

    if not cron_expr:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cron_expression 是必需的"
        )

    try:
        from croniter import croniter

        if not croniter.is_valid(cron_expr):
            raise ValueError("无效的格式")

        # 生成接下来的 5 个执行时间
        cron = croniter(cron_expr, datetime.now())
        next_times = [cron.get_next(datetime).strftime('%Y-%m-%d %H:%M:%S') for _ in range(5)]

        return {
            "valid": True,
            "message": "有效的 Crontab 表达式",
            "next_times": next_times,
            "description": generate_cron_description(cron_expr)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的 Crontab 表达式: {str(e)}"
        )


def generate_cron_description(cron_expr: str) -> str:
    """生成 Crontab 表达式的人类可读描述"""
    parts = cron_expr.split()
    if len(parts) != 5:
        return cron_expr

    minute, hour, day, month, dow = parts

    descriptions = []
    if hour == '*' and minute == '*':
        descriptions.append("每分钟")
    elif hour == '*':
        descriptions.append(f"每小时的第 {minute} 分钟")
    elif day == '*' and month == '*' and dow == '*':
        descriptions.append(f"每天 {hour}:{minute:0>2}")
    else:
        descriptions.append(f"复杂的时间表: {cron_expr}")

    return ", ".join(descriptions)
