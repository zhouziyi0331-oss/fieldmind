"""
Step 9: 阅读器生成服务
Reader Generation Service

功能：
1. 时间轴视图生成
2. 主题聚类视图
3. 人物网络图
4. Wiki 页面生成
"""

import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict, Counter
import json

logger = logging.getLogger(__name__)


@dataclass
class TimelineEvent:
    """时间轴事件"""
    id: str
    title: str
    time: str  # 时间标签
    description: str
    participants: List[str] = field(default_factory=list)
    location: Optional[str] = None
    importance: float = 0.5
    event_type: str = ""


@dataclass
class TopicCluster:
    """主题聚类"""
    id: str
    name: str
    keywords: List[str]
    knowledge_units: List[str]  # 知识单元ID列表
    size: int = 0
    importance: float = 0.5


@dataclass
class NetworkNode:
    """网络节点"""
    id: str
    name: str
    type: str  # person, organization, location, etc.
    size: float = 1.0  # 节点大小（重要性）
    group: str = ""  # 分组


@dataclass
class NetworkLink:
    """网络连接"""
    source: str  # 源节点ID
    target: str  # 目标节点ID
    type: str  # 关系类型
    strength: float = 1.0  # 连接强度
    label: Optional[str] = None


@dataclass
class WikiPage:
    """Wiki 页面"""
    id: str
    title: str
    content: str  # Markdown 格式
    category: str
    related_pages: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class ReaderOutput:
    """阅读器输出"""
    timeline: List[TimelineEvent]
    topics: List[TopicCluster]
    network: Dict[str, Any]  # {nodes: [], links: []}
    wiki_pages: List[WikiPage]
    metadata: Dict[str, Any] = field(default_factory=dict)


class TimelineGenerator:
    """时间轴生成器"""

    def generate(self, events: List[Any], entities: List[Any]) -> List[TimelineEvent]:
        """生成时间轴"""
        timeline = []

        for event in events:
            if not hasattr(event, 'id'):
                continue

            # 提取时间
            time_label = "未知时间"
            if hasattr(event, 'when') and event.when:
                time_label = event.when[0] if event.when else "未知时间"

            # 提取参与者
            participants = []
            if hasattr(event, 'who') and event.who:
                participants = event.who

            # 提取地点
            location = None
            if hasattr(event, 'where') and event.where:
                location = event.where[0] if event.where else None

            # 创建时间轴事件
            timeline_event = TimelineEvent(
                id=event.id,
                title=event.trigger if hasattr(event, 'trigger') else "事件",
                time=time_label,
                description=event.what if hasattr(event, 'what') else "",
                participants=participants,
                location=location,
                importance=event.confidence if hasattr(event, 'confidence') else 0.5,
                event_type=event.type.value if hasattr(event, 'type') else "other"
            )
            timeline.append(timeline_event)

        # 按时间排序（简化版：按ID排序）
        timeline.sort(key=lambda e: e.time)

        logger.info(f"✅ 时间轴生成：{len(timeline)} 个事件")
        return timeline


class TopicClusterer:
    """主题聚类器"""

    def cluster(self, knowledge_units: List[Any]) -> List[TopicCluster]:
        """知识单元主题聚类"""
        # 按标签聚类
        tag_clusters = defaultdict(list)

        for unit in knowledge_units:
            if not hasattr(unit, 'tags') or not unit.tags:
                tag_clusters['其他'].append(unit)
            else:
                for tag in unit.tags:
                    tag_clusters[tag].append(unit)

        # 创建主题聚类
        clusters = []
        cluster_id = 0

        for tag, units in tag_clusters.items():
            if len(units) < 1:
                continue

            # 提取关键词
            keywords = self._extract_keywords(units)

            # 计算重要性
            avg_importance = sum(u.importance for u in units if hasattr(u, 'importance')) / len(units)

            cluster = TopicCluster(
                id=f"topic_{cluster_id}",
                name=tag,
                keywords=keywords,
                knowledge_units=[u.id for u in units if hasattr(u, 'id')],
                size=len(units),
                importance=avg_importance
            )
            clusters.append(cluster)
            cluster_id += 1

        # 按大小排序
        clusters.sort(key=lambda c: c.size, reverse=True)

        logger.info(f"✅ 主题聚类：{len(clusters)} 个主题")
        return clusters

    def _extract_keywords(self, units: List[Any]) -> List[str]:
        """提取关键词"""
        all_text = " ".join(
            u.content for u in units
            if hasattr(u, 'content') and u.content
        )

        # 简化版：提取标签
        all_tags = []
        for unit in units:
            if hasattr(unit, 'tags'):
                all_tags.extend(unit.tags)

        # 统计频率
        tag_freq = Counter(all_tags)
        keywords = [tag for tag, _ in tag_freq.most_common(10)]

        return keywords


