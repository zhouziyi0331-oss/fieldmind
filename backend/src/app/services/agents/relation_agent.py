"""
RelationAgent - 关系抽取专员

⚠️ 已废弃：此Agent将在v2.0中移除，请使用 app.tools.relation.relation_extractor

职责：从文本中抽取实体之间的关系，构建知识图谱
"""

from typing import Dict, Any, List, Tuple
import logging

from app.services.agents.base_agent import AgentBase, AgentRole, AgentTask
from app.utils.deprecation import deprecated

logger = logging.getLogger(__name__)


@deprecated(
    reason="旧Agent架构已被6-Agent v2替代",
    replacement="app.tools.relation.relation_extractor",
    version="2.0"
)
class RelationAgent(AgentBase):
    """
    关系抽取专员Agent

    能力：
    - 实体关系抽取
    - 三元组生成（主体-关系-客体）
    - 关系类型分类
    - 知识图谱构建
    """

    @property
    def role(self) -> AgentRole:
        return AgentRole.RELATION

    @property
    def name(self) -> str:
        return "关系抽取专员"

    @property
    def description(self) -> str:
        return "负责从文本中抽取实体之间的关系，构建知识图谱三元组"

    @property
    def capabilities(self) -> List[str]:
        return [
            "实体关系抽取",
            "三元组生成",
            "关系类型分类",
            "知识图谱构建",
            "关系强度评估"
        ]

    def _initialize_tools(self):
        """初始化工具"""
        # 初始化关系模式
        self.tools = {
            'relation_patterns': self._build_relation_patterns()
        }

    def _build_relation_patterns(self) -> Dict[str, List[str]]:
        """
        构建关系模式库

        Returns:
            关系模式字典
        """
        return {
            'family': ['的父亲', '的母亲', '的儿子', '的女儿', '的丈夫', '的妻子', '的兄弟', '的姐妹'],
            'organization': ['在...工作', '是...的成员', '担任...职务', '创办了', '领导'],
            'location': ['住在', '来自', '位于', '在...生活', '迁移到'],
            'time': ['于...时', '在...期间', '从...到', '...年'],
            'ownership': ['拥有', '属于', '的财产', '的土地'],
            'social': ['认识', '是...的朋友', '与...合作', '师徒关系'],
            'event': ['参与了', '经历了', '见证了', '发起了']
        }

    def _execute_task_impl(self, task: AgentTask) -> Dict[str, Any]:
        """
        执行关系抽取任务

        Args:
            task.input_data:
                - text: 输入文本（必需）
                - entities: 已识别的实体列表（可选）
                - max_relations: 最大关系数量（可选，默认100）

        Returns:
            {
                'triples': [
                    {
                        'subject': '张三',
                        'subject_type': 'PERSON',
                        'relation': '住在',
                        'relation_type': 'location',
                        'object': '北京',
                        'object_type': 'LOCATION',
                        'confidence': 0.85,
                        'evidence': '张三住在北京朝阳区'
                    },
                    ...
                ],
                'relation_types': {
                    'family': 5,
                    'location': 8,
                    'organization': 3
                },
                'total_relations': 16
            }
        """
        text = task.input_data.get('text')
        entities = task.input_data.get('entities', [])
        max_relations = task.input_data.get('max_relations', 100)

        if not text:
            raise ValueError("text 是必需的参数")

        logger.info(f"开始关系抽取，文本长度: {len(text)}字符")

        # 如果没有提供实体，先进行实体识别
        if not entities:
            logger.info("未提供实体列表，先进行实体识别...")
            entities = self._quick_entity_extraction(text)
            logger.info(f"识别到 {len(entities)} 个实体")

        # 抽取关系三元组
        triples = self._extract_relations(text, entities, max_relations)

        # 统计关系类型
        relation_types = {}
        for triple in triples:
            rel_type = triple.get('relation_type', 'unknown')
            relation_types[rel_type] = relation_types.get(rel_type, 0) + 1

        logger.info(f"关系抽取完成: 共抽取 {len(triples)} 个关系")

        return {
            'triples': triples,
            'relation_types': relation_types,
            'total_relations': len(triples),
            'entities_used': len(entities)
        }

    def _quick_entity_extraction(self, text: str) -> List[Dict[str, Any]]:
        """
        快速实体提取（简化版）

        Args:
            text: 输入文本

        Returns:
            实体列表
        """
        import jieba.posseg as pseg

        words = pseg.cut(text)
        entities = []
        seen = set()

        for word, flag in words:
            entity_type = None
            if flag == 'nr':
                entity_type = 'PERSON'
            elif flag == 'ns':
                entity_type = 'LOCATION'
            elif flag == 'nt':
                entity_type = 'ORGANIZATION'

            if entity_type and word not in seen:
                entities.append({
                    'text': word,
                    'type': entity_type
                })
                seen.add(word)

        return entities

    def _extract_relations(self, text: str, entities: List[Dict[str, Any]], max_relations: int) -> List[Dict[str, Any]]:
        """
        抽取关系三元组

        Args:
            text: 输入文本
            entities: 实体列表
            max_relations: 最大关系数量

        Returns:
            三元组列表
        """
        triples = []
        patterns = self.tools['relation_patterns']

        # 为每个实体对尝试查找关系
        for i, subject_entity in enumerate(entities):
            for j, object_entity in enumerate(entities):
                if i == j:
                    continue

                subject = subject_entity.get('text', '')
                object_text = object_entity.get('text', '')

                # 在文本中查找主体和客体之间的内容
                relations = self._find_relations_between(text, subject, object_text, patterns)

                for relation in relations:
                    triples.append({
                        'subject': subject,
                        'subject_type': subject_entity.get('type', 'UNKNOWN'),
                        'relation': relation['relation'],
                        'relation_type': relation['relation_type'],
                        'object': object_text,
                        'object_type': object_entity.get('type', 'UNKNOWN'),
                        'confidence': relation['confidence'],
                        'evidence': relation['evidence']
                    })

                    if len(triples) >= max_relations:
                        break

            if len(triples) >= max_relations:
                break

        return triples

    def _find_relations_between(self, text: str, subject: str, obj: str, patterns: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """
        查找两个实体之间的关系

        Args:
            text: 文本
            subject: 主体
            obj: 客体
            patterns: 关系模式

        Returns:
            关系列表
        """
        relations = []

        # 查找主体在文本中的位置
        subject_pos = text.find(subject)
        if subject_pos == -1:
            return relations

        # 查找客体在主体之后的位置
        obj_pos = text.find(obj, subject_pos)
        if obj_pos == -1:
            return relations

        # 提取中间文本
        between_text = text[subject_pos:obj_pos + len(obj)]

        # 匹配关系模式
        for relation_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern in between_text:
                    relations.append({
                        'relation': pattern,
                        'relation_type': relation_type,
                        'confidence': 0.7,  # 基于模式匹配的置信度
                        'evidence': between_text[:100]  # 限制长度
                    })
                    break  # 每种类型只取第一个匹配

        return relations

    def extract_relations(self, text: str, entities: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        便捷方法：抽取关系

        Args:
            text: 输入文本
            entities: 实体列表（可选）

        Returns:
            关系抽取结果字典
        """
        import uuid

        task = AgentTask(
            task_id=f"relation_{uuid.uuid4().hex[:8]}",
            task_type="extract_relations",
            input_data={
                'text': text,
                'entities': entities or [],
                'max_relations': 100
            }
        )

        result = self.execute_task(task)

        if not result.success:
            raise Exception(f"关系抽取失败: {result.errors}")

        return result.output_data
