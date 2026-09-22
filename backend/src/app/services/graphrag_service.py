"""
GraphRAG服务 - 微软图增强RAG系统集成
提供全局/局部双视角知识图谱检索
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class GraphRAGService:
    """GraphRAG服务 - 多尺度知识图谱检索"""
    def __init__(self, base_dir: Optional[str] = None, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化GraphRAG服务

        Args:
            base_dir: GraphRAG工作目录（存储索引和配置）
        """
        if base_dir is None:
            base_dir = os.path.join(
                os.path.dirname(__file__),
                '../../storage/graphrag'
            )

        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # 项目级工作区缓存
        self._workspaces: Dict[str, Path] = {}

        logger.info(f"✅ GraphRAG服务初始化完成: {self.base_dir}")

    def _get_workspace(self, project_id: Optional[str]) -> Path:
        """获取项目级工作区"""
        key = project_id if project_id else "default"

        if key not in self._workspaces:
            workspace = self.base_dir / f"project_{key}"
            workspace.mkdir(parents=True, exist_ok=True)

            # 创建输入/输出目录
            (workspace / "input").mkdir(exist_ok=True)
            (workspace / "output").mkdir(exist_ok=True)

            self._workspaces[key] = workspace

        return self._workspaces[key]

    async def index_document(
        self,
        content: str,
        project_id: Optional[str] = None,
        document_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        索引文档到GraphRAG

        Args:
            content: 文档内容
            project_id: 项目ID
            document_id: 文档ID
            metadata: 元数据

        Returns:
            索引结果
        """
        try:
            workspace = self._get_workspace(project_id)

            # 保存文档到input目录
            filename = f"doc_{document_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            input_file = workspace / "input" / filename

            with open(input_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"📄 文档已保存到GraphRAG输入: {filename}")

            # 注意：实际索引需要运行graphrag index命令
            # 这里返回准备就绪状态，实际索引由后台任务完成
            return {
                "status": "queued",
                "workspace": str(workspace),
                "input_file": str(input_file),
                "message": "文档已加入索引队列，需运行索引任务"
            }

        except Exception as e:
            logger.error(f"❌ GraphRAG索引文档失败: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    async def local_search(
        self,
        query: str,
        project_id: Optional[str] = None,
        community_level: int = 2,
        response_type: str = "multiple paragraphs"
    ) -> Dict[str, Any]:
        """
        局部搜索 - 基于实体邻域的细节检索

        Args:
            query: 查询文本
            project_id: 项目ID
            community_level: 社区层级
            response_type: 响应类型

        Returns:
            搜索结果
        """
        try:
            workspace = self._get_workspace(project_id)
            output_dir = workspace / "output"

            # 检查是否已建立索引
            if not (output_dir / "create_final_entities.parquet").exists():
                return {
                    "status": "no_index",
                    "message": "项目尚未建立GraphRAG索引，请先索引文档",
                    "results": []
                }

            # 使用graphrag.query进行本地搜索
            from graphrag.query.structured_search.local_search.search import LocalSearch
            from graphrag.query.input.loaders.dfs import (
                read_indexer_entities,
                read_indexer_relationships,
                read_indexer_text_units,
                read_indexer_covariates,
                read_indexer_reports
            )
            from graphrag.query.llm.text_utils import num_tokens

            # 加载索引数据
            entity_df = read_indexer_entities(output_dir)
            relationship_df = read_indexer_relationships(output_dir)
            text_unit_df = read_indexer_text_units(output_dir)
            covariate_df = read_indexer_covariates(output_dir) if (output_dir / "create_final_covariates.parquet").exists() else None
            report_df = read_indexer_reports(output_dir, community_level=community_level)

            # 构建本地搜索上下文
            from graphrag.query.context_builder.local_context import LocalSearchMixedContext

            context_builder = LocalSearchMixedContext(
                entities=entity_df,
                relationships=relationship_df,
                text_units=text_unit_df,
                reports=report_df,
                covariates=covariate_df
            )

            # 执行搜索
            search_engine = LocalSearch(
                context_builder=context_builder,
                token_encoder=num_tokens
            )

            result = await search_engine.asearch(query)

            return {
                "status": "success",
                "query": query,
                "response": result.response if hasattr(result, 'response') else str(result),
                "context_data": result.context_data if hasattr(result, 'context_data') else None,
                "search_type": "local"
            }

        except Exception as e:
            logger.error(f"❌ GraphRAG本地搜索失败: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "results": []
            }

    async def global_search(
        self,
        query: str,
        project_id: Optional[str] = None,
        community_level: int = 2,
        response_type: str = "multiple paragraphs"
    ) -> Dict[str, Any]:
        """
        全局搜索 - 基于社区摘要的宏观理解

        Args:
            query: 查询文本
            project_id: 项目ID
            community_level: 社区层级
            response_type: 响应类型

        Returns:
            搜索结果
        """
        try:
            workspace = self._get_workspace(project_id)
            output_dir = workspace / "output"

            # 检查是否已建立索引
            if not (output_dir / "create_final_communities.parquet").exists():
                return {
                    "status": "no_index",
                    "message": "项目尚未建立GraphRAG索引",
                    "results": []
                }

            # 使用graphrag.query进行全局搜索
            from graphrag.query.structured_search.global_search.search import GlobalSearch
            from graphrag.query.input.loaders.dfs import (
                read_indexer_entities,
                read_indexer_reports
            )
            from graphrag.query.llm.text_utils import num_tokens

            # 加载索引数据
            entity_df = read_indexer_entities(output_dir)
            report_df = read_indexer_reports(output_dir, community_level=community_level)

            # 构建全局搜索上下文
            from graphrag.query.context_builder.community_context import GlobalCommunityContext

            context_builder = GlobalCommunityContext(
                entities=entity_df,
                reports=report_df
            )

            # 执行搜索
            search_engine = GlobalSearch(
                context_builder=context_builder,
                token_encoder=num_tokens
            )

            result = await search_engine.asearch(query)

            return {
                "status": "success",
                "query": query,
                "response": result.response if hasattr(result, 'response') else str(result),
                "context_data": result.context_data if hasattr(result, 'context_data') else None,
                "search_type": "global"
            }

        except Exception as e:
            logger.error(f"❌ GraphRAG全局搜索失败: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "results": []
            }

    def get_index_status(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取索引状态

        Args:
            project_id: 项目ID

        Returns:
            索引状态信息
        """
        try:
            workspace = self._get_workspace(project_id)
            output_dir = workspace / "output"
            input_dir = workspace / "input"

            # 检查关键文件
            index_files = [
                "create_final_entities.parquet",
                "create_final_relationships.parquet",
                "create_final_communities.parquet",
                "create_final_community_reports.parquet"
            ]

            indexed = all((output_dir / f).exists() for f in index_files)

            # 统计
            input_count = len(list(input_dir.glob("*.txt"))) if input_dir.exists() else 0

            status = {
                "indexed": indexed,
                "workspace": str(workspace),
                "input_documents": input_count,
                "index_files": {}
            }

            if indexed:
                # 读取实体和社区统计
                try:
                    entities_df = pd.read_parquet(output_dir / "create_final_entities.parquet")
                    communities_df = pd.read_parquet(output_dir / "create_final_communities.parquet")
                    relationships_df = pd.read_parquet(output_dir / "create_final_relationships.parquet")

                    status["statistics"] = {
                        "entities": len(entities_df),
                        "communities": len(communities_df),
                        "relationships": len(relationships_df)
                    }
                except Exception as e:
                    logger.warning(f"⚠️ 读取索引统计失败: {e}")

            return status

        except Exception as e:
            logger.error(f"❌ 获取索引状态失败: {e}", exc_info=True)
            return {
                "indexed": False,
                "error": str(e)
            }


# 全局单例
_graphrag_service: Optional[GraphRAGService] = None


def get_graphrag_service() -> GraphRAGService:
    """获取GraphRAG服务单例"""
    global _graphrag_service
    if _graphrag_service is None:
        _graphrag_service = GraphRAGService()
    return _graphrag_service
