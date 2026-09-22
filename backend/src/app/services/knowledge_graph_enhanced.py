"""
知识图谱增强服务
集成外部算法，提升实体识别和关系抽取能力
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import jieba
import jieba.analyse
import re

logger = logging.getLogger(__name__)


class EntityExtractor:
    """实体提取器 - 增强版"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.entity_types = {
            "PERSON": ["人物", "受访者", "村民", "居民", "工匠", "师傅"],
            "LOCATION": ["地点", "村", "镇", "县", "市", "省", "街道", "路"],
            "ORGANIZATION": ["组织", "协会", "合作社", "公司", "委员会"],
            "EVENT": ["事件", "活动", "节日", "仪式", "庆典"],
            "ARTIFACT": ["物品", "工具", "器具", "产品", "作品"],
            "CONCEPT": ["概念", "理念", "传统", "习俗", "技艺"],
        }

        # 加载自定义词典（田野调查领域）
        self._load_field_dictionary()

    def _load_field_dictionary(self):
        """加载田野调查领域词典"""
        field_words = [
            # 人物相关
            "村民",
            "居民",
            "工匠",
            "传承人",
            "手艺人",
            "老艺人",
            # 地点相关
            "古村",
            "老街",
            "祠堂",
            "庙宇",
            "作坊",
            "工坊",
            # 文化相关
            "非遗",
            "传统工艺",
            "民俗",
            "习俗",
            "仪式",
            "节庆",
            # 经济相关
            "合作社",
            "产业",
            "业态",
            "市场",
            "销售",
        ]

        for word in field_words:
            jieba.add_word(word)

    def extract_entities(
        self, text: str, min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        提取实体

        Args:
            text: 文本内容
            min_confidence: 最小置信度

        Returns:
            [
                {
                    "text": "实体文本",
                    "type": "PERSON/LOCATION/...",
                    "confidence": 0.8,
                    "position": (start, end)
                }
            ]
        """
        entities = []

        # 方法1: 基于关键词提取
        keywords_entities = self._extract_by_keywords(text)
        entities.extend(keywords_entities)

        # 方法2: 基于规则提取
        rule_entities = self._extract_by_rules(text)
        entities.extend(rule_entities)

        # 方法3: 基于上下文提取
        context_entities = self._extract_by_context(text)
        entities.extend(context_entities)

        # 去重和过滤
        entities = self._deduplicate(entities)
        entities = [e for e in entities if e["confidence"] >= min_confidence]

        return entities

    def _extract_by_keywords(self, text: str) -> List[Dict]:
        """基于关键词提取"""
        entities = []

        # 使用 jieba 的 TF-IDF 提取关键词
        keywords = jieba.analyse.extract_tags(text, topK=50, withWeight=True)

        for word, weight in keywords:
            # 判断实体类型
            entity_type = self._classify_entity_type(word, text)

            if entity_type:
                entities.append(
                    {
                        "text": word,
                        "type": entity_type,
                        "confidence": weight,
                        "method": "keywords",
                    }
                )

        return entities

    def _extract_by_rules(self, text: str) -> List[Dict]:
        """基于规则提取"""
        entities = []

        # 规则1: 人名模式（X师傅、X老师、X村民）
        person_patterns = [
            r"([^\s，。]{2,4})(师傅|老师|村民|居民|工匠|传承人)",
            r"(老)?([^\s，。]{1,3})(说|表示|认为|指出)",
        ]

        for pattern in person_patterns:
            for match in re.finditer(pattern, text):
                name = match.group(1) if len(match.groups()) == 2 else match.group(2)
                entities.append(
                    {
                        "text": name,
                        "type": "PERSON",
                        "confidence": 0.7,
                        "method": "rules",
                        "position": match.span(),
                    }
                )

        # 规则2: 地点模式（XX村、XX镇）
        location_patterns = [
            r"([^\s，。]{2,6})(村|镇|县|市|街|路|巷)",
        ]

        for pattern in location_patterns:
            for match in re.finditer(pattern, text):
                location = match.group(0)
                entities.append(
                    {
                        "text": location,
                        "type": "LOCATION",
                        "confidence": 0.8,
                        "method": "rules",
                        "position": match.span(),
                    }
                )

        # 规则3: 组织模式（XX合作社、XX协会）
        org_patterns = [
            r"([^\s，。]{2,10})(合作社|协会|委员会|公司)",
        ]

        for pattern in org_patterns:
            for match in re.finditer(pattern, text):
                org = match.group(0)
                entities.append(
                    {
                        "text": org,
                        "type": "ORGANIZATION",
                        "confidence": 0.75,
                        "method": "rules",
                        "position": match.span(),
                    }
                )

        return entities

    def _extract_by_context(self, text: str) -> List[Dict]:
        """基于上下文提取"""
        entities = []

        # 分句
        sentences = re.split(r"[。！？\n]", text)

        for sentence in sentences:
            if not sentence.strip():
                continue

            # 查找共现关系
            words = jieba.lcut(sentence)

            # 人物 + 动作 模式
            for i, word in enumerate(words):
                if word in ["说", "认为", "表示", "指出", "提到"]:
                    if i > 0:
                        person = words[i - 1]
                        if len(person) >= 2:
                            entities.append(
                                {
                                    "text": person,
                                    "type": "PERSON",
                                    "confidence": 0.6,
                                    "method": "context",
                                }
                            )

        return entities

    def _classify_entity_type(self, word: str, context: str) -> Optional[str]:
        """分类实体类型"""
        # 基于后缀判断
        if word.endswith(("村", "镇", "县", "市", "街", "路")):
            return "LOCATION"

        if word.endswith(("师傅", "老师", "工匠", "传承人")):
            return "PERSON"

        if word.endswith(("合作社", "协会", "公司", "委员会")):
            return "ORGANIZATION"

        if word in ["非遗", "传统工艺", "民俗", "习俗"]:
            return "CONCEPT"

        # 基于上下文判断
        for entity_type, keywords in self.entity_types.items():
            if any(kw in context for kw in keywords):
                if word in context:
                    return entity_type

        return None

    def _deduplicate(self, entities: List[Dict]) -> List[Dict]:
        """去重"""
        seen = {}

        for entity in entities:
            text = entity["text"]

            if text not in seen:
                seen[text] = entity
            else:
                # 保留置信度更高的
                if entity["confidence"] > seen[text]["confidence"]:
                    seen[text] = entity

        return list(seen.values())


class RelationExtractor:
    """关系提取器"""

    def __init__(self):
        self.relation_patterns = {
            "位于": [
                r"(.+?)(位于|坐落于|在)(.+?)[。，]",
                r"(.+?)(的)(.+?)(在|位于)(.+?)[。，]",
            ],
            "属于": [r"(.+?)(属于|是)(.+?)[。，]"],
            "从事": [r"(.+?)(从事|制作|生产)(.+?)[。，]"],
            "拥有": [r"(.+?)(拥有|具有|有)(.+?)[。，]"],
            "参与": [r"(.+?)(参与|参加|加入)(.+?)[。，]"],
        }

    def extract_relations(
        self, text: str, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        提取关系

        Args:
            text: 文本内容
            entities: 已提取的实体

        Returns:
            [
                {
                    "subject": "实体1",
                    "relation": "关系类型",
                    "object": "实体2",
                    "confidence": 0.8
                }
            ]
        """
        relations = []

        # 方法1: 基于模式匹配
        pattern_relations = self._extract_by_patterns(text)
        relations.extend(pattern_relations)

        # 方法2: 基于实体共现
        cooccurrence_relations = self._extract_by_cooccurrence(text, entities)
        relations.extend(cooccurrence_relations)

        # 去重
        relations = self._deduplicate_relations(relations)

        return relations

    def _extract_by_patterns(self, text: str) -> List[Dict]:
        """基于模式提取关系"""
        relations = []

        for relation_type, patterns in self.relation_patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text):
                    groups = match.groups()

                    if len(groups) >= 3:
                        subject = groups[0].strip()
                        obj = groups[-1].strip()

                        if subject and obj and subject != obj:
                            relations.append(
                                {
                                    "subject": subject,
                                    "relation": relation_type,
                                    "object": obj,
                                    "confidence": 0.7,
                                    "method": "pattern",
                                }
                            )

        return relations

    def _extract_by_cooccurrence(self, text: str, entities: List[Dict]) -> List[Dict]:
        """基于实体共现提取关系"""
        relations = []

        # 分句
        sentences = re.split(r"[。！？\n]", text)

        for sentence in sentences:
            # 找到句子中的实体
            sentence_entities = [e for e in entities if e["text"] in sentence]

            # 实体对关系推断
            for i, entity1 in enumerate(sentence_entities):
                for entity2 in sentence_entities[i + 1 :]:
                    relation = self._infer_relation(entity1, entity2, sentence)

                    if relation:
                        relations.append(
                            {
                                "subject": entity1["text"],
                                "relation": relation,
                                "object": entity2["text"],
                                "confidence": 0.5,
                                "method": "cooccurrence",
                            }
                        )

        return relations

    def _infer_relation(
        self, entity1: Dict, entity2: Dict, context: str
    ) -> Optional[str]:
        """推断关系类型"""
        type1 = entity1["type"]
        type2 = entity2["type"]

        # 人物 - 地点
        if type1 == "PERSON" and type2 == "LOCATION":
            if any(kw in context for kw in ["住在", "来自", "居住"]):
                return "居住于"
            if any(kw in context for kw in ["工作", "从事"]):
                return "工作于"

        # 人物 - 组织
        if type1 == "PERSON" and type2 == "ORGANIZATION":
            if any(kw in context for kw in ["加入", "参与", "成员"]):
                return "属于"

        # 地点 - 地点
        if type1 == "LOCATION" and type2 == "LOCATION":
            if any(kw in context for kw in ["位于", "在", "属于"]):
                return "位于"

        # 默认关系
        return "相关"

    def _deduplicate_relations(self, relations: List[Dict]) -> List[Dict]:
        """去重关系"""
        seen = set()
        unique_relations = []

        for relation in relations:
            key = (relation["subject"], relation["relation"], relation["object"])

            if key not in seen:
                seen.add(key)
                unique_relations.append(relation)

        return unique_relations


