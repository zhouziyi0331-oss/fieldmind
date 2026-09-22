"""
重排模型服务（Reranker）

核心功能：
1. 对召回的候选结果进行精排
2. 输出独立的相关性分数（不与向量分数混用）
3. 支持多种重排模型

技术栈：
- sentence-transformers/cross-encoder（轻量级）
- Cohere Rerank API（云端）
- BGE Reranker（中文优化）
"""

import logging
from typing import List, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class RerankerService:
    """重排模型服务"""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        """
        初始化重排模型

        Args:
            model_name: 模型名称
                - "BAAI/bge-reranker-base" (推荐，中文优化)
                - "BAAI/bge-reranker-large" (更强，更慢)
                - "cross-encoder/ms-marco-MiniLM-L-6-v2" (英文，快速)
        """
        self.model_name = model_name
        self.model = None
        self._init_model()

    def _init_model(self):
        """初始化模型"""
        try:
            logger.info(f"🔧 初始化重排模型: {self.model_name}")

            from sentence_transformers import CrossEncoder

            self.model = CrossEncoder(self.model_name)

            logger.info(f"✅ 重排模型加载成功")

        except ImportError:
            logger.warning("⚠️ sentence-transformers 未安装")
            logger.info("   请运行: pip install sentence-transformers")
            self.model = None

        except Exception as e:
            logger.error(f"❌ 重排模型加载失败: {e}")
            self.model = None

    def predict(
        self,
        query: str,
        texts: List[str]
    ) -> List[float]:
        """
        预测相关性分数

        Args:
            query: 查询文本
            texts: 候选文本列表

        Returns:
            相关性分数列表（越高越相关）
        """
        if not self.model:
            logger.warning("重排模型未加载，返回默认分数")
            return [0.5] * len(texts)

        try:
            # 构建输入对
            pairs = [[query, text] for text in texts]

            # 预测分数
            scores = self.model.predict(pairs)

            # 转换为列表
            if isinstance(scores, np.ndarray):
                scores = scores.tolist()

            logger.info(f"   重排评分完成: {len(scores)} 个结果")

            return scores

        except Exception as e:
            logger.error(f"❌ 重排预测失败: {e}")
            return [0.5] * len(texts)

    def rerank(
        self,
        query: str,
        texts: List[str],
        top_k: int = None
    ) -> List[Tuple[int, float]]:
        """
        重排并返回排序后的索引和分数

        Args:
            query: 查询文本
            texts: 候选文本列表
            top_k: 返回前 k 个（None 表示全部）

        Returns:
            [(索引, 分数), ...] 按分数降序排列
        """
        scores = self.predict(query, texts)

        # 创建 (索引, 分数) 对
        indexed_scores = list(enumerate(scores))

        # 按分数降序排序
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        # 截取 top_k
        if top_k:
            indexed_scores = indexed_scores[:top_k]

        return indexed_scores


class CohereReranker:
    """Cohere Rerank API（云端重排）"""

    def __init__(self, api_key: str):
        """
        初始化 Cohere Reranker

        Args:
            api_key: Cohere API Key
        """
        self.api_key = api_key
        self.client = None
        self._init_client()

    def _init_client(self):
        """初始化客户端"""
        try:
            import cohere

            self.client = cohere.Client(self.api_key)
            logger.info("✅ Cohere Reranker 初始化成功")

        except ImportError:
            logger.warning("⚠️ cohere 未安装，请运行: pip install cohere")
            self.client = None

        except Exception as e:
            logger.error(f"❌ Cohere Reranker 初始化失败: {e}")
            self.client = None

    def predict(
        self,
        query: str,
        texts: List[str]
    ) -> List[float]:
        """预测相关性分数"""
        if not self.client:
            return [0.5] * len(texts)

        try:
            # 调用 Cohere Rerank API
            results = self.client.rerank(
                query=query,
                documents=texts,
                model="rerank-english-v2.0"
            )

            # 提取分数
            scores = [0.0] * len(texts)
            for result in results.results:
                scores[result.index] = result.relevance_score

            return scores

        except Exception as e:
            logger.error(f"❌ Cohere Rerank 失败: {e}")
            return [0.5] * len(texts)


# 全局单例
_reranker_service = None


def get_reranker_service(
    model_name: str = "BAAI/bge-reranker-base"
) -> RerankerService:
    """获取重排服务单例"""
    global _reranker_service
    if _reranker_service is None:
        _reranker_service = RerankerService(model_name)
    return _reranker_service


if __name__ == "__main__":
    print("=" * 80)
    print("🧪 重排模型服务测试")
    print("=" * 80)

    service = get_reranker_service()

    if service.model:
        print("\n✅ 模型加载成功")

        # 测试
        query = "什么是机器学习？"
        texts = [
            "机器学习是人工智能的一个分支。",
            "今天天气不错。",
            "深度学习是机器学习的子领域。"
        ]

        scores = service.predict(query, texts)

        print("\n相关性分数:")
        for i, (text, score) in enumerate(zip(texts, scores)):
            print(f"   {i+1}. [{score:.4f}] {text}")

    else:
        print("\n⚠️ 模型未加载")
        print("   请安装: pip install sentence-transformers")
