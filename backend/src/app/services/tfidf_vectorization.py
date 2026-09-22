"""
TF-IDF向量化服务 - 无需网络的真实向量化实现
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity
import pickle
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class TfidfVectorizationService:
    """基于TF-IDF的向量化服务 - 无需下载模型"""
    def __init__(self, embedding_dim: int = 384, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化TF-IDF向量化服务

        Args:
            embedding_dim: 目标向量维度（通过SVD降维）
        """
        self.embedding_dim = embedding_dim
        self.vectorizer = TfidfVectorizer(
            max_features=embedding_dim,  # 限制特征数量
            ngram_range=(1, 2),  # 使用unigram和bigram
            min_df=1,  # 最小文档频率
            sublinear_tf=True  # 使用子线性TF缩放
        )
        self.is_fitted = False
        self.model_name = "tfidf-local"
        self.corpus_cache = []  # 缓存文本用于重新训练

        logger.info(f"TF-IDF向量化服务初始化，目标维度: {embedding_dim}")

    def fit(self, texts: List[str]):
        """
        训练TF-IDF模型

        Args:
            texts: 训练文本列表
        """
        if not texts:
            logger.warning("训练文本为空")
            return

        try:
            self.vectorizer.fit(texts)
            self.is_fitted = True
            logger.info(f"TF-IDF模型训练完成，词汇量: {len(self.vectorizer.vocabulary_)}")
        except Exception as e:
            logger.error(f"TF-IDF训练失败: {e}")

    def vectorize_text(self, text: str) -> Optional[List[float]]:
        """
        将文本向量化

        Args:
            text: 输入文本

        Returns:
            向量列表
        """
        if not text or not text.strip():
            return None

        try:
            # 如果模型未训练，添加到缓存
            if not self.is_fitted:
                self.corpus_cache.append(text)
                # 需要至少2个文档才能训练TF-IDF
                if len(self.corpus_cache) < 2:
                    # 添加一个通用文档以避免单文档问题
                    self.corpus_cache.append("这是一个通用的参考文档用于TF-IDF训练")
                self.fit(self.corpus_cache)

            # 转换为向量
            vector = self.vectorizer.transform([text]).toarray()[0]

            # 如果维度不足，补零
            if len(vector) < self.embedding_dim:
                vector = np.pad(vector, (0, self.embedding_dim - len(vector)))
            elif len(vector) > self.embedding_dim:
                vector = vector[:self.embedding_dim]

            # 归一化
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm

            return vector.tolist()

        except Exception as e:
            logger.error(f"向量化失败: {e}")
            return None

    def vectorize_chunks(
        self,
        chunks: List[Dict[str, Any]],
        batch_size: int = 32
    ) -> List[Dict[str, Any]]:
        """
        批量向量化chunks

        Args:
            chunks: chunk列表
            batch_size: 批处理大小（保留参数以兼容接口）

        Returns:
            带有embedding的chunk列表
        """
        if not chunks:
            return []

        logger.info(f"开始向量化 {len(chunks)} 个chunks")

        # 提取所有文本
        texts = [chunk["text"] for chunk in chunks]

        # 训练模型（使用所有文本）
        self.fit(texts)

        # 批量向量化
        try:
            vectors = self.vectorizer.transform(texts).toarray()

            # 处理维度和归一化
            processed_vectors = []
            for vector in vectors:
                if len(vector) < self.embedding_dim:
                    vector = np.pad(vector, (0, self.embedding_dim - len(vector)))
                elif len(vector) > self.embedding_dim:
                    vector = vector[:self.embedding_dim]

                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm

                processed_vectors.append(vector.tolist())

            # 添加embedding到每个chunk
            from datetime import datetime
            for i, chunk in enumerate(chunks):
                chunk["embedding"] = processed_vectors[i]
                chunk["embedding_model"] = self.model_name
                chunk["vectorized_at"] = datetime.utcnow()

            logger.info(f"向量化完成: {len(chunks)} 个chunks")

        except Exception as e:
            logger.error(f"批量向量化失败: {e}")
            # fallback: 逐个向量化
            for chunk in chunks:
                embedding = self.vectorize_text(chunk["text"])
                if embedding:
                    chunk["embedding"] = embedding
                    chunk["embedding_model"] = self.model_name
                    from datetime import datetime
                    chunk["vectorized_at"] = datetime.utcnow()

        return chunks

    def save_model(self, filepath: str):
        """保存模型"""
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            logger.info(f"模型已保存: {filepath}")
        except Exception as e:
            logger.error(f"模型保存失败: {e}")

    def load_model(self, filepath: str):
        """加载模型"""
        try:
            with open(filepath, 'rb') as f:
                self.vectorizer = pickle.load(f)
            self.is_fitted = True
            logger.info(f"模型已加载: {filepath}")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
