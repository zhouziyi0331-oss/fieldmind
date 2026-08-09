"""
向量化服务 v2 - 链路十四改造版
核心改进：将完整的元数据存入ChromaDB，确保检索时能精确溯源
"""
from typing import List, Dict, Any, Optional
import logging

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    except ImportError:
        from langchain.embeddings import HuggingFaceEmbeddings

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.schemas.document_metadata import ChunkMetadata

logger = logging.getLogger(__name__)


class VectorizationServiceV2:
    """向量化服务 v2 - 元数据完整版"""

    def __init__(self):
        # 初始化嵌入模型
        # 配置使用本地缓存目录，避免从hf-mirror.com下载
        import os
        os.environ.setdefault("HF_ENDPOINT", "https://huggingface.co")

        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
            cache_folder=os.path.expanduser("~/.cache/huggingface/hub")
        )

        # 初始化ChromaDB客户端
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 获取或创建collection
        self.collection = self._get_or_create_collection()

        logger.info(f"✅ 向量化服务初始化完成 (collection={self.collection.name if self.collection else 'None'})")

    def _get_or_create_collection(self):
        """获取或创建ChromaDB collection"""
        try:
            collection_name = settings.CHROMA_COLLECTION_NAME
            return self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "FieldMind文档向量库（链路十四增强版）"}
            )
        except Exception as e:
            logger.error(f"❌ 创建ChromaDB collection失败: {e}")
            return None

    def vectorize_chunks(
        self,
        chunks: List[ChunkMetadata],
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        向量化并存储chunks（链路十四核心方法）

        Args:
            chunks: 带完整元数据的chunk列表
            batch_size: 批处理大小

        Returns:
            存储结果统计
        """
        if not chunks:
            logger.warning("⚠️ 没有chunks需要向量化")
            return {"success": False, "stored_count": 0}

        if not self.collection:
            logger.error("❌ ChromaDB collection未初始化")
            return {"success": False, "error": "ChromaDB未初始化"}

        logger.info(f"🔄 开始向量化 {len(chunks)} 个chunks...")

        stored_count = 0
        failed_count = 0

        # 分批处理
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]

            try:
                # 准备数据
                ids = []
                documents = []
                metadatas = []

                for chunk in batch_chunks:
                    # Chunk ID
                    ids.append(chunk.chunk_id)

                    # 文本内容（从custom_fields中提取）
                    text = chunk.custom_fields.get("text", "")
                    if not text:
                        logger.warning(f"⚠️ Chunk {chunk.chunk_id} 缺少文本内容")
                        continue

                    documents.append(text)

                    # 元数据（链路十四关键：完整元数据入库）
                    metadata = self._prepare_metadata(chunk)
                    metadatas.append(metadata)

                # 存入ChromaDB
                if documents:
                    self.collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas
                    )
                    stored_count += len(documents)
                    logger.debug(f"  ✅ 批次 {i//batch_size + 1}: 存储 {len(documents)} 个chunks")

            except Exception as e:
                logger.error(f"❌ 批次 {i//batch_size + 1} 存储失败: {e}")
                failed_count += len(batch_chunks)

        logger.info(f"✅ 向量化完成: 成功 {stored_count}, 失败 {failed_count}")

        return {
            "success": stored_count > 0,
            "stored_count": stored_count,
            "failed_count": failed_count,
            "total_chunks": len(chunks)
        }

    def _prepare_metadata(self, chunk: ChunkMetadata) -> Dict[str, Any]:
        """
        准备ChromaDB元数据（链路十四核心：确保所有溯源字段都存入）

        ChromaDB的限制：
        1. 只接受基本数据类型（str, int, float, bool）
        2. 不接受None值
        3. 不接受嵌套对象
        """
        # 转换为字典
        meta_dict = chunk.to_dict()

        # ChromaDB专用格式转换
        metadata = {}

        # 1. 必填字段（确保溯源）
        metadata["document_id"] = str(meta_dict["document_id"])
        metadata["source_file"] = meta_dict["source_file"]

        # 处理document_type（可能是str或DocumentType枚举）
        document_type = meta_dict["document_type"]
        if hasattr(document_type, 'value'):
            metadata["document_type"] = document_type.value
        else:
            metadata["document_type"] = str(document_type)

        # 处理source_level（可能是int或SourceLevel枚举）
        source_level = meta_dict["source_level"]
        if hasattr(source_level, 'value'):
            # 是枚举类型
            metadata["source_level"] = int(source_level.value)
        else:
            # 已经是int
            metadata["source_level"] = int(source_level)

        # 2. Chunk位置
        metadata["chunk_index"] = meta_dict["chunk_index"]
        metadata["total_chunks"] = meta_dict["total_chunks"]
        metadata["char_start"] = meta_dict["char_start"]
        metadata["char_end"] = meta_dict["char_end"]

        # 3. 引用信息（根据文档类型）
        if "page_number" in meta_dict and meta_dict["page_number"] is not None:
            metadata["page_number"] = meta_dict["page_number"]

        if "page_range" in meta_dict and meta_dict["page_range"]:
            metadata["page_range"] = meta_dict["page_range"]

        if "timestamp_start" in meta_dict and meta_dict["timestamp_start"] is not None:
            metadata["timestamp_start"] = float(meta_dict["timestamp_start"])

        if "timestamp_end" in meta_dict and meta_dict["timestamp_end"] is not None:
            metadata["timestamp_end"] = float(meta_dict["timestamp_end"])

        if "timestamp_range" in meta_dict and meta_dict["timestamp_range"]:
            metadata["timestamp_range"] = meta_dict["timestamp_range"]

        if "speaker" in meta_dict and meta_dict["speaker"]:
            metadata["speaker"] = meta_dict["speaker"]

        # 4. 项目关联
        if "project_id" in meta_dict and meta_dict["project_id"] is not None:
            metadata["project_id"] = str(meta_dict["project_id"])

        # 5. 时间信息（链路15需要）
        if "document_date" in meta_dict and meta_dict["document_date"]:
            # 存储ISO格式（用于显示）
            if isinstance(meta_dict["document_date"], str):
                metadata["document_date"] = meta_dict["document_date"]
            else:
                # datetime对象转ISO字符串
                metadata["document_date"] = meta_dict["document_date"].isoformat()

            # 同时存储Unix时间戳（用于范围查询）
            try:
                if isinstance(meta_dict["document_date"], str):
                    from datetime import datetime
                    dt = datetime.fromisoformat(meta_dict["document_date"].replace('Z', '+00:00'))
                    metadata["document_date_ts"] = int(dt.timestamp())
                else:
                    metadata["document_date_ts"] = int(meta_dict["document_date"].timestamp())
            except (ValueError, AttributeError) as e:
                logger.debug(f"日期时间戳转换失败: {e}")
            except Exception as e:
                logger.warning(f"处理文档日期时出现异常: {e}")

        if "extracted_dates" in meta_dict and meta_dict["extracted_dates"]:
            # 只保存第一个日期（ChromaDB不支持数组）
            metadata["primary_date"] = meta_dict["extracted_dates"][0]

        # 6. 内容特征
        metadata["text_length"] = meta_dict["text_length"]
        metadata["language"] = meta_dict.get("language", "zh")

        # 7. 生成引用格式（预计算，检索时直接使用）
        metadata["citation"] = chunk.format_citation()

        # 8. Chunk链接
        if "prev_chunk_id" in meta_dict and meta_dict["prev_chunk_id"]:
            metadata["prev_chunk_id"] = meta_dict["prev_chunk_id"]

        if "next_chunk_id" in meta_dict and meta_dict["next_chunk_id"]:
            metadata["next_chunk_id"] = meta_dict["next_chunk_id"]

        return metadata

    def query_with_metadata(
        self,
        query_text: str,
        n_results: int = 5,
        project_id: Optional[int] = None,
        document_types: Optional[List[str]] = None,
        source_levels: Optional[List[int]] = None,
        date_range: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        带元数据过滤的检索（链路十四+十五+十七的综合应用）

        Args:
            query_text: 查询文本
            n_results: 返回结果数
            project_id: 项目ID过滤
            document_types: 文档类型过滤（如['pdf', 'audio']）
            source_levels: 来源层级过滤（如[2, 3]只检索二度和三度报告）
            date_range: 日期范围过滤（起始日期, 结束日期）

        Returns:
            检索结果，每个结果包含text和完整的metadata（包含citation）
        """
        if not self.collection:
            logger.error("❌ ChromaDB collection未初始化")
            return []

        # 构建where条件（链路17：支持多条件组合）
        conditions = []

        if project_id is not None:
            conditions.append({"project_id": str(project_id)})

        if document_types:
            conditions.append({"document_type": {"$in": document_types}})

        if source_levels:
            conditions.append({"source_level": {"$in": source_levels}})

        # 日期范围过滤（链路15）
        # 使用Unix时间戳进行数值比较（ChromaDB只支持数字类型的$gte/$lte）
        if date_range:
            date_from, date_to = date_range

            # 将日期字符串转换为Unix时间戳
            from datetime import datetime
            ts_from = None
            ts_to = None

            try:
                if date_from:
                    dt_from = datetime.fromisoformat(date_from)
                    ts_from = int(dt_from.timestamp())

                if date_to:
                    # 结束日期设为当天的23:59:59
                    dt_to = datetime.fromisoformat(date_to + "T23:59:59")
                    ts_to = int(dt_to.timestamp())

                # 添加时间戳范围条件
                if ts_from and ts_to:
                    conditions.append({"document_date_ts": {"$gte": ts_from}})
                    conditions.append({"document_date_ts": {"$lte": ts_to}})
                elif ts_from:
                    conditions.append({"document_date_ts": {"$gte": ts_from}})
                elif ts_to:
                    conditions.append({"document_date_ts": {"$lte": ts_to}})

                logger.info(f"  📅 应用日期过滤: {date_from} ~ {date_to} (ts: {ts_from} ~ {ts_to})")

            except Exception as e:
                logger.warning(f"  ⚠️ 日期范围解析失败: {e}")
                # 失败时不应用日期过滤

        # 组装where子句
        where_clause = None
        if len(conditions) == 0:
            where_clause = None
        elif len(conditions) == 1:
            where_clause = conditions[0]
        else:
            # 多个条件使用$and
            where_clause = {"$and": conditions}

        # 执行检索
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_clause
            )

            # 格式化返回结果
            formatted_results = []
            if results and results['documents'] and len(results['documents']) > 0:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0] if 'distances' in results else [0] * len(documents)

                for doc, meta, dist in zip(documents, metadatas, distances):
                    # 如果设置了日期范围但元数据中没有document_date，进行后过滤
                    if date_range and "document_date" in meta:
                        doc_date = meta["document_date"]
                        if date_from and doc_date < date_from:
                            continue
                        if date_to and doc_date > date_to:
                            continue

                    formatted_results.append({
                        "text": doc,
                        "metadata": meta,
                        "citation": meta.get("citation", "[来源未知]"),
                        "distance": dist,
                        "relevance": 1.0 - dist  # 转换为相关性分数
                    })

            logger.info(f"✅ 检索完成: 找到 {len(formatted_results)} 个相关chunks")
            return formatted_results

        except Exception as e:
            logger.error(f"❌ 检索失败: {e}", exc_info=True)
            return []

    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        根据chunk_id获取chunk内容和元数据
        """
        if not self.collection:
            return None

        try:
            results = self.collection.get(ids=[chunk_id])

            if results and results['documents']:
                return {
                    "text": results['documents'][0],
                    "metadata": results['metadatas'][0],
                    "citation": results['metadatas'][0].get("citation", "[来源未知]")
                }
        except Exception as e:
            logger.error(f"❌ 获取chunk失败: {e}")

        return None

    def delete_by_document_id(self, document_id: int) -> bool:
        """删除指定文档的所有chunks"""
        if not self.collection:
            return False

        try:
            self.collection.delete(
                where={"document_id": str(document_id)}
            )
            logger.info(f"✅ 删除文档 {document_id} 的所有chunks")
            return True
        except Exception as e:
            logger.error(f"❌ 删除失败: {e}")
            return False


# 全局单例
_vectorization_service_v2 = None

def get_vectorization_service_v2() -> VectorizationServiceV2:
    """获取向量化服务单例"""
    global _vectorization_service_v2
    if _vectorization_service_v2 is None:
        _vectorization_service_v2 = VectorizationServiceV2()
    return _vectorization_service_v2
