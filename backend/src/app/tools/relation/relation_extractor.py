"""
Relation Extractor Tool - 关系抽取工具
从 RelationAgent 提取的核心功能

职责：从文本中抽取实体之间的关系，构建知识图谱三元组

Author: Extracted from RelationAgent
Date: 2026-08-14
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# 关系模式库
RELATION_PATTERNS = {
    'family': ['的父亲', '的母亲', '的儿子', '的女儿', '的丈夫', '的妻子', '的兄弟', '的姐妹'],
    'organization': ['在...工作', '是...的成员', '担任...职务', '创办了', '领导'],
    'location': ['住在', '来自', '位于', '在...生活', '迁移到'],
    'time': ['于...时', '在...期间', '从...到', '...年'],
    'ownership': ['拥有', '属于', '的财产', '的土地'],
    'social': ['认识', '是...的朋友', '与...合作', '师徒关系'],
    'event': ['参与了', '经历了', '见证了', '发起了']
}


def extract_relations(
    text: str,
    entities: List[Dict[str, Any]] = None,
    max_relations: int = 100
) -> Dict[str, Any]:
    """
    从文本中抽取实体关系

    Args:
        text: 输入文本
        entities: 已识别的实体列表（可选，如果为空会自动提取）
        max_relations: 最大关系数量（默认100）

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
            'total_relations': 16,
            'entities_used': 20
        }
    """
    if not text:
        raise ValueError("text 是必需的参数")

    logger.info(f"开始关系抽取，文本长度: {len(text)}字符")

    # 如果没有提供实体，先进行实体识别
    if not entities:
        logger.info("未提供实体列表，先进行实体识别...")
        entities = _quick_entity_extraction(text)
        logger.info(f"识别到 {len(entities)} 个实体")

    # 抽取关系三元组
    triples = _extract_relation_triples(text, entities, max_relations)

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


# ==================== 私有辅助函数 ====================

def _quick_entity_extraction(text: str) -> List[Dict[str, Any]]:
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


def _extract_relation_triples(
    text: str,
    entities: List[Dict[str, Any]],
    max_relations: int
) -> List[Dict[str, Any]]:
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

    # 为每个实体对尝试查找关系
    for i, subject_entity in enumerate(entities):
        for j, object_entity in enumerate(entities):
            if i == j:
                continue

            subject = subject_entity.get('text', '')
            object_text = object_entity.get('text', '')

            # 在文本中查找主体和客体之间的内容
            relations = _find_relations_between(text, subject, object_text)

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


def _find_relations_between(
    text: str,
    subject: str,
    obj: str
) -> List[Dict[str, Any]]:
    """
    查找两个实体之间的关系

    Args:
        text: 文本
        subject: 主体
        obj: 客体

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
    for relation_type, pattern_list in RELATION_PATTERNS.items():
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
