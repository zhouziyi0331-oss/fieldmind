"""
向量化和入库服务 - 完整的向量化pipeline
100%完整版本：
1. 使用FlagEmbedding（中文SOTA）
2. 同时写入SQL和ChromaDB
3. 支持时间戳和说话人metadata
"""

import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np
import chromadb
from chromadb.config import Settings

from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from app.core.database import Base
from app.models.document_chunks import DocumentChunk  # 使用正确的模型定义
from app.services.semantic_embedding import load_embedding_backend

logger = logging.getLogger(__name__)


class VectorizationService:
    """
    向量化服务 - 100%完整实现

    核心职责：
    1. 使用FlagEmbedding生成中文向量
    2. 同时写入SQL数据库（document_chunks表）
    3. 同时写入ChromaDB向量库（支持语义检索）
    4. 保留完整metadata（时间戳、说话人、来源文件）
    """

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """单例模式：确保全局只有一个实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        model_name: str = "BAAI/bge-large-zh-v1.5",
        chroma_path: str = "./chroma_db_vectors",  # 使用独立路径，避免与其他服务冲突
        collection_name: str = "fieldmind_vectors"
    ):
        """
        初始化向量化服务（单例模式）

        Args:
            model_name: FlagEmbedding模型名称
            chroma_path: ChromaDB存储路径
            collection_name: ChromaDB集合名称
        """
        # 单例模式：只初始化一次
        if self._initialized:
            return

        self.model_name = model_name
        self.model = None
        self.embedding_dim = 1024  # bge-large-zh-v1.5 默认维度
        self.vectorization_available = False

        # 初始化本地语义嵌入后端
        self._load_embedding_model()

        # 初始化ChromaDB
        self.chroma_client = None
        self.collection = None
        self.chroma_path = chroma_path
        self.collection_name = collection_name
        self._init_chromadb()

    def _load_embedding_model(self):
        """加载本地语义嵌入模型"""
        try:
            self.embedding_backend = load_embedding_backend()
            if self.embedding_backend is None:
                logger.warning("⚠️ 本地语义嵌入模型不可用，保留SQL分块并跳过语义向量化")
                return

            self.model = self.embedding_backend
            self.model_name = self.embedding_backend.model_name
            self.embedding_dim = self.embedding_backend.get_sentence_embedding_dimension()
            self.vectorization_available = True

            logger.info(f"✅ 本地语义模型加载成功，维度: {self.embedding_dim}")

        except Exception as e:
            logger.warning(f"⚠️ 本地语义模型加载失败，降级为无向量分块: {e}")
            self.model = None
            self.vectorization_available = False

    def _init_chromadb(self):
        """初始化ChromaDB客户端和集合"""
        try:
            logger.info(f"初始化ChromaDB: {self.chroma_path}")

            # 创建目录
            os.makedirs(self.chroma_path, exist_ok=True)

            # 初始化客户端 - 使用get_or_create模式
            try:
                self.chroma_client = chromadb.PersistentClient(
                    path=self.chroma_path,
                    settings=Settings(anonymized_telemetry=False)
                )
            except Exception as e:
                # 如果已存在实例，尝试使用默认设置
                logger.warning(f"ChromaDB实例已存在，尝试重用: {e}")
                self.chroma_client = chromadb.PersistentClient(
                    path=self.chroma_path,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )

            # 获取或创建集合
            try:
                self.collection = self.chroma_client.get_collection(name=self.collection_name)
                logger.info(f"✅ 连接到现有集合: {self.collection_name}")
            except Exception as e:
                logger.info(f"集合不存在，创建新集合: {e}")
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
                )
                logger.info(f"✅ 创建新集合: {self.collection_name}")

            # 标记已初始化
            VectorizationService._initialized = True

        except Exception as e:
            logger.error(f"❌ ChromaDB初始化失败: {e}")
            raise

    def vectorize_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        向量化文本chunks（增强版）

        ⭐⭐⭐ 新增：使用增强文本进行向量化
        - 如果 chunk 包含语义上下文，构建增强文本
        - 向量化增强文本（包含章节、实体、标签等）
        - 保存原始文本到 text 字段，增强文本到 metadata

        Args:
            chunks: chunk列表，每个chunk包含text和metadata

        Returns:
            向量化后的chunks（添加了embedding字段）
        """
        if not chunks:
            return []

        if self.model is None:
            logger.warning("⚠️ 真实语义模型不可用，跳过向量生成并保留结构化分块")
            for chunk in chunks:
                metadata = dict(chunk.get("metadata") or {})
                metadata["vectorization_status"] = "unavailable"
                metadata["vectorization_reason"] = "FlagEmbedding未安装或模型加载失败"
                chunk["metadata"] = metadata
            return chunks

        logger.info(f"开始向量化 {len(chunks)} 个chunks")

        # ⭐⭐⭐ 新增：构建增强文本
        try:
            from app.services.vectorization_text_builder import vectorization_text_builder

            logger.info("   🌟 构建增强文本用于向量化")

            texts_for_embedding = []
            for chunk in chunks:
                # 检查是否有语义上下文
                has_semantic_context = (
                    chunk.get("semantic_context") or
                    (chunk.get("metadata", {}).get("source_summary"))
                )

                if has_semantic_context:
                    # 构建增强文本
                    enhanced_text = vectorization_text_builder.build_enhanced_text(chunk)
                    texts_for_embedding.append(enhanced_text)

                    # 保存增强文本到 metadata（用于调试和分析）
                    if "metadata" not in chunk:
                        chunk["metadata"] = {}
                    chunk["metadata"]["enhanced_text"] = enhanced_text
                else:
                    # 没有语义上下文，使用原始文本
                    texts_for_embedding.append(chunk["text"])

            logger.info(f"   ✅ 增强文本构建完成，{sum(1 for c in chunks if c.get('metadata', {}).get('enhanced_text'))} 个 chunk 被增强")

        except Exception as e:
            logger.warning(f"   ⚠️ 增强文本构建失败，使用原始文本: {e}")
            texts_for_embedding = [chunk["text"] for chunk in chunks]

        # 批量生成向量
        try:
            embeddings = self.model.encode(texts_for_embedding)
            logger.info(f"✅ 向量化完成: {len(embeddings)} 个向量")
        except Exception as e:
            logger.error(f"❌ 向量化失败: {e}")
            raise

        # 将向量添加到chunks
        vectorized_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding.tolist()
            chunk["embedding_model"] = self.model_name
            chunk["vectorized_at"] = datetime.utcnow().isoformat()

            # ⭐ 新增：标记是否使用了增强文本
            if chunk.get("metadata", {}).get("enhanced_text"):
                chunk["metadata"]["vectorization_method"] = "enhanced"
            else:
                chunk["metadata"]["vectorization_method"] = "plain"

            vectorized_chunks.append(chunk)

        return vectorized_chunks

    def store_chunks(
        self,
        chunks: List[Dict[str, Any]],
        document_id: int,
        project_id: int,
        db: Session
    ) -> List[DocumentChunk]:
        """
        将chunks存储到SQL数据库和ChromaDB

        这是100%完整实现：
        1. 存储到SQL（document_chunks表）
        2. 存储到ChromaDB（支持语义检索）
        3. 保留完整metadata

        Args:
            chunks: chunk列表（已向量化）
            document_id: 文档ID
            project_id: 项目ID
            db: 数据库会话

        Returns:
            已保存的DocumentChunk对象列表
        """
        logger.info(f"开始存储 {len(chunks)} 个chunks（SQL + ChromaDB）")

        saved_chunks = []
        chroma_ids = []
        chroma_embeddings = []
        chroma_documents = []
        chroma_metadatas = []

        for chunk in chunks:
            # 1. 存储到SQL数据库（使用正确的字段名）
            chunk_text = chunk["text"]
            db_chunk = DocumentChunk(
                document_id=document_id,
                project_id=project_id,
                chunk_text=chunk_text,
                chunk_size=len(chunk_text),
                chunk_index=chunk.get("chunk_index", 0),
                chunking_method="semantic",
                chunking_params=None,
                embedding_vector=chunk.get("embedding"),
                embedding_model=chunk.get("embedding_model", self.model_name),
                extra_metadata=chunk.get("metadata")
            )

            db.add(db_chunk)
            db.flush()  # 生成db_chunk.id
            saved_chunks.append(db_chunk)

            # 2. 准备ChromaDB数据
            chunk_metadata = chunk.get("metadata", {})

            # 构建完整metadata（保留时间戳和说话人）
            chroma_metadata = {
                "document_id": str(document_id),
                "project_id": project_id,
                "chunk_id": str(db_chunk.id),
                "chunk_index": chunk.get("chunk_index", 0),
                "source_file": chunk_metadata.get("source_file", "unknown"),
            }

            # 添加时间戳（如果有）
            if "timestamp_start" in chunk_metadata:
                chroma_metadata["start_sec"] = float(chunk_metadata["timestamp_start"])
            if "timestamp_end" in chunk_metadata:
                chroma_metadata["end_sec"] = float(chunk_metadata["timestamp_end"])

            # 添加说话人（如果有）
            if "speaker" in chunk_metadata:
                chroma_metadata["speaker"] = str(chunk_metadata["speaker"])

            chroma_ids.append(f"chunk_{db_chunk.id}")

            # 只有embedding存在时才添加到ChromaDB
            if chunk.get("embedding") is not None:
                chroma_embeddings.append(chunk["embedding"])
                chroma_documents.append(chunk["text"])
                chroma_metadatas.append(chroma_metadata)

        # 提交SQL
        db.commit()
        logger.info(f"✅ SQL存储完成: {len(saved_chunks)} 个chunks")

        # 3. 批量写入ChromaDB（只在有embedding时）
        if chroma_embeddings:
            try:
                self.collection.add(
                    ids=chroma_ids[:len(chroma_embeddings)],  # 只添加有embedding的
                    embeddings=chroma_embeddings,
                    documents=chroma_documents,
                    metadatas=chroma_metadatas
                )
                logger.info(f"✅ ChromaDB存储完成: {len(chroma_embeddings)} 个向量")
            except Exception as e:
                logger.error(f"❌ ChromaDB存储失败: {e}")
                # 不回滚SQL，继续执行
        else:
            logger.info("⚠️ 跳过ChromaDB存储（无embedding）")

        return saved_chunks

    def query_similar(
        self,
        query_text: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        语义检索

        Args:
            query_text: 查询文本
            top_k: 返回top K个结果
            filter_metadata: 过滤条件（如project_id）

        Returns:
            相似的chunks列表
        """
        if self.model is None or self.collection is None:
            logger.info("语义向量检索不可用，返回空结果，由上层使用关键词/全文检索")
            return []

        # 向量化查询
        query_embedding = self.model.encode([query_text])[0].tolist()

        # 查询ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"]
        )

        # 格式化结果
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "chunk_id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })

        return formatted_results

    def get_chunk_statistics(self, project_id: int, db: Session) -> Dict[str, Any]:
        """
        获取项目的chunk统计信息

        Args:
            project_id: 项目ID
            db: 数据库会话

        Returns:
            统计信息字典
        """
        from sqlalchemy import func

        try:
            # 统计SQL数据库中的chunks
            total_chunks = db.query(func.count(DocumentChunk.id)).filter(
                DocumentChunk.project_id == project_id
            ).scalar()

            total_documents = db.query(func.count(func.distinct(DocumentChunk.document_id))).filter(
                DocumentChunk.project_id == project_id
            ).scalar()

            # 统计平均chunk长度
            avg_length = db.query(func.avg(DocumentChunk.text_length)).filter(
                DocumentChunk.project_id == project_id
            ).scalar()

            # 统计向量化的chunks数量
            vectorized_chunks = db.query(func.count(DocumentChunk.id)).filter(
                DocumentChunk.project_id == project_id,
                DocumentChunk.embedding.isnot(None)
            ).scalar()

            # 统计ChromaDB中的向量数量
            try:
                chroma_results = self.collection.get(
                    where={"project_id": project_id}
                )
                chroma_count = len(chroma_results["ids"]) if chroma_results["ids"] else 0
            except Exception as e:
                logger.warning(f"查询ChromaDB失败: {e}")
                chroma_count = 0

            return {
                "project_id": project_id,
                "total_chunks": total_chunks or 0,
                "total_documents": total_documents or 0,
                "vectorized_chunks": vectorized_chunks or 0,
                "chroma_vectors": chroma_count,
                "avg_chunk_length": round(float(avg_length), 2) if avg_length else 0,
                "vectorization_rate": round(vectorized_chunks / total_chunks * 100, 2) if total_chunks > 0 else 0
            }

        except Exception as e:
            logger.error(f"获取chunk统计失败: {e}")
            return {
                "project_id": project_id,
                "error": str(e)
            }


# 全局单例
_vectorization_service = None


def get_vectorization_service(db: Optional[Session] = None) -> VectorizationService:
    """获取向量化服务单例"""
    global _vectorization_service
    if _vectorization_service is None:
        _vectorization_service = VectorizationService()
    return _vectorization_service


# 默认导出
vectorization_service = get_vectorization_service()
