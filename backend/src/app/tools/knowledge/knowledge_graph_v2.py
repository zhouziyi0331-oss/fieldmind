"""
改进的知识图谱服务 v2 - 不依赖外部NLP库
使用改进的规则和停用词过滤
"""
import re
import logging
from typing import List, Dict, Any, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class KnowledgeGraphServiceV2:
    """改进的知识图谱服务 - 使用优化的规则引擎"""

    def __init__(self):
        # 停用词列表（过滤无意义的"实体"）
        self.stopwords = {
            # 通用停用词
            '这个', '那个', '一个', '什么', '如何', '为什么', '怎么', '哪里',
            '这里', '那里', '现在', '当时', '以前', '之后', '接着', '然后',
            '因此', '所以', '但是', '如果', '虽然', '而且', '或者', '以及',
            '的', '了', '在', '是', '有', '我', '你', '他', '她', '它',
            '我们', '你们', '他们', '她们', '它们', '自己', '大家', '别人',

            # 田野调查相关通用词（不是实体）
            '田野调查', '笔记', '调查地点', '主要发现', '调查时间', '访谈',
            '观察', '记录', '资料', '数据', '信息', '内容', '情况', '问题',
            '调查', '研究', '分析', '总结', '结论', '建议', '意见', '看法',
            '方式', '方法', '过程', '结果', '原因', '目的', '意义', '作用',
            '特点', '特征', '性质', '状态', '程度', '范围', '数量', '比例',

            # 常见介词和连词
            '与', '和', '及', '或', '但', '却', '而', '则', '因', '由',
            '对', '为', '从', '到', '向', '往', '朝', '沿', '按', '照',
            '关于', '根据', '通过', '经过', '按照', '依据', '基于',
        }

        # 人名特征词
        self.person_titles = {
            '先生', '女士', '教授', '博士', '老师', '师傅', '师父', '老板',
            '经理', '主任', '局长', '县长', '市长', '省长', '书记', '主席',
            '院长', '校长', '厂长', '总', '董事', '队长', '组长', '班长',
        }

        # 地名后缀
        self.location_suffixes = {
            '省', '市', '县', '区', '乡', '镇', '村', '街道', '路', '街',
            '巷', '弄', '里', '庄', '湾', '河', '江', '湖', '海', '山',
            '岛', '半岛', '平原', '盆地', '高原',
        }

        # 机构后缀
        self.org_suffixes = {
            '大学', '学院', '学校', '中学', '小学', '幼儿园', '研究所',
            '研究院', '实验室', '公司', '企业', '集团', '工厂', '车间',
            '部门', '委员会', '协会', '组织', '机构', '中心', '站', '所',
            '局', '厅', '部', '署', '司', '处', '科', '股',
        }

        # 概念后缀
        self.concept_suffixes = {
            '理论', '方法', '模式', '体系', '框架', '机制', '制度', '政策',
            '法律', '法规', '条例', '规定', '办法', '措施', '方案', '计划',
            '战略', '策略', '原则', '标准', '规范', '准则', '要求',
        }

    def extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """从文本中提取实体"""
        entities = defaultdict(list)
        seen = defaultdict(set)

        # 1. 提取日期
        date_entities = self._extract_dates(text)
        for entity in date_entities:
            if entity['name'] not in seen['date']:
                seen['date'].add(entity['name'])
                entities['date'].append(entity)

        # 2. 提取地名
        location_entities = self._extract_locations(text)
        for entity in location_entities:
            if entity['name'] not in seen['location'] and entity['name'] not in self.stopwords:
                seen['location'].add(entity['name'])
                entities['location'].append(entity)

        # 3. 提取机构名
        org_entities = self._extract_organizations(text)
        for entity in org_entities:
            if entity['name'] not in seen['organization'] and entity['name'] not in self.stopwords:
                seen['organization'].add(entity['name'])
                entities['organization'].append(entity)

        # 4. 提取概念
        concept_entities = self._extract_concepts(text)
        for entity in concept_entities:
            if entity['name'] not in seen['concept'] and entity['name'] not in self.stopwords:
                seen['concept'].add(entity['name'])
                entities['concept'].append(entity)

        # 5. 提取人名（带称谓的）
        person_entities = self._extract_persons(text)
        for entity in person_entities:
            if entity['name'] not in seen['person'] and entity['name'] not in self.stopwords:
                seen['person'].add(entity['name'])
                entities['person'].append(entity)

        return dict(entities)

    def _extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """提取日期"""
        entities = []
        patterns = [
            r'\d{4}年\d{1,2}月\d{1,2}日',
            r'\d{4}年\d{1,2}月',
            r'\d{4}年',
            r'\d{4}-\d{2}-\d{2}',
            r'\d{1,2}月\d{1,2}日',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                entities.append({
                    'id': f"date_{len(entities)}",
                    'type': 'date',
                    'name': match.group().strip(),
                    'position': match.start(),
                })

        return entities

    def _extract_locations(self, text: str) -> List[Dict[str, Any]]:
        """提取地名"""
        entities = []

        # 匹配：中文字符 + 地名后缀
        for suffix in self.location_suffixes:
            pattern = f'[一-龥]{{2,8}}{suffix}'
            for match in re.finditer(pattern, text):
                name = match.group().strip()
                if len(name) >= 3:  # 至少3个字
                    entities.append({
                        'id': f"location_{len(entities)}",
                        'type': 'location',
                        'name': name,
                        'position': match.start(),
                    })

        return entities

    def _extract_organizations(self, text: str) -> List[Dict[str, Any]]:
        """提取机构名"""
        entities = []

        # 匹配：中文字符 + 机构后缀
        for suffix in self.org_suffixes:
            pattern = f'[一-龥]{{2,15}}{suffix}'
            for match in re.finditer(pattern, text):
                name = match.group().strip()
                if len(name) >= 4:  # 至少4个字
                    entities.append({
                        'id': f"organization_{len(entities)}",
                        'type': 'organization',
                        'name': name,
                        'position': match.start(),
                    })

        return entities

    def _extract_concepts(self, text: str) -> List[Dict[str, Any]]:
        """提取概念"""
        entities = []

        # 匹配：中文字符 + 概念后缀
        for suffix in self.concept_suffixes:
            pattern = f'[一-龥]{{2,10}}{suffix}'
            for match in re.finditer(pattern, text):
                name = match.group().strip()
                if len(name) >= 4:  # 至少4个字
                    entities.append({
                        'id': f"concept_{len(entities)}",
                        'type': 'concept',
                        'name': name,
                        'position': match.start(),
                    })

        return entities

    def _extract_persons(self, text: str) -> List[Dict[str, Any]]:
        """提取人名（带称谓的）"""
        entities = []

        # 匹配：姓名 + 称谓
        for title in self.person_titles:
            # 中文姓名 + 称谓
            pattern = f'[一-龥]{{2,4}}{title}'
            for match in re.finditer(pattern, text):
                name = match.group().strip()
                entities.append({
                    'id': f"person_{len(entities)}",
                    'type': 'person',
                    'name': name,
                    'position': match.start(),
                })

        # 匹配：常见格式 "姓名（年龄/职位）"
        pattern = r'([一-龥]{2,4})（[0-9]{1,3}岁|[一-龥]{2,8}）'
        for match in re.finditer(pattern, text):
            name = match.group(1).strip()
            if name not in self.stopwords:
                entities.append({
                    'id': f"person_{len(entities)}",
                    'type': 'person',
                    'name': name,
                    'position': match.start(),
                })

        return entities

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

            # 为句子中的实体对创建关系（只关联附近的、不同类型的实体）
            for i, entity1 in enumerate(sentence_entities):
                for entity2 in sentence_entities[i+1:i+4]:  # 限制窗口大小
                    if entity1['type'] != entity2['type']:  # 不同类型才建立关系
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
            ('date', 'organization'): 'time_related',
        }

        return relation_map.get(type_pair, 'related_to')

    def build_graph_from_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从多个文档构建知识图谱"""
        all_entities = defaultdict(lambda: {'type': '', 'name': '', 'docs': set(), 'count': 0})
        all_relations = defaultdict(lambda: {'source': '', 'target': '', 'type': '', 'weight': 0})

        for doc in documents:
            content = doc.get('text_content') or doc.get('converted_content') or doc.get('content', '')
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
            if info['count'] >= 1
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
            content = doc.get('text_content') or doc.get('converted_content') or doc.get('content', '')
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


# 创建全局实例
knowledge_graph_service_v2 = KnowledgeGraphServiceV2()
