"""
蒸馏适配器核心实现

负责确定性映射蒸馏结果到标准知识格式
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import hashlib
import json


@dataclass
class AdapterResult:
    """适配器输出结果"""
    knowledge_items: List[Dict[str, Any]]
    method_items: List[Dict[str, Any]]
    relations: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class DistillationAdapter:
    """
    蒸馏适配器

    将蒸馏系统的输出映射到FieldMind的知识存储格式
    采用确定性映射策略，保证幂等性
    """

    def __init__(self, version: str = "1.0.0"):
        """
        初始化适配器

        Args:
            version: 适配器版本
        """
        self.version = version

    def adapt_knowledge_units(
        self,
        knowledge_units: List[Any],
        generation_id: str
    ) -> List[Dict[str, Any]]:
        """
        适配知识单元到标准格式

        Args:
            knowledge_units: 原始知识单元列表
            generation_id: 生成ID

        Returns:
            标准化的知识项列表
        """
        adapted = []

        for idx, unit in enumerate(knowledge_units):
            # 生成确定性ID
            unit_id = self._generate_deterministic_id(
                generation_id, "knowledge", idx, getattr(unit, 'content', str(unit))
            )

            adapted_item = {
                "id": unit_id,
                "type": "knowledge",
                "generation_id": generation_id,
                "content": getattr(unit, 'content', str(unit)),
                "category": getattr(unit, 'category', 'general'),
                "confidence": getattr(unit, 'confidence', 1.0),
                "source_chapter": getattr(unit, 'source_chapter', None),
                "evidences": getattr(unit, 'evidences', []),
                "metadata": {
                    "adapter_version": self.version,
                    "original_index": idx
                }
            }
            adapted.append(adapted_item)

        return adapted

    def adapt_method_units(
        self,
        method_units: List[Any],
        generation_id: str
    ) -> List[Dict[str, Any]]:
        """
        适配方法单元到标准格式

        Args:
            method_units: 原始方法单元列表
            generation_id: 生成ID

        Returns:
            标准化的方法项列表
        """
        adapted = []

        for idx, unit in enumerate(method_units):
            # 生成确定性ID
            unit_id = self._generate_deterministic_id(
                generation_id, "method", idx, getattr(unit, 'name', str(unit))
            )

            adapted_item = {
                "id": unit_id,
                "type": "method",
                "generation_id": generation_id,
                "name": getattr(unit, 'name', f"Method-{idx}"),
                "description": getattr(unit, 'description', ''),
                "category": getattr(unit, 'category', 'general'),
                "steps": getattr(unit, 'steps', []),
                "prerequisites": getattr(unit, 'prerequisites', []),
                "outcomes": getattr(unit, 'outcomes', []),
                "confidence": getattr(unit, 'confidence', 1.0),
                "metadata": {
                    "adapter_version": self.version,
                    "original_index": idx
                }
            }
            adapted.append(adapted_item)

        return adapted

    def adapt_relations(
        self,
        relations: List[Any],
        generation_id: str
    ) -> List[Dict[str, Any]]:
        """
        适配关系到标准格式

        Args:
            relations: 原始关系列表
            generation_id: 生成ID

        Returns:
            标准化的关系列表
        """
        adapted = []

        for idx, rel in enumerate(relations):
            relation_id = self._generate_deterministic_id(
                generation_id, "relation", idx,
                f"{getattr(rel, 'source_id', '')}-{getattr(rel, 'target_id', '')}"
            )

            adapted_item = {
                "id": relation_id,
                "type": "relation",
                "generation_id": generation_id,
                "source_id": getattr(rel, 'source_id', None),
                "target_id": getattr(rel, 'target_id', None),
                "relation_type": getattr(rel, 'relation_type', 'related_to'),
                "confidence": getattr(rel, 'confidence', 1.0),
                "metadata": {
                    "adapter_version": self.version,
                    "original_index": idx
                }
            }
            adapted.append(adapted_item)

        return adapted

    def adapt_complete_result(
        self,
        knowledge_units: List[Any],
        method_units: List[Any],
        relations: List[Any],
        generation_id: str,
        source_metadata: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """
        适配完整蒸馏结果

        Args:
            knowledge_units: 知识单元列表
            method_units: 方法单元列表
            relations: 关系列表
            generation_id: 生成ID
            source_metadata: 源文档元信息

        Returns:
            完整适配结果
        """
        adapted_knowledge = self.adapt_knowledge_units(knowledge_units, generation_id)
        adapted_methods = self.adapt_method_units(method_units, generation_id)
        adapted_relations = self.adapt_relations(relations, generation_id)

        metadata = {
            "generation_id": generation_id,
            "adapter_version": self.version,
            "total_knowledge": len(adapted_knowledge),
            "total_methods": len(adapted_methods),
            "total_relations": len(adapted_relations),
            "source_metadata": source_metadata or {}
        }

        return AdapterResult(
            knowledge_items=adapted_knowledge,
            method_items=adapted_methods,
            relations=adapted_relations,
            metadata=metadata
        )

    def _generate_deterministic_id(
        self,
        generation_id: str,
        item_type: str,
        index: int,
        content: str
    ) -> str:
        """
        生成确定性ID

        Args:
            generation_id: 生成ID
            item_type: 项目类型
            index: 索引
            content: 内容

        Returns:
            确定性ID
        """
        # 使用generation_id + type + index + content的hash生成唯一ID
        hash_input = f"{generation_id}:{item_type}:{index}:{content}"
        hash_digest = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        return f"{item_type}-{hash_digest}"
