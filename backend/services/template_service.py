import logging
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.models import TaskTemplate, CheckInTask
from backend.schemas.template import TemplateCreate, TemplateUpdate

logger = logging.getLogger(__name__)


class TemplateService:
    """模板服务"""

    @staticmethod
    def _deep_merge(parent: Any, child: Any) -> Any:
        """
        深度合并配置，子配置会覆盖父配置

        Args:
            parent: 父配置
            child: 子配置

        Returns:
            合并后的配置
        """
        # 如果子配置不是字典或数组，直接返回子配置（覆盖）
        if not isinstance(child, (dict, list)):
            return child

        # 如果父配置不是同类型，直接返回子配置
        if type(parent) != type(child):
            return child

        # 处理字典合并
        if isinstance(child, dict):
            result = dict(parent)  # 先复制父配置
            for key, value in child.items():
                if key in parent:
                    # 递归合并
                    result[key] = TemplateService._deep_merge(parent[key], value)
                else:
                    # 新字段，直接添加
                    result[key] = value
            return result

        # 处理数组合并
        if isinstance(child, list):
            # 数组按索引位置合并
            result = []
            max_len = max(len(parent), len(child))
            for i in range(max_len):
                if i < len(child):
                    if i < len(parent):
                        # 两边都有，递归合并
                        result.append(TemplateService._deep_merge(parent[i], child[i]))
                    else:
                        # 只有子配置有，直接添加
                        result.append(child[i])
                else:
                    # 只有父配置有，保留父配置
                    result.append(parent[i])
            return result

        return child

    @staticmethod
    def merge_parent_config(template: TaskTemplate, db: Session) -> Dict[str, Any]:
        """
        合并父模板的字段配置到当前模板

        Args:
            template: 当前模板对象
            db: 数据库会话

        Returns:
            合并后的完整字段配置
        """
        # 解析当前模板配置
        current_config = json.loads(str(template.field_config))

        # 如果没有父模板，直接返回当前配置
        if template.parent_id is None:
            return current_config

        # 获取父模板
        parent = db.query(TaskTemplate).filter(TaskTemplate.id == template.parent_id).first()
        if not parent:
            logger.warning(f"模板 {template.id} 的父模板 {template.parent_id} 不存在")
            return current_config

        # 递归获取父模板的完整配置（支持多层继承）
        parent_config = TemplateService.merge_parent_config(parent, db)

        # 深度合并配置：子模板的配置会覆盖父模板的同名字段
        merged = TemplateService._deep_merge(parent_config, current_config)

        return merged

    @staticmethod
    def create_template(template_data: TemplateCreate, db: Session) -> TaskTemplate:
        """
        创建新模板

        Args:
            template_data: 模板创建数据
            db: 数据库会话

        Returns:
            创建的模板对象
        """
        try:
            # 验证 field_config 是有效的 JSON
            if isinstance(template_data.field_config, str):
                json.loads(template_data.field_config)

            template = TaskTemplate(
                name=template_data.name,
                description=template_data.description,
                field_config=template_data.field_config,
                parent_id=template_data.parent_id,
                is_active=template_data.is_active,
            )
            db.add(template)
            db.commit()
            db.refresh(template)

            logger.info(f"创建模板成功: {template.name} (ID: {template.id})")
            return template

        except json.JSONDecodeError as e:
            logger.error(f"模板字段配置 JSON 格式错误: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"字段配置 JSON 格式错误: {str(e)}"
            )
        except Exception as e:
            logger.error(f"创建模板失败: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建模板失败: {str(e)}"
            )

    @staticmethod
    def get_template(template_id: int, db: Session) -> Optional[TaskTemplate]:
        """
        获取单个模板

        Args:
            template_id: 模板 ID
            db: 数据库会话

        Returns:
            模板对象或 None
        """
        return db.query(TaskTemplate).filter(TaskTemplate.id == template_id).first()

    @staticmethod
    def get_all_templates(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[TaskTemplate]:
        """
        获取所有模板列表

        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 限制记录数
            is_active: 过滤启用状态

        Returns:
            模板列表
        """
        query = db.query(TaskTemplate)

        if is_active is not None:
            query = query.filter(TaskTemplate.is_active == is_active)

        return query.order_by(TaskTemplate.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update_template(
        template_id: int,
        template_data: TemplateUpdate,
        db: Session
    ) -> TaskTemplate:
        """
        更新模板

        Args:
            template_id: 模板 ID
            template_data: 更新数据
            db: 数据库会话

        Returns:
            更新后的模板对象
        """
        template = TemplateService.get_template(template_id, db)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模板不存在"
            )

        try:
            # 更新字段
            update_data = template_data.model_dump(exclude_unset=True)

            # 验证 field_config 如果有更新
            if 'field_config' in update_data and update_data['field_config']:
                json.loads(update_data['field_config'])

            for field, value in update_data.items():
                setattr(template, field, value)

            db.commit()
            db.refresh(template)

            logger.info(f"更新模板成功: {template.name} (ID: {template.id})")
            return template

        except json.JSONDecodeError as e:
            logger.error(f"模板字段配置 JSON 格式错误: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"字段配置 JSON 格式错误: {str(e)}"
            )
        except Exception as e:
            logger.error(f"更新模板失败: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新模板失败: {str(e)}"
            )

    @staticmethod
    def delete_template(template_id: int, db: Session) -> bool:
        """
        删除模板

        Args:
            template_id: 模板 ID
            db: 数据库会话

        Returns:
            是否删除成功
        """
        template = TemplateService.get_template(template_id, db)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模板不存在"
            )

        try:
            db.delete(template)
            db.commit()
            logger.info(f"删除模板成功: {template.name} (ID: {template_id})")
            return True
        except Exception as e:
            logger.error(f"删除模板失败: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除模板失败: {str(e)}"
            )

    @staticmethod
    def _is_field_config(obj: Any) -> bool:
        """判断是否为字段配置对象"""
        return isinstance(obj, dict) and 'display_name' in obj

    @staticmethod
    def _is_object_field(obj: Any) -> bool:
        """判断是否为对象字段（包含多个子字段配置）"""
        if not isinstance(obj, dict):
            return False
        if 'display_name' in obj:
            return False
        # 检查所有值是否都是字段配置对象
        return all(
            TemplateService._is_field_config(v)
            for v in obj.values()
            if isinstance(v, dict)
        ) and len(obj) > 0

    @staticmethod
    def _process_field_value(key: str, config: Any, field_values: Dict[str, Any]) -> Any:
        """
        递归处理字段配置，生成 payload 值

        Args:
            key: 字段名
            config: 字段配置
            field_values: 用户输入值

        Returns:
            处理后的值
        """
        # 1. 普通字段配置
        if TemplateService._is_field_config(config):
            if config.get('hidden', False):
                value = config.get('default_value', '')
            else:
                value = field_values.get(key, config.get('default_value', ''))

            value_type = config.get('value_type', 'string')
            return TemplateService._validate_and_convert_value(value, value_type, key)

        # 2. 数组字段
        if isinstance(config, list):
            result = []
            for item_config in config:
                # 检查数组元素是否是字段配置对象
                if TemplateService._is_field_config(item_config):
                    # 数组元素是字段配置对象，需要序列化为 JSON 字符串
                    value = item_config.get('default_value', '')
                    value_type = item_config.get('value_type', 'string')
                    # 将对象序列化为 JSON 字符串
                    if value_type == 'json':
                        if isinstance(value, str):
                            # 如果是字符串，验证 JSON 格式
                            try:
                                json.loads(value)
                            except json.JSONDecodeError as e:
                                # 提供更详细的错误信息
                                error_detail = f"数组元素的默认值不是有效的 JSON: {value}\n"
                                error_detail += f"JSON 解析错误: {str(e)}\n"
                                error_detail += "常见问题: 数字不能有前导零（如 00.00 应改为 0.0）"
                                raise HTTPException(
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=error_detail
                                )
                            result.append(value)
                        else:
                            # 如果是对象，序列化为 JSON 字符串
                            result.append(json.dumps(value, ensure_ascii=False))
                    else:
                        result.append(TemplateService._validate_and_convert_value(value, value_type, key))
                elif isinstance(item_config, dict):
                    # 数组元素是普通对象，递归处理
                    item = {}
                    for item_key, item_value in item_config.items():
                        # 保持键名原样
                        item[item_key] = TemplateService._process_field_value(
                            item_key, item_value, field_values
                        )
                    result.append(item)
                else:
                    result.append(item_config)
            return result

        # 3. 对象字段（包含多个子字段）
        if TemplateService._is_object_field(config):
            result = {}
            for sub_key, sub_config in config.items():
                # 保持键名原样
                result[sub_key] = TemplateService._process_field_value(
                    sub_key, sub_config, field_values
                )
            return result

        # 4. 其他情况，返回原值
        return config

    @staticmethod
    def generate_preview_payload(template: TaskTemplate, db: Session) -> Dict[str, Any]:
        """
        生成模板预览 payload（使用默认值）
        完全根据模板配置动态生成

        新架构：配置完全映射到 Payload 结构

        Args:
            template: 模板对象
            db: 数据库会话

        Returns:
            预览 payload
        """
        try:
            # 合并父模板配置
            field_config = TemplateService.merge_parent_config(template, db)

            # 初始化 payload，只包含 ThreadId（唯一必需，不在模板中配置）
            payload = {
                "ThreadId": "<接龙项目ID>"
            }

            # 递归处理所有字段，保持键名原样
            for key, config in field_config.items():
                payload[key] = TemplateService._process_field_value(key, config, {})

            return payload

        except json.JSONDecodeError as e:
            logger.error(f"解析模板配置失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"解析模板配置失败: {str(e)}"
            )

    @staticmethod
    def assemble_payload_from_template(
        template: TaskTemplate,
        thread_id: str,
        field_values: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        根据模板和用户输入组装完整的 payload
        完全根据模板配置动态生成

        新架构：配置完全映射到 Payload 结构

        Args:
            template: 模板对象
            thread_id: 接龙项目 ID
            field_values: 用户填写的字段值
            db: 数据库会话

        Returns:
            完整的 payload
        """
        try:
            # 合并父模板配置
            field_config = TemplateService.merge_parent_config(template, db)

            # 初始化 payload，只包含 ThreadId（唯一必需）
            payload = {
                "ThreadId": thread_id
            }

            # 递归处理所有字段，保持键名原样
            for key, config in field_config.items():
                payload[key] = TemplateService._process_field_value(key, config, field_values)

            return payload

        except json.JSONDecodeError as e:
            logger.error(f"解析模板配置失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"解析模板配置失败"
            )
        except Exception as e:
            logger.error(f"组装 payload 失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"组装 payload 失败: {str(e)}"
            )

    @staticmethod
    def _validate_and_convert_value(value: Any, value_type: str, field_name: str) -> Any:
        """
        验证并转换字段值类型

        Args:
            value: 字段值
            value_type: 期望的类型 (string, int, double, bool, json)
            field_name: 字段名（用于错误提示）

        Returns:
            转换后的值
        """
        try:
            if value_type == 'int':
                return int(value) if value != '' else 0
            elif value_type == 'double':
                return float(value) if value != '' else 0.0
            elif value_type == 'bool':
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes')
                return bool(value)
            elif value_type == 'json':
                # JSON 类型：如果是字符串，尝试解析后再序列化；如果是对象，直接序列化
                if isinstance(value, str):
                    # 验证是否为有效 JSON
                    json.loads(value)
                    return value
                else:
                    # 将对象序列化为 JSON 字符串
                    return json.dumps(value, ensure_ascii=False)
            else:  # string
                return str(value)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"字段 '{field_name}' 类型错误：期望 {value_type}，实际值为 '{value}'，错误: {str(e)}"
            )

    @staticmethod
    def create_task_from_template(
        template_id: int,
        thread_id: str,
        field_values: Dict[str, Any],
        user_id: int,
        task_name: Optional[str],
        db: Session,
        cron_expression: Optional[str] = "0 20 * * *"
    ) -> CheckInTask:
        """
        从模板创建打卡任务

        Args:
            template_id: 模板 ID
            thread_id: 接龙项目 ID
            field_values: 用户填写的字段值
            user_id: 用户 ID
            task_name: 任务名称（可选）
            db: 数据库会话
            cron_expression: Cron 表达式（可选，默认每天 20:00）

        Returns:
            创建的任务对象
        """
        # 获取模板
        template = TemplateService.get_template(template_id, db)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模板不存在"
            )

        # 检查模板是否启用
        if template.is_active is not True:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="该模板未启用，无法创建任务"
            )

        # 组装 payload
        payload = TemplateService.assemble_payload_from_template(
            template, thread_id, field_values, db
        )

        # 生成任务名称
        if not task_name:
            signature = payload.get('Signature', 'Unknown')
            task_name = f"{template.name} - {signature}"

        # 创建任务（包含 cron_expression）
        try:
            task = CheckInTask(
                user_id=user_id,
                payload_config=json.dumps(payload, ensure_ascii=False),
                name=task_name,
                is_active=True,
                cron_expression=cron_expression or "0 20 * * *"
            )
            db.add(task)
            db.commit()
            db.refresh(task)

            logger.info(f"从模板创建任务成功: {task.name} (ID: {task.id}, 模板: {template.name}, ThreadId: {thread_id})")

            # 如果任务启用且包含 cron_expression，立即添加到调度器
            if task.is_scheduled_enabled:
                from backend.services.task_service import TaskService
                TaskService._reload_scheduler_for_task(task, db)

            return task

        except Exception as e:
            logger.error(f"从模板创建任务失败: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建任务失败: {str(e)}"
            )
