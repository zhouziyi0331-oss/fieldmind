"""
Unified Knowledge Graph Engine
整合6个知识图谱版本的统一引擎

Core Features:
- Multi-strategy entity extraction (jieba NLP + comprehensive regex rules)
- Enhanced relation extraction with strength calculation
- Cross-document entity alignment and disambiguation
- Entity timeline tracking across documents
- Advanced graph query API (subgraph, path finding)
- Community detection and graph statistics
"""

from typing import Dict, List, Any, Optional, Set, Tuple
import re
from datetime import datetime
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# Try to import jieba for NLP-based extraction
try:
    import jieba
    import jieba.posseg as pseg
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    logger.warning("jieba not available, falling back to regex-only extraction")


class MultiStrategyEntityExtractor:
    """
    多策略实体提取器
    整合 v2 的全面规则 + improved 的 jieba NLP
    """

    def __init__(self, use_jieba: bool = True):
        self.use_jieba = use_jieba and JIEBA_AVAILABLE

        # Comprehensive stopwords from v2 (最完整的停用词列表)
        self.stopwords = {
            # 指示代词和疑问词
            '这个', '那个', '一个', '什么', '如何', '为什么', '怎么', '哪里',
            '这里', '那里', '现在', '当时', '以前', '之后', '接着', '然后',

            # 连接词和转折词
            '因此', '所以', '但是', '如果', '虽然', '而且', '或者', '以及',
            '不过', '然而', '可是', '只是', '因为', '由于', '通过', '根据',

            # 田野调查相关通用词
            '调查', '研究', '发现', '认为', '表示', '指出', '提到', '描述',
            '分析', '总结', '归纳', '整理', '记录', '观察', '访谈', '收集',

            # 介词和连词
            '在', '对', '从', '向', '到', '给', '把', '被', '让', '叫',
            '和', '与', '及', '同', '跟', '为', '以', '按', '依', '据',

            # 其他常见停用词
            '的', '了', '是', '我', '你', '他', '她', '它', '们', '这',
            '那', '些', '此', '着', '过', '吗', '呢', '啊', '呀', '吧'
        }

        # Entity type vocabularies from v2
        self.person_titles = {
            '先生', '女士', '教授', '博士', '老师', '师傅', '大师',
            '村民', '居民', '农民', '工人', '干部', '领导', '主任',
            '书记', '乡长', '村长', '组长', '队长', '会长', '理事',
            '长老', '族长', '家长', '老人', '青年', '儿童', '学生'
        }

        self.location_suffixes = {
            '省', '市', '县', '区', '乡', '镇', '村', '组', '屯', '寨',
            '街', '路', '巷', '弄', '里', '坊', '社区', '居委会',
            '地区', '区域', '流域', '山区', '平原', '盆地',
            '山', '河', '江', '湖', '海', '岛', '峰', '谷', '洞', '泉'
        }

        self.org_suffixes = {
            '大学', '学院', '学校', '研究所', '研究院', '中心', '实验室',
            '公司', '企业', '集团', '组织', '协会', '学会', '联合会',
            '委员会', '办公室', '局', '厅', '部', '处', '科', '股',
            '合作社', '互助组', '生产队', '工作组', '项目组'
        }

        self.concept_suffixes = {
            '理论', '方法', '模式', '体系', '框架', '机制', '制度',
            '文化', '传统', '习俗', '仪式', '礼仪', '节日', '活动',
            '技术', '工艺', '技能', '手艺', '艺术', '风格', '流派',
            '观念', '思想', '意识', '认知', '价值观', '世界观'
        }

        # POS tag to entity type mapping for jieba
        self.pos_to_entity_type = {
            'nr': 'person',       # 人名
            'ns': 'location',     # 地名
            'nt': 'organization', # 机构名
            't': 'date',          # 时间词
            'nz': 'concept',      # 其他专有名词
        }

        # Regex patterns
        self._compile_patterns()

    def _compile_patterns(self):
        """编译正则表达式模式"""
        # Date patterns (完整日期格式)
        self.date_pattern = re.compile(
            r'\d{4}年(?:\d{1,2}月)?(?:\d{1,2}日)?|'
            r'\d{4}-\d{1,2}-\d{1,2}|'
            r'\d{1,2}月\d{1,2}日|'
            r'(?:清朝|明朝|民国|新中国)\S{0,10}年|'
            r'(?:春秋|战国|秦汉|唐宋|元明清)时期'
        )

        # Chinese name pattern (2-4个汉字)
        self.name_pattern = re.compile(r'[一-龥]{2,4}(?:' + '|'.join(self.person_titles) + ')')

    def extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        提取实体 - 自动选择最佳策略

        Returns:
            {
                'person': [{'text': '张教授', 'type': 'person', 'offset': 10, ...}],
                'location': [...],
                'organization': [...],
                'date': [...],
                'concept': [...]
            }
        """
        if self.use_jieba:
            return self._extract_with_jieba(text)
        else:
            return self._extract_with_regex(text)

    def _extract_with_jieba(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """使用 jieba 词性标注提取 + regex 补充"""
        entities = defaultdict(list)

        # Jieba POS tagging
        words = list(pseg.cut(text))
        offset = 0

        for item in words:
            word = item.word
            pos = item.flag
            word_len = len(word)

            # Skip stopwords and short words
            if word in self.stopwords or word_len < 2:
                offset += word_len
                continue

            # Map POS tag to entity type
            entity_type = self.pos_to_entity_type.get(pos)

            if entity_type:
                entities[entity_type].append({
                    'text': word,
                    'type': entity_type,
                    'offset': offset,
                    'length': word_len,
                    'extraction_method': 'jieba_pos'
                })

            offset += word_len

        # Supplement with regex for patterns jieba might miss
        regex_entities = self._extract_with_regex(text)

        # Merge results (避免重复)
        for entity_type, entity_list in regex_entities.items():
            existing_texts = {e['text'] for e in entities[entity_type]}
            for entity in entity_list:
                if entity['text'] not in existing_texts:
                    entity['extraction_method'] = 'regex_supplement'
                    entities[entity_type].append(entity)

        return dict(entities)

    def _extract_with_regex(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """使用规则和正则表达式提取"""
        entities = {
            'person': self._extract_persons(text),
            'location': self._extract_locations(text),
            'organization': self._extract_organizations(text),
            'date': self._extract_dates(text),
            'concept': self._extract_concepts(text)
        }
        return entities

    def _extract_persons(self, text: str) -> List[Dict[str, Any]]:
        """提取人名"""
        persons = []

        # Pattern: 姓名 + 称谓
        for match in self.name_pattern.finditer(text):
            person_text = match.group()
            if person_text not in self.stopwords:
                persons.append({
                    'text': person_text,
                    'type': 'person',
                    'offset': match.start(),
                    'length': len(person_text),
                    'extraction_method': 'regex'
                })

        return persons

    def _extract_locations(self, text: str) -> List[Dict[str, Any]]:
        """提取地名"""
        locations = []

        # Pattern: 名称 + 地点后缀
        for suffix in self.location_suffixes:
            pattern = re.compile(r'[一-龥]{2,8}' + re.escape(suffix))
            for match in pattern.finditer(text):
                loc_text = match.group()
                if loc_text not in self.stopwords:
                    locations.append({
                        'text': loc_text,
                        'type': 'location',
                        'offset': match.start(),
                        'length': len(loc_text),
                        'extraction_method': 'regex'
                    })

        return locations

    def _extract_organizations(self, text: str) -> List[Dict[str, Any]]:
        """提取机构名"""
        organizations = []

        # Pattern: 名称 + 机构后缀
        for suffix in self.org_suffixes:
            pattern = re.compile(r'[一-龥]{2,15}' + re.escape(suffix))
            for match in pattern.finditer(text):
                org_text = match.group()
                if org_text not in self.stopwords:
                    organizations.append({
                        'text': org_text,
                        'type': 'organization',
                        'offset': match.start(),
                        'length': len(org_text),
                        'extraction_method': 'regex'
                    })

        return organizations

    def _extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """提取日期"""
        dates = []

        for match in self.date_pattern.finditer(text):
            date_text = match.group()
            dates.append({
                'text': date_text,
                'type': 'date',
                'offset': match.start(),
                'length': len(date_text),
                'extraction_method': 'regex'
            })

        return dates

    def _extract_concepts(self, text: str) -> List[Dict[str, Any]]:
        """提取概念术语"""
        concepts = []

        # Pattern: 名称 + 概念后缀
        for suffix in self.concept_suffixes:
            pattern = re.compile(r'[一-龥]{2,10}' + re.escape(suffix))
            for match in pattern.finditer(text):
                concept_text = match.group()
                if concept_text not in self.stopwords:
                    concepts.append({
                        'text': concept_text,
                        'type': 'concept',
                        'offset': match.start(),
                        'length': len(concept_text),
                        'extraction_method': 'regex'
                    })

        return concepts


class EnhancedRelationExtractor:
    """
    增强的关系提取器
    添加关系强度计算和类型推断
    """

    def __init__(self, window_size: int = 100):
        self.window_size = window_size

    def extract_relations(
        self,
        text: str,
        entities: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        提取实体关系

        Returns:
            [
                {
                    'source': '张教授',
                    'source_type': 'person',
                    'target': '北京大学',
                    'target_type': 'organization',
                    'relation_type': 'affiliated_with',
                    'strength': 0.85,
                    'context': '...张教授在北京大学...',
                    'distance': 5
                },
                ...
            ]
        """
        relations = []

        # Flatten all entities with their positions
        all_entities = []
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                entity['entity_type'] = entity_type
                all_entities.append(entity)

        # Sort by offset
        all_entities.sort(key=lambda e: e['offset'])

        # Find co-occurrences within window
        for i, entity1 in enumerate(all_entities):
            for entity2 in all_entities[i+1:]:
                distance = entity2['offset'] - entity1['offset']

                if distance > self.window_size:
                    break

                # Extract context
                start = max(0, entity1['offset'] - 20)
                end = min(len(text), entity2['offset'] + entity2['length'] + 20)
                context = text[start:end]

                # Infer relation type
                relation_type = self._infer_relation_type(
                    entity1['entity_type'],
                    entity2['entity_type']
                )

                # Calculate relation strength
                strength = self._calculate_strength(distance, context)

                relations.append({
                    'source': entity1['text'],
                    'source_type': entity1['entity_type'],
                    'target': entity2['text'],
                    'target_type': entity2['entity_type'],
                    'relation_type': relation_type,
                    'strength': strength,
                    'context': context,
                    'distance': distance
                })

        return relations

    def _infer_relation_type(self, type1: str, type2: str) -> str:
        """推断关系类型"""
        relation_map = {
            ('person', 'organization'): 'affiliated_with',
            ('person', 'location'): 'located_in',
            ('person', 'person'): 'related_to',
            ('organization', 'location'): 'located_in',
            ('concept', 'person'): 'proposed_by',
            ('concept', 'location'): 'practiced_in',
            ('date', 'person'): 'time_of',
            ('date', 'location'): 'time_of',
        }

        return relation_map.get((type1, type2), 'related_to')

    def _calculate_strength(self, distance: int, context: str) -> float:
        """
        计算关系强度
        基于距离和上下文中的连接词
        """
        # Base strength from distance (距离越近，强度越高)
        distance_strength = max(0.1, 1.0 - (distance / self.window_size))

        # Boost from connection words
        connection_words = ['的', '在', '是', '有', '与', '和', '及', '为', '从', '到']
        connection_count = sum(1 for word in connection_words if word in context)
        connection_boost = min(0.3, connection_count * 0.1)

        return min(1.0, distance_strength + connection_boost)


