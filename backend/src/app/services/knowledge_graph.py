"""
知识图谱服务
提取文档中的实体和关系，构建知识网络
"""
import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """知识图谱服务 - 从文档提取实体和关系"""

    def __init__(self):
        self.entity_patterns = {
            'person': r'(?:[A-Z][a-z]+\s){1,3}[A-Z][a-z]+|[一-龥]{2,4}(?:先生|女士|教授|博士|老师)?',
            'location': r'(?:[A-Z][a-z]+\s){1,2}(?:City|County|Province|State|Country)|[一-龥]{2,6}(?:省|市|县|区|村|镇|街道)',
            'organization': r'(?:[A-Z][a-z]+\s){1,3}(?:University|Company|Institute|Department)|[一-龥]{2,10}(?:大学|公司|研究所|学院|部门|组织)',
            'date': r'\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}',
            'concept': r'(?:[A-Z][a-z]+\s){1,3}[A-Z][a-z]+|[一-龥]{2,6}(?:理论|方法|模式|体系|框架|机制)',
        }

        # 关系关键词
        self.relation_keywords = {
            'work_at': ['工作于', '任职于', '就职于', 'works at', 'employed by'],
            'located_in': ['位于', '在', '地处', 'located in', 'in'],
            'related_to': ['相关', '关联', '涉及', 'related to', 'associated with'],
            'studied_at': ['就读于', '毕业于', '学习于', 'studied at', 'graduated from'],
            'research_on': ['研究', '探讨', '分析', 'research on', 'study on'],
            'collaborate_with': ['合作', '协作', '共同', 'collaborate with', 'work with'],
        }

    def extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """从文本中提取实体"""
        entities = defaultdict(list)
        seen = defaultdict(set)

        for entity_type, pattern in self.entity_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entity_text = match.group().strip()
                # 去重和长度过滤
                if entity_text and len(entity_text) > 1 and entity_text not in seen[entity_type]:
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
            sentence_entities = [e for e in all_entities if e['name'] in sentence]

            # 为句子中的实体对创建关系
            for i, entity1 in enumerate(sentence_entities):
                for entity2 in sentence_entities[i+1:]:
                    relation_type = self._infer_relation_type(
                        sentence, entity1, entity2
                    )

                    if relation_type:
                        relations.append({
                            'source': entity1['id'],
                            'target': entity2['id'],
                            'type': relation_type,
                            'context': sentence[:100],
                        })

        return relations

    def _infer_relation_type(self, text: str, entity1: Dict, entity2: Dict) -> Optional[str]:
        """推断两个实体之间的关系类型"""
        # 查找关系关键词
        for relation_type, keywords in self.relation_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return relation_type

        # 默认关系
        return 'related_to'

    def build_graph_from_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从多个文档构建知识图谱"""
        all_entities = defaultdict(list)
        all_relations = []

        for doc in documents:
            text_content = doc.get('text_content', '')
            if not text_content:
                continue

            # 提取实体
            doc_entities = self.extract_entities(text_content)

            # 合并实体
            for entity_type, entity_list in doc_entities.items():
                all_entities[entity_type].extend(entity_list)

            # 提取关系
            doc_relations = self.extract_relations(text_content, doc_entities)
            all_relations.extend(doc_relations)

        # 实体去重（基于名称）
        unique_entities = self._deduplicate_entities(all_entities)

        # 关系去重
        unique_relations = self._deduplicate_relations(all_relations)

        # 构建图谱数据结构
        graph = {
            'nodes': self._format_nodes(unique_entities),
            'edges': self._format_edges(unique_relations),
            'statistics': {
                'total_nodes': sum(len(v) for v in unique_entities.values()),
                'total_edges': len(unique_relations),
                'node_types': {k: len(v) for k, v in unique_entities.items()},
            }
        }

        return graph

    def _deduplicate_entities(self, entities: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """实体去重"""
        unique = defaultdict(list)

        for entity_type, entity_list in entities.items():
            seen_names = set()
            for entity in entity_list:
                name = entity['name']
                if name not in seen_names:
                    seen_names.add(name)
                    unique[entity_type].append(entity)

        return dict(unique)

    def _deduplicate_relations(self, relations: List[Dict]) -> List[Dict]:
        """关系去重"""
        seen = set()
        unique = []

        for relation in relations:
            key = (relation['source'], relation['target'], relation['type'])
            if key not in seen:
                seen.add(key)
                unique.append(relation)

        return unique

    def _format_nodes(self, entities: Dict[str, List[Dict]]) -> List[Dict]:
        """格式化节点数据"""
        nodes = []

        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                nodes.append({
                    'id': entity['id'],
                    'label': entity['name'],
                    'type': entity_type,
                    'group': entity_type,
                })

        return nodes

    def _format_edges(self, relations: List[Dict]) -> List[Dict]:
        """格式化边数据"""
        edges = []

        for i, relation in enumerate(relations):
            edges.append({
                'id': f"edge_{i}",
                'source': relation['source'],
                'target': relation['target'],
                'label': relation['type'],
                'type': relation['type'],
            })

        return edges

    def extract_keywords(self, text: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """提取关键词（简单的TF-IDF方法）"""
        # 简单的中文分词（按字符和标点）
        words = re.findall(r'[一-龥]{2,}|[a-zA-Z]{3,}', text)

        # 计数
        word_freq = defaultdict(int)
        for word in words:
            if len(word) >= 2:
                word_freq[word] += 1

        # 排序
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        # 返回top_k
        keywords = []
        for word, freq in sorted_words[:top_k]:
            keywords.append({
                'text': word,
                'value': freq,
                'frequency': freq,
            })

        return keywords


# 全局服务实例
knowledge_graph_service = KnowledgeGraphService()
