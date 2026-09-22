"""Graphiti时间感知知识图谱服务 - 事件驱动的时态知识图谱"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import asyncio
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

try:
    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType
    GRAPHITI_AVAILABLE = True
except ImportError:
    logger.warning("Graphiti not installed. Run: pip install graphiti-core")
    GRAPHITI_AVAILABLE = False
    Graphiti = None
    EpisodeType = None


# 全局实例缓存
_graphiti_instances: Dict[str, Graphiti] = {}


class GraphitiService:
    """Graphiti时间感知知识图谱服务

    Graphiti是一个时态知识图谱系统，特点：
    1. 时间感知：每个事件都有时间戳
    2. 事件驱动：基于episodes（事件/对话）构建图谱
    3. 增量更新：支持图谱的动态演化
    4. 自动推理：自动提取实体、关系和时间信息
    """
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """初始化Graphiti服务"""
        self.available = False
        self.unavailable_reason = None
        self.timeout_seconds = 15

        if not GRAPHITI_AVAILABLE:
            self.unavailable_reason = "Graphiti SDK未安装"
            logger.warning("Graphiti not available - temporal knowledge graph disabled")
            return

        # 从配置读取Neo4j连接信息
        from app.core.config import settings

        self.neo4j_uri = settings.neo4j.uri
        self.neo4j_user = settings.neo4j.user
        self.neo4j_password = settings.neo4j.password

        # 验证Neo4j配置
        if not all([self.neo4j_uri, self.neo4j_user, self.neo4j_password]):
            logger.warning("⚠️ Neo4j配置不完整，Graphiti功能可能受限")

        # 配置OpenAI API（Graphiti默认使用OpenAI）
        self.openai_api_key = settings.ai.openai_api_key or os.getenv("OPENAI_API_KEY", "")
        if not self.openai_api_key:
            logger.warning("⚠️ OPENAI_API_KEY未配置，Graphiti功能可能受限")

        os.environ["OPENAI_API_KEY"] = self.openai_api_key

        self.available, self.unavailable_reason = self._check_neo4j_health()
        if self.available:
            logger.info("✅ Graphiti服务初始化完成")
        else:
            logger.warning(f"Graphiti暂不可用: {self.unavailable_reason}")

    def _check_neo4j_health(self) -> tuple[bool, Optional[str]]:
        """快速探测Neo4j，避免外部连接失败时长时间重试。"""
        try:
            parsed = urlparse(self.neo4j_uri)
            host = parsed.hostname or "localhost"
            port = parsed.port or 7687
            with socket.create_connection((host, port), timeout=1.5):
                return True, None
        except Exception as exc:
            return False, f"Neo4j不可达 ({self.neo4j_uri}): {exc}"

    def health_check(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "sdk_installed": GRAPHITI_AVAILABLE,
            "neo4j_uri": getattr(self, "neo4j_uri", None),
            "reason": self.unavailable_reason,
        }

    def _get_instance(self, project_id: Optional[str] = None) -> Optional[Graphiti]:
        """获取或创建Graphiti实例

        每个项目使用独立的Graphiti实例，避免跨项目数据混淆
        """
        if not GRAPHITI_AVAILABLE or not self.available:
            return None

        key = project_id or "global"

        if key not in _graphiti_instances:
            try:
                # 创建Graphiti实例
                # Graphiti会自动使用环境变量中的OPENAI_API_KEY
                instance = Graphiti(
                    uri=self.neo4j_uri,
                    user=self.neo4j_user,
                    password=self.neo4j_password,
                    store_raw_episode_content=True,
                    max_coroutines=4,
                )

                _graphiti_instances[key] = instance
                logger.info(f"✅ 创建Graphiti实例: {key}")

            except Exception as e:
                logger.error(f"❌ 创建Graphiti实例失败: {e}", exc_info=True)
                return None

        return _graphiti_instances[key]

    async def add_episode(
        self,
        content: str,
        episode_type: str,
        project_id: Optional[str] = None,
        document_id: Optional[int] = None,
        source_description: Optional[str] = None,
        reference_time: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """添加事件到时态知识图谱

        Args:
            content: 事件内容（文档文本或对话内容）
            episode_type: 事件类型（message/text/json）
            project_id: 项目ID
            document_id: 文档ID（如果是文档事件）
            source_description: 事件来源描述
            reference_time: 事件发生时间
            metadata: 额外元数据

        Returns:
            包含episode_id和提取的实体/关系信息的字典
        """
        if not GRAPHITI_AVAILABLE or not self.available:
            logger.warning("Graphiti不可用")
            return {
                "success": False,
                "status": "unavailable",
                "error": self.unavailable_reason or "Graphiti不可用",
            }

        try:
            graphiti = self._get_instance(project_id)
            if not graphiti:
                return {"success": False, "error": "Failed to get Graphiti instance"}

            # 设置参考时间（默认当前时间）
            ref_time = reference_time or datetime.now()

            # 解析episode类型
            if episode_type == "message":
                ep_type = EpisodeType.message
            elif episode_type == "json":
                ep_type = EpisodeType.json
            else:
                ep_type = EpisodeType.text

            # 添加episode
            logger.info(f"📝 开始添加episode到Graphiti，类型: {episode_type}")

            result = await asyncio.wait_for(
                graphiti.add_episode(
                    name=source_description or f"Document_{document_id}" if document_id else "Episode",
                    episode_body=content,
                    source=ep_type,
                    source_description=source_description or "FieldMind Document",
                    reference_time=ref_time,
                    group_id=str(project_id) if project_id else None,
                ),
                timeout=self.timeout_seconds,
            )

            logger.info(f"✅ Episode已添加到Graphiti")

            return {
                "success": True,
                "status": "executed",
                "episode_id": getattr(result, 'uuid', None),
                "episode_name": source_description,
                "reference_time": ref_time.isoformat(),
                "metadata": metadata or {}
            }

        except Exception as e:
            logger.error(f"❌ 添加episode失败: {e}", exc_info=True)
            return {
                "success": False,
                "status": "failed",
                "error": f"Graphiti调用失败: {e}",
            }

    async def search(
        self,
        query: str,
        project_id: Optional[str] = None,
        num_results: int = 5,
        center_node_uuid: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """搜索时态知识图谱

        Args:
            query: 搜索查询
            project_id: 项目ID
            num_results: 返回结果数量
            center_node_uuid: 中心节点UUID（用于局部搜索）

        Returns:
            相关的图谱节点和边
        """
        if not GRAPHITI_AVAILABLE or not self.available:
            return []

        try:
            graphiti = self._get_instance(project_id)
            if not graphiti:
                return []

            logger.info(f"🔍 搜索Graphiti图谱: {query}")

            # 搜索图谱
            results = await asyncio.wait_for(
                graphiti.search(
                    query=query,
                    num_results=num_results,
                    center_node_uuid=center_node_uuid,
                    group_ids=[str(project_id)] if project_id else None,
                ),
                timeout=self.timeout_seconds,
            )

            logger.info(f"✅ Graphiti搜索返回 {len(results)} 个结果")

            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "uuid": getattr(result, 'uuid', None),
                    "name": getattr(result, 'name', ''),
                    "content": getattr(result, 'summary', '') or getattr(result, 'fact', ''),
                    "created_at": getattr(result, 'created_at', None),
                })

            return formatted_results

        except Exception as e:
            logger.error(f"❌ Graphiti搜索失败: {e}", exc_info=True)
            return []

    async def get_episodes_by_time_range(
        self,
        project_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """按时间范围获取事件，并明确报告插件不可用或查询失败。"""
        if not GRAPHITI_AVAILABLE or not self.available:
            return {
                "status": "unavailable",
                "results": [],
                "reason": self.unavailable_reason or "Graphiti不可用",
            }

        try:
            graphiti = self._get_instance(project_id)
            if not graphiti:
                return {
                    "status": "unavailable",
                    "results": [],
                    "reason": "Graphiti实例创建失败",
                }

            logger.info(f"⏰ 查询时间范围: {start_time} 到 {end_time}")
            reference_time = end_time or datetime.now()
            episodes = await asyncio.wait_for(
                graphiti.retrieve_episodes(
                    reference_time=reference_time,
                    last_n=max(limit * 5, limit),
                    group_ids=[str(project_id)] if project_id else None,
                ),
                timeout=self.timeout_seconds,
            )
            results = []
            for episode in episodes:
                timestamp = getattr(episode, "valid_at", None) or getattr(
                    episode, "created_at", None
                )
                if start_time and timestamp and timestamp < start_time:
                    continue
                if end_time and timestamp and timestamp > end_time:
                    continue
                results.append({
                    "uuid": getattr(episode, "uuid", None),
                    "name": getattr(episode, "name", ""),
                    "content": getattr(episode, "content", ""),
                    "valid_at": (
                        timestamp.isoformat()
                        if hasattr(timestamp, "isoformat")
                        else timestamp
                    ),
                })
                if len(results) >= limit:
                    break

            return {"status": "executed", "results": results}

        except Exception as e:
            logger.error(f"❌ 按时间查询失败: {e}", exc_info=True)
            return {"status": "failed", "results": [], "reason": str(e)}

    async def get_entity_timeline(
        self,
        entity_name: str,
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取实体的时间线

        追踪一个实体（人、地点、概念）在不同时间点的状态变化
        """
        if not GRAPHITI_AVAILABLE or not self.available:
            return []

        try:
            graphiti = self._get_instance(project_id)
            if not graphiti:
                return []

            logger.info(f"📅 获取实体时间线: {entity_name}")

            # 搜索该实体相关的所有节点
            results = await asyncio.wait_for(
                graphiti.search(
                    query=entity_name,
                    num_results=20,
                    group_ids=[str(project_id)] if project_id else None,
                ),
                timeout=self.timeout_seconds,
            )

            # 按时间排序
            timeline = []
            for result in results:
                if hasattr(result, 'created_at') and result.created_at:
                    timeline.append({
                        "time": result.created_at,
                        "content": getattr(result, 'summary', '') or getattr(result, 'fact', ''),
                        "uuid": getattr(result, 'uuid', None)
                    })

            # 按时间排序
            timeline.sort(key=lambda x: x['time'])

            logger.info(f"✅ 实体时间线包含 {len(timeline)} 个时间点")
            return timeline

        except Exception as e:
            logger.error(f"❌ 获取实体时间线失败: {e}", exc_info=True)
            return []

    async def close(self, project_id: Optional[str] = None):
        """关闭Graphiti连接"""
        key = project_id or "global"

        if key in _graphiti_instances:
            try:
                instance = _graphiti_instances[key]
                await asyncio.wait_for(instance.close(), timeout=5)
                del _graphiti_instances[key]
                logger.info(f"✅ 关闭Graphiti实例: {key}")
            except Exception as e:
                logger.error(f"❌ 关闭Graphiti实例失败: {e}")


# 单例服务
_graphiti_service: Optional[GraphitiService] = None


def get_graphiti_service() -> GraphitiService:
    """获取Graphiti服务单例"""
    global _graphiti_service
    if _graphiti_service is None:
        _graphiti_service = GraphitiService()
    return _graphiti_service
