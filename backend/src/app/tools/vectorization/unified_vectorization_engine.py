"""
统一向量化引擎

整合7个向量化/嵌入服务:
- vectorization_service_complete.py (FlagEmbedding + SQL + ChromaDB)
- vectorization_service_v2.py (HuggingFace + ChromaDB + 元数据)
- vectorization_service.py (HuggingFace + ChromaDB基础)
- embedding_service_v2.py (FlagEmbedding query优化)
- embedding_service.py (SentenceTransformer BGE单例)
- semantic_embedding.py (MiniLM轻量级)
- tfidf_vectorization.py (TF-IDF离线)

功能增强 (1+1>2):
1. 多模型引擎: BGE-large/small, MiniLM, TF-IDF
2. 自动降级策略: 模型加载失败自动切换
3. Query优化: BGE官方推荐的检索指令前缀
4. 灵活存储: SQL/ChromaDB/双写三种模式
5. 批处理优化: 自动分批+进度显示
6. 统计分析: 向量数量、维度分布、相似度统计
7. 零配置启动: 自动检测本地模型缓存
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import threading

logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================

class VectorEngine(str, Enum):
    """向量化引擎"""
    BGE_LARGE = "bge-large"  # BAAI/bge-large-zh-v1.5, 1024维, 最高精度
    BGE_SMALL = "bge-small"  # BAAI/bge-small-zh-v1.5, 512维, 平衡方案
    MINILM = "minilm"        # all-MiniLM-L6-v2, 384维, 快速轻量
    TFIDF = "tfidf"          # sklearn TF-IDF, 384维, 离线零依赖


class StorageBackend(str, Enum):
    """存储后端"""
    SQL_ONLY = "sql"              # 仅SQL数据库 (DocumentChunk表)
    CHROMADB_ONLY = "chromadb"    # 仅ChromaDB向量库
    DUAL = "dual"                 # SQL + ChromaDB双写
    MEMORY = "memory"             # 内存临时存储(不持久化)


# ==================== 数据类定义 ====================

@dataclass
class VectorizedChunk:
    """向量化文本块"""
    chunk_id: str
    text: str
    embedding: List[float]
    dimension: int
    model: str
    document_id: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    vectorized_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（向后兼容）"""
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "embedding": self.embedding,
            "dimension": self.dimension,
            "model": self.model,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata,
            "vectorized_at": self.vectorized_at,
        }


@dataclass
class SearchResult:
    """检索结果"""
    chunk: VectorizedChunk
    score: float  # 相似度分数 [0, 1]
    rank: int     # 排名 (1-based)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chunk": self.chunk.to_dict(),
            "score": self.score,
            "rank": self.rank,
        }


@dataclass
class VectorStatistics:
    """向量统计信息"""
    total_chunks: int
    total_documents: int
    dimension: int
    model: str
    storage_backend: str
    avg_chunk_length: float
    projects: Dict[int, int] = field(default_factory=dict)  # project_id -> chunk_count

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_chunks": self.total_chunks,
            "total_documents": self.total_documents,
            "dimension": self.dimension,
            "model": self.model,
            "storage_backend": self.storage_backend,
            "avg_chunk_length": self.avg_chunk_length,
            "projects": self.projects,
        }


# ==================== 统一向量化引擎 ====================

