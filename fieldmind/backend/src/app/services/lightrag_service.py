"""
LightRAG服务 - 图谱增强RAG系统

LightRAG通过知识图谱增强文档检索能力，支持多种检索模式：
- naive: 传统向量检索
- local: 实体相关的局部图谱检索
- global: 社区摘要的全局图谱检索
- hybrid: 结合local和global
- mix: 自适应选择最佳模式
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import asyncio
from typing import Any

try:
    from lightrag import LightRAG, QueryParam
    from lightrag.utils import EmbeddingFunc
    LIGHTRAG_AVAILABLE = True
    LIGHTRAG_IMPORT_ERROR = None
except Exception as exc:  # LightRAG 是可选增强，不得阻塞主处理链路。
    LightRAG = Any
    QueryParam = Any
    EmbeddingFunc = Any
    LIGHTRAG_AVAILABLE = False
    LIGHTRAG_IMPORT_ERROR = str(exc)
import numpy as np

logger = logging.getLogger(__name__)

# 全局LightRAG实例
_lightrag_instances: Dict[str, LightRAG] = {}
_lightrag_initialized: set[str] = set()


class LightRAGService:
    """LightRAG服务封装"""

    def __init__(self):
        self.working_dir = Path("/Users/alwan/FieldMind/backend/src/data/lightrag_storage")
        self.working_dir.mkdir(parents=True, exist_ok=True)

    def _get_instance(self, project_id: Optional[str] = None) -> LightRAG:
        """
        获取或创建LightRAG实例（按项目隔离）

        Args:
            project_id: 项目ID，None表示全局实例
        """
        if not LIGHTRAG_AVAILABLE:
            raise RuntimeError(f"LightRAG依赖不可用: {LIGHTRAG_IMPORT_ERROR}")

        key = project_id or "global"

        if key not in _lightrag_instances:
            # 为每个项目创建独立的工作目录
            instance_dir = self.working_dir / key
            instance_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"🔧 创建LightRAG实例: {key} at {instance_dir}")

            # 配置OpenAI API
            from app.core.config import settings

            # 使用正确的字段名
            openai_key = settings.ai.openai_api_key or os.getenv("OPENAI_API_KEY", "")
            if not openai_key:
                logger.warning("⚠️ OPENAI_API_KEY未配置，LightRAG功能可能受限")
            os.environ["OPENAI_API_KEY"] = openai_key

            # 创建自定义的LLM函数
            async def custom_llm_func(
                prompt: str,
                system_prompt: str = None,
                **kwargs
            ) -> str:
                """使用OpenAI API的自定义LLM函数"""
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=openai_key)

                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    **kwargs
                )

                return response.choices[0].message.content

            # 创建自定义的embedding函数
            async def custom_embedding_func(texts: List[str]) -> np.ndarray:
                """使用OpenAI API的自定义embedding函数"""
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=openai_key)

                response = await client.embeddings.create(
                    model="text-embedding-3-small",
                    input=texts
                )

                embeddings = [item.embedding for item in response.data]
                return np.array(embeddings)

            # 创建LightRAG实例
            _lightrag_instances[key] = LightRAG(
                working_dir=str(instance_dir),
                llm_model_func=custom_llm_func,
                embedding_func=EmbeddingFunc(
                    embedding_dim=1536,
                    max_token_size=8192,
                    func=custom_embedding_func,
                ),
            )

        return _lightrag_instances[key]

    async def insert_document(
        self,
        content: str,
        document_id: str,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        插入文档到LightRAG知识图谱

        Args:
            content: 文档内容
            document_id: 文档ID
            project_id: 项目ID
            metadata: 元数据

        Returns:
            是否成功
        """
        try:
            rag = self._get_instance(project_id)
            key = project_id or "global"
            if key not in _lightrag_initialized:
                await rag.initialize_storages()
                _lightrag_initialized.add(key)

            logger.info(f"📄 插入文档到LightRAG: doc_id={document_id}, project={project_id}")

            # LightRAG的insert是同步方法，在executor中运行
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, rag.insert, content)

            logger.info(f"✅ 文档已插入LightRAG知识图谱")
            return True

        except Exception as e:
            logger.error(f"❌ LightRAG插入文档失败: {e}", exc_info=True)
            return False

    async def query(
        self,
        query_text: str,
        project_id: Optional[str] = None,
        mode: str = "hybrid",
        only_need_context: bool = True,
        top_k: int = 5
    ) -> str:
        """
        查询LightRAG知识图谱

        Args:
            query_text: 查询文本
            project_id: 项目ID
            mode: 检索模式 (naive/local/global/hybrid/mix)
            only_need_context: 仅返回上下文（不调用LLM生成答案）
            top_k: 返回结果数量

        Returns:
            检索到的上下文或完整答案
        """
        try:
            rag = self._get_instance(project_id)

            logger.info(f"🔍 LightRAG查询: query={query_text[:50]}, mode={mode}, project={project_id}")

            # 创建查询参数
            param = QueryParam(
                mode=mode,
                only_need_context=only_need_context,
                top_k=top_k
            )

            # LightRAG的query是同步方法
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, rag.query, query_text, param)

            logger.info(f"✅ LightRAG查询完成，结果长度: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"❌ LightRAG查询失败: {e}", exc_info=True)
            return ""

    async def delete_by_entity(
        self,
        entity_name: str,
        project_id: Optional[str] = None
    ) -> bool:
        """
        根据实体名称删除相关知识

        Args:
            entity_name: 实体名称
            project_id: 项目ID

        Returns:
            是否成功
        """
        try:
            rag = self._get_instance(project_id)

            logger.info(f"🗑️ 删除LightRAG实体: entity={entity_name}, project={project_id}")

            # 使用LightRAG的删除API
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, rag.delete_by_entity, entity_name)

            logger.info(f"✅ 实体已从LightRAG删除")
            return True

        except Exception as e:
            logger.error(f"❌ LightRAG删除实体失败: {e}", exc_info=True)
            return False

    async def get_statistics(
        self,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取知识图谱统计信息

        Args:
            project_id: 项目ID

        Returns:
            统计信息
        """
        try:
            rag = self._get_instance(project_id)

            # 读取图谱文件大小作为指标
            key = project_id or "global"
            instance_dir = self.working_dir / key

            stats = {
                "project_id": project_id,
                "working_dir": str(instance_dir),
                "exists": instance_dir.exists(),
                "files": []
            }

            if instance_dir.exists():
                for file_path in instance_dir.rglob("*"):
                    if file_path.is_file():
                        stats["files"].append({
                            "name": file_path.name,
                            "size": file_path.stat().st_size
                        })

            return stats

        except Exception as e:
            logger.error(f"❌ 获取LightRAG统计失败: {e}", exc_info=True)
            return {}


# 单例服务
_lightrag_service: Optional[LightRAGService] = None


def get_lightrag_service() -> LightRAGService:
    """获取LightRAG服务单例"""
    global _lightrag_service
    if _lightrag_service is None:
        _lightrag_service = LightRAGService()
    return _lightrag_service