class PersonNetworkBuilder:
    """人物网络构建器"""

    def build(
        self,
        entities: List[Any],
        relations: List[Any]
    ) -> Dict[str, Any]:
        """构建人物网络图"""
        nodes = []
        links = []

        # 创建节点
        entity_dict = {}
        for entity in entities:
            if not hasattr(entity, 'id') or not hasattr(entity, 'name'):
                continue

            entity_type = entity.type.value if hasattr(entity, 'type') else 'other'

            # 计算节点大小（基于关联数）
            related_count = len(entity.mentions) if hasattr(entity, 'mentions') else 1
            node_size = min(1 + related_count * 0.1, 5.0)

            node = NetworkNode(
                id=entity.id,
                name=entity.name,
                type=entity_type,
                size=node_size,
                group=entity_type
            )
            nodes.append(node)
            entity_dict[entity.id] = node

        # 创建连接
        for relation in relations:
            if not (hasattr(relation, 'source_id') and hasattr(relation, 'target_id')):
                continue

            # 检查节点是否存在
            if relation.source_id not in entity_dict or relation.target_id not in entity_dict:
                continue

            rel_type = relation.type.value if hasattr(relation, 'type') else 'related'
            rel_label = self._relation_to_label(rel_type)

            link = NetworkLink(
                source=relation.source_id,
                target=relation.target_id,
                type=rel_type,
                strength=relation.confidence if hasattr(relation, 'confidence') else 1.0,
                label=rel_label
            )
            links.append(link)

        # 转为字典格式（用于前端可视化）
        network = {
            'nodes': [
                {
                    'id': n.id,
                    'name': n.name,
                    'type': n.type,
                    'size': n.size,
                    'group': n.group
                }
                for n in nodes
            ],
            'links': [
                {
                    'source': l.source,
                    'target': l.target,
                    'type': l.type,
                    'strength': l.strength,
                    'label': l.label
                }
                for l in links
            ]
        }

        logger.info(f"✅ 人物网络构建：{len(nodes)} 个节点，{len(links)} 个连接")
        return network

    def _relation_to_label(self, rel_type: str) -> str:
        """关系类型转标签"""
        mapping = {
            'family': '家人',
            'colleague': '同事',
            'teacher_student': '师生',
            'friend': '朋友',
            'member_of': '成员',
            'superior_subordinate': '上下级',
        }
        return mapping.get(rel_type, rel_type)


class WikiPageGenerator:
    """Wiki 页面生成器"""

    def generate(
        self,
        entities: List[Any],
        events: List[Any],
        knowledge_units: List[Any],
        relations: List[Any]
    ) -> List[WikiPage]:
        """生成 Wiki 页面"""
        pages = []
        page_id = 0

        # 1. 为每个实体创建页面
        for entity in entities:
            if not hasattr(entity, 'name'):
                continue

            content = self._generate_entity_page(entity, relations, events)

            page = WikiPage(
                id=f"wiki_{page_id}",
                title=entity.name,
                content=content,
                category=entity.type.value if hasattr(entity, 'type') else 'entity',
                tags=[entity.type.value] if hasattr(entity, 'type') else []
            )
            pages.append(page)
            page_id += 1

        # 2. 为每个事件创建页面
        for event in events:
            if not hasattr(event, 'trigger'):
                continue

            content = self._generate_event_page(event, entities, relations)

            page = WikiPage(
                id=f"wiki_{page_id}",
                title=event.trigger,
                content=content,
                category='event',
                tags=[event.type.value] if hasattr(event, 'type') else []
            )
            pages.append(page)
            page_id += 1

        # 3. 创建主题索引页面
        index_page = self._generate_index_page(pages)
        pages.insert(0, index_page)

        # 4. 建立页面间链接
        self._link_pages(pages)

        logger.info(f"✅ Wiki 页面生成：{len(pages)} 个页面")
        return pages

    def _generate_entity_page(
        self,
        entity: Any,
        relations: List[Any],
        events: List[Any]
    ) -> str:
        """生成实体页面（Markdown）"""
        content = f"# {entity.name}\n\n"

        # 基本信息
        if hasattr(entity, 'type'):
            content += f"**类型**: {entity.type.value}\n\n"

        # 别名
        if hasattr(entity, 'aliases') and entity.aliases:
            aliases = ', '.join(entity.aliases)
            content += f"**别名**: {aliases}\n\n"

        # 描述
        content += "## 描述\n\n"
        if hasattr(entity, 'description') and entity.description:
            content += f"{entity.description}\n\n"
        else:
            content += f"{entity.name}是一个{entity.type.value if hasattr(entity, 'type') else '实体'}。\n\n"

        # 关系
        related_rels = [
            r for r in relations
            if hasattr(r, 'source_id') and (r.source_id == entity.id or r.target_id == entity.id)
        ]

        if related_rels:
            content += "## 相关关系\n\n"
            for rel in related_rels[:10]:  # 最多10个
                if hasattr(rel, 'source_name') and hasattr(rel, 'target_name'):
                    if rel.source_id == entity.id:
                        content += f"- {entity.name} → [[{rel.target_name}]] ({rel.type.value if hasattr(rel, 'type') else '相关'})\n"
                    else:
                        content += f"- [[{rel.source_name}]] → {entity.name} ({rel.type.value if hasattr(rel, 'type') else '相关'})\n"
            content += "\n"

        # 参与的事件
        related_events = [
            e for e in events
            if hasattr(e, 'who') and entity.name in e.who
        ]

        if related_events:
            content += "## 参与的事件\n\n"
            for event in related_events[:10]:
                event_title = event.trigger if hasattr(event, 'trigger') else '事件'
                content += f"- [[{event_title}]]\n"
            content += "\n"

        return content

    def _generate_event_page(
        self,
        event: Any,
        entities: List[Any],
        relations: List[Any]
    ) -> str:
        """生成事件页面（Markdown）"""
        content = f"# {event.trigger}\n\n"

        # 事件类型
        if hasattr(event, 'type'):
            content += f"**类型**: {event.type.value}\n\n"

        # 5W1H
        content += "## 事件详情\n\n"

        if hasattr(event, 'who') and event.who:
            content += f"**参与者**: {', '.join(f'[[{name}]]' for name in event.who)}\n\n"

        if hasattr(event, 'when') and event.when:
            content += f"**时间**: {', '.join(event.when)}\n\n"

        if hasattr(event, 'where') and event.where:
            content += f"**地点**: {', '.join(f'[[{loc}]]' for loc in event.where)}\n\n"

        if hasattr(event, 'what') and event.what:
            content += f"**描述**: {event.what}\n\n"

        if hasattr(event, 'why') and event.why:
            content += f"**原因**: {event.why}\n\n"

        if hasattr(event, 'how') and event.how:
            content += f"**方式**: {event.how}\n\n"

        return content

    def _generate_index_page(self, pages: List[WikiPage]) -> WikiPage:
        """生成索引页面"""
        content = "# 知识库索引\n\n"

        # 按类别分组
        by_category = defaultdict(list)
        for page in pages:
            by_category[page.category].append(page)

        # 生成目录
        for category, category_pages in sorted(by_category.items()):
            content += f"## {category}\n\n"
            for page in sorted(category_pages, key=lambda p: p.title):
                content += f"- [[{page.title}]]\n"
            content += "\n"

        return WikiPage(
            id="wiki_index",
            title="知识库索引",
            content=content,
            category="index",
            tags=['index']
        )

    def _link_pages(self, pages: List[WikiPage]):
        """建立页面间链接"""
        # 提取所有 [[链接]]
        import re
        link_pattern = r'\[\[([^\]]+)\]\]'

        page_dict = {p.title: p for p in pages}

        for page in pages:
            links = re.findall(link_pattern, page.content)
            for link in links:
                if link in page_dict:
                    page.related_pages.append(page_dict[link].id)