class KnowledgeGraphEnhancer:
    """知识图谱增强服务"""

    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.relation_extractor = RelationExtractor()

    def enhance_document(
        self, text: str, existing_entities: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        增强文档知识提取

        Args:
            text: 文档文本
            existing_entities: 已有实体（可选）

        Returns:
            {
                "entities": [...],
                "relations": [...],
                "statistics": {...}
            }
        """
        logger.info("开始知识图谱增强处理")

        # 1. 提取实体
        entities = self.entity_extractor.extract_entities(text)

        # 2. 合并已有实体
        if existing_entities:
            entities = self._merge_entities(entities, existing_entities)

        # 3. 提取关系
        relations = self.relation_extractor.extract_relations(text, entities)

        # 4. 统计信息
        statistics = self._calculate_statistics(entities, relations)

        logger.info(
            f"知识图谱增强完成: " f"实体={len(entities)}, 关系={len(relations)}"
        )

        return {
            "entities": entities,
            "relations": relations,
            "statistics": statistics,
            "timestamp": datetime.now().isoformat(),
        }

    def _merge_entities(
        self, new_entities: List[Dict], existing_entities: List[Dict]
    ) -> List[Dict]:
        """合并新旧实体"""
        entity_map = {e["text"]: e for e in existing_entities}

        for entity in new_entities:
            text = entity["text"]
            if text in entity_map:
                # 更新置信度（取最大值）
                entity_map[text]["confidence"] = max(
                    entity_map[text]["confidence"], entity["confidence"]
                )
            else:
                entity_map[text] = entity

        return list(entity_map.values())

    def _calculate_statistics(
        self, entities: List[Dict], relations: List[Dict]
    ) -> Dict[str, Any]:
        """计算统计信息"""
        from collections import Counter

        entity_type_counts = Counter(e["type"] for e in entities)
        relation_type_counts = Counter(r["relation"] for r in relations)

        return {
            "total_entities": len(entities),
            "total_relations": len(relations),
            "entities_by_type": dict(entity_type_counts),
            "relations_by_type": dict(relation_type_counts),
            "avg_confidence": (
                sum(e["confidence"] for e in entities) / len(entities)
                if entities
                else 0
            ),
        }


# 全局实例
knowledge_graph_enhancer = KnowledgeGraphEnhancer()
