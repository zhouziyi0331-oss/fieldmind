"""
类型强制转换

处理 LLM 输出的常见类型错误
"""
from typing import Any, get_origin, get_args
from pydantic import BaseModel
from enum import Enum
from app.core.logging import logger


def coerce_model_data(
    data: dict,
    model_class: type[BaseModel],
    lenient: bool = False
) -> dict:
    """强制转换整个模型的数据

    Args:
        data: 原始数据字典
        model_class: 目标 Pydantic 模型
        lenient: 是否宽松模式（转换失败时使用默认值）

    Returns:
        转换后的数据字典
    """
    coerced = {}

    for field_name, field_info in model_class.model_fields.items():
        if field_name not in data:
            # 字段缺失
            if lenient and field_info.default is not None:
                coerced[field_name] = field_info.default
            continue

        value = data[field_name]
        target_type = field_info.annotation

        try:
            coerced[field_name] = coerce_value(value, target_type)
        except Exception as e:
            if lenient:
                # 宽松模式：使用默认值或 None
                if field_info.default is not None and field_info.default != ...:
                    coerced[field_name] = field_info.default
                    logger.warning(f"字段 {field_name} 转换失败，使用默认值: {e}")
                else:
                    logger.warning(f"字段 {field_name} 转换失败，跳过: {e}")
            else:
                # 严格模式：传递原值，让 Pydantic 验证失败
                coerced[field_name] = value
                logger.warning(f"字段 {field_name} 转换失败，保留原值: {e}")

    return coerced


def coerce_value(value: Any, target_type: type) -> Any:
    """强制转换单个值

    Args:
        value: 原始值
        target_type: 目标类型

    Returns:
        转换后的值

    Raises:
        ValueError: 无法转换
    """
    origin = get_origin(target_type)

    # 如果已经是正确类型，直接返回（需要先检查origin避免泛型类型错误）
    if origin is None:
        try:
            if isinstance(value, target_type):
                return value
        except TypeError:
            # 某些类型不支持 isinstance 检查
            pass

    # 处理 None
    if value is None:
        return None

    # str
    if target_type is str:
        return str(value)

    # int
    elif target_type is int:
        if isinstance(value, str):
            # 移除常见格式字符
            value = value.replace(',', '').replace(' ', '').strip()
            # 处理 "123.0" -> 123
            if '.' in value:
                return int(float(value))
        return int(value)

    # float
    elif target_type is float:
        if isinstance(value, str):
            value = value.replace(',', '').replace(' ', '').strip()
        return float(value)

    # bool
    elif target_type is bool:
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'y', '是', '对')
        return bool(value)

    # List
    elif origin is list:
        if not isinstance(value, list):
            value = [value]  # 单个值包装为列表

        args = get_args(target_type)
        if args:
            item_type = args[0]
            return [coerce_value(item, item_type) for item in value]
        return list(value)

    # Dict
    elif origin is dict:
        if not isinstance(value, dict):
            raise ValueError(f"无法将 {type(value)} 转换为 dict")

        args = get_args(target_type)
        if len(args) == 2:
            key_type, value_type = args
            return {
                coerce_value(k, key_type): coerce_value(v, value_type)
                for k, v in value.items()
            }
        return dict(value)

    # Optional (Union with None)
    elif origin is type(None) or str(origin) == 'typing.Union':
        args = get_args(target_type)
        if args:
            # 过滤 NoneType
            non_none_types = [t for t in args if t is not type(None)]

            if value is None:
                return None

            if len(non_none_types) == 1:
                # Optional[T]
                return coerce_value(value, non_none_types[0])
            else:
                # Union[T1, T2, ...]
                # 尝试每种类型
                for t in non_none_types:
                    try:
                        return coerce_value(value, t)
                    except:
                        continue
                raise ValueError(f"无法将 {value} 转换为 {target_type} 的任何类型")

    # Enum
    elif isinstance(target_type, type) and issubclass(target_type, Enum):
        if isinstance(value, target_type):
            return value

        # 尝试从值创建
        try:
            return target_type(value)
        except ValueError:
            pass

        # 尝试从名称创建
        try:
            return target_type[str(value).upper()]
        except KeyError:
            pass

        # 尝试部分匹配
        value_lower = str(value).lower()
        for member in target_type:
            if member.value.lower() == value_lower or member.name.lower() == value_lower:
                return member

        raise ValueError(f"无法将 {value} 转换为 {target_type}")

    # Pydantic 模型
    elif isinstance(target_type, type) and issubclass(target_type, BaseModel):
        if isinstance(value, dict):
            return target_type(**value)
        elif isinstance(value, target_type):
            return value
        else:
            raise ValueError(f"无法将 {type(value)} 转换为 {target_type}")

    # 默认：返回原值
    else:
        return value
