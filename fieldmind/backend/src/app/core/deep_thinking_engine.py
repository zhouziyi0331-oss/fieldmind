"""
深度思考引擎 (Deep Thinking Engine)

封装Claude Extended Thinking功能，提供：
1. 扩展思考模式（Extended Thinking）
2. 思考预算管理
3. 思考过程提取和分析
4. 思考质量评估
5. 自适应思考深度

基于Claude 3.7 Sonnet的扩展思考能力
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import anthropic
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class DeepThinkingEngine:
    """深度思考引擎"""

    def __init__(self):
        """初始化深度思考引擎"""
        self.client = None
        self.extended_thinking_model = "claude-3-7-sonnet-20250219"
        self.default_thinking_budget = 10000  # 默认思考token预算

        # 思考深度配置
        self.thinking_levels = {
            'quick': {'budget': 2000, 'description': '快速思考'},
            'normal': {'budget': 5000, 'description': '标准思考'},
            'deep': {'budget': 10000, 'description': '深度思考'},
            'thorough': {'budget': 20000, 'description': '彻底思考'},
            'extreme': {'budget': 50000, 'description': '极致思考'}
        }

        self._init_client()

        logger.info("✅ 深度思考引擎初始化")

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

    # ==================== 核心思考方法 ====================

    def think_and_respond(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        thinking_level: str = 'normal',
        custom_budget: Optional[int] = None,
        max_tokens: int = 8192,
        context: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        深度思考并生成回答

        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            thinking_level: 思考深度级别 (quick/normal/deep/thorough/extreme)
            custom_budget: 自定义思考预算（覆盖level）
            max_tokens: 最大输出tokens
            context: 对话历史上下文

        Returns:
            包含思考过程和回答的完整结果
        """
        if not self.client:
            return self._fallback_response("深度思考引擎未初始化")

        try:
            # 确定思考预算
            if custom_budget:
                thinking_budget = custom_budget
            elif thinking_level in self.thinking_levels:
                thinking_budget = self.thinking_levels[thinking_level]['budget']
            else:
                thinking_budget = self.default_thinking_budget

            logger.info(
                f"🧠 开始深度思考: level={thinking_level}, "
                f"budget={thinking_budget} tokens"
            )

            # 构建消息
            messages = []

            # 添加上下文历史
            if context:
                messages.extend(context)

            # 添加当前提示
            messages.append({
                "role": "user",
                "content": prompt
            })

            # 调用扩展思考API
            start_time = datetime.now()

            response = self.client.messages.create(
                model=self.extended_thinking_model,
                max_tokens=max_tokens,
                thinking={
                    "type": "enabled",
                    "budget_tokens": thinking_budget
                },
                messages=messages,
                system=system_prompt or self._get_default_system_prompt()
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            # 提取思考过程和回答
            thinking_process = self._extract_thinking(response)
            answer = self._extract_answer(response)

            # 分析思考质量
            thinking_analysis = self._analyze_thinking(
                thinking_process,
                thinking_budget
            )

            result = {
                'answer': answer,
                'thinking_process': thinking_process,
                'thinking_analysis': thinking_analysis,
                'model': self.extended_thinking_model,
                'thinking_level': thinking_level,
                'thinking_budget': thinking_budget,
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                },
                'processing_time': processing_time,
                'timestamp': datetime.utcnow().isoformat()
            }

            logger.info(
                f"✅ 深度思考完成: "
                f"thinking_tokens={thinking_analysis.get('thinking_length', 0)}, "
                f"time={processing_time:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(f"❌ 深度思考失败: {e}")
            return self._fallback_response(f"思考失败: {str(e)}")

    def stream_think_and_respond(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        thinking_level: str = 'normal',
        custom_budget: Optional[int] = None,
        max_tokens: int = 8192
    ):
        """
        流式深度思考并生成回答

        Args:
            同think_and_respond

        Yields:
            流式思考片段和回答片段
        """
        if not self.client:
            yield {'error': '深度思考引擎未初始化'}
            return

        try:
            # 确定思考预算
            if custom_budget:
                thinking_budget = custom_budget
            elif thinking_level in self.thinking_levels:
                thinking_budget = self.thinking_levels[thinking_level]['budget']
            else:
                thinking_budget = self.default_thinking_budget

            logger.info(f"🧠 开始流式深度思考: level={thinking_level}")

            # 流式调用
            with self.client.messages.stream(
                model=self.extended_thinking_model,
                max_tokens=max_tokens,
                thinking={
                    "type": "enabled",
                    "budget_tokens": thinking_budget
                },
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                system=system_prompt or self._get_default_system_prompt()
            ) as stream:
                # 追踪思考和回答内容
                full_thinking = ""
                full_answer = ""
                current_type = None

                for event in stream:
                    # 处理不同类型的流式事件
                    if hasattr(event, 'type'):
                        if event.type == 'content_block_start':
                            # 内容块开始
                            if hasattr(event, 'content_block'):
                                block = event.content_block
                                if hasattr(block, 'type'):
                                    current_type = block.type
                                    if block.type == 'thinking':
                                        yield {
                                            'type': 'thinking_start',
                                            'message': '🧠 思考中...'
                                        }
                                    elif block.type == 'text':
                                        yield {
                                            'type': 'answer_start',
                                            'message': '💬 回答中...'
                                        }

                        elif event.type == 'content_block_delta':
                            # 内容增量
                            if hasattr(event, 'delta'):
                                delta = event.delta
                                if hasattr(delta, 'type'):
                                    if delta.type == 'thinking_delta':
                                        # 思考内容增量
                                        thinking_text = delta.thinking
                                        full_thinking += thinking_text
                                        yield {
                                            'type': 'thinking_delta',
                                            'content': thinking_text
                                        }
                                    elif delta.type == 'text_delta':
                                        # 回答内容增量
                                        text = delta.text
                                        full_answer += text
                                        yield {
                                            'type': 'answer_delta',
                                            'content': text
                                        }

                        elif event.type == 'content_block_stop':
                            # 内容块结束
                            if current_type == 'thinking':
                                yield {
                                    'type': 'thinking_complete',
                                    'full_thinking': full_thinking
                                }
                            elif current_type == 'text':
                                yield {
                                    'type': 'answer_complete',
                                    'full_answer': full_answer
                                }

                        elif event.type == 'message_stop':
                            # 消息结束
                            thinking_analysis = self._analyze_thinking(
                                full_thinking,
                                thinking_budget
                            )
                            yield {
                                'type': 'complete',
                                'thinking_analysis': thinking_analysis
                            }

        except Exception as e:
            logger.error(f"❌ 流式深度思考失败: {e}")
            yield {'error': str(e)}

    # ==================== 自适应思考 ====================

    def auto_think(
        self,
        prompt: str,
        complexity_hint: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 8192
    ) -> Dict[str, Any]:
        """
        自适应深度思考

        根据问题复杂度自动选择合适的思考深度

        Args:
            prompt: 用户输入
            complexity_hint: 复杂度提示 (simple/moderate/complex/very_complex)
            system_prompt: 系统提示词
            max_tokens: 最大输出tokens

        Returns:
            思考和回答结果
        """
        # 分析问题复杂度
        if complexity_hint:
            complexity = complexity_hint
        else:
            complexity = self._analyze_complexity(prompt)

        # 映射复杂度到思考级别
        complexity_to_level = {
            'simple': 'quick',
            'moderate': 'normal',
            'complex': 'deep',
            'very_complex': 'thorough',
            'extremely_complex': 'extreme'
        }

        thinking_level = complexity_to_level.get(complexity, 'normal')

        logger.info(
            f"🤖 自适应思考: "
            f"complexity={complexity}, level={thinking_level}"
        )

        return self.think_and_respond(
            prompt=prompt,
            system_prompt=system_prompt,
            thinking_level=thinking_level,
            max_tokens=max_tokens
        )

    def _analyze_complexity(self, prompt: str) -> str:
        """
        分析问题复杂度

        基于启发式规则：
        - 问题长度
        - 关键词识别
        - 句子结构
        """
        prompt_length = len(prompt)

        # 复杂问题关键词
        complex_keywords = [
            '分析', '比较', '评估', '解释', '论证', '推导',
            'analyze', 'compare', 'evaluate', 'explain', 'argue', 'derive',
            '为什么', '如何', '怎样', 'why', 'how',
            '深入', '详细', '全面', 'deep', 'detailed', 'comprehensive'
        ]

        # 非常复杂问题关键词
        very_complex_keywords = [
            '系统性', '多维度', '跨学科', '综合',
            'systematic', 'multi-dimensional', 'interdisciplinary', 'comprehensive',
            '批判性', '辩证', 'critical', 'dialectical'
        ]

        # 计算复杂度得分
        score = 0

        # 长度因素
        if prompt_length > 500:
            score += 3
        elif prompt_length > 200:
            score += 2
        elif prompt_length > 100:
            score += 1

        # 关键词因素
        for keyword in complex_keywords:
            if keyword in prompt:
                score += 1

        for keyword in very_complex_keywords:
            if keyword in prompt:
                score += 2

        # 问号数量（多个问题）
        question_marks = prompt.count('?') + prompt.count('？')
        if question_marks > 2:
            score += 2
        elif question_marks > 1:
            score += 1

        # 映射得分到复杂度
        if score >= 8:
            return 'extremely_complex'
        elif score >= 5:
            return 'very_complex'
        elif score >= 3:
            return 'complex'
        elif score >= 1:
            return 'moderate'
        else:
            return 'simple'

    # ==================== 思考分析 ====================

    def _extract_thinking(self, response) -> Optional[str]:
        """提取思考过程"""
        try:
            for block in response.content:
                if hasattr(block, 'type') and block.type == "thinking":
                    return block.thinking
            return None
        except Exception as e:
            logger.error(f"提取思考过程失败: {e}")
            return None

    def _extract_answer(self, response) -> str:
        """提取回答内容"""
        try:
            for block in response.content:
                if hasattr(block, 'type') and block.type == "text":
                    return block.text
            return "无回答内容"
        except Exception as e:
            logger.error(f"提取回答内容失败: {e}")
            return "回答解析失败"

    def _analyze_thinking(
        self,
        thinking_process: Optional[str],
        budget: int
    ) -> Dict[str, Any]:
        """
        分析思考质量

        评估指标：
        - 思考深度（长度）
        - 结构化程度
        - 逻辑链条
        - 预算使用率
        """
        if not thinking_process:
            return {
                'thinking_length': 0,
                'budget_usage': 0,
                'depth_score': 0,
                'quality': 'no_thinking'
            }

        thinking_length = len(thinking_process)
        estimated_tokens = thinking_length // 4  # 简单估算

        # 预算使用率
        budget_usage = min((estimated_tokens / budget) * 100, 100)

        # 深度评分（基于关键指标）
        depth_indicators = {
            'logical_chains': thinking_process.count('因为') + thinking_process.count('所以') +
                            thinking_process.count('because') + thinking_process.count('therefore'),
            'considerations': thinking_process.count('考虑') + thinking_process.count('注意') +
                            thinking_process.count('consider') + thinking_process.count('note'),
            'alternatives': thinking_process.count('另一方面') + thinking_process.count('alternatively'),
            'conclusions': thinking_process.count('结论') + thinking_process.count('总结') +
                         thinking_process.count('conclusion') + thinking_process.count('summary')
        }

        depth_score = min(
            (sum(depth_indicators.values()) / 10) * 100,
            100
        )

        # 质量评级
        if depth_score >= 70:
            quality = 'excellent'
        elif depth_score >= 50:
            quality = 'good'
        elif depth_score >= 30:
            quality = 'moderate'
        else:
            quality = 'basic'

        return {
            'thinking_length': thinking_length,
            'estimated_thinking_tokens': estimated_tokens,
            'budget': budget,
            'budget_usage': round(budget_usage, 2),
            'depth_score': round(depth_score, 2),
            'depth_indicators': depth_indicators,
            'quality': quality
        }

    # ==================== 辅助方法 ====================

    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        return """你是FieldMind智能助手，具有深度思考能力。

在回答问题时，请：
1. 充分思考问题的各个方面
2. 考虑多种可能的角度和解释
3. 建立清晰的逻辑推理链条
4. 得出有充分依据的结论

你的思考过程会被记录和分析，以持续改进回答质量。"""

    def _fallback_response(self, error_message: str) -> Dict[str, Any]:
        """降级响应"""
        return {
            'answer': f"抱歉，{error_message}",
            'thinking_process': None,
            'error': True,
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_thinking_levels(self) -> Dict[str, Dict[str, Any]]:
        """获取所有思考级别配置"""
        return self.thinking_levels

    def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            'initialized': self.client is not None,
            'model': self.extended_thinking_model,
            'default_budget': self.default_thinking_budget,
            'available_levels': list(self.thinking_levels.keys()),
            'timestamp': datetime.utcnow().isoformat()
        }


# 全局单例
_deep_thinking_engine_instance = None


def get_deep_thinking_engine() -> DeepThinkingEngine:
    """获取深度思考引擎单例"""
    global _deep_thinking_engine_instance
    if _deep_thinking_engine_instance is None:
        _deep_thinking_engine_instance = DeepThinkingEngine()
    return _deep_thinking_engine_instance
