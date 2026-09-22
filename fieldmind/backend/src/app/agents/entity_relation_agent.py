"""
实体关系 Agent
负责从文本中提取实体之间的关系
"""
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from .base_agent import BaseAgent
from .agent_registry import register_agent

logger = logging.getLogger(__name__)


@register_agent(
    name="entity_relation_agent",
    description="从文本中提取实体之间的关系",
    version="1.0.0",
    capabilities=["entity_extraction", "relation_extraction", "nlp"],
    dependencies=["entity_agent"]
)
class EntityRelationAgent(BaseAgent):
    """
    实体关系提取 Agent

    功能：
    - 识别文本中的实体
    - 提取实体之间的关系
    - 关系类型分类
    - 置信度评估
    """

    # 预定义的关系类型
    RELATION_TYPES = {
        "位于": ["在", "位于", "坐落于", "地处"],
        "属于": ["属于", "隶属", "归属"],
        "相关": ["相关", "关联", "联系"],
        "包含": ["包含", "包括", "含有"],
        "继承": ["继承", "传承", "延续"],
        "影响": ["影响", "作用", "促进", "推动"],
        "时间": ["在...时", "于", "当时"],
        "因果": ["因为", "由于", "导致", "造成"],
        "对比": ["相比", "对比", "不同于"],
        "协作": ["合作", "协作", "配合"],
    }

    def __init__(self):
        super().__init__()
        self.name = "EntityRelationAgent"
        logger.info("实体关系 Agent 已初始化")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行实体关系提取

        Args:
            input_data: {
                "text": str,  # 文本内容
                "entities": List[Dict],  # 已提取的实体列表（可选）
                "extract_entities": bool  # 是否先提取实体（默认True）
            }

        Returns:
            {
                "relations": List[Dict],  # 关系列表
                "entities": List[Dict],  # 实体列表
                "relation_count": int,  # 关系数量
                "confidence": float  # 整体置信度
            }
        """
        text = input_data.get("text", "")
        entities = input_data.get("entities", [])
        extract_entities = input_data.get("extract_entities", True)

        if not text:
            return {"relations": [], "entities": [], "relation_count": 0, "confidence": 0.0}

        # 如果没有提供实体，先提取实体
        if extract_entities and not entities:
            entities = self._extract_entities(text)

        # 提取关系
        relations = self._extract_relations(text, entities)

        # 计算整体置信度
        avg_confidence = sum(r["confidence"] for r in relations) / len(relations) if relations else 0.0

        return {
            "relations": relations,
            "entities": entities,
            "relation_count": len(relations),
            "confidence": avg_confidence,
            "extracted_at": datetime.now().isoformat()
        }

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        提取实体（简化版）

        Args:
            text: 文本内容

        Returns:
            实体列表
        """
        # 这里简化处理，实际应该调用 NER 模型
        # 临时使用简单的规则匹配
        entities = []

        # 提取人名（示例）
        import re
        person_pattern = r'[一-龥]{2,4}(?:老师|先生|女士|同志|师傅)'
        persons = re.findall(person_pattern, text)

        for idx, person in enumerate(set(persons)):
            entities.append({
                "id": f"person_{idx}",
                "text": person,
                "type": "PERSON",
                "position": text.find(person)
            })

        # 提取地名（示例）
        location_pattern = r'[一-龥]+(?:村|镇|县|市|省|区|乡|街道)'
        locations = re.findall(location_pattern, text)

        for idx, loc in enumerate(set(locations)):
            entities.append({
                "id": f"location_{idx}",
                "text": loc,
                "type": "LOCATION",
                "position": text.find(loc)
            })

        return entities

    def _extract_relations(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        提取实体之间的关系

        Args:
            text: 文本内容
            entities: 实体列表

        Returns:
            关系列表
        """
        relations = []

        # 对于每对实体，检测它们之间的关系
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                relation = self._detect_relation(text, entity1, entity2)
                if relation:
                    relations.append(relation)

        return relations

    def _detect_relation(
        self,
        text: str,
        entity1: Dict[str, Any],
        entity2: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        检测两个实体之间的关系

        Args:
            text: 文本内容
            entity1: 实体1
            entity2: 实体2

        Returns:
            关系字典，如果没有关系返回 None
        """
        e1_text = entity1["text"]
        e2_text = entity2["text"]

        # 获取两个实体之间的文本
        pos1 = entity1["position"]
        pos2 = entity2["position"]

        if pos1 < pos2:
            between_text = text[pos1 + len(e1_text):pos2]
            source = entity1
            target = entity2
        else:
            between_text = text[pos2 + len(e2_text):pos1]
            source = entity2
            target = entity1

        # 检测关系类型
        for relation_type, keywords in self.RELATION_TYPES.items():
            for keyword in keywords:
                if keyword in between_text:
                    # 计算置信度（基于距离和关键词匹配）
                    distance = abs(pos1 - pos2)
                    confidence = max(0.5, 1.0 - (distance / 1000))

                    return {
                        "source": source["id"],
                        "source_text": source["text"],
                        "target": target["id"],
                        "target_text": target["text"],
                        "relation_type": relation_type,
                        "relation_keyword": keyword,
                        "confidence": confidence,
                        "context": between_text.strip()[:50]  # 上下文片段
                    }

        return None

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        return "text" in input_data and input_data["text"]

    def get_capabilities(self) -> List[str]:
        """返回 Agent 能力"""
        return ["entity_extraction", "relation_extraction", "nlp"]
