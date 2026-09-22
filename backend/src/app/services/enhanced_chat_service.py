"""
增强AI对话服务（重构版）
拆分超长 chat_with_skill 函数为职责单一的组件
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import anthropic
from anthropic import Anthropic

from app.services.long_memory_service import long_memory_service
from app.core.rag_engine import rag_engine

logger = logging.getLogger(__name__)


class ContextBuilder:
    """上下文构建器 - 负责构建各种上下文"""
    def __init__(self, project_id: Optional[int] = None, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.project_id = project_id

    def build_memory_context(
        self, query: str, session_id: str, memory_config: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        构建记忆上下文

        Returns:
            {
                "cognee": "...",
                "lightrag": "...",
                "mem0": "...",
                "graphiti": "...",
                "graphrag": "..."
            }
        """
        contexts = {
            "cognee": "",
            "lightrag": "",
            "mem0": "",
            "graphiti": "",
            "graphrag": "",
        }

        if not memory_config:
            return contexts

        try:
            # Cognee 认知图谱
            if memory_config.get("use_cognee"):
                contexts["cognee"] = self._fetch_cognee_context(query)

            # LightRAG 轻量检索
            if memory_config.get("use_lightrag"):
                contexts["lightrag"] = self._fetch_lightrag_context(query)

            # Mem0 长期记忆
            if memory_config.get("use_mem0"):
                contexts["mem0"] = self._fetch_mem0_context(session_id)

            # Graphiti 图谱记忆
            if memory_config.get("use_graphiti"):
                contexts["graphiti"] = self._fetch_graphiti_context(query)

            # GraphRAG 知识图谱
            if memory_config.get("use_graphrag"):
                contexts["graphrag"] = self._fetch_graphrag_context(query)

        except Exception as e:
            logger.error(f"构建记忆上下文失败: {e}")

        return contexts

    def _fetch_cognee_context(self, query: str) -> str:
        """获取 Cognee 上下文"""
        # TODO: 实现 Cognee 集成
        return ""

    def _fetch_lightrag_context(self, query: str) -> str:
        """获取 LightRAG 上下文"""
        # TODO: 实现 LightRAG 集成
        return ""

    def _fetch_mem0_context(self, session_id: str) -> str:
        """获取 Mem0 上下文"""
        # TODO: 实现 Mem0 集成
        return ""

    def _fetch_graphiti_context(self, query: str) -> str:
        """获取 Graphiti 上下文"""
        # TODO: 实现 Graphiti 集成
        return ""

    def _fetch_graphrag_context(self, query: str) -> str:
        """获取 GraphRAG 上下文"""
        # TODO: 实现 GraphRAG 集成
        return ""

    def build_rag_context(self, query: str) -> str:
        """构建 RAG 检索上下文"""
        if not self.project_id:
            return ""

        try:
            rag_results = rag_engine.search(
                query=query, project_id=self.project_id, top_k=5
            )

            if not rag_results:
                return ""

            context_parts = ["相关文档片段:\n"]
            for i, result in enumerate(rag_results, 1):
                context_parts.append(
                    f"{i}. [{result.get('document_name', '未知文档')}]\n"
                    f"{result.get('content', '')}\n"
                )

            return "\n".join(context_parts)

        except Exception as e:
            logger.error(f"RAG 检索失败: {e}")
            return ""

    def merge_contexts(self, contexts: Dict[str, str]) -> str:
        """合并所有上下文为一个字符串"""
        merged_parts = []

        for name, content in contexts.items():
            if content:
                merged_parts.append(f"[{name.upper()} 上下文]\n{content}\n")

        return "\n".join(merged_parts) if merged_parts else ""


class PromptBuilder:
    """提示词构建器"""

    @staticmethod
    def build_system_prompt(skill_config: Optional[Dict] = None) -> str:
        """构建系统提示词"""
        base_prompt = (
            "你是一个专业的田野调查助手，擅长分析田野材料、" "提取知识、进行深度洞察。"
        )

        if not skill_config:
            return base_prompt

        skill_name = skill_config.get("skill_name", "通用助手")
        workflow_prompt = skill_config.get("workflow_prompt", "")

        if workflow_prompt:
            return f"{base_prompt}\n\n技能: {skill_name}\n\n{workflow_prompt}"

        return base_prompt

    @staticmethod
    def build_user_message(
        query: str, context: str, parameters: Optional[Dict] = None
    ) -> str:
        """构建用户消息"""
        message_parts = []

        # 添加上下文
        if context:
            message_parts.append(f"背景信息:\n{context}\n")

        # 添加参数
        if parameters:
            param_str = "\n".join([f"- {k}: {v}" for k, v in parameters.items()])
            message_parts.append(f"参数:\n{param_str}\n")

        # 添加查询
        message_parts.append(f"问题: {query}")

        return "\n".join(message_parts)


