"""
EntityAgent - 实体识别专员

⚠️ 已废弃：此Agent将在v2.0中移除，请使用 app.tools.entity.ner_extractor

职责：从文本中识别命名实体（人名、地名、机构名、时间等）
"""

from typing import Dict, Any, List
import logging

from app.services.agents.base_agent import AgentBase, AgentRole, AgentTask
from app.utils.deprecation import deprecated

logger = logging.getLogger(__name__)


@deprecated(
    reason="旧Agent架构已被6-Agent v2替代",
    replacement="app.tools.entity.ner_extractor",
    version="2.0"
)
class EntityAgent(AgentBase):
    """
    实体识别专员Agent

    能力：
    - 命名实体识别（NER）
    - 实体消歧与合并
    - 实体类型分类
    - 实体关键信息提取
    """

    @property
    def role(self) -> AgentRole:
        return AgentRole.ENTITY

    @property
    def name(self) -> str:
        return "实体识别专员"

    @property
    def description(self) -> str:
        return "负责从文本中识别和提取命名实体，包括人名、地名、机构名、时间等"

    @property
    def capabilities(self) -> List[str]:
        return [
            "命名实体识别（NER）",
            "实体类型分类",
            "实体消歧与合并",
            "实体频率统计",
            "上下文提取"
        ]

    def _initialize_tools(self):
        """初始化工具"""
        # 延迟导入避免循环依赖
        try:
            from app.services.dynamic_discovery import DynamicDiscoveryEngine
            self.tools = {
                'discovery_engine': DynamicDiscoveryEngine(enable_ner=False)
            }
        except ImportError as e:
            logger.warning(f"DynamicDiscoveryEngine导入失败: {e}")
            self.tools = {}

    def _execute_task_impl(self, task: AgentTask) -> Dict[str, Any]:
        """
        执行实体识别任务

        Args:
            task.input_data:
                - text: 输入文本（必需）
                - merge_threshold: 实体合并阈值（可选，默认0.85）
                - extract_context: 是否提取上下文（可选，默认True）

        Returns:
            {
                'entities': [
                    {
                        'text': '张三',
                        'type': 'PERSON',
                        'count': 5,
                        'positions': [12, 45, 78, ...],
                        'contexts': ['...张三说...', '...'],
                        'aliases': ['老张', '张先生']
                    },
                    ...
                ],
                'entity_types': {
                    'PERSON': 10,
                    'LOCATION': 8,
                    'ORGANIZATION': 5,
                    'TIME': 3
                },
                'total_entities': 26
            }
        """
        text = task.input_data.get('text')
        merge_threshold = task.input_data.get('merge_threshold', 0.85)
        extract_context = task.input_data.get('extract_context', True)

        if not text:
            raise ValueError("text 是必需的参数")

        logger.info(f"开始实体识别，文本长度: {len(text)}字符")

        # 切分为段落
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 20]
        if not paragraphs:
            paragraphs = [text]

        logger.info(f"切分为 {len(paragraphs)} 个段落")

        # 使用动态发现引擎提取实体
        if 'discovery_engine' in self.tools:
            merged_entities = self.tools['discovery_engine'].extract_and_merge_entities(
                paragraphs,
                merge_threshold=merge_threshold
            )
        else:
            # Fallback: 使用简单的jieba分词
            merged_entities = self._extract_entities_fallback(text)

        # 统计实体类型
        entity_types = {}
        for entity in merged_entities:
            entity_type = entity.get('type', 'UNKNOWN')
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

        # 如果需要，提取上下文
        if extract_context:
            merged_entities = self._enrich_with_context(merged_entities, text)

        logger.info(f"实体识别完成: 共识别 {len(merged_entities)} 个实体")

        return {
            'entities': merged_entities,
            'entity_types': entity_types,
            'total_entities': len(merged_entities)
        }

    def _extract_entities_fallback(self, text: str) -> List[Dict[str, Any]]:
        """
        备用实体提取方法（使用jieba + 简单规则）

        Args:
            text: 输入文本

        Returns:
            实体列表
        """
        import jieba
        import jieba.posseg as pseg

        logger.info("使用jieba词性标注进行实体识别")

        words = pseg.cut(text)

        entities = []
        entity_dict = {}

        for word, flag in words:
            # 根据词性标注判断实体类型
            entity_type = None
            if flag == 'nr':  # 人名
                entity_type = 'PERSON'
            elif flag == 'ns':  # 地名
                entity_type = 'LOCATION'
            elif flag == 'nt':  # 机构名
                entity_type = 'ORGANIZATION'
            elif flag == 't':  # 时间
                entity_type = 'TIME'

            if entity_type:
                if word not in entity_dict:
                    entity_dict[word] = {
                        'text': word,
                        'type': entity_type,
                        'count': 0,
                        'positions': []
                    }
                entity_dict[word]['count'] += 1

        # 转换为列表
        entities = list(entity_dict.values())

        # 按频率排序
        entities.sort(key=lambda x: x['count'], reverse=True)

        return entities[:50]  # 返回前50个

    def _enrich_with_context(self, entities: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """
        为实体添加上下文信息

        Args:
            entities: 实体列表
            text: 原始文本

        Returns:
            enriched实体列表
        """
        for entity in entities:
            entity_text = entity.get('text', '')
            if not entity_text:
                continue

            # 查找所有出现位置
            contexts = []
            pos = 0
            while True:
                pos = text.find(entity_text, pos)
                if pos == -1:
                    break

                # 提取上下文（前后各30个字符）
                start = max(0, pos - 30)
                end = min(len(text), pos + len(entity_text) + 30)
                context = text[start:end]

                contexts.append({
                    'text': context,
                    'position': pos
                })

                pos += len(entity_text)

            entity['contexts'] = contexts[:5]  # 只保留前5个
            entity['positions'] = [c['position'] for c in contexts]

        return entities

    def extract_entities(self, text: str, merge_threshold: float = 0.85) -> Dict[str, Any]:
        """
        便捷方法：提取实体

        Args:
            text: 输入文本
            merge_threshold: 合并阈值

        Returns:
            实体识别结果字典
        """
        import uuid

        task = AgentTask(
            task_id=f"entity_{uuid.uuid4().hex[:8]}",
            task_type="extract_entities",
            input_data={
                'text': text,
                'merge_threshold': merge_threshold,
                'extract_context': True
            }
        )

        result = self.execute_task(task)

        if not result.success:
            raise Exception(f"实体识别失败: {result.errors}")

        return result.output_data
