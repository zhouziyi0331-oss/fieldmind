"""
向量存储服务 - LLM Wiki风格

支持：
- 文档向量化和存储
- 语义相似度搜索
- 批量处理和索引优化
- pgvector高性能检索
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import hashlib
import logging
from datetime import datetime

from app.models.knowledge_graph import VectorChunk, VectorIndex

logger = logging.getLogger(__name__)


class VectorStore:
    """
    向量存储服务

    使用PostgreSQL的pgvector扩展实现高性能向量检索
    """

    def __init__(self, db: Session, embedding_model):
        self.db = db
        self.embedding_model = embedding_model
        self.dimension = 1536  # OpenAI ada-002

    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ) -> int:
        """
        添加文档到向量存储

        参数:
            documents: 文档列表
            chunk_size: 每个块的token数
            chunk_overlap: 块之间的重叠token数

        返回:
            添加的块数量
        """
        logger.info(f"开始向量化 {len(documents)} 个文档")

        chunks_added = 0

        for doc in documents:
            # 1. 分块
            doc_chunks = self._chunk_document(
                doc['content'],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )

            # 2. 批量生成嵌入
            contents = [chunk['content'] for chunk in doc_chunks]
            embeddings = await self._batch_embed(contents)

            # 3. 保存到数据库
            for i, (chunk, embedding) in enumerate(zip(doc_chunks, embeddings)):
                content_hash = hashlib.sha256(chunk['content'].encode()).hexdigest()

                # 检查是否已存在
                existing = self.db.query(VectorChunk).filter(
                    VectorChunk.content_hash == content_hash
                ).first()

                if existing:
                    logger.debug(f"块已存在，跳过: {content_hash[:16]}")
                    continue

                vector_chunk = VectorChunk(
                    content=chunk['content'],
                    content_hash=content_hash,
                    document_id=doc.get('document_id'),
                    chunk_index=i,
                    chunk_size=len(chunk['content']),
                    source_type=doc.get('source_type', 'unknown'),
                    source_id=doc.get('source_id'),
                    embedding=embedding,
                    entities=chunk.get('entities', []),
                    semantic_tags=chunk.get('tags', []),
                    language=doc.get('language', 'zh')
                )

                self.db.add(vector_chunk)
                chunks_added += 1

            # 批量提交
            if chunks_added % 100 == 0:
                self.db.commit()

        self.db.commit()

        logger.info(f"成功添加 {chunks_added} 个向量块")

        # 更新索引统计
        self._update_index_stats()

        return chunks_added

    def _chunk_document(
        self,
        text: str,
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """
        文档分块

        使用滑动窗口分块，保持语义连贯性
        """
        # 简化版：按段落分块
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        current_size = 0

        for para in paragraphs:
            para_size = len(para)

            if current_size + para_size > chunk_size and current_chunk:
                # 保存当前块
                chunks.append({
                    'content': current_chunk.strip(),
                    'size': current_size
                })

                # 重叠部分
                if chunk_overlap > 0:
                    overlap_text = current_chunk[-chunk_overlap:]
                    current_chunk = overlap_text + "\n\n" + para
                    current_size = len(overlap_text) + para_size
                else:
                    current_chunk = para
                    current_size = para_size
            else:
                current_chunk += "\n\n" + para if current_chunk else para
                current_size += para_size

        # 最后一个块
        if current_chunk:
            chunks.append({
                'content': current_chunk.strip(),
                'size': current_size
            })

        return chunks

    async def _batch_embed(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """批量生成嵌入"""
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]

            try:
                # 调用嵌入模型
                embeddings = await self.embedding_model.embed_batch(batch)
                all_embeddings.extend(embeddings)

            except Exception as e:
                logger.error(f"批量嵌入失败: {str(e)}")
                # 降级到单个嵌入
                for text in batch:
                    emb = await self.embedding_model.embed(text)
                    all_embeddings.append(emb)

        return all_embeddings

    async def similarity_search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        语义相似度搜索

        使用pgvector的余弦相似度搜索
        """
        # 1. 查询向量化
        query_embedding = await self.embedding_model.embed(query)

        # 2. 构建SQL查询
        sql = """
            SELECT
                chunk_id,
                content,
                document_id,
                source_type,
                entities,
                semantic_tags,
                1 - (embedding <=> :query_vec::vector) as similarity
            FROM vector_chunks
            WHERE 1 - (embedding <=> :query_vec::vector) > :threshold
        """

        # 添加过滤条件
        params = {
            "query_vec": query_embedding,
            "threshold": threshold,
            "top_k": top_k
        }

        if filters:
            if 'source_type' in filters:
                sql += " AND source_type = :source_type"
                params['source_type'] = filters['source_type']

            if 'document_id' in filters:
                sql += " AND document_id = :document_id"
                params['document_id'] = filters['document_id']

        sql += " ORDER BY embedding <=> :query_vec::vector LIMIT :top_k"

        # 3. 执行查询
        result = self.db.execute(text(sql), params)
        rows = result.fetchall()

        # 4. 格式化结果
        results = []
        for row in rows:
            results.append({
                "chunk_id": row[0],
                "content": row[1],
                "document_id": row[2],
                "source_type": row[3],
                "entities": row[4],
                "tags": row[5],
                "similarity": float(row[6]),
                "method": "vector"
            })

        logger.info(f"向量搜索返回 {len(results)} 个结果")

        return results

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        混合搜索：向量 + 关键词

        结合语义搜索和全文检索
        """
        # 1. 向量搜索
        vector_results = await self.similarity_search(query, top_k=top_k*2)

        # 2. 关键词搜索（PostgreSQL全文检索）
        keyword_results = await self._keyword_search(query, top_k=top_k*2)

        # 3. 混合排序
        combined = self._combine_results(
            vector_results,
            keyword_results,
            vector_weight,
            keyword_weight
        )

        return combined[:top_k]

    async def _keyword_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """关键词全文检索"""
        sql = """
            SELECT
                chunk_id,
                content,
                document_id,
                source_type,
                ts_rank(to_tsvector('chinese', content), plainto_tsquery('chinese', :query)) as rank
            FROM vector_chunks
            WHERE to_tsvector('chinese', content) @@ plainto_tsquery('chinese', :query)
            ORDER BY rank DESC
            LIMIT :top_k
        """

        result = self.db.execute(text(sql), {"query": query, "top_k": top_k})
        rows = result.fetchall()

        results = []
        for row in rows:
            results.append({
                "chunk_id": row[0],
                "content": row[1],
                "document_id": row[2],
                "source_type": row[3],
                "score": float(row[4]),
                "method": "keyword"
            })

        return results

    def _combine_results(
        self,
        vector_results: List[Dict],
        keyword_results: List[Dict],
        vector_weight: float,
        keyword_weight: float
    ) -> List[Dict]:
        """混合排序算法"""
        # 合并结果
        combined = {}

        # 向量结果
        for result in vector_results:
            chunk_id = result['chunk_id']
            combined[chunk_id] = {
                **result,
                'combined_score': result.get('similarity', 0) * vector_weight
            }

        # 关键词结果
        for result in keyword_results:
            chunk_id = result['chunk_id']
            if chunk_id in combined:
                combined[chunk_id]['combined_score'] += result.get('score', 0) * keyword_weight
                combined[chunk_id]['method'] = 'hybrid'
            else:
                combined[chunk_id] = {
                    **result,
                    'combined_score': result.get('score', 0) * keyword_weight
                }

        # 按组合分数排序
        sorted_results = sorted(
            combined.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )

        return sorted_results

    def create_index(self, index_name: str, index_type: str = 'ivfflat', lists: int = 100):
        """
        创建向量索引

        参数:
            index_name: 索引名称
            index_type: ivfflat 或 hnsw
            lists: IVFFlat的lists参数
        """
        logger.info(f"创建向量索引: {index_name}, 类型: {index_type}")

        try:
            if index_type == 'ivfflat':
                sql = f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON vector_chunks
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = {lists})
                """
            elif index_type == 'hnsw':
                sql = f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON vector_chunks
                    USING hnsw (embedding vector_cosine_ops)
                """
            else:
                raise ValueError(f"不支持的索引类型: {index_type}")

            self.db.execute(text(sql))
            self.db.commit()

            # 保存索引配置
            index_config = VectorIndex(
                index_name=index_name,
                index_type=index_type,
                lists=lists if index_type == 'ivfflat' else None,
                distance_metric='cosine',
                total_vectors=self._get_vector_count()
            )
            self.db.add(index_config)
            self.db.commit()

            logger.info(f"向量索引创建成功: {index_name}")

        except Exception as e:
            logger.error(f"创建索引失败: {str(e)}")
            self.db.rollback()
            raise

    def _get_vector_count(self) -> int:
        """获取向量总数"""
        result = self.db.execute(text("SELECT COUNT(*) FROM vector_chunks"))
        return result.scalar()

    def _update_index_stats(self):
        """更新索引统计"""
        total = self._get_vector_count()

        # 更新所有索引的统计信息
        indexes = self.db.query(VectorIndex).all()
        for index in indexes:
            index.total_vectors = total
            index.updated_at = datetime.utcnow()

        self.db.commit()

    async def delete_by_document(self, document_id: int):
        """删除指定文档的所有向量块"""
        self.db.query(VectorChunk).filter(
            VectorChunk.document_id == document_id
        ).delete()
        self.db.commit()

        logger.info(f"已删除文档 {document_id} 的所有向量块")

    def get_statistics(self) -> Dict[str, Any]:
        """获取向量存储统计信息"""
        total_chunks = self._get_vector_count()

        # 按来源类型统计
        sql = """
            SELECT source_type, COUNT(*) as count
            FROM vector_chunks
            GROUP BY source_type
        """
        result = self.db.execute(text(sql))
        by_source = {row[0]: row[1] for row in result.fetchall()}

        # 按语言统计
        sql = """
            SELECT language, COUNT(*) as count
            FROM vector_chunks
            GROUP BY language
        """
        result = self.db.execute(text(sql))
        by_language = {row[0]: row[1] for row in result.fetchall()}

        return {
            "total_chunks": total_chunks,
            "by_source_type": by_source,
            "by_language": by_language,
            "dimension": self.dimension
        }


class EmbeddingModel:
    """
    嵌入模型封装

    支持多种嵌入模型
    """

    def __init__(self, model_name: str = "text-embedding-ada-002", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key

        if api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

    async def embed(self, text: str) -> List[float]:
        """单个文本嵌入"""
        if not self.client:
            # 返回随机向量用于测试
            import random
            return [random.random() for _ in range(1536)]

        response = self.client.embeddings.create(
            model=self.model_name,
            input=text
        )

        return response.data[0].embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量文本嵌入"""
        if not self.client:
            import random
            return [[random.random() for _ in range(1536)] for _ in texts]

        response = self.client.embeddings.create(
            model=self.model_name,
            input=texts
        )

        return [item.embedding for item in response.data]
