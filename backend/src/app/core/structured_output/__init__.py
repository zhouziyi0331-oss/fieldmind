"""
结构化输出系统

基于 Instructor 的设计，为 FieldMind 提供类型安全的 LLM 输出
"""

from .client import StructuredOutputClient
from .validators import ValidationStrategy, StrictValidation, CoerciveValidation
from .streaming import PartialModel, stream_partial
from .schema_generator import generate_json_schema

__all__ = [
    "StructuredOutputClient",
    "ValidationStrategy",
    "StrictValidation",
    "CoerciveValidation",
    "PartialModel",
    "stream_partial",
    "generate_json_schema",
]
