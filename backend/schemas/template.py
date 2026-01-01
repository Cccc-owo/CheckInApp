from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, field_validator
import json


class FieldOption(BaseModel):
    """字段选项（用于 select 类型）"""
    label: str = Field(..., description="选项显示文本")
    value: str = Field(..., description="选项值")


class FieldConfigItem(BaseModel):
    """单个字段配置项"""
    display_name: str = Field(..., description="字段显示名称")
    field_type: str = Field(..., description="字段输入类型：text, textarea, number, select")
    default_value: str = Field(default="", description="默认值")
    required: bool = Field(default=True, description="是否必填")
    hidden: bool = Field(default=False, description="是否隐藏（直接使用默认值）")
    placeholder: Optional[str] = Field(None, description="输入提示")
    value_type: str = Field(default="string", description="值类型：string, int, double")
    options: Optional[List[FieldOption]] = Field(None, description="选项列表（仅 select 类型）")

    @field_validator('field_type')
    @classmethod
    def validate_field_type(cls, v):
        allowed_types = ['text', 'textarea', 'number', 'select']
        if v not in allowed_types:
            raise ValueError(f'field_type must be one of {allowed_types}')
        return v

    @field_validator('value_type')
    @classmethod
    def validate_value_type(cls, v):
        allowed_types = ['string', 'int', 'double']
        if v not in allowed_types:
            raise ValueError(f'value_type must be one of {allowed_types}')
        return v


class FieldConfigValues(BaseModel):
    """Values 字段的嵌套配置（如 location, temperature 等）"""
    pass

    class Config:
        extra = 'allow'  # 允许任意字段


class FieldConfig(BaseModel):
    """完整的字段配置"""
    signature: Optional[FieldConfigItem] = None
    texts: Optional[FieldConfigItem] = None
    values: Optional[Dict[str, FieldConfigItem]] = Field(None, description="Values 字段的嵌套配置")


class TemplateBase(BaseModel):
    """模板基础 Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    parent_id: Optional[int] = Field(None, description="父模板 ID（用于继承）")
    field_config: Union[str, FieldConfig] = Field(..., description="字段配置（JSON 字符串或对象）")
    is_active: bool = Field(default=True, description="是否启用")

    @field_validator('field_config')
    @classmethod
    def validate_field_config(cls, v):
        """验证并转换 field_config"""
        if isinstance(v, str):
            try:
                # 尝试解析 JSON 字符串
                config_dict = json.loads(v)
                return json.dumps(config_dict)  # 返回格式化的 JSON 字符串
            except json.JSONDecodeError:
                raise ValueError('field_config must be valid JSON string')
        elif isinstance(v, dict):
            # 如果是字典，转换为 JSON 字符串
            return json.dumps(v)
        elif isinstance(v, FieldConfig):
            # 如果是 FieldConfig 对象，转换为 JSON 字符串
            return v.model_dump_json(exclude_none=True)
        else:
            raise ValueError('field_config must be JSON string, dict, or FieldConfig object')


class TemplateCreate(TemplateBase):
    """创建模板 Schema"""
    pass


class TemplateUpdate(BaseModel):
    """更新模板 Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    parent_id: Optional[int] = Field(None, description="父模板 ID（用于继承）")
    field_config: Optional[Union[str, FieldConfig]] = Field(None, description="字段配置（JSON 字符串或对象）")
    is_active: Optional[bool] = Field(None, description="是否启用")

    @field_validator('field_config')
    @classmethod
    def validate_field_config(cls, v):
        """验证并转换 field_config"""
        if v is None:
            return v

        if isinstance(v, str):
            try:
                config_dict = json.loads(v)
                return json.dumps(config_dict)
            except json.JSONDecodeError:
                raise ValueError('field_config must be valid JSON string')
        elif isinstance(v, dict):
            return json.dumps(v)
        elif isinstance(v, FieldConfig):
            return v.model_dump_json(exclude_none=True)
        else:
            raise ValueError('field_config must be JSON string, dict, or FieldConfig object')


class TemplateResponse(BaseModel):
    """模板响应 Schema"""
    id: int
    name: str
    description: Optional[str]
    parent_id: Optional[int]
    field_config: str  # JSON 字符串
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TaskFromTemplateRequest(BaseModel):
    """从模板创建任务的请求 Schema"""
    template_id: int = Field(..., description="模板 ID")
    thread_id: str = Field(..., min_length=1, description="接龙项目 ID")
    field_values: Dict[str, Any] = Field(default_factory=dict, description="用户填写的字段值")
    task_name: Optional[str] = Field(None, max_length=100, description="任务名称（可选）")


class TemplatePreviewResponse(BaseModel):
    """模板预览响应 Schema"""
    template_id: int
    template_name: str
    preview_payload: Dict[str, Any] = Field(..., description="预览生成的 payload（使用默认值）")
    field_config: Dict[str, Any] = Field(..., description="字段配置（用于前端渲染表单）")
