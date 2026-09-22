"""
优化的向量化服务 - Week 2 Day 1-2
批量处理 + GPU 加速 + 内存优化
"""
import numpy as np
import torch
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
from tqdm import tqdm
import time

logger = logging.getLogger(__name__)


class OptimizedVectorizationService:
    """优化的向量化服务"""

    def __init__(
        self,
        model_path: str = "./models/bge-large-zh-v1.5",
        batch_size: int = 64,
        use_gpu: bool = True
    ):
        """
        初始化向量化服务

        Args:
            model_path: 模型路径
            batch_size: 批次大小
            use_gpu: 是否使用 GPU
        """
        self.model_path = model_path
        self.batch_size = batch_size

        # 检测 GPU 可用性
        self.device = self._detect_device(use_gpu)

        # 加载模型
        self.model = self._load_model()

        logger.info(
            f"✅ 向量化服务已初始化 "
            f"(设备: {self.device}, 批次: {batch_size})"
        )

    def _detect_device(self, use_gpu: bool) -> str:
        """检测可用设备"""
        if use_gpu and torch.cuda.is_available():
            device = "cuda"
            logger.info(f"🎮 使用 GPU: {torch.cuda.get_device_name(0)}")
        elif use_gpu and torch.backends.mps.is_available():
            device = "mps"  # Apple Silicon
            logger.info("🍎 使用 Apple Silicon GPU (MPS)")
        else:
            device = "cpu"
            logger.info("💻 使用 CPU")

        return device

    def _load_model(self):
        """加载嵌入模型"""
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(
                self.model_path,
                device=self.device
            )

            # 设置为评估模式
            model.eval()

            logger.info(f"✅ 模型已加载: {self.model_path}")
            return model

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            raise

    def vectorize_batch(
        self,
        texts: List[str],
        show_progress: bool = True,
        normalize: bool = True
    ) -> np.ndarray:
        """
        批量向量化文本

        Args:
            texts: 文本列表
            show_progress: 是否显示进度
            normalize: 是否归一化向量

        Returns:
            向量数组 (n, embedding_dim)
        """
        if not texts:
            return np.array([])

        start_time = time.time()
        total_texts = len(texts)

        logger.info(f"开始向量化 {total_texts} 个文本...")

        all_embeddings = []

        # 分批处理
        for i in tqdm(
            range(0, total_texts, self.batch_size),
            desc="向量化",
            disable=not show_progress
        ):
            batch = texts[i:i + self.batch_size]

            # 批量编码
            with torch.no_grad():  # 禁用梯度计算以节省内存
                embeddings = self.model.encode(
                    batch,
                    batch_size=self.batch_size,
                    device=self.device,
                    show_progress_bar=False,
                    normalize_embeddings=normalize,
                    convert_to_numpy=True
                )

            all_embeddings.append(embeddings)

            # 清理 GPU 缓存
            if self.device in ["cuda", "mps"]:
                torch.cuda.empty_cache() if self.device == "cuda" else None

        # 合并所有批次
        result = np.vstack(all_embeddings)

        duration = time.time() - start_time
        speed = total_texts / duration

        logger.info(
            f"✅ 向量化完成: {total_texts} 文本, "
            f"耗时: {duration:.2f}s, 速度: {speed:.1f} 文本/秒"
        )

        return result

    def vectorize_with_metadata(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        向量化并附加元数据

        Args:
            texts: 文本列表
            metadatas: 元数据列表
            show_progress: 是否显示进度

        Returns:
            包含向量和元数据的列表
        """
        if len(texts) != len(metadatas):
            raise ValueError("texts 和 metadatas 长度必须相同")

        embeddings = self.vectorize_batch(texts, show_progress)

        results = []
        for i, (text, embedding, metadata) in enumerate(
            zip(texts, embeddings, metadatas)
        ):
            results.append({
                "text": text,
                "embedding": embedding.tolist(),
                "metadata": metadata,
                "index": i
            })

        return results

    def batch_insert_to_chromadb(
        self,
        collection,
        embeddings: np.ndarray,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str],
        batch_size: int = 100
    ):
        """
        批量插入到 ChromaDB

        Args:
            collection: ChromaDB 集合
            embeddings: 向量数组
            documents: 文档列表
            metadatas: 元数据列表
            ids: ID 列表
            batch_size: 插入批次大小
        """
        total = len(embeddings)

        logger.info(f"开始批量插入 {total} 条数据到 ChromaDB...")

        for i in tqdm(range(0, total, batch_size), desc="插入ChromaDB"):
            end = min(i + batch_size, total)

            collection.add(
                embeddings=embeddings[i:end].tolist(),
                documents=documents[i:end],
                metadatas=metadatas[i:end],
                ids=ids[i:end]
            )

        logger.info(f"✅ 批量插入完成: {total} 条")

    def similarity_search(
        self,
        collection,
        query_text: str,
        top_k: int = 10,
        filter: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        相似度搜索

        Args:
            collection: ChromaDB 集合
            query_text: 查询文本
            top_k: 返回结果数量
            filter: 过滤条件

        Returns:
            搜索结果列表
        """
        # 向量化查询
        query_embedding = self.vectorize_batch(
            [query_text],
            show_progress=False
        )[0]

        # 搜索
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=filter
        )

        # 格式化结果
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })

        return formatted_results

    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        import psutil
        process = psutil.Process()

        memory_info = {
            "cpu_memory_mb": process.memory_info().rss / 1024 / 1024,
            "cpu_memory_percent": process.memory_percent()
        }

        if self.device == "cuda" and torch.cuda.is_available():
            memory_info.update({
                "gpu_memory_allocated_mb": torch.cuda.memory_allocated() / 1024 / 1024,
                "gpu_memory_reserved_mb": torch.cuda.memory_reserved() / 1024 / 1024
            })

        return memory_info

    def benchmark(self, sample_texts: List[str]) -> Dict[str, Any]:
        """
        性能基准测试

        Args:
            sample_texts: 样本文本列表

        Returns:
            基准测试结果
        """
        logger.info("开始性能基准测试...")

        # 测试不同批次大小
        batch_sizes = [16, 32, 64, 128]
        results = {}

        for bs in batch_sizes:
            if bs > len(sample_texts):
                continue

            original_batch_size = self.batch_size
            self.batch_size = bs

            start = time.time()
            self.vectorize_batch(sample_texts, show_progress=False)
            duration = time.time() - start

            results[f"batch_{bs}"] = {
                "duration": duration,
                "speed": len(sample_texts) / duration
            }

            self.batch_size = original_batch_size

        # 内存使用
        memory = self.get_memory_usage()

        return {
            "device": self.device,
            "batch_size_tests": results,
            "memory_usage": memory
        }


# 全局实例
_vectorization_service: Optional[OptimizedVectorizationService] = None


def get_vectorization_service() -> OptimizedVectorizationService:
    """获取全局向量化服务实例"""
    global _vectorization_service

    if _vectorization_service is None:
        _vectorization_service = OptimizedVectorizationService()

    return _vectorization_service
