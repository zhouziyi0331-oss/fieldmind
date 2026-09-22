"""
真实嵌入服务 (Real Embedding Service)

使用 sentence-transformers 替代模拟实现
"""
from typing import List, Optional
import numpy as np
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class RealEmbeddingService:
    """
    真实嵌入服务

    使用 sentence-transformers 模型生成文本嵌入
    """

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5"):
        """
        初始化嵌入服务

        Args:
            model_name: 模型名称
                - BAAI/bge-small-zh-v1.5: 中文嵌入，速度快
                - BAAI/bge-base-zh-v1.5: 中文嵌入，效果好
                - BAAI/bge-large-zh-v1.5: 中文嵌入，效果最好
                - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2: 多语言
        """
        self.model_name = model_name
        self.model = None
        self.embedding_dim = None
        self._initialize_model()

    def _initialize_model(self):
        """延迟初始化模型（避免启动时加载）"""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"正在加载嵌入模型: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)

            # 获取嵌入维度
            test_embedding = self.model.encode("测试")
            self.embedding_dim = len(test_embedding)

            logger.info(f"✅ 嵌入模型加载成功: {self.model_name} (维度: {self.embedding_dim})")

        except ImportError:
            logger.error("❌ sentence-transformers 未安装，回退到模拟模式")
            self.model = None
            self.embedding_dim = 768
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {str(e)}，回退到模拟模式")
            self.model = None
            self.embedding_dim = 768

    async def embed_text(self, text: str) -> np.ndarray:
        """
        生成文本嵌入

        Args:
            text: 文本

        Returns:
            嵌入向量
        """
        if self.model is None:
            # 回退到模拟模式
            return self._simulate_embedding(text)

        try:
            # 使用真实模型
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding

        except Exception as e:
            logger.error(f"嵌入生成失败: {str(e)}，回退到模拟模式")
            return self._simulate_embedding(text)

    async def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        批量生成嵌入

        Args:
            texts: 文本列表
            batch_size: 批次大小

        Returns:
            嵌入向量列表
        """
        if self.model is None:
            return [self._simulate_embedding(text) for text in texts]

        try:
            # 使用真实模型批量处理
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 10
            )
            return list(embeddings)

        except Exception as e:
            logger.error(f"批量嵌入失败: {str(e)}，回退到模拟模式")
            return [self._simulate_embedding(text) for text in texts]

    def _simulate_embedding(self, text: str) -> np.ndarray:
        """模拟嵌入（回退方案）"""
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        seed = int.from_bytes(hash_obj.digest()[:4], 'big')
        np.random.seed(seed)
        embedding = np.random.randn(self.embedding_dim)
        embedding = embedding / np.linalg.norm(embedding)
        return embedding


# 全局单例
_embedding_service_instance: Optional[RealEmbeddingService] = None


def get_embedding_service(model_name: str = "BAAI/bge-small-zh-v1.5") -> RealEmbeddingService:
    """获取全局嵌入服务实例（单例模式）"""
    global _embedding_service_instance

    if _embedding_service_instance is None:
        _embedding_service_instance = RealEmbeddingService(model_name)

    return _embedding_service_instance
