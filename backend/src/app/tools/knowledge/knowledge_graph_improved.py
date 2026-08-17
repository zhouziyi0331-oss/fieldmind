"""
改进的知识图谱服务 - 使用 jieba 进行更准确的实体识别
"""
import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

# 尝试导入 jieba，如果不存在则回退到正则
try:
    import jieba
    import jieba.posseg as pseg
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    logger.warning("jieba not installed, falling back to regex-based extraction")


class ImprovedKnowledgeGraphService:
    """改进的知识图谱服务 - 使用 NLP 进行实体提取"""

    def __init__(self):
        self.use_jieba = JIEBA_AVAILABLE

        # jieba 词性标注映射
        self.pos_to_entity_type = {
            'nr': 'person',      # 人名
            'ns': 'location',    # 地名
            'nt': 'organization', # 机构名
            't': 'date',         # 时间词
            'nz': 'concept',     # 其他专有名词
        }

        # 正则表达式（备用方案）
        self.entity_patterns = {
            'location': r'[一-龥]{2,6}(?:省|市|县|区|村|镇|街道|乡)',
            'organization': r'[一-龥]{2,10}(?:大学|公司|研究所|学院|部门|组织|协会|委员会)',
            'date': r'\d{4}年(?:\d{1,2}月)?(?:\d{1,2}日)?|\d{4}-\d{2}-\d{2}',
            'concept': r'[一-龥]{2,6}(?:理论|方法|模式|体系|框架|机制|制度|政策)',
        }

        # 停用词列表（过滤无意义的实体）
        self.stopwords = {
            '这个', '那个', '一个', '什么', '如何', '为什么', '怎么', '哪里',
            '这里', '那里', '现在', '当时', '以前', '之后', '接着', '然后',
            '因此', '所以', '但是', '如果', '虽然', '虽', '但', '和', '与',
            '的', '了', '在', '是', '有', '我', '你', '他', '她', '它',
            '我们', '你们', '他们', '她们', '它们', '自己', '大家', '别人',
            '田野调查', '笔记', '调查地点', '主要发现', '调查时间', '访谈',
            '观察', '记录', '资料', '数据', '信息', '内容', '情况', '问题',
        }

    def extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """从文本中提取实体"""
        if self.use_jieba:
            return self._extract_entities_jieba(text)
        else:
            return self._extract_entities_regex(text)

    def _extract_entities_jieba(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """使用 jieba 进行实体提取"""
        entities = defaultdict(list)
        seen = defaultdict(set)

        # 词性标注
        words = pseg.cut(text)
        position = 0

        for word, flag in words:
            # 跳过停用词
            if word in self.stopwords or len(word) < 2:
                position += len(word)
                continue

            # 根据词性判断实体类型
            entity_type = self.pos_to_entity_type.get(flag)

            if entity_type and word not in seen[entity_type]:
                seen[entity_type].add(word)
                entities[entity_type].append({
                    'id': f"{entity_type}_{len(entities[entity_type])}",
                    'type': entity_type,
                    'name': word,
                    'position': position,
                })

            position += len(word)

        # 补充正则提取（针对特定模式）
        regex_entities = self._extract_entities_regex(text)
        for entity_type, entity_list in regex_entities.items():
            for entity in entity_list:
                if entity['name'] not in seen[entity_type]:
                    seen[entity_type].add(entity['name'])
                    entities[entity_type].append(entity)

        return dict(entities)

    def _extract_entities_regex(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """使用正则表达式提取实体（备用方案）"""
        entities = defaultdict(list)
        seen = defaultdict(set)

        for entity_type, pattern in self.entity_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entity_text = match.group().strip()
                # 去重、长度过滤、停用词过滤
                if (entity_text and
                    len(entity_text) >= 2 and
                    entity_text not in seen[entity_type] and
                    entity_text not in self.stopwords):
                    seen[entity_type].add(entity_text)
                    entities[entity_type].append({
                        'id': f"{entity_type}_{len(entities[entity_type])}",
                        'type': entity_type,
                        'name': entity_text,
                        'position': match.start(),
                    })

        return dict(entities)

    def extract_relations(self, text: str, entities: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """从文本中提取实体关系"""
        relations = []

        # 将所有实体展平
        all_entities = []
        for entity_list in entities.values():
            all_entities.extend(entity_list)

        # 按位置排序
        all_entities.sort(key=lambda x: x['position'])

        # 查找共现关系（在同一句子中的实体）
        sentences = re.split(r'[。！？\n.!?]', text)

        for sentence in sentences:
            if not sentence.strip():
                continue

            sentence_entities = [e for e in all_entities if e['name'] in sentence]

            # 为句子中的实体对创建关系（限制距离）
            for i, entity1 in enumerate(sentence_entities):
                for entity2 in sentence_entities[i+1:i+4]:  # 只关联附近的实体
                    if entity1['type'] != entity2['type']:  # 不同类型的实体才建立关系
                        relation = {
                            'source': entity1['id'],
                            'target': entity2['id'],
                            'type': self._infer_relation_type(entity1['type'], entity2['type']),
                            'weight': 1,
                        }
                        relations.append(relation)

        return relations

    def _infer_relation_type(self, type1: str, type2: str) -> str:
        """根据实体类型推断关系类型"""
        type_pair = tuple(sorted([type1, type2]))

        relation_map = {
            ('location', 'organization'): 'located_in',
            ('location', 'person'): 'lives_in',
            ('organization', 'person'): 'works_at',
            ('concept', 'person'): 'researches',
            ('date', 'person'): 'time_related',
            ('date', 'location'): 'time_related',
        }

        return relation_map.get(type_pair, 'related_to')

    def build_graph_from_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从多个文档构建知识图谱"""
        all_entities = defaultdict(lambda: {'type': '', 'name': '', 'docs': set(), 'count': 0})
        all_relations = defaultdict(lambda: {'source': '', 'target': '', 'type': '', 'weight': 0})

        for doc in documents:
            content = doc.get('converted_content') or doc.get('content', '')
            if not content:
                continue

            # 提取实体
            entities = self.extract_entities(content)
            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    key = entity['name']
                    all_entities[key]['type'] = entity_type
                    all_entities[key]['name'] = entity['name']
                    all_entities[key]['docs'].add(doc.get('id', 0))
                    all_entities[key]['count'] += 1

            # 提取关系
            relations = self.extract_relations(content, entities)
            for relation in relations:
                # 使用实体名称作为关系键
                source_name = next((e['name'] for entity_list in entities.values()
                                  for e in entity_list if e['id'] == relation['source']), None)
                target_name = next((e['name'] for entity_list in entities.values()
                                  for e in entity_list if e['id'] == relation['target']), None)

                if source_name and target_name:
                    key = f"{source_name}--{target_name}"
                    all_relations[key]['source'] = source_name
                    all_relations[key]['target'] = target_name
                    all_relations[key]['type'] = relation['type']
                    all_relations[key]['weight'] += 1

        # 转换为列表格式
        nodes = [
            {
                'id': name,
                'label': name,
                'type': info['type'],
                'group': info['type'],
                'value': info['count'],
                'title': f"{name} (出现{info['count']}次)",
            }
            for name, info in all_entities.items()
            if info['count'] >= 1  # 至少出现1次
        ]

        edges = [
            {
                'source': info['source'],
                'target': info['target'],
                'type': info['type'],
                'weight': info['weight'],
            }
            for info in all_relations.values()
            if info['weight'] >= 1
        ]

        return {
            'nodes': nodes,
            'edges': edges,
            'statistics': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'node_types': self._count_by_type(nodes),
            }
        }

    def _count_by_type(self, nodes: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计各类型节点数量"""
        counts = defaultdict(int)
        for node in nodes:
            counts[node['type']] += 1
        return dict(counts)

    def extract_keywords(self, documents: List[Dict[str, Any]], top_k: int = 50) -> List[Dict[str, Any]]:
        """提取关键词（高频实体）"""
        entity_freq = defaultdict(lambda: {'type': '', 'count': 0})

        for doc in documents:
            content = doc.get('converted_content') or doc.get('content', '')
            if not content:
                continue

            entities = self.extract_entities(content)
            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    key = entity['name']
                    entity_freq[key]['type'] = entity_type
                    entity_freq[key]['count'] += 1

        # 按频率排序
        keywords = [
            {
                'keyword': name,
                'type': info['type'],
                'frequency': info['count'],
            }
            for name, info in entity_freq.items()
        ]
        keywords.sort(key=lambda x: x['frequency'], reverse=True)

        return keywords[:top_k]
