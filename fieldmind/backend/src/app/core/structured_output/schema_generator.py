"""
JSON Schema 生成器

从 Pydantic 模型生成 JSON Schema
"""
from typing import Any, Dict, get_origin, get_args
from pydantic import BaseModel
from enum import Enum


def generate_json_schema(
    model_class: type[BaseModel],
    include_descriptions: bool = True
) -> Dict[str, Any]:
    """从 Pydantic 模型生成 JSON Schema

    Args:
        model_class: Pydantic 模型类
        include_descriptions: 是否包含字段描述

    Returns:
        JSON Schema 字典
    """
    schema = {
        "type": "object",
        "properties": {},
        "required": []
    }

    # 添加模型描述
    if model_class.__doc__ and include_descriptions:
        schema["description"] = model_class.__doc__.strip()

    # 遍历字段
    for field_name, field_info in model_class.model_fields.items():
        # 生成字段 Schema
        property_schema = _convert_field_to_schema(field_info, include_descriptions)

        schema["properties"][field_name] = property_schema

        # 检查是否必需
        if field_info.is_required():
            schema["required"].append(field_name)

    return schema


def _convert_field_to_schema(field_info, include_descriptions: bool) -> Dict[str, Any]:
    """转换单个字段为 JSON Schema"""
    field_type = field_info.annotation
    schema = _convert_type_to_schema(field_type)

    # 添加描述
    if include_descriptions and field_info.description:
        schema["description"] = field_info.description

    # 添加约束
    if hasattr(field_info, 'ge') and field_info.ge is not None:
        schema["minimum"] = field_info.ge

    if hasattr(field_info, 'le') and field_info.le is not None:
        schema["maximum"] = field_info.le

    if hasattr(field_info, 'gt') and field_info.gt is not None:
        schema["exclusiveMinimum"] = field_info.gt

    if hasattr(field_info, 'lt') and field_info.lt is not None:
        schema["exclusiveMaximum"] = field_info.lt

    if hasattr(field_info, 'min_length') and field_info.min_length is not None:
        schema["minLength"] = field_info.min_length

    if hasattr(field_info, 'max_length') and field_info.max_length is not None:
        schema["maxLength"] = field_info.max_length

    if hasattr(field_info, 'pattern') and field_info.pattern is not None:
        schema["pattern"] = field_info.pattern

    # 默认值（需要处理 Pydantic 的特殊类型）
    if hasattr(field_info, 'default') and field_info.default is not None:
        # 检查是否是 Pydantic 的特殊未定义类型
        default_value = field_info.default
        if not isinstance(default_value, type) and str(type(default_value)) != "<class 'pydantic_core._pydantic_core.PydanticUndefinedType'>":
            try:
                # 尝试序列化以确保可以 JSON 化
                import json
                json.dumps(default_value)
                schema["default"] = default_value
            except (TypeError, ValueError):
                # 无法序列化，跳过
                pass

    return schema


def _convert_type_to_schema(python_type) -> Dict[str, Any]:
    """转换 Python 类型到 JSON Schema 类型"""
    # 处理 Optional (Union with None)
    origin = get_origin(python_type)

    # 基础类型
    if python_type is str:
        return {"type": "string"}

    elif python_type is int:
        return {"type": "integer"}

    elif python_type is float:
        return {"type": "number"}

    elif python_type is bool:
        return {"type": "boolean"}

    # List
    elif origin is list:
        args = get_args(python_type)
        if args:
            item_type = args[0]
            return {
                "type": "array",
                "items": _convert_type_to_schema(item_type)
            }
        return {"type": "array"}

    # Dict
    elif origin is dict:
        args = get_args(python_type)
        if len(args) == 2:
            # Dict[str, ValueType]
            value_type = args[1]
            return {
                "type": "object",
                "additionalProperties": _convert_type_to_schema(value_type)
            }
        return {"type": "object"}

    # Union (包括 Optional)
    elif origin is type(None) or str(origin) == 'typing.Union':
        args = get_args(python_type)
        if args:
            # 过滤掉 NoneType
            non_none_types = [t for t in args if t is not type(None)]

            if len(non_none_types) == 1:
                # Optional[T] 情况
                return _convert_type_to_schema(non_none_types[0])
            else:
                # Union[T1, T2, ...] - 使用 anyOf
                return {
                    "anyOf": [_convert_type_to_schema(t) for t in non_none_types]
                }

    # Enum
    elif isinstance(python_type, type) and issubclass(python_type, Enum):
        return {
            "type": "string",
            "enum": [e.value for e in python_type]
        }

    # 嵌套 Pydantic 模型
    elif isinstance(python_type, type) and issubclass(python_type, BaseModel):
        return generate_json_schema(python_type)

    # 默认
    else:
        return {"type": "string"}


def schema_to_prompt(schema: Dict[str, Any], indent: int = 0) -> str:
    """将 JSON Schema 转换为人类可读的 Prompt

    用于在没有原生 JSON Schema 支持时的备选方案
    """
    lines = []
    prefix = "  " * indent

    if schema.get("description"):
        lines.append(f"{prefix}# {schema['description']}")

    if schema.get("type") == "object":
        lines.append(f"{prefix}{{")

        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for prop_name, prop_schema in properties.items():
            is_required = prop_name in required
            req_marker = "*" if is_required else ""

            prop_type = prop_schema.get("type", "any")
            prop_desc = prop_schema.get("description", "")

            desc_text = f" // {prop_desc}" if prop_desc else ""

            if prop_type == "object":
                lines.append(f'{prefix}  "{prop_name}"{req_marker}: {schema_to_prompt(prop_schema, indent+1)}{desc_text}')
            elif prop_type == "array":
                item_schema = prop_schema.get("items", {})
                item_type = item_schema.get("type", "any")
                lines.append(f'{prefix}  "{prop_name}"{req_marker}: [{item_type}]{desc_text}')
            else:
                lines.append(f'{prefix}  "{prop_name}"{req_marker}: {prop_type}{desc_text}')

        lines.append(f"{prefix}}}")

    return "\n".join(lines)
