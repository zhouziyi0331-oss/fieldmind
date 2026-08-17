"""
EntityRelationAgent - 实体关系分析专员

职责：
1. 从文本中识别人物、地点、组织、事件
2. 分析实体之间的关系（亲属、权力、经济、地理等）
3. 构建初步的关系网络

输入：
- text_content: 文档文本
- entities: 动态发现引擎提取的实体（可选，用于增强）

输出：
- entities: 结构化的实体列表
- relations: 实体关系三元组
- entity_types: 实体类型统计
"""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict

from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class EntityRelationAgent(BaseAgent):
    """实体关系分析专员"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # 社会学田野调查常见的关系类型
        self.relation_patterns = {
            # 权力关系
            'power': [
                (r'(\w+)是(\w+)的?(书记|村长|主任|干部|领导)', 'manages'),
                (r'(\w+)管理(\w+)', 'manages'),
                (r'(\w+)领导(\w+)', 'leads'),
            ],
            # 亲属关系
            'kinship': [
                (r'(\w+)是(\w+)的?(父亲|母亲|儿子|女儿|兄弟|姐妹|丈夫|妻子)', 'family'),
                (r'(\w+)和(\w+)是(夫妻|兄弟|姐妹)', 'family'),
            ],
            # 地理关系
            'geographic': [
                (r'(\w+)位于(\w+)', 'located_in'),
                (r'(\w+)在(\w+)(村|镇|县|市)', 'located_in'),
                (r'(\w+)属于(\w+)', 'belongs_to'),
            ],
            # 经济关系
            'economic': [
                (r'(\w+)在(\w+)(工作|打工|务工|经营)', 'works_at'),
                (r'(\w+)从事(\w+)', 'engages_in'),
                (r'(\w+)种植(\w+)', 'cultivates'),
                (r'(\w+)养殖(\w+)', 'raises'),
            ],
            # 社会关系
            'social': [
                (r'(\w+)认识(\w+)', 'knows'),
                (r'(\w+)帮助(\w+)', 'helps'),
                (r'(\w+)支持(\w+)', 'supports'),
            ]
        }

        # 实体类型识别规则
        self.entity_type_rules = {
            'person': [r'\w+(书记|村长|主任|大爷|大妈|师傅)', r'[张李王刘陈杨赵黄周吴]\w{0,2}'],
            'location': [r'\w+(村|镇|县|市|乡|街道|社区)', r'\w+(山|河|湖|路|街)'],
            'organization': [r'\w+(委员会|合作社|公司|企业|政府|部门)'],
            'event': [r'\w+(会议|活动|节日|仪式|典礼)'],
        }

    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行实体关系分析

        Args:
            input_data: 包含 text_content 和可选的 entities

        Returns:
            实体和关系分析结果
        """
        text_content = input_data.get('text_content', '')
        pre_entities = input_data.get('entities', [])

        if not text_content:
            return {
                'entities': [],
                'relations': [],
                'entity_types': {},
                'confidence': 0.0
            }

        # 第一步：识别实体
        entities = self._extract_entities(text_content, pre_entities)

        # 第二步：识别关系
        relations = self._extract_relations(text_content, entities)

        # 第三步：统计实体类型
        entity_types = self._count_entity_types(entities)

        # 计算置信度
        confidence = self._calculate_confidence(entities, relations)

        return {
            'entities': entities,
            'relations': relations,
            'entity_types': entity_types,
            'confidence': confidence,
            'warnings': self._generate_warnings(entities, relations)
        }

    def _extract_entities(
        self,
        text: str,
        pre_entities: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        提取实体

        Args:
            text: 文本内容
            pre_entities: 动态发现引擎提取的实体

        Returns:
            实体列表，格式：[{'name': '张书记', 'type': 'person', 'mentions': 5}]
        """
        entity_dict = defaultdict(lambda: {'mentions': 0, 'type': 'unknown', 'contexts': []})

        # 整合预提取的实体
        for entity in pre_entities:
            name = entity.get('entity', entity.get('name', ''))
            if name:
                entity_dict[name]['mentions'] += entity.get('count', 1)
                entity_dict[name]['type'] = self._infer_entity_type(name)

        # 基于规则提取更多实体
        for entity_type, patterns in self.entity_type_rules.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    name = match if isinstance(match, str) else match[0]
                    if len(name) >= 2:  # 过滤太短的匹配
                        entity_dict[name]['mentions'] += 1
                        if entity_dict[name]['type'] == 'unknown':
                            entity_dict[name]['type'] = entity_type

        # 提取上下文（每个实体最多3个上下文片段）
        for name in entity_dict.keys():
            contexts = self._extract_contexts(text, name, max_contexts=3)
            entity_dict[name]['contexts'] = contexts

        # 转换为列表格式
        entities = [
            {
                'name': name,
                'type': info['type'],
                'mentions': info['mentions'],
                'contexts': info['contexts']
            }
            for name, info in entity_dict.items()
        ]

        # 按提及次数排序
        entities.sort(key=lambda x: x['mentions'], reverse=True)

        logger.info(f"提取了 {len(entities)} 个实体")
        return entities

    def _infer_entity_type(self, name: str) -> str:
        """
        推断实体类型

        Args:
            name: 实体名称

        Returns:
            实体类型：person/location/organization/event/unknown
        """
        for entity_type, patterns in self.entity_type_rules.items():
            for pattern in patterns:
                if re.search(pattern, name):
                    return entity_type
        return 'unknown'

    def _extract_contexts(self, text: str, entity: str, max_contexts: int = 3) -> List[str]:
        """
        提取实体的上下文片段

        Args:
            text: 完整文本
            entity: 实体名称
            max_contexts: 最多返回多少个上下文

        Returns:
            上下文片段列表
        """
        contexts = []
        sentences = re.split(r'[。！？]', text)

        for sentence in sentences:
            if entity in sentence and len(sentence) > 10:
                contexts.append(sentence.strip() + '。')
                if len(contexts) >= max_contexts:
                    break

        return contexts

    def _extract_relations(
        self,
        text: str,
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        提取实体之间的关系

        Args:
            text: 文本内容
            entities: 已识别的实体列表

        Returns:
            关系列表，格式：[{'source': '张书记', 'target': '李家村', 'relation': 'manages'}]
        """
        relations = []
        entity_names = {e['name'] for e in entities}

        # 使用模式匹配提取关系
        for relation_type, patterns in self.relation_patterns.items():
            for pattern, relation_label in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    groups = match.groups()
                    if len(groups) >= 2:
                        source = groups[0]
                        target = groups[1]

                        # 验证source和target是否在实体列表中
                        if source in entity_names and target in entity_names:
                            relations.append({
                                'source': source,
                                'target': target,
                                'relation': relation_label,
                                'relation_type': relation_type,
                                'context': match.group(0)
                            })

        # 去重（同样的source-target-relation只保留一个）
        unique_relations = []
        seen = set()
        for rel in relations:
            key = (rel['source'], rel['target'], rel['relation'])
            if key not in seen:
                seen.add(key)
                unique_relations.append(rel)

        logger.info(f"提取了 {len(unique_relations)} 个关系")
        return unique_relations

    def _count_entity_types(self, entities: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        统计各类型实体的数量

        Args:
            entities: 实体列表

        Returns:
            类型统计，如 {'person': 5, 'location': 3}
        """
        type_counts = defaultdict(int)
        for entity in entities:
            type_counts[entity['type']] += 1
        return dict(type_counts)

    def _calculate_confidence(
        self,
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]]
    ) -> float:
        """
        计算分析置信度

        Args:
            entities: 实体列表
            relations: 关系列表

        Returns:
            置信度 0-1
        """
        # 简单的启发式规则
        if not entities:
            return 0.0

        # 因素1：实体数量（适中为佳）
        entity_score = min(len(entities) / 20.0, 1.0)

        # 因素2：关系密度
        if len(entities) > 1:
            max_possible_relations = len(entities) * (len(entities) - 1)
            relation_density = len(relations) / max_possible_relations
            relation_score = min(relation_density * 10, 1.0)
        else:
            relation_score = 0.0

        # 因素3：类型多样性
        type_diversity = len(self._count_entity_types(entities)) / 5.0
        type_score = min(type_diversity, 1.0)

        # 加权平均
        confidence = 0.4 * entity_score + 0.4 * relation_score + 0.2 * type_score

        return round(confidence, 2)

    def _generate_warnings(
        self,
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]]
    ) -> List[str]:
        """
        生成警告信息

        Args:
            entities: 实体列表
            relations: 关系列表

        Returns:
            警告信息列表
        """
        warnings = []

        if len(entities) == 0:
            warnings.append("未提取到任何实体，文本可能不包含结构化信息")
        elif len(entities) < 5:
            warnings.append("提取的实体数量较少，可能影响分析深度")

        if len(relations) == 0:
            warnings.append("未识别到实体关系，无法构建关系网络")

        unknown_count = sum(1 for e in entities if e['type'] == 'unknown')
        if unknown_count > len(entities) * 0.5:
            warnings.append(f"有 {unknown_count} 个实体类型未知，建议扩展实体识别规则")

        return warnings

    def get_required_inputs(self) -> List[str]:
        """必需的输入字段"""
        return ['text_content']

    def get_output_schema(self) -> Dict[str, str]:
        """输出schema"""
        return {
            'entities': 'List[Dict] - 实体列表',
            'relations': 'List[Dict] - 关系列表',
            'entity_types': 'Dict[str, int] - 实体类型统计',
            'confidence': 'float - 分析置信度'
        }
