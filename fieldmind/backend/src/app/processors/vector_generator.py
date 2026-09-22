"""
向量生成器
将文本转换为向量表示
"""

import os
from typing import List, Optional, Dict, Any
import numpy as np

from app.core.logging import logger, log_ai_request
from app.core.exceptions import AIServiceException
from app.core.errors import ErrorCode


class VectorGenerator:
    """向量生成器（统一接口）"""

    def __init__(
        self,
        provider: str = "openai",
        model: str = "text-embedding-ada-002"
    ):
        """
        初始化向量生成器

        Args:
            provider: 提供商（openai, huggingface等）
            model: 模型名称
        """
        self.provider = provider
        self.model = model

        # 根据提供商选择具体实现
        if provider == "openai":
            self.generator = OpenAIEmbedding(model)
        elif provider == "huggingface":
            self.generator = HuggingFaceEmbedding(model)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def generate(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        生成向量

        Args:
            texts: 文本列表
            batch_size: 批处理大小

        Returns:
            List[List[float]]: 向量列表
        """
        return self.generator.generate(texts, batch_size)

    def generate_single(self, text: str) -> List[float]:
        """
        生成单个向量

        Args:
            text: 文本

        Returns:
            List[float]: 向量
        """
        vectors = self.generate([text])
        return vectors[0] if vectors else []


class OpenAIEmbedding:
    """OpenAI 向量生成"""

    def __init__(self, model: str = "text-embedding-ada-002"):
        """
        初始化 OpenAI 向量生成

        Args:
            model: 模型名称
        """
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            logger.warning("OPENAI_API_KEY 未设置")

    def generate(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        批量生成向量

        Args:
            texts: 文本列表
            batch_size: 批处理大小

        Returns:
            List[List[float]]: 向量列表
        """
        import time
        import openai

        if not self.api_key:
            raise AIServiceException(
                error_code=ErrorCode.AI_SERVICE_ERROR,
                message="OpenAI API key not configured"
            )

        openai.api_key = self.api_key

        all_embeddings = []

        # 分批处理
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            start_time = time.time()

            try:
                response = openai.Embedding.create(
                    input=batch,
                    model=self.model
                )

                duration = time.time() - start_time

                # 提取向量
                embeddings = [item['embedding'] for item in response['data']]
                all_embeddings.extend(embeddings)

                # 记录日志
                log_ai_request(
                    provider="openai",
                    model=self.model,
                    operation="embedding",
                    tokens=response['usage']['total_tokens'],
                    duration=duration,
                    success=True
                )

                logger.info(
                    f"生成向量: {len(batch)} 个文本, 耗时 {duration:.2f}s",
                    model=self.model,
                    tokens=response['usage']['total_tokens']
                )

            except Exception as e:
                logger.error(f"OpenAI 向量生成失败: {e}")

                log_ai_request(
                    provider="openai",
                    model=self.model,
                    operation="embedding",
                    duration=time.time() - start_time,
                    success=False,
                    error=str(e)
                )

                raise AIServiceException(
                    error_code=ErrorCode.AI_SERVICE_ERROR,
                    message=f"Failed to generate embeddings: {str(e)}"
                )

        return all_embeddings


class HuggingFaceEmbedding:
    """HuggingFace 向量生成（本地模型）"""

    def __init__(self, model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        初始化 HuggingFace 向量生成

        Args:
            model: 模型名称
        """
        self.model_name = model
        self.model = None

    def _load_model(self):
        """延迟加载模型"""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info(f"加载 HuggingFace 模型: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)

            except Exception as e:
                logger.error(f"加载模型失败: {e}")
                raise AIServiceException(
                    error_code=ErrorCode.AI_SERVICE_ERROR,
                    message=f"Failed to load model: {str(e)}"
                )

    def generate(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        批量生成向量

        Args:
            texts: 文本列表
            batch_size: 批处理大小

        Returns:
            List[List[float]]: 向量列表
        """
        import time

        self._load_model()

        start_time = time.time()

        try:
            # 生成向量
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )

            duration = time.time() - start_time

            # 转换为列表
            embeddings_list = [emb.tolist() for emb in embeddings]

            log_ai_request(
                provider="huggingface",
                model=self.model_name,
                operation="embedding",
                tokens=sum(len(text.split()) for text in texts),
                duration=duration,
                success=True
            )

            logger.info(
                f"生成向量: {len(texts)} 个文本, 耗时 {duration:.2f}s",
                model=self.model_name
            )

            return embeddings_list

        except Exception as e:
            logger.error(f"HuggingFace 向量生成失败: {e}")

            log_ai_request(
                provider="huggingface",
                model=self.model_name,
                operation="embedding",
                duration=time.time() - start_time,
                success=False,
                error=str(e)
            )

            raise AIServiceException(
                error_code=ErrorCode.AI_SERVICE_ERROR,
                message=f"Failed to generate embeddings: {str(e)}"
            )


class MockEmbedding:
    """
    Mock 向量生成（用于测试）

    生成随机向量
    """

    def __init__(self, dimension: int = 1536):
        """
        初始化 Mock 向量生成

        Args:
            dimension: 向量维度
        """
        self.dimension = dimension

    def generate(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        生成随机向量

        Args:
            texts: 文本列表
            batch_size: 批处理大小（忽略）

        Returns:
            List[List[float]]: 随机向量列表
        """
        embeddings = []

        for text in texts:
            # 生成随机向量
            vector = np.random.rand(self.dimension).astype(np.float32)

            # 归一化
            vector = vector / np.linalg.norm(vector)

            embeddings.append(vector.tolist())

        logger.info(f"生成 Mock 向量: {len(texts)} 个文本")

        return embeddings


# 便捷函数
def get_vector_generator(
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> VectorGenerator:
    """
    获取向量生成器

    Args:
        provider: 提供商（从环境变量读取，如果未提供）
        model: 模型名称（从环境变量读取，如果未提供）

    Returns:
        VectorGenerator: 向量生成器
    """
    provider = provider or os.getenv("EMBEDDING_PROVIDER", "openai")
    model = model or os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

    return VectorGenerator(provider=provider, model=model)
