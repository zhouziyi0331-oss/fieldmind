"""
FieldMind 知识蒸馏系统

基于 WorkBuddy 第二大脑 v1.4.4 完整实现
"""

from app.distillation.normalizer import SourceNormalizer, NormalizedSource, SourceMetadata
from app.distillation.knowledge import KnowledgeDistiller, KnowledgeUnit
from app.distillation.method import MethodDistiller, MethodUnit
from app.distillation.adapter import DistillationAdapter
from app.distillation.packager import DistillationPackager
from app.distillation.validator import SBPACKValidator
from app.distillation.pipeline import DistillationPipeline

__all__ = [
    "SourceNormalizer",
    "NormalizedSource",
    "SourceMetadata",
    "KnowledgeDistiller",
    "KnowledgeUnit",
    "MethodDistiller",
    "MethodUnit",
    "DistillationAdapter",
    "DistillationPackager",
    "SBPACKValidator",
    "DistillationPipeline",
]

__version__ = "1.0.0"