class ReaderGenerationService:
    """阅读器生成服务"""

    def __init__(self):
        self.timeline_generator = TimelineGenerator()
        self.topic_clusterer = TopicClusterer()
        self.network_builder = PersonNetworkBuilder()
        self.wiki_generator = WikiPageGenerator()

    async def generate(
        self,
        entities: List[Any],
        relations: List[Any],
        events: List[Any],
        knowledge_units: List[Any]
    ) -> Dict[str, Any]:
        """
        生成阅读器

        Args:
            entities: 实体列表
            relations: 关系列表
            events: 事件列表
            knowledge_units: 知识单元列表

        Returns:
            阅读器生成结果
        """
        logger.info(f"开始生成阅读器")

        # 并行生成各个视图
        timeline, topics, network, wiki_pages = await asyncio.gather(
            asyncio.to_thread(self.timeline_generator.generate, events, entities),
            asyncio.to_thread(self.topic_clusterer.cluster, knowledge_units),
            asyncio.to_thread(self.network_builder.build, entities, relations),
            asyncio.to_thread(self.wiki_generator.generate, entities, events, knowledge_units, relations)
        )

        # 创建输出对象
        reader_output = ReaderOutput(
            timeline=timeline,
            topics=topics,
            network=network,
            wiki_pages=wiki_pages,
            metadata={
                'timeline_events': len(timeline),
                'topic_clusters': len(topics),
                'network_nodes': len(network['nodes']),
                'network_links': len(network['links']),
                'wiki_pages': len(wiki_pages),
            }
        )

        # 转为字典
        result = {
            'timeline': [
                {
                    'id': e.id,
                    'title': e.title,
                    'time': e.time,
                    'description': e.description,
                    'participants': e.participants,
                    'location': e.location,
                    'importance': e.importance,
                    'event_type': e.event_type
                }
                for e in timeline
            ],
            'topics': [
                {
                    'id': t.id,
                    'name': t.name,
                    'keywords': t.keywords,
                    'knowledge_units': t.knowledge_units,
                    'size': t.size,
                    'importance': t.importance
                }
                for t in topics
            ],
            'network': network,
            'wiki_pages': [
                {
                    'id': p.id,
                    'title': p.title,
                    'content': p.content,
                    'category': p.category,
                    'related_pages': p.related_pages,
                    'tags': p.tags
                }
                for p in wiki_pages
            ],
            'metadata': reader_output.metadata
        }

        logger.info(f"✅ 阅读器生成完成")
        return result
