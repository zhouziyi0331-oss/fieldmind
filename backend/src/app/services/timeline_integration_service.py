"""
时间线集成服务 (Timeline Integration Service)

功能：
1. 历任村支书时间序列（组织继任关系）
2. 事件时间线构建（按时间排序）
3. 与知识图谱联动（时间线 → 图谱节点）
4. 时间区间查询（查询某时间段的事件/人物）
5. 时间线可视化导出

设计原则：
- 支持精确时间（年月日）和模糊时间（约1990年代）
- 历任关系清晰标注（第一代、第二代、第三代...）
- 与知识图谱双向关联
- 所有标注都是中文
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, date
from collections import defaultdict
from app.core.logging import logger
from pydantic import BaseModel, Field

from app.models.knowledge_graph import (
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeType,
)


class TimelineEvent(BaseModel):
    """时间线事件"""
    event_id: str = Field(..., description="事件ID")
    event_name: str = Field(..., description="事件名称（中文）")
    event_type: str = Field(..., description="事件类型：人事变动/民俗活动/历史事件")

    # 时间信息
    start_time: Optional[datetime] = Field(None, description="开始时间（精确）")
    end_time: Optional[datetime] = Field(None, description="结束时间（精确）")
    year: Optional[int] = Field(None, description="年份（模糊时间）")
    decade: Optional[str] = Field(None, description="年代（如'1990年代'）")
    time_precision: str = Field("year", description="时间精度：year/month/day/decade")

    # 关联信息
    related_nodes: List[str] = Field(default_factory=list, description="相关图谱节点ID")
    related_documents: List[str] = Field(default_factory=list, description="相关调研文件")
    related_skills: List[str] = Field(default_factory=list, description="相关Skills")

    # 描述
    description: str = Field("", description="事件描述")
    evidence: List[str] = Field(default_factory=list, description="证据来源")

    # 元数据
    importance: float = Field(0.5, ge=0.0, le=1.0, description="重要性")
    project_name: str = Field("", description="所属项目")


class SuccessionChain(BaseModel):
    """继任链（历任村支书、历任会长等）"""
    chain_id: str = Field(..., description="继任链ID")
    position_name: str = Field(..., description="职位名称（如'村支书'）")
    organization: str = Field(..., description="所属组织（如'XX村委会'）")

    # 历任人员
    succession_list: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="历任列表：[{person_id, name, generation, start_year, end_year}]"
    )

    total_generations: int = Field(0, description="总代数")
    span_years: int = Field(0, description="跨越年数")


class TimelineQueryResult(BaseModel):
    """时间线查询结果"""
    query_type: str = Field(..., description="查询类型")
    time_range: Dict[str, Any] = Field(..., description="时间区间")

    events: List[TimelineEvent] = Field(default_factory=list, description="事件列表")
    total_events: int = Field(0, description="事件总数")

    # 按类型统计
    event_type_stats: Dict[str, int] = Field(default_factory=dict, description="事件类型统计")


class TimelineVisualizationExport(BaseModel):
    """时间线可视化导出格式"""
    timeline_name: str = Field(..., description="时间线名称")
    events: List[Dict[str, Any]] = Field(default_factory=list, description="事件数据")
    succession_chains: List[SuccessionChain] = Field(default_factory=list, description="继任链")

    # 时间范围
    min_year: Optional[int] = Field(None, description="最早年份")
    max_year: Optional[int] = Field(None, description="最晚年份")

    # 统计信息
    total_events: int = Field(0, description="事件总数")
    total_people: int = Field(0, description="涉及人数")


class TimelineIntegrationService:
    """
    时间线集成服务

    核心功能：
    1. 从图谱边提取时间信息
    2. 构建历任继任链
    3. 时间区间查询
    4. 与知识图谱双向关联
    """
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """初始化时间线服务"""
        self.events: Dict[str, TimelineEvent] = {}
        self.succession_chains: Dict[str, SuccessionChain] = {}

        logger.info("时间线集成服务初始化完成")


    def extract_timeline_from_graph(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        project_name: str = ""
    ) -> None:
        """
        从知识图谱提取时间线信息

        Args:
            nodes: 图谱节点列表
            edges: 图谱边列表
            project_name: 项目名称
        """
        logger.info(f"开始提取时间线: {len(edges)}条边")

        # 1. 从边的 temporal_info 提取事件
        for edge in edges:
            temporal_info = edge.temporal_info
            if not temporal_info:
                continue

            # 构建事件ID
            event_id = f"event_{edge.source}_{edge.target}_{edge.type.value}"

            # 获取节点名称
            source_node = next((n for n in nodes if n.id == edge.source), None)
            target_node = next((n for n in nodes if n.id == edge.target), None)

            if not source_node or not target_node:
                continue

            # 解析时间信息
            start_time = None
            end_time = None
            year = None
            decade = None
            time_precision = "year"

            # 支持多种时间格式
            if "year" in temporal_info:
                year = temporal_info["year"]
                start_time = datetime(year, 1, 1)
                time_precision = "year"

            if "start_year" in temporal_info:
                year = temporal_info["start_year"]
                start_time = datetime(year, 1, 1)

            if "end_year" in temporal_info:
                end_year = temporal_info["end_year"]
                end_time = datetime(end_year, 12, 31)

            if "decade" in temporal_info:
                decade = temporal_info["decade"]
                time_precision = "decade"

            # 构建事件名称
            event_name = f"{source_node.name} → {target_node.name} ({edge.type.value})"

            # 事件类型
            event_type = self._classify_event_type(edge.type)

            # 创建事件
            event = TimelineEvent(
                event_id=event_id,
                event_name=event_name,
                event_type=event_type,
                start_time=start_time,
                end_time=end_time,
                year=year,
                decade=decade,
                time_precision=time_precision,
                related_nodes=[edge.source, edge.target],
                related_documents=edge.source_documents if hasattr(edge, 'source_documents') else [],
                description=f"{edge.type.value}: {', '.join(edge.evidence[:2])}",
                evidence=edge.evidence,
                importance=edge.weight,
                project_name=project_name,
            )

            self.events[event_id] = event

        logger.info(f"提取完成: {len(self.events)}个时间线事件")


    def _classify_event_type(self, edge_type: EdgeType) -> str:
        """
        根据边类型分类事件类型

        Args:
            edge_type: 边类型

        Returns:
            事件类型（中文）
        """
        if edge_type in [EdgeType.ORGANIZATIONAL_SUCCESSION, EdgeType.POSITION_HELD]:
            return "人事变动"
        elif edge_type in [EdgeType.CULTURAL_INHERITANCE, EdgeType.SKILL_TRANSMISSION]:
            return "文化传承"
        elif edge_type in [EdgeType.PARTICIPATED_IN, EdgeType.ORGANIZED]:
            return "民俗活动"
        else:
            return "其他事件"


    def build_succession_chains(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge]
    ) -> List[SuccessionChain]:
        """
        构建历任继任链（如：历任村支书）

        算法：
        1. 找出所有 ORGANIZATIONAL_SUCCESSION 类型的边
        2. 按组织分组
        3. 按时间排序
        4. 标注代数（第一代、第二代...）

        Args:
            nodes: 图谱节点列表
            edges: 图谱边列表

        Returns:
            继任链列表
        """
        logger.info("开始构建继任链")

        # 找出所有继任关系边
        succession_edges = [
            e for e in edges
            if e.type == EdgeType.ORGANIZATIONAL_SUCCESSION
        ]

        if not succession_edges:
            logger.warning("未找到继任关系边")
            return []

        # 按组织分组（从边的证据或节点属性推断组织）
        org_groups = defaultdict(list)

        for edge in succession_edges:
            # 从证据中提取组织名称（简化处理）
            org_name = "默认组织"
            if edge.evidence:
                # 尝试从证据文本中提取组织名
                for evidence_text in edge.evidence:
                    if "村委会" in evidence_text:
                        org_name = "村委会"
                        break
                    elif "协会" in evidence_text:
                        org_name = "协会"
                        break

            org_groups[org_name].append(edge)

        # 为每个组织构建继任链
        chains = []

        for org_name, org_edges in org_groups.items():
            # 按时间排序
            sorted_edges = sorted(
                org_edges,
                key=lambda e: e.temporal_info.get("year", 0) if e.temporal_info else 0
            )

            # 构建继任列表
            succession_list = []
            for generation, edge in enumerate(sorted_edges, start=1):
                source_node = next((n for n in nodes if n.id == edge.source), None)
                target_node = next((n for n in nodes if n.id == edge.target), None)

                if not source_node or not target_node:
                    continue

                # 提取时间信息
                temporal = edge.temporal_info or {}
                start_year = temporal.get("start_year") or temporal.get("year")
                end_year = temporal.get("end_year")

                # 前任（source）
                if generation == 1:
                    succession_list.append({
                        "person_id": source_node.id,
                        "name": source_node.name,
                        "generation": generation,
                        "generation_label": f"第{generation}代",
                        "start_year": start_year,
                        "end_year": None,
                    })

                # 继任者（target）
                succession_list.append({
                    "person_id": target_node.id,
                    "name": target_node.name,
                    "generation": generation + 1,
                    "generation_label": f"第{generation + 1}代",
                    "start_year": start_year,
                    "end_year": end_year,
                })

            # 计算跨越年数
            years = [s["start_year"] for s in succession_list if s["start_year"]]
            span_years = max(years) - min(years) if len(years) >= 2 else 0

            # 创建继任链
            chain = SuccessionChain(
                chain_id=f"chain_{org_name}",
                position_name="村支书",  # TODO: 从边信息推断具体职位
                organization=org_name,
                succession_list=succession_list,
                total_generations=len(succession_list),
                span_years=span_years,
            )

            chains.append(chain)
            self.succession_chains[chain.chain_id] = chain

        logger.info(f"继任链构建完成: {len(chains)}条链")
        return chains


    def query_by_time_range(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        event_type: Optional[str] = None
    ) -> TimelineQueryResult:
        """
        按时间区间查询事件

        Args:
            start_year: 起始年份
            end_year: 结束年份
            event_type: 事件类型过滤

        Returns:
            查询结果
        """
        filtered_events = []

        for event in self.events.values():
            # 时间过滤
            if start_year and event.year and event.year < start_year:
                continue
            if end_year and event.year and event.year > end_year:
                continue

            # 类型过滤
            if event_type and event.event_type != event_type:
                continue

            filtered_events.append(event)

        # 按时间排序
        filtered_events.sort(key=lambda e: e.year or 0)

        # 统计事件类型
        type_stats = defaultdict(int)
        for event in filtered_events:
            type_stats[event.event_type] += 1

        result = TimelineQueryResult(
            query_type="时间区间查询",
            time_range={
                "start_year": start_year,
                "end_year": end_year,
                "event_type": event_type,
            },
            events=filtered_events,
            total_events=len(filtered_events),
            event_type_stats=dict(type_stats),
        )

        logger.info(
            f"时间区间查询: {start_year}-{end_year}, "
            f"找到{len(filtered_events)}个事件"
        )

        return result


    def query_by_person(
        self,
        person_id: str,
        person_name: str = ""
    ) -> TimelineQueryResult:
        """
        查询某人物相关的所有时间线事件

        Args:
            person_id: 人物节点ID
            person_name: 人物名称（用于日志）

        Returns:
            查询结果
        """
        related_events = [
            event for event in self.events.values()
            if person_id in event.related_nodes
        ]

        # 按时间排序
        related_events.sort(key=lambda e: e.year or 0)

        result = TimelineQueryResult(
            query_type="人物时间线查询",
            time_range={"person_id": person_id, "person_name": person_name},
            events=related_events,
            total_events=len(related_events),
            event_type_stats={},
        )

        logger.info(
            f"人物时间线查询: {person_name} ({person_id}), "
            f"找到{len(related_events)}个事件"
        )

        return result


    def export_visualization_data(
        self,
        project_name: str = "跨项目时间线"
    ) -> TimelineVisualizationExport:
        """
        导出可视化数据（供前端时间线组件使用）

        Args:
            project_name: 项目名称

        Returns:
            可视化导出数据
        """
        # 收集所有事件
        events_data = []
        all_years = []
        people_ids = set()

        for event in self.events.values():
            event_dict = {
                "id": event.event_id,
                "name": event.event_name,
                "type": event.event_type,
                "year": event.year,
                "start_time": event.start_time.isoformat() if event.start_time else None,
                "end_time": event.end_time.isoformat() if event.end_time else None,
                "description": event.description,
                "importance": event.importance,
                "related_nodes": event.related_nodes,
            }
            events_data.append(event_dict)

            if event.year:
                all_years.append(event.year)

            people_ids.update(event.related_nodes)

        # 时间范围
        min_year = min(all_years) if all_years else None
        max_year = max(all_years) if all_years else None

        export = TimelineVisualizationExport(
            timeline_name=project_name,
            events=events_data,
            succession_chains=list(self.succession_chains.values()),
            min_year=min_year,
            max_year=max_year,
            total_events=len(events_data),
            total_people=len(people_ids),
        )

        logger.info(
            f"时间线导出: {export.total_events}个事件, "
            f"时间跨度: {min_year}-{max_year}"
        )

        return export


    def link_to_knowledge_graph(
        self,
        event_id: str,
        node_id: str
    ) -> bool:
        """
        将时间线事件关联到知识图谱节点（双向关联）

        Args:
            event_id: 事件ID
            node_id: 图谱节点ID

        Returns:
            是否成功
        """
        if event_id not in self.events:
            logger.error(f"事件不存在: {event_id}")
            return False

        event = self.events[event_id]
        if node_id not in event.related_nodes:
            event.related_nodes.append(node_id)
            logger.info(f"关联成功: 事件 {event_id} ↔ 节点 {node_id}")

        return True


# 单例实例
_timeline_service = None

def get_timeline_service() -> TimelineIntegrationService:
    """获取时间线服务单例"""
    global _timeline_service
    if _timeline_service is None:
        _timeline_service = TimelineIntegrationService()
    return _timeline_service
