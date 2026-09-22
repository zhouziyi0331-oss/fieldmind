"""
真实LLM服务 (Real LLM Service)

使用 OpenAI API 或本地模型替代模拟实现
"""
from typing import List, Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class RealLLMService:
    """
    真实LLM服务

    支持多种LLM后端：
    - OpenAI (gpt-3.5-turbo, gpt-4)
    - 本地模型 (通过ollama)
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        初始化LLM服务

        Args:
            provider: 提供商 (openai, ollama)
            model: 模型名称
            api_key: API密钥
            base_url: API基础URL
        """
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """初始化LLM客户端"""
        try:
            if self.provider == "openai":
                from openai import OpenAI

                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                logger.info(f"✅ OpenAI客户端初始化成功: {self.model}")

            elif self.provider == "ollama":
                # Ollama本地模型
                from openai import OpenAI
                self.client = OpenAI(
                    base_url="http://localhost:11434/v1",
                    api_key="ollama"  # Ollama不需要真实API key
                )
                logger.info(f"✅ Ollama客户端初始化成功: {self.model}")

            else:
                logger.warning(f"⚠️  未知的LLM提供商: {self.provider}，回退到模拟模式")
                self.client = None

        except ImportError:
            logger.error("❌ openai库未安装，回退到模拟模式")
            self.client = None
        except Exception as e:
            logger.error(f"❌ LLM客户端初始化失败: {str(e)}，回退到模拟模式")
            self.client = None

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        生成文本

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            生成的文本
        """
        if self.client is None:
            return self._simulate_generation(prompt)

        try:
            messages = []

            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM生成失败: {str(e)}，回退到模拟模式")
            return self._simulate_generation(prompt)

    async def generate_with_context(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        基于上下文生成答案（RAG专用）

        Args:
            query: 用户查询
            context: 检索到的上下文
            conversation_history: 对话历史

        Returns:
            生成的答案
        """
        system_prompt = """你是一个智能知识助手，基于提供的上下文回答用户问题。

要求：
1. 答案必须基于上下文，不要编造信息
2. 如果上下文中没有相关信息，明确告知用户
3. 回答要准确、简洁、有条理
4. 尽可能引用上下文中的原文
"""

        user_prompt = f"""## 上下文信息

{context}

## 用户问题

{query}

## 回答要求

请基于上述上下文回答用户问题。如果上下文中没有相关信息，请告知用户。"""

        # 构建完整的消息历史
        messages = [{"role": "system", "content": system_prompt}]

        # 添加对话历史（最近3轮）
        if conversation_history:
            for msg in conversation_history[-3:]:
                messages.append(msg)

        messages.append({"role": "user", "content": user_prompt})

        if self.client is None:
            return self._simulate_generation(query)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"RAG生成失败: {str(e)}，回退到模拟模式")
            return self._simulate_generation(query)

    def _simulate_generation(self, query: str) -> str:
        """模拟生成（回退方案）"""
        return f"根据提供的上下文，关于「{query}」的信息如下：这是系统基于检索到的文档生成的回答。（注意：当前使用模拟模式，请配置真实LLM以获得更好的效果）"


# 全局单例
_llm_service_instance: Optional[RealLLMService] = None


def get_llm_service(
    provider: str = "openai",
    model: str = "gpt-3.5-turbo"
) -> RealLLMService:
    """获取全局LLM服务实例（单例模式）"""
    global _llm_service_instance

    if _llm_service_instance is None:
        _llm_service_instance = RealLLMService(provider=provider, model=model)

    return _llm_service_instance
