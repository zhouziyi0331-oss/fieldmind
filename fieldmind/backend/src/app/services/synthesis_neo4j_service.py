"""
SynthesisAgent的Neo4j驾驭工程集成服务
负责将综合记忆转换为Neo4j知识图谱结构

核心功能：
1. 脉络树构建 (Context Tree): 大脉络 → 子脉络层级结构
2. 时间线构建 (Timeline): 事件时序关系
3. 主题图谱构建 (Theme Graph): 概念关联网络
4. 关键词网络 (Keyword Network): 关键术语关系
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from app.services.graph_database_integration_v2 import GraphDatabaseIntegrationV2

logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================

@dataclass
class ContextNode:
    """脉络节点"""
    context_id: str
    project_id: int
    title: str
    description: str
    level: int  # 0=根脉络, 1=一级子脉络, 2=二级子脉络...
    parent_id: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None


@dataclass
class TimelineEvent:
    """时间线事件"""
    event_id: str
    project_id: int
    timestamp: datetime
    event_type: str  # e.g., "document_added", "insight_generated", "skill_updated"
    title: str
    description: str
    related_entities: List[str] = None  # 关联的实体ID列表
    metadata: Dict[str, Any] = None


@dataclass
class ThemeNode:
    """主题节点"""
    theme_id: str
    project_id: int
    name: str
    description: str
    importance: float  # 0.0-1.0, 主题重要性评分
    related_keywords: List[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class KeywordNode:
    """关键词节点"""
    keyword: str
    project_id: int
    frequency: int  # 出现频率
    context_ids: List[str] = None  # 所属脉络
    metadata: Dict[str, Any] = None


# ==================== 主服务类 ====================

class SynthesisNeo4jService:
    """
    SynthesisAgent的Neo4j图谱集成服务

    与驾驭工程(GraphDatabaseIntegrationV2)深度结合，
    将记忆综合结果转换为结构化知识图谱。
    """

    def __init__(self):
        """初始化服务"""
        self.neo4j_service = GraphDatabaseIntegrationV2()
        logger.info("✅ SynthesisNeo4jService初始化完成")

    # ==================== 脉络树构建 ====================

    def create_context_tree(
        self,
        project_id: int,
        root_context: ContextNode,
        sub_contexts: List[ContextNode]
    ) -> Dict[str, Any]:
        """
        构建脉络树：大脉络 → 子脉络的层级结构

        Args:
            project_id: 项目ID
            root_context: 根脉络节点
            sub_contexts: 子脉络列表

        Returns:
            创建结果统计
        """
        logger.info(f"🌲 开始构建脉络树: 项目{project_id}, 根脉络={root_context.title}")

        created_nodes = 0
        created_relationships = 0

        try:
            # 1. 创建根脉络节点
            root_props = {
                'context_id': root_context.context_id,
                'project_id': project_id,
                'title': root_context.title,
                'description': root_context.description,
                'level': 0,
                'created_at': root_context.created_at.isoformat() if root_context.created_at else datetime.utcnow().isoformat(),
                'metadata': root_context.metadata or {}
            }

            self.neo4j_service.create_node(
                labels=['Context', 'RootContext'],
                properties=root_props
            )
            created_nodes += 1
            logger.info(f"  ✅ 创建根脉络: {root_context.title}")

            # 2. 创建子脉络并建立层级关系
            for sub_context in sub_contexts:
                sub_props = {
                    'context_id': sub_context.context_id,
                    'project_id': project_id,
                    'title': sub_context.title,
                    'description': sub_context.description,
                    'level': sub_context.level,
                    'parent_id': sub_context.parent_id or root_context.context_id,
                    'created_at': sub_context.created_at.isoformat() if sub_context.created_at else datetime.utcnow().isoformat(),
                    'metadata': sub_context.metadata or {}
                }

                # 创建子脉络节点
                self.neo4j_service.create_node(
                    labels=['Context', 'SubContext'],
                    properties=sub_props
                )
                created_nodes += 1

                # 建立父子关系
                parent_id = sub_context.parent_id or root_context.context_id
                self.neo4j_service.create_relationship(
                    start_node_id=parent_id,
                    end_node_id=sub_context.context_id,
                    relationship_type='HAS_SUB_CONTEXT',
                    properties={
                        'created_at': datetime.utcnow().isoformat(),
                        'level_diff': 1
                    }
                )
                created_relationships += 1

            logger.info(f"✅ 脉络树构建完成: {created_nodes}个节点, {created_relationships}个关系")

            return {
                'success': True,
                'root_context_id': root_context.context_id,
                'nodes_created': created_nodes,
                'relationships_created': created_relationships
            }

        except Exception as e:
            logger.error(f"❌ 脉络树构建失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'nodes_created': created_nodes,
                'relationships_created': created_relationships
            }

    def query_context_tree(self, project_id: int, root_context_id: str) -> Dict[str, Any]:
        """
        查询完整脉络树结构

        Args:
            project_id: 项目ID
            root_context_id: 根脉络ID

        Returns:
            树状结构数据
        """
        query = """
        MATCH path = (root:RootContext {project_id: $project_id, context_id: $root_id})
                     -[:HAS_SUB_CONTEXT*0..5]->(sub:Context)
        RETURN root, collect(DISTINCT sub) as sub_contexts,
               collect(DISTINCT relationships(path)) as relationships
        """

        result = self.neo4j_service.execute_query(
            query,
            {'project_id': project_id, 'root_id': root_context_id}
        )

        return result

    # ==================== 时间线构建 ====================

    def create_timeline(
        self,
        project_id: int,
        events: List[TimelineEvent]
    ) -> Dict[str, Any]:
        """
        构建时间线：按时序创建事件节点及NEXT关系

        Args:
            project_id: 项目ID
            events: 事件列表（应已按时间排序）

        Returns:
            创建结果统计
        """
        logger.info(f"⏰ 开始构建时间线: 项目{project_id}, {len(events)}个事件")

        created_nodes = 0
        created_relationships = 0

        try:
            # 按时间排序
            sorted_events = sorted(events, key=lambda e: e.timestamp)

            # 创建事件节点
            for event in sorted_events:
                event_props = {
                    'event_id': event.event_id,
                    'project_id': project_id,
                    'timestamp': event.timestamp.isoformat(),
                    'event_type': event.event_type,
                    'title': event.title,
                    'description': event.description,
                    'related_entities': event.related_entities or [],
                    'metadata': event.metadata or {}
                }

                self.neo4j_service.create_node(
                    labels=['TimelineEvent', event.event_type],
                    properties=event_props
                )
                created_nodes += 1

            # 建立时序关系 (NEXT)
            for i in range(len(sorted_events) - 1):
                current_event = sorted_events[i]
                next_event = sorted_events[i + 1]

                time_diff = (next_event.timestamp - current_event.timestamp).total_seconds()

                self.neo4j_service.create_relationship(
                    start_node_id=current_event.event_id,
                    end_node_id=next_event.event_id,
                    relationship_type='NEXT',
                    properties={
                        'time_diff_seconds': time_diff,
                        'created_at': datetime.utcnow().isoformat()
                    }
                )
                created_relationships += 1

            logger.info(f"✅ 时间线构建完成: {created_nodes}个事件, {created_relationships}个时序关系")

            return {
                'success': True,
                'events_created': created_nodes,
                'temporal_links': created_relationships,
                'time_span': {
                    'start': sorted_events[0].timestamp.isoformat() if sorted_events else None,
                    'end': sorted_events[-1].timestamp.isoformat() if sorted_events else None
                }
            }

        except Exception as e:
            logger.error(f"❌ 时间线构建失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def query_timeline(
        self,
        project_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        查询时间线事件

        Args:
            project_id: 项目ID
            start_time: 起始时间（可选）
            end_time: 结束时间（可选）
            event_type: 事件类型过滤（可选）

        Returns:
            事件列表
        """
        conditions = ['e.project_id = $project_id']
        params = {'project_id': project_id}

        if start_time:
            conditions.append('e.timestamp >= $start_time')
            params['start_time'] = start_time.isoformat()

        if end_time:
            conditions.append('e.timestamp <= $end_time')
            params['end_time'] = end_time.isoformat()

        if event_type:
            conditions.append('e.event_type = $event_type')
            params['event_type'] = event_type

        where_clause = ' AND '.join(conditions)

        query = f"""
        MATCH (e:TimelineEvent)
        WHERE {where_clause}
        OPTIONAL MATCH (e)-[r:NEXT]->(next:TimelineEvent)
        RETURN e, next, r
        ORDER BY e.timestamp ASC
        """

        result = self.neo4j_service.execute_query(query, params)
        return result

    # ==================== 主题图谱构建 ====================

    def create_theme_graph(
        self,
        project_id: int,
        themes: List[ThemeNode],
        relationships: List[Dict[str, Any]]  # [{'from': theme_id, 'to': theme_id, 'type': str, 'weight': float}]
    ) -> Dict[str, Any]:
        """
        构建主题图谱：概念之间的关联网络

        Args:
            project_id: 项目ID
            themes: 主题节点列表
            relationships: 主题间关系列表

        Returns:
            创建结果统计
        """
        logger.info(f"🎨 开始构建主题图谱: 项目{project_id}, {len(themes)}个主题")

        created_nodes = 0
        created_relationships = 0

        try:
            # 1. 创建主题节点
            for theme in themes:
                theme_props = {
                    'theme_id': theme.theme_id,
                    'project_id': project_id,
                    'name': theme.name,
                    'description': theme.description,
                    'importance': theme.importance,
                    'related_keywords': theme.related_keywords or [],
                    'metadata': theme.metadata or {}
                }

                self.neo4j_service.create_node(
                    labels=['Theme', 'Concept'],
                    properties=theme_props
                )
                created_nodes += 1

            # 2. 创建主题间关系
            for rel in relationships:
                self.neo4j_service.create_relationship(
                    start_node_id=rel['from'],
                    end_node_id=rel['to'],
                    relationship_type=rel.get('type', 'RELATES_TO'),
                    properties={
                        'weight': rel.get('weight', 0.5),
                        'created_at': datetime.utcnow().isoformat()
                    }
                )
                created_relationships += 1

            logger.info(f"✅ 主题图谱构建完成: {created_nodes}个主题, {created_relationships}个关联")

            return {
                'success': True,
                'themes_created': created_nodes,
                'relationships_created': created_relationships
            }

        except Exception as e:
            logger.error(f"❌ 主题图谱构建失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def query_theme_graph(
        self,
        project_id: int,
        center_theme_id: Optional[str] = None,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        查询主题图谱

        Args:
            project_id: 项目ID
            center_theme_id: 中心主题ID（可选，如不提供则返回所有主题）
            max_depth: 最大关联深度

        Returns:
            主题网络数据
        """
        if center_theme_id:
            query = f"""
            MATCH path = (center:Theme {{project_id: $project_id, theme_id: $theme_id}})
                         -[:RELATES_TO*0..{max_depth}]-(related:Theme)
            RETURN center, collect(DISTINCT related) as related_themes,
                   collect(DISTINCT relationships(path)) as relationships
            """
            params = {'project_id': project_id, 'theme_id': center_theme_id}
        else:
            query = """
            MATCH (t:Theme {project_id: $project_id})
            OPTIONAL MATCH (t)-[r:RELATES_TO]-(other:Theme)
            RETURN collect(DISTINCT t) as themes, collect(DISTINCT r) as relationships
            """
            params = {'project_id': project_id}

        result = self.neo4j_service.execute_query(query, params)
        return result

    # ==================== 关键词网络 ====================

    def create_keyword_network(
        self,
        project_id: int,
        keywords: List[KeywordNode],
        co_occurrences: List[Dict[str, Any]]  # [{'keyword1': str, 'keyword2': str, 'count': int}]
    ) -> Dict[str, Any]:
        """
        构建关键词网络：关键词共现关系

        Args:
            project_id: 项目ID
            keywords: 关键词节点列表
            co_occurrences: 共现关系列表

        Returns:
            创建结果统计
        """
        logger.info(f"🔑 开始构建关键词网络: 项目{project_id}, {len(keywords)}个关键词")

        created_nodes = 0
        created_relationships = 0

        try:
            # 1. 创建关键词节点
            for kw in keywords:
                kw_props = {
                    'keyword': kw.keyword,
                    'project_id': project_id,
                    'frequency': kw.frequency,
                    'context_ids': kw.context_ids or [],
                    'metadata': kw.metadata or {}
                }

                self.neo4j_service.create_node(
                    labels=['Keyword'],
                    properties=kw_props
                )
                created_nodes += 1

            # 2. 创建共现关系
            for co_occur in co_occurrences:
                self.neo4j_service.create_relationship(
                    start_node_id=co_occur['keyword1'],
                    end_node_id=co_occur['keyword2'],
                    relationship_type='CO_OCCURS_WITH',
                    properties={
                        'count': co_occur['count'],
                        'created_at': datetime.utcnow().isoformat()
                    }
                )
                created_relationships += 1

            logger.info(f"✅ 关键词网络构建完成: {created_nodes}个关键词, {created_relationships}个共现关系")

            return {
                'success': True,
                'keywords_created': created_nodes,
                'co_occurrences': created_relationships
            }

        except Exception as e:
            logger.error(f"❌ 关键词网络构建失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def query_keyword_network(
        self,
        project_id: int,
        keyword: Optional[str] = None,
        min_frequency: int = 1
    ) -> Dict[str, Any]:
        """
        查询关键词网络

        Args:
            project_id: 项目ID
            keyword: 中心关键词（可选）
            min_frequency: 最小频率过滤

        Returns:
            关键词网络数据
        """
        if keyword:
            query = """
            MATCH (k:Keyword {project_id: $project_id, keyword: $keyword})
            OPTIONAL MATCH (k)-[r:CO_OCCURS_WITH]-(related:Keyword)
            WHERE related.frequency >= $min_freq
            RETURN k, collect(DISTINCT related) as related_keywords,
                   collect(DISTINCT r) as co_occurrences
            """
            params = {'project_id': project_id, 'keyword': keyword, 'min_freq': min_frequency}
        else:
            query = """
            MATCH (k:Keyword {project_id: $project_id})
            WHERE k.frequency >= $min_freq
            OPTIONAL MATCH (k)-[r:CO_OCCURS_WITH]-(other:Keyword)
            RETURN collect(DISTINCT k) as keywords, collect(DISTINCT r) as co_occurrences
            ORDER BY k.frequency DESC
            """
            params = {'project_id': project_id, 'min_freq': min_frequency}

        result = self.neo4j_service.execute_query(query, params)
        return result

    # ==================== 综合查询方法 ====================

    def get_project_knowledge_graph(self, project_id: int) -> Dict[str, Any]:
        """
        获取项目完整知识图谱概览

        包含：脉络树、时间线、主题图谱、关键词网络的统计信息

        Args:
            project_id: 项目ID

        Returns:
            知识图谱概览数据
        """
        logger.info(f"📊 获取项目{project_id}的知识图谱概览")

        try:
            # 统计各类节点和关系数量
            stats_query = """
            MATCH (n)
            WHERE n.project_id = $project_id
            WITH labels(n) as node_labels
            UNWIND node_labels as label
            RETURN label, count(*) as count
            """

            stats_result = self.neo4j_service.execute_query(stats_query, {'project_id': project_id})

            return {
                'project_id': project_id,
                'timestamp': datetime.utcnow().isoformat(),
                'statistics': stats_result,
                'components': {
                    'context_tree': '脉络树',
                    'timeline': '时间线',
                    'theme_graph': '主题图谱',
                    'keyword_network': '关键词网络'
                }
            }

        except Exception as e:
            logger.error(f"❌ 获取知识图谱概览失败: {e}", exc_info=True)
            return {
                'error': str(e)
            }


# ==================== 工厂函数 ====================

def get_synthesis_neo4j_service() -> SynthesisNeo4jService:
    """获取SynthesisNeo4jService实例"""
    return SynthesisNeo4jService()
