"""
增强AI对话服务 V2 - 完全整合版
Enhanced AI Chat Service V2 - Fully Integrated

整合模块：
1. MemoryAggregator - 8源记忆整合
2. DeepThinkingEngine - 扩展思考
3. SkillChatAdapter - 技能驱动对话
4. RAG引擎
5. 中文NLP分析

提供统一、强大的对话能力
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import anthropic
from anthropic import Anthropic

from app.core.memory_aggregator import get_memory_aggregator
from app.core.deep_thinking_engine import get_deep_thinking_engine
from app.core.skill_chat_adapter import create_skill_chat_adapter
from app.core.rag_engine import rag_engine

logger = logging.getLogger(__name__)


class EnhancedChatServiceV2:
    """增强AI对话服务 V2"""

    def __init__(self, db: Session):
        """
        初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.client = None
        self.default_model = "claude-3-5-sonnet-20241022"

        # 加载整合模块
        self.memory_aggregator = get_memory_aggregator()
        self.thinking_engine = get_deep_thinking_engine()
        self.skill_adapter = create_skill_chat_adapter(db)

        # 中文NLP服务（延迟加载）
        self._chinese_nlp = None

        self._init_client()

        logger.info("✅ 增强AI对话服务V2初始化完成")

    def _init_client(self):
        """初始化Anthropic客户端"""
        try:
            import os
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self.client = Anthropic(api_key=api_key)
                logger.debug("✅ Anthropic客户端已加载")
            else:
                logger.warning("⚠️ 未找到ANTHROPIC_API_KEY")
        except Exception as e:
            logger.error(f"❌ 初始化Anthropic客户端失败: {e}")

    @property
    def chinese_nlp(self):
        """中文NLP服务（延迟加载）"""
        if self._chinese_nlp is None:
            try:
                from app.services.chinese_nlp_service import get_chinese_nlp_service
                self._chinese_nlp = get_chinese_nlp_service()
                logger.debug("✅ 中文NLP服务已加载")
            except Exception as e:
                logger.warning(f"⚠️ 中文NLP服务加载失败: {e}")
        return self._chinese_nlp

    # ==================== 主要对话接口 ====================

    def chat(
        self,
        query: str,
        session_id: str,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        统一对话接口

        Args:
            query: 用户查询
            session_id: 会话ID
            project_id: 项目ID
            user_id: 用户ID
            config: 对话配置 {
                # 功能开关
                'use_memory': bool,
                'use_deep_thinking': bool,
                'use_skill': bool,
                'use_rag': bool,
                'use_chinese_nlp': bool,

                # 记忆配置
                'memory_config': {...},
                'enabled_memory_sources': [...],

                # 思考配置
                'thinking_level': str,
                'thinking_budget': int,

                # 技能配置
                'skill_config': {...},
                'auto_select_skill': bool,

                # 其他
                'max_tokens': int,
                'temperature': float
            }

        Returns:
            完整的对话结果
        """
        if not self.client:
            return self._error_response("AI服务未初始化")

        try:
            start_time = datetime.now()
            config = config or {}

            logger.info(
                f"💬 开始对话: session={session_id}, "
                f"query_length={len(query)}, "
                f"config_keys={list(config.keys())}"
            )

            # === 阶段1: 准备阶段 ===
            preparation_result = self._prepare_chat_context(
                query=query,
                session_id=session_id,
                project_id=project_id,
                user_id=user_id,
                config=config
            )

            # === 阶段2: 对话生成 ===
            if config.get('use_deep_thinking', False):
                # 使用深度思考模式
                generation_result = self._generate_with_thinking(
                    query=query,
                    context=preparation_result,
                    config=config
                )
            else:
                # 使用标准模式
                generation_result = self._generate_standard(
                    query=query,
                    context=preparation_result,
                    config=config
                )

            # === 阶段3: 后处理阶段 ===
            final_result = self._post_process_response(
                generation_result=generation_result,
                preparation_result=preparation_result,
                config=config
            )

            # === 阶段4: 保存阶段 ===
            self._save_conversation(
                session_id=session_id,
                project_id=project_id,
                query=query,
                result=final_result,
                config=config
            )

            processing_time = (datetime.now() - start_time).total_seconds()
            final_result['processing_time'] = processing_time

            logger.info(
                f"✅ 对话完成: time={processing_time:.2f}s, "
                f"tokens={final_result.get('usage', {}).get('total_tokens', 0)}"
            )

            return final_result

        except Exception as e:
            logger.error(f"❌ 对话失败: {e}", exc_info=True)
            return self._error_response(f"对话处理失败: {str(e)}")

    def stream_chat(
        self,
        query: str,
        session_id: str,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        流式对话接口

        Args:
            同chat()

        Yields:
            流式响应块
        """
        if not self.client:
            yield {'error': 'AI服务未初始化'}
            return

        try:
            config = config or {}

            logger.info(f"💬 开始流式对话: session={session_id}")

            # === 准备阶段 ===
            yield {'type': 'status', 'message': '准备上下文...'}

            preparation_result = self._prepare_chat_context(
                query=query,
                session_id=session_id,
                project_id=project_id,
                user_id=user_id,
                config=config
            )

            # === 生成阶段 ===
            yield {'type': 'status', 'message': '生成回答...'}

            if config.get('use_deep_thinking', False):
                # 流式深度思考
                yield from self._stream_generate_with_thinking(
                    query=query,
                    context=preparation_result,
                    config=config
                )
            else:
                # 流式标准生成
                yield from self._stream_generate_standard(
                    query=query,
                    context=preparation_result,
                    config=config
                )

            # === 完成 ===
            yield {'type': 'complete'}

        except Exception as e:
            logger.error(f"❌ 流式对话失败: {e}")
            yield {'error': str(e)}

    # ==================== 准备阶段 ====================

    def _prepare_chat_context(
        self,
        query: str,
        session_id: str,
        project_id: Optional[int],
        user_id: Optional[int],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        准备对话上下文

        整合：
        - 记忆检索
        - RAG检索
        - 技能准备
        - 中文NLP分析
        """
        context = {
            'query': query,
            'session_id': session_id,
            'project_id': project_id,
            'user_id': user_id
        }

        # 1. 记忆整合
        if config.get('use_memory', True):
            memory_result = self.memory_aggregator.aggregate_memory(
                query=query,
                session_id=session_id,
                project_id=project_id,
                memory_config=config.get('memory_config'),
                enabled_sources=config.get('enabled_memory_sources')
            )
            context['memory'] = memory_result
            logger.debug(f"✅ 记忆整合: {memory_result['sources_used']}")

        # 2. RAG检索
        if config.get('use_rag', True):
            rag_result = self._retrieve_rag_context(query, project_id)
            context['rag'] = rag_result
            logger.debug(f"✅ RAG检索: {len(rag_result.get('sources', []))} 来源")

        # 3. 技能准备
        if config.get('use_skill', False):
            skill_result = self._prepare_skill_context(
                query=query,
                project_id=project_id,
                skill_config=config.get('skill_config'),
                auto_select=config.get('auto_select_skill', False)
            )
            context['skill'] = skill_result
            if skill_result:
                logger.debug(f"✅ 技能准备: {skill_result.get('metadata', {}).get('skill_name')}")

        # 4. 中文NLP分析
        if config.get('use_chinese_nlp', False):
            nlp_result = self._analyze_chinese_nlp(query)
            context['chinese_nlp'] = nlp_result
            logger.debug(f"✅ 中文NLP分析完成")

        return context

    def _retrieve_rag_context(
        self,
        query: str,
        project_id: Optional[int]
    ) -> Dict[str, Any]:
        """RAG检索"""
        try:
            result = rag_engine.query(
                question=query,
                top_k=5,
                return_sources=True
            )

            sources = result.get('sources', [])

            return {
                'sources': sources,
                'count': len(sources),
                'context_text': self._format_rag_sources(sources)
            }

        except Exception as e:
            logger.warning(f"⚠️ RAG检索失败: {e}")
            return {'sources': [], 'count': 0, 'context_text': ''}

    def _prepare_skill_context(
        self,
        query: str,
        project_id: Optional[int],
        skill_config: Optional[Dict[str, Any]],
        auto_select: bool
    ) -> Optional[Dict[str, Any]]:
        """准备技能上下文"""
        try:
            # 自动选择技能
            if auto_select and not skill_config:
                recommendation = self.skill_adapter.auto_select_skill(
                    user_query=query,
                    project_id=project_id
                )
                if recommendation:
                    skill_config = {
                        'skill_id': recommendation['skill']['id'],
                        'skill_name': recommendation['skill']['name']
                    }

            # 准备技能上下文
            if skill_config:
                return self.skill_adapter.prepare_skill_context(
                    skill_config=skill_config,
                    user_query=query,
                    project_id=project_id
                )

            return None

        except Exception as e:
            logger.warning(f"⚠️ 技能准备失败: {e}")
            return None

    def _analyze_chinese_nlp(self, query: str) -> Optional[Dict[str, Any]]:
        """中文NLP分析"""
        try:
            if not self.chinese_nlp:
                return None

            health = self.chinese_nlp.health_check()
            if not health.get('available'):
                return None

            result = self.chinese_nlp.analyse_text(query)

            return {
                'keywords': self._extract_keywords_from_nlp(result),
                'entities': self._extract_entities_from_nlp(result),
                'full_result': result
            }

        except Exception as e:
            logger.warning(f"⚠️ 中文NLP分析失败: {e}")
            return None

    # ==================== 生成阶段 ====================

    def _generate_standard(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """标准生成模式"""
        try:
            # 构建系统提示词
            system_prompt = self._build_system_prompt(context)

            # 构建完整消息
            full_message = self._build_full_message(query, context)

            # 调用Claude API
            response = self.client.messages.create(
                model=self.default_model,
                max_tokens=config.get('max_tokens', 8192),
                temperature=config.get('temperature', 1.0),
                messages=[{
                    "role": "user",
                    "content": full_message
                }],
                system=system_prompt
            )

            # 提取回答
            answer = self._extract_text_from_response(response)

            return {
                'answer': answer,
                'model': self.default_model,
                'mode': 'standard',
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                }
            }

        except Exception as e:
            logger.error(f"❌ 标准生成失败: {e}")
            raise

    def _generate_with_thinking(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """深度思考生成模式"""
        try:
            # 构建提示词
            system_prompt = self._build_system_prompt(context)
            full_message = self._build_full_message(query, context)

            # 调用深度思考引擎
            thinking_result = self.thinking_engine.think_and_respond(
                prompt=full_message,
                system_prompt=system_prompt,
                thinking_level=config.get('thinking_level', 'normal'),
                custom_budget=config.get('thinking_budget'),
                max_tokens=config.get('max_tokens', 8192)
            )

            return {
                'answer': thinking_result['answer'],
                'thinking_process': thinking_result['thinking_process'],
                'thinking_analysis': thinking_result['thinking_analysis'],
                'model': thinking_result['model'],
                'mode': 'deep_thinking',
                'usage': thinking_result['usage']
            }

        except Exception as e:
            logger.error(f"❌ 深度思考生成失败: {e}")
            raise

    def _stream_generate_standard(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ):
        """流式标准生成"""
        try:
            system_prompt = self._build_system_prompt(context)
            full_message = self._build_full_message(query, context)

            with self.client.messages.stream(
                model=self.default_model,
                max_tokens=config.get('max_tokens', 8192),
                messages=[{"role": "user", "content": full_message}],
                system=system_prompt
            ) as stream:
                for text in stream.text_stream:
                    yield {
                        'type': 'text',
                        'content': text
                    }

        except Exception as e:
            logger.error(f"❌ 流式标准生成失败: {e}")
            yield {'error': str(e)}

    def _stream_generate_with_thinking(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ):
        """流式深度思考生成"""
        try:
            system_prompt = self._build_system_prompt(context)
            full_message = self._build_full_message(query, context)

            yield from self.thinking_engine.stream_think_and_respond(
                prompt=full_message,
                system_prompt=system_prompt,
                thinking_level=config.get('thinking_level', 'normal'),
                custom_budget=config.get('thinking_budget'),
                max_tokens=config.get('max_tokens', 8192)
            )

        except Exception as e:
            logger.error(f"❌ 流式深度思考生成失败: {e}")
            yield {'error': str(e)}

    # ==================== 后处理阶段 ====================

    def _post_process_response(
        self,
        generation_result: Dict[str, Any],
        preparation_result: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """后处理响应"""
        result = {
            'answer': generation_result['answer'],
            'model': generation_result['model'],
            'mode': generation_result['mode'],
            'usage': generation_result['usage']
        }

        # 添加思考过程（如果有）
        if 'thinking_process' in generation_result:
            result['thinking_process'] = generation_result['thinking_process']
            result['thinking_analysis'] = generation_result['thinking_analysis']

        # 应用技能后处理
        if config.get('use_skill') and preparation_result.get('skill'):
            skill_result = self.skill_adapter.apply_skill_to_response(
                response=result['answer'],
                skill_context=preparation_result['skill'],
                execution_metadata={
                    'query': preparation_result['query'],
                    'user_id': preparation_result.get('user_id')
                }
            )
            result['skill_applied'] = skill_result
            result['answer'] = skill_result['response']

        # 添加来源信息
        if preparation_result.get('rag'):
            result['sources'] = preparation_result['rag'].get('sources', [])

        # 添加元数据
        result['metadata'] = {
            'memory_used': preparation_result.get('memory') is not None,
            'rag_used': preparation_result.get('rag') is not None,
            'skill_used': preparation_result.get('skill') is not None,
            'chinese_nlp_used': preparation_result.get('chinese_nlp') is not None,
            'memory_sources': preparation_result.get('memory', {}).get('sources_used', []),
            'timestamp': datetime.utcnow().isoformat()
        }

        return result

    # ==================== 保存阶段 ====================

    def _save_conversation(
        self,
        session_id: str,
        project_id: Optional[int],
        query: str,
        result: Dict[str, Any],
        config: Dict[str, Any]
    ):
        """保存对话到各个记忆系统"""
        try:
            if not config.get('use_memory', True):
                return

            # 保存到记忆系统
            self.memory_aggregator.save_to_memory(
                content=f"用户: {query}\n助手: {result['answer']}",
                session_id=session_id,
                project_id=project_id,
                metadata={
                    'model': result['model'],
                    'usage': result['usage']
                },
                target_sources=config.get('save_to_memory_sources', ['long_memory', 'cognee', 'mem0'])
            )

            logger.debug(f"💾 对话已保存到记忆系统")

        except Exception as e:
            logger.warning(f"⚠️ 保存对话失败: {e}")

    # ==================== 辅助方法 ====================

    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """构建系统提示词"""
        base_prompt = """你是FieldMind智能助手，专注于田野调查、学术研究和知识管理。

你的能力：
- 分析和理解复杂的研究文档
- 提供深度的学术见解和分析
- 帮助用户整理和发现知识脉络
- 基于已有材料进行推理和归纳

请以专业、准确、有条理的方式回答问题。"""

        # 添加技能提示词
        if context.get('skill') and context['skill'].get('system_prompt'):
            base_prompt += "\n\n" + context['skill']['system_prompt']

        return base_prompt

    def _build_full_message(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """构建完整消息"""
        parts = []

        # 记忆上下文
        if context.get('memory'):
            memory_context = context['memory'].get('context', '')
            if memory_context:
                parts.append(f"<记忆上下文>\n{memory_context}\n</记忆上下文>")

        # RAG上下文
        if context.get('rag'):
            rag_context = context['rag'].get('context_text', '')
            if rag_context:
                parts.append(f"<文档上下文>\n{rag_context}\n</文档上下文>")

        # 中文NLP分析
        if context.get('chinese_nlp'):
            nlp_info = self._format_nlp_context(context['chinese_nlp'])
            if nlp_info:
                parts.append(f"<语言分析>\n{nlp_info}\n</语言分析>")

        # 用户问题
        parts.append(f"<用户问题>\n{query}\n</用户问题>")

        return "\n\n".join(parts)

    def _format_rag_sources(self, sources: List[Dict]) -> str:
        """格式化RAG来源"""
        if not sources:
            return ""

        parts = []
        for idx, source in enumerate(sources[:5], 1):
            parts.append(
                f"### 来源 {idx}: {source.get('document_name', '未知')}\n"
                f"{source.get('content', '')}\n"
            )

        return "\n".join(parts)

    def _format_nlp_context(self, nlp_result: Dict) -> str:
        """格式化NLP上下文"""
        parts = []

        if nlp_result.get('keywords'):
            keywords_str = ', '.join(nlp_result['keywords'][:10])
            parts.append(f"关键词: {keywords_str}")

        if nlp_result.get('entities'):
            entities_str = ', '.join([f"{e['text']}({e['type']})" for e in nlp_result['entities'][:10]])
            parts.append(f"实体: {entities_str}")

        return "\n".join(parts)

    def _extract_keywords_from_nlp(self, nlp_result: Dict) -> List[str]:
        """从NLP结果提取关键词"""
        keywords = []

        if 'jieba' in nlp_result and nlp_result['jieba'].get('keywords'):
            keywords.extend([kw['keyword'] for kw in nlp_result['jieba']['keywords'][:10]])

        return keywords

    def _extract_entities_from_nlp(self, nlp_result: Dict) -> List[Dict]:
        """从NLP结果提取实体"""
        entities = []

        if 'lac' in nlp_result and nlp_result['lac'].get('entities'):
            entities.extend(nlp_result['lac']['entities'][:10])

        return entities

    def _extract_text_from_response(self, response) -> str:
        """从响应中提取文本"""
        try:
            for block in response.content:
                if block.type == "text":
                    return block.text
            return "无响应内容"
        except Exception as e:
            logger.error(f"提取文本失败: {e}")
            return "响应解析失败"

    def _error_response(self, message: str) -> Dict[str, Any]:
        """错误响应"""
        return {
            'error': True,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }

    # ==================== 服务管理 ====================

    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'client_initialized': self.client is not None,
            'memory_aggregator': self.memory_aggregator is not None,
            'thinking_engine': self.thinking_engine.get_engine_status(),
            'skill_adapter': self.skill_adapter.get_adapter_status(),
            'chinese_nlp': self.chinese_nlp.health_check() if self.chinese_nlp else None,
            'timestamp': datetime.utcnow().isoformat()
        }


# 工厂函数
def create_enhanced_chat_service_v2(db: Session) -> EnhancedChatServiceV2:
    """创建增强对话服务V2实例"""
    return EnhancedChatServiceV2(db)
