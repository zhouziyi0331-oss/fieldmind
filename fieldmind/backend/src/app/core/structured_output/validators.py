"""
验证策略

不同的验证模式
"""
from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel


class ValidationStrategy(ABC):
    """验证策略接口"""

    @abstractmethod
    def validate(self, value: Any, field_info) -> Any:
        """验证并可能转换值"""
        pass


class StrictValidation(ValidationStrategy):
    """严格验证 - 不做任何转换"""

    def validate(self, value: Any, field_info) -> Any:
        # 不做转换，让 Pydantic 严格验证
        return value


class CoerciveValidation(ValidationStrategy):
    """强制转换验证 - 尽力转换类型"""

    def validate(self, value: Any, field_info) -> Any:
        from .type_coercion import coerce_value
        return coerce_value(value, field_info.annotation)


class LenientValidation(ValidationStrategy):
    """宽松验证 - 转换失败时使用默认值"""

    def validate(self, value: Any, field_info) -> Any:
        from .type_coercion import coerce_value
        try:
            return coerce_value(value, field_info.annotation)
        except Exception:
            # 使用默认值
            if field_info.default is not None and field_info.default != ...:
                return field_info.default
            return None