class ResponseFormatter:
    """响应格式化器"""

    @staticmethod
    def format_response(
        ai_response: str,
        thinking_content: Optional[str] = None,
        contexts_used: Optional[Dict[str, bool]] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """格式化 AI 响应"""
        return {
            "response": ai_response,
            "thinking": thinking_content,
            "contexts_used": contexts_used or {},
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def format_error(error_message: str) -> Dict[str, Any]:
        """格式化错误响应"""
        return {
            "response": f"抱歉，处理过程中出现错误: {error_message}",
            "error": True,
            "timestamp": datetime.now().isoformat(),
        }


class EnhancedChatService:
    """增强AI对话服务（重构版）"""

    def __init__(self):
        self.client = None
        self.default_model = "claude-3-5-sonnet-20241022"
        self.extended_thinking_model = "claude-3-7-sonnet-20250219"
        self._init_client()

    def _init_client(self):
        """初始化Anthropic客户端"""
        try:
            import os

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self.client = Anthropic(api_key=api_key)
                logger.info("增强AI对话服务初始化成功")
            else:
                logger.warning("未找到ANTHROPIC_API_KEY，AI对话功能将禁用")
        except Exception as e:
            logger.error(f"初始化Anthropic客户端失败: {e}")

    def chat_with_skill(
        self,
        query: str,
        session_id: str,
        skill_config: Optional[Dict] = None,
        memory_config: Optional[Dict] = None,
        project_id: Optional[int] = None,
        use_deep_thinking: bool = False,
        use_long_context: bool = True,
        max_tokens: int = 8192,
    ) -> Dict[str, Any]:
        """
        基于技能模型的AI对话（重构版）

        拆分逻辑:
        1. ContextBuilder 负责所有上下文构建
        2. PromptBuilder 负责提示词生成
        3. ResponseFormatter 负责响应格式化
        4. 主函数只负责流程编排
        """
        if not self.client:
            return ResponseFormatter.format_error("AI服务未初始化")

        try:
            # 步骤 1: 构建上下文
            context_builder = ContextBuilder(project_id)
            memory_contexts = context_builder.build_memory_context(
                query, session_id, memory_config
            )
            rag_context = context_builder.build_rag_context(query)

            # 合并所有上下文
            all_contexts = {**memory_contexts, "rag": rag_context}
            merged_context = context_builder.merge_contexts(all_contexts)

            # 步骤 2: 构建提示词
            prompt_builder = PromptBuilder()
            system_prompt = prompt_builder.build_system_prompt(skill_config)
            user_message = prompt_builder.build_user_message(
                query,
                merged_context,
                skill_config.get("parameters") if skill_config else None,
            )

            # 步骤 3: 调用 AI
            ai_response, thinking_content = self._call_claude(
                system_prompt=system_prompt,
                user_message=user_message,
                use_deep_thinking=use_deep_thinking,
                max_tokens=max_tokens,
            )

            # 步骤 4: 格式化响应
            contexts_used = {
                name: bool(content) for name, content in all_contexts.items()
            }

            return ResponseFormatter.format_response(
                ai_response=ai_response,
                thinking_content=thinking_content,
                contexts_used=contexts_used,
                metadata={
                    "model": (
                        self.extended_thinking_model
                        if use_deep_thinking
                        else self.default_model
                    ),
                    "skill": skill_config.get("skill_name") if skill_config else None,
                    "session_id": session_id,
                },
            )

        except Exception as e:
            logger.error(f"对话处理失败: {e}", exc_info=True)
            return ResponseFormatter.format_error(str(e))

    def _call_claude(
        self,
        system_prompt: str,
        user_message: str,
        use_deep_thinking: bool,
        max_tokens: int,
    ) -> tuple[str, Optional[str]]:
        """
        调用 Claude API

        Returns:
            (response_text, thinking_content)
        """
        model = (
            self.extended_thinking_model if use_deep_thinking else self.default_model
        )

        messages = [{"role": "user", "content": user_message}]

        # 扩展思考模式
        if use_deep_thinking:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                thinking={"type": "enabled", "budget_tokens": 10000},
                messages=messages,
                system=system_prompt,
            )

            # 提取思考内容和响应
            thinking_content = None
            response_text = ""

            for block in response.content:
                if block.type == "thinking":
                    thinking_content = block.thinking
                elif block.type == "text":
                    response_text = block.text

            return response_text, thinking_content

        # 标准模式
        else:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=messages,
                system=system_prompt,
            )

            response_text = response.content[0].text if response.content else ""
            return response_text, None

    def simple_chat(
        self,
        query: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        简单对话（无技能、无记忆）

        Args:
            query: 用户问题
            context: 可选上下文
            system_prompt: 可选系统提示词

        Returns:
            AI响应文本
        """
        if not self.client:
            return "AI服务未初始化"

        try:
            prompt_builder = PromptBuilder()
            user_message = prompt_builder.build_user_message(query, context or "")

            response_text, _ = self._call_claude(
                system_prompt=system_prompt or "你是一个有帮助的助手。",
                user_message=user_message,
                use_deep_thinking=False,
                max_tokens=4096,
            )

            return response_text

        except Exception as e:
            logger.error(f"简单对话失败: {e}")
            return f"抱歉，出现错误: {str(e)}"


# 全局实例
enhanced_chat_service = EnhancedChatService()
