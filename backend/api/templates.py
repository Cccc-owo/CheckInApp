from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.models import User
from backend.dependencies import get_db, get_current_user, get_current_admin_user
from backend.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TaskFromTemplateRequest,
    TemplatePreviewResponse
)
from backend.schemas.task import TaskResponse
from backend.services.template_service import TemplateService

router = APIRouter()


@router.get("/", response_model=List[TemplateResponse], summary="获取所有模板列表")
async def get_all_templates(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=500, description="限制记录数"),
    is_active: Optional[bool] = Query(None, description="过滤启用状态"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有模板列表（普通用户可访问）

    - **skip**: 跳过记录数
    - **limit**: 限制记录数
    - **is_active**: 过滤启用状态
    """
    try:
        templates = TemplateService.get_all_templates(db, skip, limit, is_active)
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模板列表失败: {str(e)}"
        )


@router.get("/active", response_model=List[TemplateResponse], summary="获取启用的模板列表")
async def get_active_templates(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=500, description="限制记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有启用的模板（用户创建任务时使用）

    - **skip**: 跳过记录数
    - **limit**: 限制记录数
    """
    try:
        templates = TemplateService.get_all_templates(db, skip, limit, is_active=True)
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模板列表失败: {str(e)}"
        )


@router.get("/{template_id}", response_model=TemplateResponse, summary="获取单个模板详情")
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个模板的详细信息（普通用户只能访问启用的模板）

    - **template_id**: 模板 ID
    """
    template = TemplateService.get_template(template_id, db)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )

    # 普通用户只能访问启用的模板
    if not current_user.is_admin and template.is_active is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此模板"
        )

    return template


@router.get("/{template_id}/preview", response_model=TemplatePreviewResponse, summary="预览模板生成的 payload")
async def preview_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    预览模板生成的 payload（使用默认值，普通用户只能访问启用的模板）

    - **template_id**: 模板 ID
    """
    template = TemplateService.get_template(template_id, db)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )

    # 普通用户只能访问启用的模板
    if not current_user.is_admin and template.is_active is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此模板"
        )

    try:
        preview_payload = TemplateService.generate_preview_payload(template, db)
        # 使用合并后的配置
        merged_config = TemplateService.merge_parent_config(template, db)

        return {
            "template_id": template.id,
            "template_name": template.name,
            "preview_payload": preview_payload,
            "field_config": merged_config
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成预览失败: {str(e)}"
        )


@router.post("/", response_model=TemplateResponse, summary="创建新模板（管理员）")
async def create_template(
    template_data: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    创建新的打卡任务模板（仅管理员）

    - **name**: 模板名称
    - **description**: 模板描述
    - **field_config**: 字段配置（JSON）
    - **is_active**: 是否启用
    """
    return TemplateService.create_template(template_data, db)


@router.put("/{template_id}", response_model=TemplateResponse, summary="更新模板（管理员）")
async def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    更新模板信息（仅管理员）

    - **template_id**: 模板 ID
    - **name**: 模板名称
    - **description**: 模板描述
    - **field_config**: 字段配置（JSON）
    - **is_active**: 是否启用
    """
    return TemplateService.update_template(template_id, template_data, db)


@router.delete("/{template_id}", summary="删除模板（管理员）")
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    删除模板（仅管理员）

    - **template_id**: 模板 ID
    """
    TemplateService.delete_template(template_id, db)
    return {"message": "模板删除成功"}


@router.post("/create-task", response_model=TaskResponse, summary="从模板创建任务")
async def create_task_from_template(
    request: TaskFromTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    从模板创建打卡任务

    - **template_id**: 模板 ID
    - **thread_id**: 接龙项目 ID
    - **field_values**: 用户填写的字段值
    - **task_name**: 任务名称（可选）
    - **cron_expression**: Cron 表达式（可选，默认每天 20:00）
    """
    task = TemplateService.create_task_from_template(
        template_id=request.template_id,
        thread_id=request.thread_id,
        field_values=request.field_values,
        user_id=current_user.id,
        task_name=request.task_name,
        db=db,
        cron_expression=request.cron_expression
    )
    return task