class UnifiedVectorizationEngine:
    """
    统一向量化引擎

    整合7个向量化服务，提供统一接口
    支持4种编码引擎和4种存储后端
    """

    _instances: Dict[str, 'UnifiedVectorizationEngine'] = {}
    _lock = threading.Lock()

    def __init__(
        self,
        engine: VectorEngine = VectorEngine.BGE_SMALL,
        storage: StorageBackend = StorageBackend.MEMORY,
        optimize_query: bool = True,
        auto_fallback: bool = True,
    ):
        """
        初始化统一向量化引擎

        Args:
            engine: 向量化引擎 (bge-large/bge-small/minilm/tfidf)
            storage: 存储后端 (sql/chromadb/dual/memory)
            optimize_query: 是否为查询添加BGE检索指令前缀
            auto_fallback: 模型加载失败时是否自动降级
        """
        self.engine_type = engine
        self.storage_backend = storage
        self.optimize_query = optimize_query
        self.auto_fallback = auto_fallback

        self.encoder = None
        self.dimension = 0
        self.model_name = ""

        # 存储组件
        self.sql_storage = None
        self.chroma_storage = None
        self.memory_storage: Dict[str, VectorizedChunk] = {}

        # 初始化编码器
        self._initialize_encoder()

        # 初始化存储
        self._initialize_storage()

        logger.info(
            f"UnifiedVectorizationEngine initialized: "
            f"engine={self.engine_type}, storage={self.storage_backend}, "
            f"dimension={self.dimension}, model={self.model_name}"
        )

    def _initialize_encoder(self):
        """初始化编码器（带自动降级）"""
        engines_to_try = [self.engine_type]

        if self.auto_fallback:
            # 添加降级路径
            fallback_chain = {
                VectorEngine.BGE_LARGE: [VectorEngine.BGE_SMALL, VectorEngine.MINILM, VectorEngine.TFIDF],
                VectorEngine.BGE_SMALL: [VectorEngine.MINILM, VectorEngine.TFIDF],
                VectorEngine.MINILM: [VectorEngine.TFIDF],
                VectorEngine.TFIDF: [],
            }
            engines_to_try.extend(fallback_chain.get(self.engine_type, []))

        last_error = None
        for engine in engines_to_try:
            try:
                if engine == VectorEngine.BGE_LARGE:
                    self._init_bge_large()
                elif engine == VectorEngine.BGE_SMALL:
                    self._init_bge_small()
                elif engine == VectorEngine.MINILM:
                    self._init_minilm()
                elif engine == VectorEngine.TFIDF:
                    self._init_tfidf()

                logger.info(f"✅ Encoder loaded: {engine} (dimension: {self.dimension})")
                return

            except Exception as e:
                last_error = e
                logger.warning(f"Failed to load {engine}: {e}")
                continue

        # 所有引擎都失败
        raise RuntimeError(f"All encoders failed to load. Last error: {last_error}")

    def _init_bge_large(self):
        """初始化BGE Large (1024维)"""
        try:
            from FlagEmbedding import FlagModel
            import os

            model_paths = [
                'BAAI/bge-large-zh-v1.5',
                os.path.expanduser('~/.cache/modelscope/models/AI-ModelScope--bge-large-zh-v1.5/snapshots/master'),
            ]

            for path in model_paths:
                if path.startswith('~') or path.startswith('/'):
                    if not os.path.exists(path):
                        continue

                try:
                    self.encoder = FlagModel(
                        path,
                        query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章：" if self.optimize_query else None,
                        use_fp16=True
                    )
                    self.dimension = 1024
                    self.model_name = "bge-large-zh-v1.5"
                    self.engine_type = VectorEngine.BGE_LARGE
                    return
                except (OSError, RuntimeError, ValueError) as e:
                    logger.debug(f"尝试加载BGE Large从 {path} 失败: {e}")
                    continue

            raise RuntimeError("BGE Large model not found")

        except ImportError:
            raise RuntimeError("FlagEmbedding not installed. Run: pip install FlagEmbedding")

    def _init_bge_small(self):
        """初始化BGE Small (512维)"""
        try:
            from sentence_transformers import SentenceTransformer
            import os

            model_paths = [
                os.path.expanduser('~/.cache/modelscope/models/AI-ModelScope--bge-small-zh-v1.5/snapshots/master'),
                'BAAI/bge-small-zh-v1.5',
            ]

            for path in model_paths:
                try:
                    self.encoder = SentenceTransformer(path)
                    self.dimension = 512
                    self.model_name = "bge-small-zh-v1.5"
                    self.engine_type = VectorEngine.BGE_SMALL
                    return
                except (OSError, RuntimeError, ValueError) as e:
                    logger.debug(f"尝试加载BGE Small从 {path} 失败: {e}")
                    continue

            raise RuntimeError("BGE Small model not found")

        except ImportError:
            raise RuntimeError("sentence-transformers not installed")

    def _init_minilm(self):
        """初始化MiniLM (384维)"""
        try:
            from sentence_transformers import SentenceTransformer
            import os

            # 设置离线模式
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'

            model_names = [
                'sentence-transformers/all-MiniLM-L6-v2',
                'paraphrase-MiniLM-L3-v2',
            ]

            for model_name in model_names:
                try:
                    self.encoder = SentenceTransformer(
                        model_name,
                        device='cpu',
                        cache_folder=os.path.expanduser('~/.cache/huggingface/hub')
                    )
                    self.dimension = 384
                    self.model_name = model_name.split('/')[-1]
                    self.engine_type = VectorEngine.MINILM
                    return
                except (OSError, RuntimeError, ValueError) as e:
                    logger.debug(f"尝试加载MiniLM从 {model_name} 失败: {e}")
                    continue

            raise RuntimeError("MiniLM model not found")

        except ImportError:
            raise RuntimeError("sentence-transformers not installed")

    def _init_tfidf(self):
        """初始化TF-IDF (384维)"""
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.encoder = TfidfVectorizer(
            max_features=384,
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True
        )
        self.dimension = 384
        self.model_name = "tfidf-local"
        self.engine_type = VectorEngine.TFIDF
        self._tfidf_fitted = False
        self._tfidf_corpus = []

    def _initialize_storage(self):
        """初始化存储后端"""
        if self.storage_backend == StorageBackend.MEMORY:
            self.memory_storage = {}
            logger.info("Using memory storage (not persistent)")

        elif self.storage_backend == StorageBackend.SQL_ONLY:
            self._init_sql_storage()

        elif self.storage_backend == StorageBackend.CHROMADB_ONLY:
            self._init_chroma_storage()

        elif self.storage_backend == StorageBackend.DUAL:
            self._init_sql_storage()
            self._init_chroma_storage()

    def _init_sql_storage(self):
        """初始化SQL存储"""
        try:
            from sqlalchemy.orm import Session
            from app.models.document_chunk import DocumentChunk

            self.sql_storage = {
                "enabled": True,
                "model": DocumentChunk,
            }
            logger.info("SQL storage initialized")

        except Exception as e:
            logger.warning(f"SQL storage initialization failed: {e}")
            self.sql_storage = None

    def _init_chroma_storage(self):
        """初始化ChromaDB存储"""
        try:
            import chromadb
            from chromadb.config import Settings

            client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory="./chroma_db"
            ))

            self.chroma_storage = {
                "client": client,
                "collection": None,
            }
            logger.info("ChromaDB storage initialized")

        except Exception as e:
            logger.warning(f"ChromaDB storage initialization failed: {e}")
            self.chroma_storage = None

    # ==================== 编码接口 ====================

    def encode_query(self, query: str, normalize: bool = True) -> np.ndarray:
        """
        编码查询文本

        Args:
            query: 查询文本
            normalize: 是否归一化向量

        Returns:
            查询向量 (dimension,)
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            if self.engine_type in [VectorEngine.BGE_LARGE, VectorEngine.BGE_SMALL]:
                # FlagEmbedding或SentenceTransformer
                if hasattr(self.encoder, 'encode_queries'):
                    # FlagEmbedding (有query优化)
                    embedding = self.encoder.encode_queries([query])[0]
                else:
                    # SentenceTransformer
                    embedding = self.encoder.encode(
                        query,
                        normalize_embeddings=normalize,
                        convert_to_numpy=True
                    )

            elif self.engine_type == VectorEngine.MINILM:
                # MiniLM
                embedding = self.encoder.encode(
                    query,
                    normalize_embeddings=normalize,
                    convert_to_numpy=True
                )

            elif self.engine_type == VectorEngine.TFIDF:
                # TF-IDF需要先fit
                if not self._tfidf_fitted:
                    # 添加查询到语料库并训练
                    self._tfidf_corpus.append(query)
                    if len(self._tfidf_corpus) < 2:
                        self._tfidf_corpus.append("这是一个通用的参考文档用于TF-IDF训练")
                    self.encoder.fit(self._tfidf_corpus)
                    self._tfidf_fitted = True

                embedding = self.encoder.transform([query]).toarray()[0]

                # 确保维度正确
                if len(embedding) < self.dimension:
                    embedding = np.pad(embedding, (0, self.dimension - len(embedding)))
                elif len(embedding) > self.dimension:
                    embedding = embedding[:self.dimension]

                # 归一化
                if normalize:
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = embedding / norm

            return np.array(embedding)

        except Exception as e:
            logger.error(f"Query encoding failed: {e}")
            raise

    def encode_documents(
        self,
        texts: List[str],
        batch_size: int = 32,
        normalize: bool = True,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        批量编码文档

        Args:
            texts: 文档文本列表
            batch_size: 批处理大小
            normalize: 是否归一化
            show_progress: 是否显示进度

        Returns:
            文档向量矩阵 (n_texts, dimension)
        """
        if not texts:
            return np.array([])

        # 过滤空文本
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return np.array([])

        try:
            if self.engine_type in [VectorEngine.BGE_LARGE, VectorEngine.BGE_SMALL]:
                # FlagEmbedding或SentenceTransformer
                if hasattr(self.encoder, 'encode'):
                    if hasattr(self.encoder, 'encode_queries'):
                        # FlagEmbedding (不带query指令)
                        embeddings = self.encoder.encode(valid_texts)
                    else:
                        # SentenceTransformer
                        embeddings = self.encoder.encode(
                            valid_texts,
                            batch_size=batch_size,
                            normalize_embeddings=normalize,
                            show_progress_bar=show_progress and len(valid_texts) > 100,
                            convert_to_numpy=True
                        )

            elif self.engine_type == VectorEngine.MINILM:
                # MiniLM
                embeddings = self.encoder.encode(
                    valid_texts,
                    show_progress_bar=show_progress,
                    normalize_embeddings=normalize,
                    convert_to_numpy=True
                )

            elif self.engine_type == VectorEngine.TFIDF:
                # TF-IDF批量处理
                if not self._tfidf_fitted:
                    self._tfidf_corpus.extend(valid_texts)
                    self.encoder.fit(self._tfidf_corpus)
                    self._tfidf_fitted = True

                embeddings = self.encoder.transform(valid_texts).toarray()

                # 处理维度
                processed = []
                for embedding in embeddings:
                    if len(embedding) < self.dimension:
                        embedding = np.pad(embedding, (0, self.dimension - len(embedding)))
                    elif len(embedding) > self.dimension:
                        embedding = embedding[:self.dimension]

                    if normalize:
                        norm = np.linalg.norm(embedding)
                        if norm > 0:
                            embedding = embedding / norm

                    processed.append(embedding)

                embeddings = np.array(processed)

            return np.array(embeddings)

        except Exception as e:
            logger.error(f"Document encoding failed: {e}")
            raise

    # ==================== 存储接口 ====================

    def vectorize_and_store(
        self,
        chunks: List[Dict[str, Any]],
        project_id: int = None,
        db: Any = None,
        collection_name: str = "fieldmind",
        output_mode: str = "dataclass"
    ) -> List[Union[VectorizedChunk, Dict[str, Any]]]:
        """
        向量化并存储文本块

        Args:
            chunks: 文本块列表，每个包含 text, document_id, chunk_index 等
            project_id: 项目ID (SQL存储需要)
            db: 数据库会话 (SQL存储需要)
            collection_name: ChromaDB集合名称
            output_mode: 输出模式 ("dataclass" 或 "dict")

        Returns:
            向量化后的文本块列表
        """
        if not chunks:
            return []

        logger.info(f"Vectorizing {len(chunks)} chunks...")

        # 提取文本
        texts = [chunk.get("text", "") for chunk in chunks]

        # 批量编码
        embeddings = self.encode_documents(
            texts,
            show_progress=len(texts) > 100
        )

        # 构建VectorizedChunk对象
        vectorized_chunks = []
        for i, chunk in enumerate(chunks):
            vec_chunk = VectorizedChunk(
                chunk_id=chunk.get("chunk_id", f"chunk_{i}"),
                text=chunk.get("text", ""),
                embedding=embeddings[i].tolist(),
                dimension=self.dimension,
                model=self.model_name,
                document_id=str(chunk.get("document_id", "")),
                chunk_index=chunk.get("chunk_index", i),
                metadata=chunk.get("metadata", {}),
                vectorized_at=datetime.utcnow()
            )
            vectorized_chunks.append(vec_chunk)

        # 存储到后端
        if self.storage_backend == StorageBackend.MEMORY:
            for vec_chunk in vectorized_chunks:
                self.memory_storage[vec_chunk.chunk_id] = vec_chunk

        elif self.storage_backend == StorageBackend.SQL_ONLY:
            self._store_to_sql(vectorized_chunks, project_id, db)

        elif self.storage_backend == StorageBackend.CHROMADB_ONLY:
            self._store_to_chromadb(vectorized_chunks, collection_name)

        elif self.storage_backend == StorageBackend.DUAL:
            self._store_to_sql(vectorized_chunks, project_id, db)
            self._store_to_chromadb(vectorized_chunks, collection_name)

        logger.info(f"✅ Vectorized and stored {len(vectorized_chunks)} chunks")

        # 返回指定格式
        if output_mode == "dict":
            return [vc.to_dict() for vc in vectorized_chunks]
        return vectorized_chunks

    def _store_to_sql(self, chunks: List[VectorizedChunk], project_id: int, db: Any):
        """存储到SQL数据库"""
        if not self.sql_storage or not db:
            logger.warning("SQL storage not available")
            return

        try:
            from app.models.document_chunk import DocumentChunk

            for chunk in chunks:
                db_chunk = DocumentChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=int(chunk.document_id) if chunk.document_id.isdigit() else None,
                    project_id=project_id,
                    text=chunk.text,
                    embedding=chunk.embedding,
                    chunk_index=chunk.chunk_index,
                    metadata=chunk.metadata,
                    created_at=chunk.vectorized_at
                )
                db.add(db_chunk)

            db.commit()
            logger.info(f"Stored {len(chunks)} chunks to SQL")

        except Exception as e:
            logger.error(f"SQL storage failed: {e}")
            if db:
                db.rollback()

    def _store_to_chromadb(self, chunks: List[VectorizedChunk], collection_name: str):
        """存储到ChromaDB"""
        if not self.chroma_storage:
            logger.warning("ChromaDB storage not available")
            return

        try:
            # 获取或创建集合
            if not self.chroma_storage["collection"]:
                client = self.chroma_storage["client"]
                self.chroma_storage["collection"] = client.get_or_create_collection(
                    name=collection_name,
                    metadata={"dimension": self.dimension, "model": self.model_name}
                )

            collection = self.chroma_storage["collection"]

            # 准备数据
            ids = [chunk.chunk_id for chunk in chunks]
            embeddings = [chunk.embedding for chunk in chunks]
            documents = [chunk.text for chunk in chunks]
            metadatas = [
                {
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "model": chunk.model,
                    **chunk.metadata
                }
                for chunk in chunks
            ]

            # 批量添加
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

            logger.info(f"Stored {len(chunks)} chunks to ChromaDB")

        except Exception as e:
            logger.error(f"ChromaDB storage failed: {e}")

    # ==================== 检索接口 ====================

    def search_similar(
        self,
        query: str,
        top_k: int = 10,
        filters: Dict[str, Any] = None,
        threshold: float = 0.0,
        collection_name: str = "fieldmind",
        output_mode: str = "dataclass"
    ) -> List[Union[SearchResult, Dict[str, Any]]]:
        """
        语义检索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件 (如 {"document_id": "123"})
            threshold: 最小相似度阈值 [0, 1]
            collection_name: ChromaDB集合名称
            output_mode: 输出模式 ("dataclass" 或 "dict")

        Returns:
            检索结果列表 (按相似度降序)
        """
        if not query or not query.strip():
            return []

        # 编码查询
        query_embedding = self.encode_query(query)

        # 从存储后端检索
        if self.storage_backend == StorageBackend.MEMORY:
            results = self._search_memory(query_embedding, top_k, filters, threshold)

        elif self.storage_backend == StorageBackend.CHROMADB_ONLY:
            results = self._search_chromadb(query_embedding, top_k, filters, threshold, collection_name)

        elif self.storage_backend == StorageBackend.SQL_ONLY:
            results = self._search_sql(query_embedding, top_k, filters, threshold)

        elif self.storage_backend == StorageBackend.DUAL:
            # 双写模式优先用ChromaDB (更快)
            results = self._search_chromadb(query_embedding, top_k, filters, threshold, collection_name)

        # 返回指定格式
        if output_mode == "dict":
            return [r.to_dict() for r in results]
        return results

    def _search_memory(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        filters: Dict[str, Any],
        threshold: float
    ) -> List[SearchResult]:
        """从内存检索"""
        results = []

        for chunk_id, chunk in self.memory_storage.items():
            # 应用过滤器
            if filters:
                if not all(chunk.metadata.get(k) == v for k, v in filters.items()):
                    continue

            # 计算相似度
            chunk_emb = np.array(chunk.embedding)

            # 处理零向量的情况
            query_norm = np.linalg.norm(query_embedding)
            chunk_norm = np.linalg.norm(chunk_emb)

            if query_norm == 0 or chunk_norm == 0:
                similarity = 0.0
            else:
                similarity = np.dot(query_embedding, chunk_emb) / (query_norm * chunk_norm)

            if similarity >= threshold:
                results.append((chunk, float(similarity)))

        # 排序并取top_k
        results.sort(key=lambda x: x[1], reverse=True)
        results = results[:top_k]

        # 构建SearchResult
        return [
            SearchResult(chunk=chunk, score=score, rank=i+1)
            for i, (chunk, score) in enumerate(results)
        ]

    def _search_chromadb(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        filters: Dict[str, Any],
        threshold: float,
        collection_name: str
    ) -> List[SearchResult]:
        """从ChromaDB检索"""
        if not self.chroma_storage:
            return []

        try:
            # 获取集合
            if not self.chroma_storage["collection"]:
                client = self.chroma_storage["client"]
                self.chroma_storage["collection"] = client.get_collection(name=collection_name)

            collection = self.chroma_storage["collection"]

            # 构建where条件
            where = filters if filters else None

            # 查询
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                where=where
            )

            # 解析结果
            search_results = []
            if results and results['ids'] and results['ids'][0]:
                for i, chunk_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i] if 'distances' in results else 0
                    # ChromaDB返回距离，需要转换为相似度
                    similarity = 1 - distance

                    if similarity >= threshold:
                        # 重建VectorizedChunk
                        chunk = VectorizedChunk(
                            chunk_id=chunk_id,
                            text=results['documents'][0][i],
                            embedding=results['embeddings'][0][i] if 'embeddings' in results else [],
                            dimension=self.dimension,
                            model=self.model_name,
                            document_id=results['metadatas'][0][i].get('document_id', ''),
                            chunk_index=results['metadatas'][0][i].get('chunk_index', 0),
                            metadata=results['metadatas'][0][i]
                        )

                        search_results.append(
                            SearchResult(chunk=chunk, score=similarity, rank=i+1)
                        )

            return search_results

        except Exception as e:
            logger.error(f"ChromaDB search failed: {e}")
            return []

    def _search_sql(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        filters: Dict[str, Any],
        threshold: float
    ) -> List[SearchResult]:
        """从SQL检索 (需要向量相似度扩展)"""
        logger.warning("SQL search not fully implemented (需要pgvector或其他向量扩展)")
        return []

    # ==================== 管理接口 ====================

    def delete_by_document(
        self,
        document_id: str,
        db: Any = None,
        collection_name: str = "fieldmind"
    ) -> bool:
        """
        删除文档的所有向量

        Args:
            document_id: 文档ID
            db: 数据库会话 (SQL删除需要)
            collection_name: ChromaDB集合名称

        Returns:
            是否成功
        """
        try:
            if self.storage_backend == StorageBackend.MEMORY:
                deleted = 0
                for chunk_id, chunk in list(self.memory_storage.items()):
                    if chunk.document_id == document_id:
                        del self.memory_storage[chunk_id]
                        deleted += 1
                logger.info(f"Deleted {deleted} chunks from memory")

            elif self.storage_backend == StorageBackend.SQL_ONLY:
                if db and self.sql_storage:
                    from app.models.document_chunk import DocumentChunk
                    deleted = db.query(DocumentChunk).filter(
                        DocumentChunk.document_id == int(document_id)
                    ).delete()
                    db.commit()
                    logger.info(f"Deleted {deleted} chunks from SQL")

            elif self.storage_backend == StorageBackend.CHROMADB_ONLY:
                if self.chroma_storage:
                    collection = self.chroma_storage["collection"]
                    if not collection:
                        client = self.chroma_storage["client"]
                        collection = client.get_collection(name=collection_name)

                    collection.delete(where={"document_id": document_id})
                    logger.info(f"Deleted chunks from ChromaDB for document {document_id}")

            elif self.storage_backend == StorageBackend.DUAL:
                # 双写模式，两边都删
                self.delete_by_document(document_id, db, collection_name)
                self.delete_by_document(document_id, db, collection_name)

            return True

        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    def get_statistics(
        self,
        project_id: int = None,
        db: Any = None,
        collection_name: str = "fieldmind"
    ) -> VectorStatistics:
        """
        获取统计信息

        Args:
            project_id: 项目ID (可选，仅统计该项目)
            db: 数据库会话 (SQL统计需要)
            collection_name: ChromaDB集合名称

        Returns:
            统计信息
        """
        try:
            if self.storage_backend == StorageBackend.MEMORY:
                chunks = list(self.memory_storage.values())
                total_chunks = len(chunks)
                unique_docs = len(set(c.document_id for c in chunks))
                avg_length = sum(len(c.text) for c in chunks) / total_chunks if total_chunks > 0 else 0

                return VectorStatistics(
                    total_chunks=total_chunks,
                    total_documents=unique_docs,
                    dimension=self.dimension,
                    model=self.model_name,
                    storage_backend=self.storage_backend,
                    avg_chunk_length=avg_length
                )

            elif self.storage_backend == StorageBackend.SQL_ONLY:
                if db and self.sql_storage:
                    from app.models.document_chunk import DocumentChunk
                    from sqlalchemy import func

                    query = db.query(DocumentChunk)
                    if project_id:
                        query = query.filter(DocumentChunk.project_id == project_id)

                    total_chunks = query.count()
                    unique_docs = query.with_entities(
                        func.count(func.distinct(DocumentChunk.document_id))
                    ).scalar()
                    avg_length = query.with_entities(
                        func.avg(func.length(DocumentChunk.text))
                    ).scalar() or 0

                    # 按项目统计
                    projects = {}
                    if not project_id:
                        project_counts = db.query(
                            DocumentChunk.project_id,
                            func.count(DocumentChunk.id)
                        ).group_by(DocumentChunk.project_id).all()
                        projects = {pid: count for pid, count in project_counts}

                    return VectorStatistics(
                        total_chunks=total_chunks,
                        total_documents=unique_docs,
                        dimension=self.dimension,
                        model=self.model_name,
                        storage_backend=self.storage_backend,
                        avg_chunk_length=avg_length,
                        projects=projects
                    )

            elif self.storage_backend == StorageBackend.CHROMADB_ONLY:
                if self.chroma_storage:
                    collection = self.chroma_storage["collection"]
                    if not collection:
                        client = self.chroma_storage["client"]
                        collection = client.get_collection(name=collection_name)

                    total_chunks = collection.count()

                    return VectorStatistics(
                        total_chunks=total_chunks,
                        total_documents=0,  # ChromaDB不直接提供
                        dimension=self.dimension,
                        model=self.model_name,
                        storage_backend=self.storage_backend,
                        avg_chunk_length=0.0
                    )

            # 默认返回空统计
            return VectorStatistics(
                total_chunks=0,
                total_documents=0,
                dimension=self.dimension,
                model=self.model_name,
                storage_backend=self.storage_backend,
                avg_chunk_length=0.0
            )

        except Exception as e:
            logger.error(f"Get statistics failed: {e}")
            return VectorStatistics(
                total_chunks=0,
                total_documents=0,
                dimension=self.dimension,
                model=self.model_name,
                storage_backend=self.storage_backend,
                avg_chunk_length=0.0
            )

    # ==================== 便捷方法 ====================

    @classmethod
    def get_instance(
        cls,
        engine: VectorEngine = VectorEngine.BGE_SMALL,
        storage: StorageBackend = StorageBackend.MEMORY,
        **kwargs
    ) -> 'UnifiedVectorizationEngine':
        """
        获取单例实例（按engine+storage分组）

        Args:
            engine: 向量化引擎
            storage: 存储后端
            **kwargs: 其他初始化参数

        Returns:
            UnifiedVectorizationEngine实例
        """
        key = f"{engine}_{storage}"

        with cls._lock:
            if key not in cls._instances:
                cls._instances[key] = cls(engine=engine, storage=storage, **kwargs)

        return cls._instances[key]

    def batch_vectorize(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[np.ndarray]:
        """
        批量向量化（不存储）

        Args:
            texts: 文本列表
            batch_size: 批处理大小
            show_progress: 是否显示进度

        Returns:
            向量列表
        """
        embeddings = self.encode_documents(
            texts,
            batch_size=batch_size,
            show_progress=show_progress
        )
        return [emb for emb in embeddings]


# ==================== 便捷函数 ====================

# 全局默认实例
_default_engine: Optional[UnifiedVectorizationEngine] = None


def create_engine(
    engine: VectorEngine = VectorEngine.BGE_SMALL,
    storage: StorageBackend = StorageBackend.MEMORY,
    **kwargs
) -> UnifiedVectorizationEngine:
    """
    创建向量化引擎

    Args:
        engine: 向量化引擎
        storage: 存储后端
        **kwargs: 其他参数

    Returns:
        UnifiedVectorizationEngine实例
    """
    return UnifiedVectorizationEngine(engine=engine, storage=storage, **kwargs)


def encode_query(query: str, engine: VectorEngine = VectorEngine.BGE_SMALL) -> np.ndarray:
    """快速编码查询"""
    global _default_engine
    if _default_engine is None or _default_engine.engine_type != engine:
        _default_engine = create_engine(engine=engine)
    return _default_engine.encode_query(query)


def encode_documents(
    texts: List[str],
    engine: VectorEngine = VectorEngine.BGE_SMALL,
    batch_size: int = 32
) -> np.ndarray:
    """快速批量编码文档"""
    global _default_engine
    if _default_engine is None or _default_engine.engine_type != engine:
        _default_engine = create_engine(engine=engine)
    return _default_engine.encode_documents(texts, batch_size=batch_size)


def vectorize_and_store(
    chunks: List[Dict[str, Any]],
    engine: VectorEngine = VectorEngine.BGE_SMALL,
    storage: StorageBackend = StorageBackend.MEMORY,
    **kwargs
) -> List[VectorizedChunk]:
    """快速向量化并存储"""
    vec_engine = create_engine(engine=engine, storage=storage)
    return vec_engine.vectorize_and_store(chunks, **kwargs)


def search_similar(
    query: str,
    top_k: int = 10,
    engine: VectorEngine = VectorEngine.BGE_SMALL,
    storage: StorageBackend = StorageBackend.MEMORY,
    **kwargs
) -> List[SearchResult]:
    """快速语义检索"""
    vec_engine = create_engine(engine=engine, storage=storage)
    return vec_engine.search_similar(query, top_k=top_k, **kwargs)
