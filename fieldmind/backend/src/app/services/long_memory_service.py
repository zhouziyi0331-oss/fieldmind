"""
长记忆系统服务 - 集成Anthropic Memory Tool和向量检索
支持大文档处理和碎片化对话记忆
"""
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import anthropic
from anthropic.types import ToolParam

from app.core.rag_engine import rag_engine
from app.services.vectorization_service_complete import VectorizationService

# 创建单例实例
vectorization_service = VectorizationService()

logger = logging.getLogger(__name__)


class LongMemoryService:
    """长记忆系统服务"""

    def __init__(self):
        self.client = None
        self.memory_enabled = False
        self._init_anthropic_client()

    def _init_anthropic_client(self):
        """初始化Anthropic客户端"""
        try:
            import os
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self.client = anthropic.Anthropic(api_key=api_key)
                self.memory_enabled = True
                logger.info("✅ Anthropic长记忆系统初始化成功")
            else:
                logger.warning("⚠️ 未找到ANTHROPIC_API_KEY，长记忆功能将禁用")
        except Exception as e:
            logger.error(f"❌ 初始化Anthropic客户端失败: {e}")

    def search_long_term_memory(
        self,
        query: str,
        project_id: Optional[int] = None,
        top_k: int = 10,
        relevance_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        搜索长期记忆（向量检索）

        Args:
            query: 查询文本
            project_id: 项目ID（用于过滤）
            top_k: 返回结果数量
            relevance_threshold: 相关度阈值

        Returns:
            相关记忆片段列表
        """
        try:
            # 使用向量化服务搜索
            results = vectorization_service.search_similar(
                query=query,
                top_k=top_k,
                relevance_threshold=relevance_threshold
            )

            # 过滤项目相关的结果
            if project_id:
                results = [
                    r for r in results
                    if r.get('metadata', {}).get('project_id') == project_id
                ]

            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'content': result['text'],
                    'source': result['metadata'].get('source', 'unknown'),
                    'document_id': result['metadata'].get('document_id'),
                    'document_name': result['metadata'].get('filename', '未知文档'),
                    'relevance_score': result['relevance_score'],
                    'timestamp': result['metadata'].get('timestamp'),
                    'chunk_index': result['metadata'].get('chunk_index', 0)
                })

            logger.info(f"长期记忆检索完成: {len(formatted_results)} 个结果")
            return formatted_results

        except Exception as e:
            logger.error(f"长期记忆检索失败: {e}")
            return []

    def save_conversation_to_memory(
        self,
        session_id: str,
        messages: List[Dict[str, str]],
        project_id: Optional[int] = None
    ) -> bool:
        """
        保存对话到长期记忆

        Args:
            session_id: 会话ID
            messages: 消息列表 [{"role": "user", "content": "..."}, ...]
            project_id: 项目ID

        Returns:
            是否成功
        """
        try:
            # 将对话内容向量化并存储
            for idx, msg in enumerate(messages):
                # 构建元数据
                metadata = {
                    'source': 'conversation',
                    'session_id': session_id,
                    'project_id': project_id,
                    'role': msg['role'],
                    'message_index': idx,
                    'timestamp': datetime.utcnow().isoformat()
                }

                # 存储到向量数据库
                vectorization_service.add_text(
                    text=msg['content'],
                    metadata=metadata
                )

            logger.info(f"保存对话到长期记忆: session={session_id}, messages={len(messages)}")
            return True

        except Exception as e:
            logger.error(f"保存对话到长期记忆失败: {e}")
            return False

    def build_memory_context(
        self,
        query: str,
        session_id: str,
        project_id: Optional[int] = None,
        config: Optional[Dict] = None
    ) -> str:
        """
        构建记忆上下文（用于注入到AI提示词）

        Args:
            query: 当前查询
            session_id: 会话ID
            project_id: 项目ID
            config: 配置 {search_depth, relevance_threshold, max_context_tokens}

        Returns:
            格式化的上下文字符串
        """
        config = config or {}
        search_depth = config.get('search_depth', 10)
        relevance_threshold = config.get('relevance_threshold', 0.7)
        max_tokens = config.get('max_context_tokens', 8000)

        # 1. 检索短期记忆（当前会话）
        short_term = self._get_session_context(session_id, limit=5)

        # 2. 检索中期记忆（项目近期对话）
        mid_term = self._get_project_recent_context(project_id, days=7, limit=10)

        # 3. 检索长期记忆（相关文档和历史对话）
        long_term = self.search_long_term_memory(
            query=query,
            project_id=project_id,
            top_k=search_depth,
            relevance_threshold=relevance_threshold
        )

        # 4. 构建上下文字符串
        context_parts = []

        if short_term:
            context_parts.append("## 短期记忆（当前会话）\n" + short_term)

        if mid_term:
            context_parts.append("## 中期记忆（近期对话）\n" + mid_term)

        if long_term:
            long_term_text = "\n\n".join([
                f"来源: {item['document_name']} (相关度: {item['relevance_score']:.2f})\n{item['content']}"
                for item in long_term[:5]
            ])
            context_parts.append("## 长期记忆（相关知识）\n" + long_term_text)

        full_context = "\n\n".join(context_parts)

        # 5. 截断到最大token数（粗略估计：1 token ≈ 4 characters）
        max_chars = max_tokens * 4
        if len(full_context) > max_chars:
            full_context = full_context[:max_chars] + "\n...(上下文已截断)"

        return full_context

    def _get_session_context(self, session_id: str, limit: int = 5) -> str:
        """获取会话短期上下文"""
        try:
            # TODO: 从数据库获取最近的消息
            # 这里简化实现
            return ""
        except Exception as e:
            logger.error(f"获取会话上下文失败: {e}")
            return ""

    def _get_project_recent_context(
        self,
        project_id: Optional[int],
        days: int = 7,
        limit: int = 10
    ) -> str:
        """获取项目中期上下文"""
        try:
            # TODO: 从数据库获取项目近期对话
            return ""
        except Exception as e:
            logger.error(f"获取项目上下文失败: {e}")
            return ""

    def get_memory_statistics(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取记忆系统统计信息

        Args:
            project_id: 项目ID

        Returns:
            统计信息
        """
        try:
            stats = {
                'memory_enabled': self.memory_enabled,
                'vector_count': 0,  # TODO: 从向量数据库获取
                'document_count': 0,
                'conversation_count': 0,
                'total_tokens_estimated': 0
            }

            return stats
        except Exception as e:
            logger.error(f"获取记忆统计失败: {e}")
            return {}


# 全局实例
long_memory_service = LongMemoryService()
