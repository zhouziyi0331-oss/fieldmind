"""
Cognee AI Memory Service
为FieldMind提供持久化AI记忆能力

核心功能：
1. remember - 存储文档、对话到知识图谱
2. recall - 从知识图谱检索相关信息
3. forget - 删除数据集
4. improve - 从反馈中学习

集成场景：
- 文档上传后自动remember到知识图谱
- 聊天时从recall获取上下文
- 深度处理后将分析结果remember
- 项目级别的记忆隔离
"""

from __future__ import annotations

import asyncio
import logging
import socket
from typing import List, Dict, Any, Optional
from pathlib import Path
from urllib.parse import urlparse

try:
    import cognee
    from cognee import SearchType, RememberResult
    COGNEE_AVAILABLE = True
except ImportError:
    COGNEE_AVAILABLE = False
    logging.warning("Cognee not installed. Run: pip install cognee==1.4.0")

from app.core.config import settings

logger = logging.getLogger(__name__)


class CogneeService:
    """Cognee AI记忆服务"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.initialized = False
        self.available = False
        self.unavailable_reason: Optional[str] = None
        self.timeout_seconds = 20
        self._setup_lock = asyncio.Lock()

        if not COGNEE_AVAILABLE:
            self.unavailable_reason = "Cognee SDK未安装"
            logger.warning("Cognee SDK不可用")
            return

    def _check_neo4j_health(self) -> tuple[bool, Optional[str]]:
        """在进入Cognee前快速确认Neo4j端口，避免外部插件长时间阻塞。"""
        try:
            parsed = urlparse(settings.neo4j.uri)
            host = parsed.hostname or "localhost"
            port = parsed.port or 7687
            with socket.create_connection((host, port), timeout=1.5):
                return True, None
        except Exception as exc:
            return False, f"Neo4j不可达 ({settings.neo4j.uri}): {exc}"

    def health_check(self) -> Dict[str, Any]:
        reason = self.unavailable_reason
        if not self.available and COGNEE_AVAILABLE and not reason:
            healthy, reason = self._check_neo4j_health()
            if healthy:
                reason = "Cognee尚未初始化"
        return {
            "available": self.available,
            "sdk_installed": COGNEE_AVAILABLE,
            "neo4j_uri": settings.neo4j.uri,
            "reason": reason,
        }

    async def initialize(self):
        """初始化Cognee配置"""
        if self.initialized:
            return

        async with self._setup_lock:
            if self.initialized:
                return

            try:
                healthy, reason = self._check_neo4j_health()
                if not healthy:
                    self.unavailable_reason = reason
                    logger.warning(f"Cognee外部图谱不可用: {reason}")
                    return

                # Cognee 1.4 在启用多用户访问控制时要求 graph handler
                # 与 provider 一致。当前项目按 project_<id> 隔离数据集，
                # 因此显式使用对应 handler，避免默认 handler 误配。
                import os
                os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")

                # 配置Neo4j图数据库
                cognee.config.set_graph_db_config({
                    "graph_database_url": settings.neo4j.uri,
                    "graph_database_name": "neo4j",
                    "graph_database_provider": "neo4j",
                    "graph_dataset_database_handler": "neo4j",
                    "graph_database_username": settings.neo4j.user,
                    "graph_database_password": settings.neo4j.password,
                })

                # 配置LanceDB向量数据库（本地）
                cognee.config.set_vector_db_config({
                    "vector_db_provider": "lancedb",
                    "vector_dataset_database_handler": "lancedb",
                })

                # 配置数据目录
                data_root = Path("/Users/alwan/FieldMind/backend/src/data/cognee_data")
                data_root.mkdir(parents=True, exist_ok=True)
                cognee.config.data_root_directory(str(data_root))

                system_root = Path("/Users/alwan/FieldMind/backend/src/data/cognee_system")
                system_root.mkdir(parents=True, exist_ok=True)
                cognee.config.system_root_directory(str(system_root))

                # 配置LLM（使用OpenAI）
                if settings.ai.openai_api_key:
                    os.environ["LLM_API_KEY"] = settings.ai.openai_api_key
                    os.environ["LLM_PROVIDER"] = "openai"
                    os.environ["LLM_MODEL"] = "gpt-4o-mini"

                self.initialized = True
                self.available = True
                logger.info("Cognee服务初始化成功")

            except Exception as e:
                self.unavailable_reason = f"Cognee初始化失败: {e}"
                logger.error(f"Cognee初始化失败: {e}", exc_info=True)
                return

    async def remember_document(
        self,
        content: str,
        document_id: str,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RememberResult:
        """
        将文档内容存储到知识图谱

        Args:
            content: 文档内容
            document_id: 文档ID
            project_id: 项目ID（用于数据隔离）
            metadata: 额外元数据

        Returns:
            RememberResult: 存储结果
        """
        await self.initialize()

        if not COGNEE_AVAILABLE or not self.available:
            raise RuntimeError(self.unavailable_reason or "Cognee不可用")

        try:
            # 构建dataset名称（项目级别隔离）
            dataset_name = f"project_{project_id}" if project_id else "default"

            # 存储到知识图谱
            logger.info(f"Remember文档 {document_id} 到数据集 {dataset_name}")
            result = await asyncio.wait_for(
                cognee.remember(
                    [content],
                    dataset_name=dataset_name,
                    self_improvement=True,
                ),
                timeout=self.timeout_seconds,
            )

            logger.info(f"文档 {document_id} 已存储到Cognee知识图谱")
            return result

        except Exception as e:
            logger.error(f"Remember文档失败: {e}", exc_info=True)
            raise

    async def remember_conversation(
        self,
        messages: List[Dict[str, str]],
        session_id: str,
        project_id: Optional[str] = None
    ) -> RememberResult:
        """
        存储对话到会话记忆

        Args:
            messages: 对话消息列表 [{"role": "user", "content": "..."}, ...]
            session_id: 会话ID
            project_id: 项目ID

        Returns:
            RememberResult: 存储结果
        """
        await self.initialize()

        if not COGNEE_AVAILABLE or not self.available:
            raise RuntimeError(self.unavailable_reason or "Cognee不可用")

        try:
            # 将对话格式化为文本
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in messages
            ])

            # 存储到会话记忆（快速缓存，后台同步到图谱）
            logger.info(f"Remember会话 {session_id}")
            result = await asyncio.wait_for(
                cognee.remember(
                    conversation_text,
                    session_id=session_id,
                ),
                timeout=self.timeout_seconds,
            )

            logger.info(f"会话 {session_id} 已存储")
            return result

        except Exception as e:
            logger.error(f"Remember会话失败: {e}", exc_info=True)
            raise

    async def recall_context(
        self,
        query: str,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        search_type: str = "insights",
        top_k: int = 5
    ) -> List[Any]:
        """
        从知识图谱检索相关上下文

        Args:
            query: 查询文本
            project_id: 项目ID（限定搜索范围）
            session_id: 会话ID（优先搜索会话记忆）
            search_type: 搜索类型 - "insights"/"chunks"/"graph_completion"
            top_k: 返回结果数量

        Returns:
            List[Any]: 检索结果
        """
        await self.initialize()

        if not COGNEE_AVAILABLE or not self.available:
            raise RuntimeError(self.unavailable_reason or "Cognee不可用")

        try:
            # 映射搜索类型
            search_type_map = {
                "insights": SearchType.INSIGHTS,
                "chunks": SearchType.CHUNKS,
                "graph_completion": SearchType.GRAPH_COMPLETION,
            }
            query_type = search_type_map.get(search_type, SearchType.INSIGHTS)

            # 构建数据集列表
            datasets = None
            if project_id:
                datasets = [f"project_{project_id}"]

            # 检索
            logger.info(f"Recall查询: {query[:50]}... (类型: {search_type})")
            results = await asyncio.wait_for(
                cognee.recall(
                    query_text=query,
                    query_type=query_type,
                    datasets=datasets,
                    session_id=session_id,
                ),
                timeout=self.timeout_seconds,
            )

            logger.info(f"检索到 {len(results)} 条结果")
            return results[:top_k]

        except Exception as e:
            logger.error(f"Recall查询失败: {e}", exc_info=True)
            return []

    async def forget_dataset(
        self,
        project_id: Optional[str] = None,
        dataset_name: Optional[str] = None
    ):
        """
        删除数据集

        Args:
            project_id: 项目ID
            dataset_name: 数据集名称（如果指定则忽略project_id）
        """
        await self.initialize()

        if not COGNEE_AVAILABLE or not self.available:
            raise RuntimeError(self.unavailable_reason or "Cognee不可用")

        try:
            if dataset_name:
                target = dataset_name
            elif project_id:
                target = f"project_{project_id}"
            else:
                raise ValueError("必须指定project_id或dataset_name")

            logger.info(f"删除数据集: {target}")
            await cognee.forget(dataset=target)
            logger.info(f"数据集 {target} 已删除")

        except Exception as e:
            logger.error(f"删除数据集失败: {e}", exc_info=True)
            raise

    async def improve_from_feedback(
        self,
        feedback: str,
        context: Optional[str] = None
    ):
        """
        从用户反馈中学习改进

        Args:
            feedback: 反馈内容
            context: 相关上下文
        """
        await self.initialize()

        if not COGNEE_AVAILABLE or not self.available:
            raise RuntimeError(self.unavailable_reason or "Cognee不可用")

        try:
            logger.info("处理用户反馈以改进记忆")
            await cognee.improve(
                feedback_text=feedback,
                context=context
            )
            logger.info("反馈已处理")

        except Exception as e:
            logger.error(f"处理反馈失败: {e}", exc_info=True)
            raise


# 全局单例
_cognee_service: Optional[CogneeService] = None


def get_cognee_service() -> CogneeService:
    """获取Cognee服务单例"""
    global _cognee_service
    if _cognee_service is None:
        _cognee_service = CogneeService()
    return _cognee_service