class EntityAlignmentEngine:
    """
    跨文档实体对齐引擎
    NEW FEATURE 1: 实体消歧和合并
    """

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.entity_clusters: Dict[str, Set[str]] = defaultdict(set)
        self.canonical_names: Dict[str, str] = {}

    def align_entities(
        self,
        entities_by_doc: Dict[str, Dict[str, List[Dict[str, Any]]]]
    ) -> Dict[str, List[str]]:
        """
        跨文档对齐实体

        Args:
            entities_by_doc: {doc_id: {entity_type: [entities]}}

        Returns:
            {canonical_entity: [variant1, variant2, ...]}
        """
        # Group by entity type
        entities_by_type = defaultdict(list)
        for doc_id, entities_dict in entities_by_doc.items():
            for entity_type, entity_list in entities_dict.items():
                for entity in entity_list:
                    entities_by_type[entity_type].append({
                        'text': entity['text'],
                        'doc_id': doc_id,
                        'type': entity_type
                    })

        # Align within each type
        aligned = {}
        for entity_type, entities in entities_by_type.items():
            type_aligned = self._align_same_type(entities)
            aligned.update(type_aligned)

        return aligned

    def _align_same_type(self, entities: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """对齐同类型实体"""
        clusters = defaultdict(set)
        entity_texts = list(set(e['text'] for e in entities))

        # Simple string similarity clustering
        for i, text1 in enumerate(entity_texts):
            for text2 in entity_texts[i+1:]:
                if self._is_similar(text1, text2):
                    # Merge clusters
                    canonical = min(text1, text2, key=len)  # 选择较短的作为规范名
                    clusters[canonical].add(text1)
                    clusters[canonical].add(text2)

        # Entities that didn't cluster with anything
        for text in entity_texts:
            if not any(text in variants for variants in clusters.values()):
                clusters[text] = {text}

        return {canonical: list(variants) for canonical, variants in clusters.items()}

    def _is_similar(self, text1: str, text2: str) -> bool:
        """判断两个实体是否相似"""
        # Exact match
        if text1 == text2:
            return True

        # One contains the other (e.g., "张教授" vs "张三教授")
        if text1 in text2 or text2 in text1:
            return True

        # Levenshtein-like: character overlap
        common = sum(1 for c in text1 if c in text2)
        similarity = common / max(len(text1), len(text2))

        return similarity >= self.similarity_threshold


class EntityTimelineTracker:
    """
    实体时间线追踪器
    NEW FEATURE 2: 跨文档追踪实体演变
    """

    def __init__(self):
        self.timelines: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def build_timeline(
        self,
        entity: str,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        构建实体时间线

        Args:
            entity: 实体名称
            documents: [{'id': doc_id, 'content': text, 'timestamp': datetime, 'metadata': {...}}]

        Returns:
            [
                {
                    'timestamp': datetime,
                    'doc_id': 'doc123',
                    'mention_count': 5,
                    'context_snippets': ['...', '...'],
                    'co_entities': ['实体A', '实体B']
                },
                ...
            ] (按时间排序)
        """
        timeline = []

        for doc in documents:
            content = doc['content']
            if entity not in content:
                continue

            # Count mentions
            mention_count = content.count(entity)

            # Extract context snippets
            snippets = self._extract_snippets(entity, content, max_snippets=3)

            # Find co-occurring entities (简化版)
            co_entities = self._find_co_entities(entity, content)

            timeline.append({
                'timestamp': doc.get('timestamp', datetime.now()),
                'doc_id': doc['id'],
                'mention_count': mention_count,
                'context_snippets': snippets,
                'co_entities': co_entities,
                'metadata': doc.get('metadata', {})
            })

        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'])

        return timeline

    def _extract_snippets(self, entity: str, text: str, max_snippets: int = 3) -> List[str]:
        """提取实体周围的上下文片段"""
        snippets = []
        start = 0

        while len(snippets) < max_snippets:
            pos = text.find(entity, start)
            if pos == -1:
                break

            snippet_start = max(0, pos - 50)
            snippet_end = min(len(text), pos + len(entity) + 50)
            snippet = text[snippet_start:snippet_end].strip()
            snippets.append(f"...{snippet}...")

            start = pos + len(entity)

        return snippets

    def _find_co_entities(self, target_entity: str, text: str) -> List[str]:
        """查找共现实体（简化版，使用规则）"""
        # 简单的共现检测：查找同一句中的其他大写开头词组
        co_entities = set()

        # Split by sentences
        sentences = re.split(r'[。！？]', text)

        for sentence in sentences:
            if target_entity in sentence:
                # Find other potential entities (简化：查找2-4个连续汉字)
                potential = re.findall(r'[一-龥]{2,4}', sentence)
                co_entities.update([e for e in potential if e != target_entity])

        return list(co_entities)[:10]  # Limit to top 10


class GraphQueryEngine:
    """
    图查询引擎
    NEW FEATURE 3: 子图提取和路径查询
    """

    def __init__(self, graph_data: Dict[str, Any]):
        """
        Args:
            graph_data: {
                'nodes': [{'id': 'entity1', 'type': 'person', ...}],
                'edges': [{'source': 'entity1', 'target': 'entity2', 'type': 'related_to', ...}]
            }
        """
        self.nodes = {node['id']: node for node in graph_data.get('nodes', [])}
        self.edges = graph_data.get('edges', [])

        # Build adjacency list
        self.adjacency = defaultdict(list)
        for edge in self.edges:
            self.adjacency[edge['source']].append({
                'target': edge['target'],
                'type': edge.get('type', 'related_to'),
                'strength': edge.get('strength', 1.0)
            })

    def get_subgraph(
        self,
        center_entity: str,
        max_depth: int = 2,
        entity_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        提取以某实体为中心的子图

        Returns:
            {'nodes': [...], 'edges': [...]}
        """
        visited = set()
        subgraph_nodes = []
        subgraph_edges = []

        def traverse(entity: str, depth: int):
            if depth > max_depth or entity in visited:
                return

            visited.add(entity)

            # Add node
            if entity in self.nodes:
                node = self.nodes[entity]
                if entity_types is None or node.get('type') in entity_types:
                    subgraph_nodes.append(node)

            # Traverse neighbors
            for neighbor in self.adjacency.get(entity, []):
                target = neighbor['target']

                # Add edge
                edge = {
                    'source': entity,
                    'target': target,
                    'type': neighbor['type'],
                    'strength': neighbor['strength']
                }
                if edge not in subgraph_edges:
                    subgraph_edges.append(edge)

                traverse(target, depth + 1)

        traverse(center_entity, 0)

        return {
            'nodes': subgraph_nodes,
            'edges': subgraph_edges,
            'center': center_entity,
            'depth': max_depth
        }

    def find_path(
        self,
        source: str,
        target: str,
        max_length: int = 5
    ) -> Optional[List[str]]:
        """
        查找两个实体之间的最短路径 (BFS)

        Returns:
            ['entity1', 'entity2', 'entity3'] or None
        """
        if source not in self.nodes or target not in self.nodes:
            return None

        from collections import deque

        queue = deque([(source, [source])])
        visited = {source}

        while queue:
            current, path = queue.popleft()

            if len(path) > max_length:
                continue

            if current == target:
                return path

            for neighbor in self.adjacency.get(current, []):
                neighbor_id = neighbor['target']
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return None

    def find_common_neighbors(
        self,
        entity1: str,
        entity2: str
    ) -> List[str]:
        """查找两个实体的共同邻居"""
        neighbors1 = {n['target'] for n in self.adjacency.get(entity1, [])}
        neighbors2 = {n['target'] for n in self.adjacency.get(entity2, [])}

        return list(neighbors1 & neighbors2)


class CommunityDetector:
    """
    社区检测器
    NEW FEATURE 4: 使用 Louvain 算法进行实体聚类
    """

    def detect_communities(
        self,
        graph_data: Dict[str, Any],
        resolution: float = 1.0
    ) -> Dict[str, int]:
        """
        检测社区

        Returns:
            {entity_id: community_id}
        """
        try:
            import networkx as nx
            from networkx.algorithms import community
        except ImportError:
            logger.warning("networkx not available, using simple clustering")
            return self._simple_clustering(graph_data)

        # Build NetworkX graph
        G = nx.Graph()

        for node in graph_data.get('nodes', []):
            G.add_node(node['id'], **node)

        for edge in graph_data.get('edges', []):
            G.add_edge(
                edge['source'],
                edge['target'],
                weight=edge.get('strength', 1.0)
            )

        # Louvain community detection
        communities = community.louvain_communities(G, resolution=resolution)

        # Map entity to community ID
        entity_to_community = {}
        for comm_id, comm_nodes in enumerate(communities):
            for node in comm_nodes:
                entity_to_community[node] = comm_id

        return entity_to_community

    def _simple_clustering(self, graph_data: Dict[str, Any]) -> Dict[str, int]:
        """简单聚类（当 networkx 不可用时）"""
        # Connected components using Union-Find
        parent = {}

        def find(x):
            if x not in parent:
                parent[x] = x
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Union connected entities
        for edge in graph_data.get('edges', []):
            union(edge['source'], edge['target'])

        # Assign community IDs
        communities = {}
        community_map = {}
        next_id = 0

        for node in graph_data.get('nodes', []):
            root = find(node['id'])
            if root not in community_map:
                community_map[root] = next_id
                next_id += 1
            communities[node['id']] = community_map[root]

        return communities


class GraphStatistics:
    """
    图统计分析器
    NEW FEATURE 5: PageRank, 中心性, 质量评估
    """

    def __init__(self, graph_data: Dict[str, Any]):
        self.graph_data = graph_data
        self.nodes = {n['id']: n for n in graph_data.get('nodes', [])}
        self.edges = graph_data.get('edges', [])

    def calculate_pagerank(
        self,
        damping: float = 0.85,
        max_iter: int = 100
    ) -> Dict[str, float]:
        """
        计算 PageRank

        Returns:
            {entity_id: pagerank_score}
        """
        try:
            import networkx as nx
        except ImportError:
            logger.warning("networkx not available, using simple degree centrality")
            return self._simple_degree_centrality()

        G = self._build_networkx_graph()
        pagerank = nx.pagerank(G, alpha=damping, max_iter=max_iter)

        return pagerank

    def calculate_centrality(self) -> Dict[str, Dict[str, float]]:
        """
        计算多种中心性指标

        Returns:
            {
                entity_id: {
                    'degree': 0.5,
                    'betweenness': 0.3,
                    'closeness': 0.7
                }
            }
        """
        try:
            import networkx as nx
        except ImportError:
            return {node_id: {'degree': 0} for node_id in self.nodes}

        G = self._build_networkx_graph()

        degree = nx.degree_centrality(G)
        betweenness = nx.betweenness_centrality(G)
        closeness = nx.closeness_centrality(G)

        centrality = {}
        for node_id in self.nodes:
            centrality[node_id] = {
                'degree': degree.get(node_id, 0),
                'betweenness': betweenness.get(node_id, 0),
                'closeness': closeness.get(node_id, 0)
            }

        return centrality

    def assess_quality(self) -> Dict[str, Any]:
        """
        评估图质量

        Returns:
            {
                'node_count': 100,
                'edge_count': 250,
                'density': 0.05,
                'avg_degree': 5.0,
                'connected_components': 3,
                'largest_component_size': 85
            }
        """
        node_count = len(self.nodes)
        edge_count = len(self.edges)

        if node_count == 0:
            return {'node_count': 0, 'edge_count': 0, 'density': 0}

        # Density
        max_edges = node_count * (node_count - 1) / 2
        density = edge_count / max_edges if max_edges > 0 else 0

        # Average degree
        avg_degree = (2 * edge_count) / node_count if node_count > 0 else 0

        # Connected components (simplified)
        components = self._count_components()

        return {
            'node_count': node_count,
            'edge_count': edge_count,
            'density': round(density, 4),
            'avg_degree': round(avg_degree, 2),
            'connected_components': len(components),
            'largest_component_size': max(len(c) for c in components) if components else 0
        }

    def _build_networkx_graph(self):
        """构建 NetworkX 图"""
        import networkx as nx

        G = nx.Graph()
        for node_id in self.nodes:
            G.add_node(node_id)
        for edge in self.edges:
            G.add_edge(edge['source'], edge['target'])

        return G

    def _simple_degree_centrality(self) -> Dict[str, float]:
        """简单度中心性（当 networkx 不可用时）"""
        degree = defaultdict(int)
        for edge in self.edges:
            degree[edge['source']] += 1
            degree[edge['target']] += 1

        max_degree = max(degree.values()) if degree else 1
        return {node_id: degree[node_id] / max_degree for node_id in self.nodes}

    def _count_components(self) -> List[Set[str]]:
        """计算连通分量"""
        parent = {}

        def find(x):
            if x not in parent:
                parent[x] = x
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        for edge in self.edges:
            union(edge['source'], edge['target'])

        components_map = defaultdict(set)
        for node_id in self.nodes:
            root = find(node_id)
            components_map[root].add(node_id)

        return list(components_map.values())


class UnifiedKnowledgeGraphEngine:
    """
    统一知识图谱引擎
    整合所有功能，提供单一入口点

    Features:
    1. Multi-strategy entity extraction (jieba + regex)
    2. Enhanced relation extraction with strength calculation
    3. Cross-document entity alignment (NEW)
    4. Entity timeline tracking (NEW)
    5. Advanced graph query API (NEW)
    6. Community detection (NEW)
    7. Graph statistics and quality assessment (NEW)
    8. Batch processing and caching (from builder_optimized)
    """

    def __init__(
        self,
        use_jieba: bool = True,
        relation_window: int = 100,
        similarity_threshold: float = 0.85
    ):
        # Core components
        self.entity_extractor = MultiStrategyEntityExtractor(use_jieba=use_jieba)
        self.relation_extractor = EnhancedRelationExtractor(window_size=relation_window)
        self.entity_aligner = EntityAlignmentEngine(similarity_threshold=similarity_threshold)
        self.timeline_tracker = EntityTimelineTracker()

        # Storage
        self.graphs: Dict[str, Dict[str, Any]] = {}  # {doc_id: graph_data}
        self.unified_graph: Optional[Dict[str, Any]] = None

        # Cache
        self._entity_cache: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        self._relation_cache: Dict[str, List[Dict[str, Any]]] = {}

    def build_graph_from_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        从单个文档构建知识图谱

        Args:
            doc_id: 文档ID
            content: 文档内容
            metadata: 文档元数据

        Returns:
            {
                'doc_id': 'doc123',
                'nodes': [{'id': 'entity1', 'type': 'person', ...}],
                'edges': [{'source': 'entity1', 'target': 'entity2', ...}],
                'metadata': {...},
                'statistics': {...}
            }
        """
        # Extract entities
        entities = self.entity_extractor.extract_entities(content)
        self._entity_cache[doc_id] = entities

        # Extract relations
        relations = self.relation_extractor.extract_relations(content, entities)
        self._relation_cache[doc_id] = relations

        # Build graph structure
        nodes = []
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                nodes.append({
                    'id': entity['text'],
                    'type': entity_type,
                    'extraction_method': entity.get('extraction_method', 'unknown'),
                    'occurrences': [entity['offset']],
                    'doc_id': doc_id
                })

        edges = []
        for relation in relations:
            edges.append({
                'source': relation['source'],
                'target': relation['target'],
                'type': relation['relation_type'],
                'strength': relation['strength'],
                'context': relation.get('context', ''),
                'doc_id': doc_id
            })

        graph_data = {
            'doc_id': doc_id,
            'nodes': nodes,
            'edges': edges,
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat()
        }

        # Calculate statistics
        stats = GraphStatistics(graph_data)
        graph_data['statistics'] = stats.assess_quality()

        # Store
        self.graphs[doc_id] = graph_data

        return graph_data

    def build_unified_graph(
        self,
        align_entities: bool = True,
        detect_communities: bool = True
    ) -> Dict[str, Any]:
        """
        构建跨文档统一图谱

        整合所有文档的知识图谱，进行实体对齐和社区检测

        Returns:
            {
                'nodes': [...],
                'edges': [...],
                'entity_alignment': {canonical: [variants]},
                'communities': {entity: community_id},
                'statistics': {...},
                'pagerank': {entity: score}
            }
        """
        if not self.graphs:
            logger.warning("No graphs to unify")
            return {'nodes': [], 'edges': []}

        # Merge all nodes and edges
        all_nodes = []
        all_edges = []
        entity_to_docs = defaultdict(list)

        for doc_id, graph in self.graphs.items():
            for node in graph['nodes']:
                all_nodes.append(node)
                entity_to_docs[node['id']].append(doc_id)

            for edge in graph['edges']:
                all_edges.append(edge)

        # Entity alignment
        entity_alignment = {}
        if align_entities:
            entities_by_doc = {
                doc_id: self._entity_cache.get(doc_id, {})
                for doc_id in self.graphs.keys()
            }
            entity_alignment = self.entity_aligner.align_entities(entities_by_doc)

            # Merge aligned entities in nodes
            all_nodes = self._merge_aligned_nodes(all_nodes, entity_alignment)
            all_edges = self._merge_aligned_edges(all_edges, entity_alignment)

        # Deduplicate
        unique_nodes = self._deduplicate_nodes(all_nodes)
        unique_edges = self._deduplicate_edges(all_edges)

        unified_graph = {
            'nodes': unique_nodes,
            'edges': unique_edges,
            'entity_alignment': entity_alignment,
            'source_documents': list(self.graphs.keys()),
            'created_at': datetime.now().isoformat()
        }

        # Community detection
        if detect_communities:
            detector = CommunityDetector()
            communities = detector.detect_communities(unified_graph)
            unified_graph['communities'] = communities

        # Calculate statistics
        stats = GraphStatistics(unified_graph)
        unified_graph['statistics'] = stats.assess_quality()
        unified_graph['pagerank'] = stats.calculate_pagerank()
        unified_graph['centrality'] = stats.calculate_centrality()

        self.unified_graph = unified_graph

        return unified_graph

    def query_graph(
        self,
        center_entity: str,
        max_depth: int = 2,
        entity_types: Optional[List[str]] = None,
        use_unified: bool = True
    ) -> Dict[str, Any]:
        """
        查询子图

        Args:
            center_entity: 中心实体
            max_depth: 最大深度
            entity_types: 过滤实体类型
            use_unified: 使用统一图谱还是单文档图谱

        Returns:
            子图数据
        """
        if use_unified and self.unified_graph:
            graph_data = self.unified_graph
        else:
            # Merge all document graphs
            graph_data = {
                'nodes': [n for g in self.graphs.values() for n in g['nodes']],
                'edges': [e for g in self.graphs.values() for e in g['edges']]
            }

        query_engine = GraphQueryEngine(graph_data)
        return query_engine.get_subgraph(center_entity, max_depth, entity_types)

    def find_path(
        self,
        source: str,
        target: str,
        max_length: int = 5,
        use_unified: bool = True
    ) -> Optional[List[str]]:
        """
        查找实体间路径

        Returns:
            路径实体列表 or None
        """
        if use_unified and self.unified_graph:
            graph_data = self.unified_graph
        else:
            graph_data = {
                'nodes': [n for g in self.graphs.values() for n in g['nodes']],
                'edges': [e for g in self.graphs.values() for e in g['edges']]
            }

        query_engine = GraphQueryEngine(graph_data)
        return query_engine.find_path(source, target, max_length)

    def get_entity_timeline(
        self,
        entity: str,
        documents: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取实体时间线

        Args:
            entity: 实体名称
            documents: 文档列表 (包含 id, content, timestamp, metadata)

        Returns:
            时间线事件列表
        """
        if documents is None:
            # Use cached graphs
            documents = []
            for doc_id, graph in self.graphs.items():
                # Reconstruct document from cache
                documents.append({
                    'id': doc_id,
                    'content': '',  # Need to store original content
                    'timestamp': datetime.fromisoformat(graph.get('created_at', datetime.now().isoformat())),
                    'metadata': graph.get('metadata', {})
                })

        return self.timeline_tracker.build_timeline(entity, documents)

    def get_top_entities(
        self,
        top_k: int = 10,
        metric: str = 'pagerank',
        use_unified: bool = True
    ) -> List[Tuple[str, float]]:
        """
        获取重要实体排名

        Args:
            top_k: 返回前K个
            metric: 排名指标 ('pagerank', 'degree', 'betweenness', 'closeness')

        Returns:
            [(entity, score), ...]
        """
        if use_unified and self.unified_graph:
            graph_data = self.unified_graph
        else:
            graph_data = {
                'nodes': [n for g in self.graphs.values() for n in g['nodes']],
                'edges': [e for g in self.graphs.values() for e in g['edges']]
            }

        stats = GraphStatistics(graph_data)

        if metric == 'pagerank':
            scores = stats.calculate_pagerank()
        else:
            centrality = stats.calculate_centrality()
            scores = {entity: metrics[metric] for entity, metrics in centrality.items()}

        # Sort and return top K
        sorted_entities = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_entities[:top_k]

    def export_graph(
        self,
        format: str = 'json',
        use_unified: bool = True
    ) -> Any:
        """
        导出图谱

        Args:
            format: 'json', 'graphml', 'cytoscape'
            use_unified: 导出统一图谱或所有文档图谱

        Returns:
            导出的图谱数据
        """
        if use_unified and self.unified_graph:
            graph_data = self.unified_graph
        else:
            graph_data = {
                'graphs': self.graphs,
                'total_documents': len(self.graphs)
            }

        if format == 'json':
            return graph_data
        elif format == 'graphml':
            return self._export_graphml(graph_data)
        elif format == 'cytoscape':
            return self._export_cytoscape(graph_data)
        else:
            raise ValueError(f"Unsupported format: {format}")

    # Helper methods

    def _merge_aligned_nodes(
        self,
        nodes: List[Dict[str, Any]],
        alignment: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """合并对齐的节点"""
        canonical_to_node = {}

        for node in nodes:
            node_id = node['id']

            # Find canonical form
            canonical = node_id
            for canon, variants in alignment.items():
                if node_id in variants:
                    canonical = canon
                    break

            if canonical not in canonical_to_node:
                canonical_to_node[canonical] = {
                    'id': canonical,
                    'type': node['type'],
                    'variants': set(),
                    'occurrences': [],
                    'doc_ids': set()
                }

            # Merge info
            canonical_to_node[canonical]['variants'].add(node_id)
            canonical_to_node[canonical]['occurrences'].extend(node.get('occurrences', []))
            canonical_to_node[canonical]['doc_ids'].add(node.get('doc_id', ''))

        # Convert sets to lists
        for node in canonical_to_node.values():
            node['variants'] = list(node['variants'])
            node['doc_ids'] = list(node['doc_ids'])

        return list(canonical_to_node.values())

    def _merge_aligned_edges(
        self,
        edges: List[Dict[str, Any]],
        alignment: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """更新边以使用规范实体名"""
        def get_canonical(entity: str) -> str:
            for canon, variants in alignment.items():
                if entity in variants:
                    return canon
            return entity

        merged_edges = []
        for edge in edges:
            edge['source'] = get_canonical(edge['source'])
            edge['target'] = get_canonical(edge['target'])
            merged_edges.append(edge)

        return merged_edges

    def _deduplicate_nodes(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重节点"""
        unique = {}
        for node in nodes:
            node_id = node['id']
            if node_id not in unique:
                unique[node_id] = node
            else:
                # Merge occurrences
                unique[node_id].setdefault('occurrences', []).extend(node.get('occurrences', []))
                unique[node_id].setdefault('doc_ids', set()).update(node.get('doc_ids', set()))

        return list(unique.values())

    def _deduplicate_edges(self, edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重边并合并权重"""
        edge_map = {}

        for edge in edges:
            key = (edge['source'], edge['target'], edge['type'])

            if key not in edge_map:
                edge_map[key] = edge
                edge_map[key]['count'] = 1
            else:
                # Aggregate strength
                edge_map[key]['strength'] = max(
                    edge_map[key].get('strength', 0),
                    edge.get('strength', 0)
                )
                edge_map[key]['count'] += 1

        return list(edge_map.values())

    def _export_graphml(self, graph_data: Dict[str, Any]) -> str:
        """导出为 GraphML 格式"""
        # Simplified GraphML export
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])

        graphml = ['<?xml version="1.0" encoding="UTF-8"?>']
        graphml.append('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">')
        graphml.append('  <graph id="KnowledgeGraph" edgedefault="undirected">')

        # Nodes
        for node in nodes:
            graphml.append(f'    <node id="{node["id"]}">')
            graphml.append(f'      <data key="type">{node.get("type", "unknown")}</data>')
            graphml.append('    </node>')

        # Edges
        for i, edge in enumerate(edges):
            graphml.append(f'    <edge id="e{i}" source="{edge["source"]}" target="{edge["target"]}">')
            graphml.append(f'      <data key="type">{edge.get("type", "related_to")}</data>')
            graphml.append(f'      <data key="strength">{edge.get("strength", 1.0)}</data>')
            graphml.append('    </edge>')

        graphml.append('  </graph>')
        graphml.append('</graphml>')

        return '\n'.join(graphml)

    def _export_cytoscape(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """导出为 Cytoscape.js 格式"""
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])

        cytoscape_data = {
            'elements': {
                'nodes': [
                    {
                        'data': {
                            'id': node['id'],
                            'label': node['id'],
                            'type': node.get('type', 'unknown')
                        }
                    }
                    for node in nodes
                ],
                'edges': [
                    {
                        'data': {
                            'id': f"{edge['source']}-{edge['target']}",
                            'source': edge['source'],
                            'target': edge['target'],
                            'type': edge.get('type', 'related_to'),
                            'strength': edge.get('strength', 1.0)
                        }
                    }
                    for edge in edges
                ]
            }
        }

        return cytoscape_data


# Convenience function for quick usage
def create_knowledge_graph(
    content: str,
    doc_id: Optional[str] = None,
    use_jieba: bool = True
) -> Dict[str, Any]:
    """
    快速创建知识图谱（单文档）

    Usage:
        graph = create_knowledge_graph(document_text)
    """
    engine = UnifiedKnowledgeGraphEngine(use_jieba=use_jieba)
    return engine.build_graph_from_document(
        doc_id=doc_id or f"doc_{datetime.now().timestamp()}",
        content=content
    )

