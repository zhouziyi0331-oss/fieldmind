"""
NER Extractor Tool - 命名实体识别工具
从 EntityAgent 提取的核心功能

职责：从文本中识别命名实体（人名、地名、机构名、时间等）

Author: Extracted from EntityAgent
Date: 2026-08-14
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def extract_entities(
    text: str,
    merge_threshold: float = 0.85,
    extract_context: bool = True
) -> Dict[str, Any]:
    """
    从文本中提取命名实体

    Args:
        text: 输入文本
        merge_threshold: 实体合并阈值（默认0.85）
        extract_context: 是否提取上下文（默认True）

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
    if not text:
        raise ValueError("text 是必需的参数")

    logger.info(f"开始实体识别，文本长度: {len(text)}字符")

    # 切分为段落
    paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 20]
    if not paragraphs:
        paragraphs = [text]

    logger.info(f"切分为 {len(paragraphs)} 个段落")

    # 使用动态发现引擎提取实体
    try:
        from app.services.dynamic_discovery import DynamicDiscoveryEngine
        discovery_engine = DynamicDiscoveryEngine(enable_ner=False)
        merged_entities = discovery_engine.extract_and_merge_entities(
            paragraphs,
            merge_threshold=merge_threshold
        )
    except (ImportError, Exception) as e:
        logger.warning(f"DynamicDiscoveryEngine不可用，使用备用方法: {e}")
        merged_entities = _extract_entities_fallback(text)

    # 统计实体类型
    entity_types = {}
    for entity in merged_entities:
        entity_type = entity.get('type', 'UNKNOWN')
        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

    # 如果需要，提取上下文
    if extract_context:
        merged_entities = _enrich_with_context(merged_entities, text)

    logger.info(f"实体识别完成: 共识别 {len(merged_entities)} 个实体")

    return {
        'entities': merged_entities,
        'entity_types': entity_types,
        'total_entities': len(merged_entities)
    }


# ==================== 私有辅助函数 ====================

def _extract_entities_fallback(text: str) -> List[Dict[str, Any]]:
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


def _enrich_with_context(entities: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
    """
    为实体添加上下文信息

    Args:
        entities: 实体列表
        text: 原始文本

    Returns:
        enriched实体列表
    """
    for entity in entities:
        entity_text = entity['text']
        contexts = []

        # 查找实体在文本中的所有位置
        start = 0
        positions = []
        while True:
            pos = text.find(entity_text, start)
            if pos == -1:
                break
            positions.append(pos)

            # 提取上下文（前后各30个字符）
            context_start = max(0, pos - 30)
            context_end = min(len(text), pos + len(entity_text) + 30)
            context = text[context_start:context_end]

            # 清理上下文
            context = context.replace('\n', ' ').strip()
            if context and context not in contexts:
                contexts.append(context)

            start = pos + 1

        entity['positions'] = positions
        entity['contexts'] = contexts[:5]  # 最多保留5个上下文

    return entities
