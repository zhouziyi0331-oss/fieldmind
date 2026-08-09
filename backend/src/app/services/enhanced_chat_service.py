"""
增强AI对话服务 - 支持技能模型、深度思考、长上下文
Enhanced AI Chat Service with Skill-based Models, Deep Thinking, and Long Context
"""
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import anthropic
from anthropic import Anthropic

from app.services.long_memory_service import long_memory_service
from app.core.rag_engine import rag_engine

logger = logging.getLogger(__name__)


class EnhancedChatService:
    """增强AI对话服务"""

    def __init__(self):
        self.client = None
        self.default_model = "claude-3-5-sonnet-20241022"
        self.extended_thinking_model = "claude-3-7-sonnet-20250219"  # 支持扩展思考
        self._init_client()

    def _init_client(self):
        """初始化Anthropic客户端"""
        try:
            import os
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self.client = Anthropic(api_key=api_key)
                logger.info("✅ 增强AI对话服务初始化成功")
            else:
                logger.warning("⚠️ 未找到ANTHROPIC_API_KEY，AI对话功能将禁用")
        except Exception as e:
            logger.error(f"❌ 初始化Anthropic客户端失败: {e}")

    def chat_with_skill(
        self,
        query: str,
        session_id: str,
        skill_config: Optional[Dict] = None,
        memory_config: Optional[Dict] = None,
        project_id: Optional[int] = None,
        use_deep_thinking: bool = False,
        use_long_context: bool = True,
        max_tokens: int = 8192
    ) -> Dict[str, Any]:
        """
        基于技能模型的AI对话

        Args:
            query: 用户问题
            session_id: 会话ID
            skill_config: 技能配置 {skill_id, skill_name, workflow_prompt, parameters}
            memory_config: 记忆配置 {search_depth, relevance_threshold, max_context_tokens}
            project_id: 项目ID
            use_deep_thinking: 是否使用深度思考（扩展思考模式）
            use_long_context: 是否使用长上下文记忆
            max_tokens: 最大输出tokens

        Returns:
            对话结果
        """
        if not self.client:
            return self._fallback_response("AI服务未初始化")

        try:
            # 1. 构建系统提示词
            system_prompt = self._build_system_prompt(skill_config)

            # 2. 构建记忆上下文
            memory_context = ""
            if use_long_context:
                memory_context = long_memory_service.build_memory_context(
                    query=query,
                    session_id=session_id,
                    project_id=project_id,
                    config=memory_config or {}
                )

            # 3. 检索相关文档（RAG）
            rag_context = self._build_rag_context(query, project_id)

            # 4. 构建完整消息
            full_message = self._build_message_with_context(
                query=query,
                memory_context=memory_context,
                rag_context=rag_context
            )

            # 5. 选择模型
            model = self.extended_thinking_model if use_deep_thinking else self.default_model

            # 6. 调用Claude API
            start_time = datetime.now()

            # 如果使用深度思考，启用扩展思考模式
            if use_deep_thinking and model == self.extended_thinking_model:
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    thinking={
                        "type": "enabled",
                        "budget_tokens": 10000
                    },
                    messages=[{
                        "role": "user",
                        "content": full_message
                    }],
                    system=system_prompt
                )
            else:
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{
                        "role": "user",
                        "content": full_message
                    }],
                    system=system_prompt
                )

            processing_time = (datetime.now() - start_time).total_seconds()

            # 7. 提取响应内容
            answer = self._extract_response_content(response)
            thinking_process = self._extract_thinking_process(response)

            # 8. 保存对话到长期记忆
            if use_long_context:
                long_memory_service.save_conversation_to_memory(
                    session_id=session_id,
                    messages=[
                        {"role": "user", "content": query},
                        {"role": "assistant", "content": answer}
                    ],
                    project_id=project_id
                )

            # 9. 构建返回结果
            result = {
                'answer': answer,
                'thinking_process': thinking_process if use_deep_thinking else None,
                'model': model,
                'processing_time': processing_time,
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'memory_used': use_long_context,
                'deep_thinking_used': use_deep_thinking,
                'skill_applied': skill_config.get('skill_name') if skill_config else None,
                'sources': self._extract_sources(rag_context),
                'timestamp': datetime.utcnow().isoformat()
            }

            logger.info(
                f"增强AI对话完成: session={session_id}, "
                f"model={model}, tokens={response.usage.output_tokens}"
            )

            return result

        except Exception as e:
            logger.error(f"增强AI对话失败: {e}")
            return self._fallback_response(f"对话处理失败: {str(e)}")

    def _build_system_prompt(self, skill_config: Optional[Dict] = None) -> str:
        """构建系统提示词"""
        base_prompt = """你是FieldMind智能助手，专注于田野调查、学术研究和知识管理。

你的能力：
- 分析和理解复杂的研究文档
- 提供深度的学术见解和分析
- 帮助用户整理和发现知识脉络
- 基于已有材料进行推理和归纳

请以专业、准确、有条理的方式回答问题。"""

        if skill_config:
            skill_name = skill_config.get('skill_name', '通用技能')
            workflow_prompt = skill_config.get('workflow_prompt', '')

            skill_prompt = f"""

## 当前激活的技能模型: {skill_name}

{workflow_prompt}

请按照上述技能模型的工作流程和方法论来处理用户的请求。"""

            base_prompt += skill_prompt

        return base_prompt

    def _build_rag_context(self, query: str, project_id: Optional[int] = None) -> str:
        """构建RAG检索上下文"""
        try:
            # 使用RAG引擎检索相关文档
            rag_result = rag_engine.query(
                question=query,
                top_k=5,
                return_sources=True
            )

            sources = rag_result.get('sources', [])
            if not sources:
                return ""

            context_parts = ["## 相关文档片段\n"]
            for idx, source in enumerate(sources[:5], 1):
                context_parts.append(
                    f"### 来源 {idx}: {source.get('document_name', '未知文档')}\n"
                    f"{source.get('content', '')}\n"
                )

            return "\n".join(context_parts)

        except Exception as e:
            logger.error(f"构建RAG上下文失败: {e}")
            return ""

    def _build_message_with_context(
        self,
        query: str,
        memory_context: str,
        rag_context: str
    ) -> str:
        """构建包含上下文的完整消息"""
        message_parts = []

        if memory_context:
            message_parts.append(f"<记忆上下文>\n{memory_context}\n</记忆上下文>\n")

        if rag_context:
            message_parts.append(f"<文档上下文>\n{rag_context}\n</文档上下文>\n")

        message_parts.append(f"<用户问题>\n{query}\n</用户问题>")

        return "\n".join(message_parts)

    def _extract_response_content(self, response) -> str:
        """提取响应内容"""
        try:
            for block in response.content:
                if block.type == "text":
                    return block.text
            return "无响应内容"
        except Exception as e:
            logger.error(f"提取响应内容失败: {e}")
            return "响应解析失败"

    def _extract_thinking_process(self, response) -> Optional[str]:
        """提取思考过程（仅扩展思考模式）"""
        try:
            for block in response.content:
                if hasattr(block, 'type') and block.type == "thinking":
                    return block.thinking
            return None
        except Exception as e:
            logger.error(f"提取思考过程失败: {e}")
            return None

    def _extract_sources(self, rag_context: str) -> List[Dict[str, Any]]:
        """从RAG上下文中提取来源信息"""
        # 简化实现，实际应该从rag_engine返回的结构化数据中提取
        sources = []
        if "来源" in rag_context:
            # TODO: 实现更好的来源提取逻辑
            pass
        return sources

    def _fallback_response(self, error_message: str) -> Dict[str, Any]:
        """降级响应"""
        return {
            'answer': f"抱歉，{error_message}",
            'error': True,
            'timestamp': datetime.utcnow().isoformat()
        }

    def stream_chat_with_skill(
        self,
        query: str,
        session_id: str,
        skill_config: Optional[Dict] = None,
        memory_config: Optional[Dict] = None,
        project_id: Optional[int] = None,
        use_deep_thinking: bool = False,
        use_long_context: bool = True
    ):
        """
        流式AI对话（支持实时输出）

        Returns:
            生成器，逐块返回响应
        """
        if not self.client:
            yield {"error": "AI服务未初始化"}
            return

        try:
            # 构建系统提示词和上下文（同上）
            system_prompt = self._build_system_prompt(skill_config)

            memory_context = ""
            if use_long_context:
                memory_context = long_memory_service.build_memory_context(
                    query=query,
                    session_id=session_id,
                    project_id=project_id,
                    config=memory_config or {}
                )

            rag_context = self._build_rag_context(query, project_id)
            full_message = self._build_message_with_context(query, memory_context, rag_context)

            model = self.extended_thinking_model if use_deep_thinking else self.default_model

            # 流式调用
            with self.client.messages.stream(
                model=model,
                max_tokens=8192,
                messages=[{"role": "user", "content": full_message}],
                system=system_prompt
            ) as stream:
                for text in stream.text_stream:
                    yield {
                        'type': 'text',
                        'content': text
                    }

        except Exception as e:
            logger.error(f"流式对话失败: {e}")
            yield {"error": str(e)}


# 全局实例
enhanced_chat_service = EnhancedChatService()
