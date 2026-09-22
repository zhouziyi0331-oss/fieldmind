"""
混合检索服务 - Hybrid Search Service

结合向量检索和元数据过滤，提供更精准的检索结果

核心功能：
1. 向量语义检索
2. 元数据过滤（章节、标签、实体、时间、空间）
3. 表格结构化查询
4. 结果重排序（Reranking）
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class HybridSearchService:
    """
    混合检索服务

    支持：
    - 向量语义检索（基于 ChromaDB 或 FlagEmbedding）
    - 元数据过滤（章节、标签、实体等）
    - 表格结构化查询（SQL-like）
    - 结果重排序
    """

    def __init__(self, db_session=None):
        self.db = db_session
        self.vector_service = None
        self._init_vector_service()

    def _init_vector_service(self):
        """初始化向量服务"""
        try:
            from app.services.vectorization_service_complete import VectorizationService
            self.vector_service = VectorizationService()
        except Exception as e:
            logger.warning(f"⚠️ 向量服务初始化失败: {e}")

    def search(
        self,
        query: str,
        project_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        use_reranking: bool = False
    ) -> List[Dict[str, Any]]:
        """
        混合检索

        Args:
            query: 查询文本
            project_id: 项目ID（可选）
            filters: 过滤条件，支持：
                - chapter: 章节名称
                - section: 小节名称
                - domain_tags: 领域标签列表
                - entities: 实体名称列表
                - temporal_context: 时间上下文
                - spatial_context: 空间上下文
                - is_table: 是否仅检索表格
            limit: 返回结果数量
            use_reranking: 是否使用重排序

        Returns:
            检索结果列表
        """
        logger.info(f"🔍 混合检索: query='{query}', filters={filters}")

        # 第一步：向量检索（获取候选集）
        vector_results = self._vector_search(query, project_id, limit * 3)  # 多取一些候选

        # 第二步：元数据过滤
        if filters:
            vector_results = self._filter_by_metadata(vector_results, filters)

        # 第三步：重排序（可选）
        if use_reranking:
            vector_results = self._rerank(query, vector_results)

        # 限制返回数量
        results = vector_results[:limit]

        logger.info(f"✅ 检索完成: 返回 {len(results)} 个结果")
        return results

    def _vector_search(
        self,
        query: str,
        project_id: Optional[int],
        limit: int
    ) -> List[Dict[str, Any]]:
        """向量检索"""
        if not self.db:
            logger.warning("⚠️ 数据库连接未初始化")
            return []

        try:
            from app.models.document_chunk import DocumentChunk

            # 生成查询向量
            if self.vector_service and self.vector_service.model:
                query_embedding = self.vector_service.model.encode([query])[0].tolist()
            else:
                logger.warning("⚠️ 向量服务不可用，仅使用元数据检索")
                query_embedding = None

            # 查询数据库
            query_builder = self.db.query(DocumentChunk)

            if project_id:
                query_builder = query_builder.filter(DocumentChunk.project_id == project_id)

            chunks = query_builder.all()

            # 如果有向量，计算相似度
            if query_embedding:
                results_with_score = []
                for chunk in chunks:
                    if chunk.embedding:
                        # 计算余弦相似度
                        score = self._cosine_similarity(query_embedding, chunk.embedding)
                        results_with_score.append((chunk, score))

                # 按相似度排序
                results_with_score.sort(key=lambda x: x[1], reverse=True)
                results = [chunk.to_dict() for chunk, score in results_with_score[:limit]]

                # 添加相似度分数
                for i, (chunk, score) in enumerate(results_with_score[:limit]):
                    results[i]["similarity_score"] = float(score)
            else:
                # 没有向量，返回前N个
                results = [chunk.to_dict() for chunk in chunks[:limit]]

            return results

        except Exception as e:
            logger.error(f"❌ 向量检索失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []

    def _filter_by_metadata(
        self,
        results: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """元数据过滤"""
        filtered = []

        for result in results:
            if self._match_filters(result, filters):
                filtered.append(result)

        logger.info(f"   元数据过滤: {len(results)} → {len(filtered)}")
        return filtered

    def _match_filters(self, chunk: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查 chunk 是否匹配过滤条件"""

        # 章节过滤
        if "chapter" in filters:
            if chunk.get("chapter_title") != filters["chapter"]:
                return False

        # 小节过滤
        if "section" in filters:
            if chunk.get("section_title") != filters["section"]:
                return False

        # 领域标签过滤
        if "domain_tags" in filters:
            chunk_tags = chunk.get("domain_tags") or []
            filter_tags = filters["domain_tags"]
            if not any(tag in chunk_tags for tag in filter_tags):
                return False

        # 实体过滤
        if "entities" in filters:
            chunk_entities = chunk.get("key_entities") or []
            chunk_entity_names = [e.get("name") if isinstance(e, dict) else e for e in chunk_entities]
            filter_entities = filters["entities"]
            if not any(entity in chunk_entity_names for entity in filter_entities):
                return False

        # 时间上下文过滤
        if "temporal_context" in filters:
            if filters["temporal_context"] not in (chunk.get("temporal_context") or ""):
                return False

        # 空间上下文过滤
        if "spatial_context" in filters:
            if filters["spatial_context"] not in (chunk.get("spatial_context") or ""):
                return False

        # 表格过滤
        if "is_table" in filters:
            if chunk.get("is_table_chunk") != filters["is_table"]:
                return False

        return True

    def _rerank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重排序（基于多个因素）"""
        logger.info("   🔄 重排序中...")

        scored_results = []

        for result in results:
            # 计算综合得分
            score = 0.0

            # 1. 向量相似度（如果有）
            if "similarity_score" in result:
                score += result["similarity_score"] * 0.5

            # 2. 实体匹配度
            chunk_entities = result.get("key_entities") or []
            entity_names = [e.get("name") if isinstance(e, dict) else e for e in chunk_entities]
            entity_match = sum(1 for e in entity_names if e in query)
            score += entity_match * 0.2

            # 3. 增强置信度
            confidence = result.get("enhancement_confidence") or 0
            score += (confidence / 100) * 0.1

            # 4. 表格数据加权（如果查询包含"表格"、"数据"等）
            if any(keyword in query for keyword in ["表格", "数据", "统计"]):
                if result.get("is_table_chunk"):
                    score += 0.2

            scored_results.append((result, score))

        # 按得分排序
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # 返回结果，添加重排序分数
        reranked = []
        for result, score in scored_results:
            result["rerank_score"] = float(score)
            reranked.append(result)

        return reranked

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        import numpy as np

        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def search_table(
        self,
        project_id: Optional[int] = None,
        sheet_name: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        表格结构化查询

        Args:
            project_id: 项目ID
            sheet_name: 工作表名称
            conditions: 查询条件（类似 SQL WHERE）
                例如: {"col_1": {"$gt": 1000}, "col_2": "某值"}
            limit: 返回结果数量

        Returns:
            表格行数据列表
        """
        logger.info(f"📊 表格查询: sheet={sheet_name}, conditions={conditions}")

        if not self.db:
            return []

        try:
            from app.models.document_chunk import DocumentChunk

            # 查询表格 chunks
            query = self.db.query(DocumentChunk).filter(
                DocumentChunk.is_table_chunk == 1
            )

            if project_id:
                query = query.filter(DocumentChunk.project_id == project_id)

            if sheet_name:
                query = query.filter(DocumentChunk.table_sheet_name == sheet_name)

            chunks = query.all()

            results = []

            for chunk in chunks:
                structured_data = chunk.structured_data

                if not structured_data:
                    continue

                # 解析结构化数据（如果是字符串）
                if isinstance(structured_data, str):
                    try:
                        structured_data = json.loads(structured_data)
                    except:
                        continue

                rows = structured_data.get("rows", [])

                # 应用条件过滤
                for row in rows:
                    if self._match_table_conditions(row, conditions):
                        results.append({
                            "chunk_id": chunk.chunk_id,
                            "sheet_name": chunk.table_sheet_name,
                            "row": row
                        })

                if len(results) >= limit:
                    break

            logger.info(f"✅ 表格查询完成: 返回 {len(results)} 行")
            return results[:limit]

        except Exception as e:
            logger.error(f"❌ 表格查询失败: {e}")
            return []

    def _match_table_conditions(
        self,
        row: Dict[str, Any],
        conditions: Optional[Dict[str, Any]]
    ) -> bool:
        """检查表格行是否匹配条件"""
        if not conditions:
            return True

        cells = row.get("cells", [])

        for col_key, condition in conditions.items():
            # 提取列索引
            if col_key.startswith("col_"):
                col_idx = int(col_key.split("_")[1])
            else:
                continue

            if col_idx >= len(cells):
                return False

            cell = cells[col_idx]
            cell_value = cell.get("value")

            # 处理条件
            if isinstance(condition, dict):
                # 操作符条件（如 {"$gt": 1000}）
                for op, target_value in condition.items():
                    if op == "$gt" and not (cell_value and cell_value > target_value):
                        return False
                    elif op == "$lt" and not (cell_value and cell_value < target_value):
                        return False
                    elif op == "$eq" and cell_value != target_value:
                        return False
                    elif op == "$ne" and cell_value == target_value:
                        return False
                    elif op == "$in" and cell_value not in target_value:
                        return False
            else:
                # 直接值匹配
                if cell_value != condition:
                    return False

        return True


# 全局实例（需要在使用时传入 db_session）
def get_hybrid_search_service(db_session) -> HybridSearchService:
    """获取混合检索服务实例"""
    return HybridSearchService(db_session)


if __name__ == "__main__":
    print("=" * 80)
    print("🔍 混合检索服务")
    print("=" * 80)
    print("\n使用示例：")
    print("""
# 1. 向量检索 + 元数据过滤
results = search_service.search(
    query="王大爷谈了什么美食",
    filters={
        "chapter": "第一章：传统美食",
        "domain_tags": ["饮食", "民俗"]
    }
)

# 2. 表格结构化查询
table_results = search_service.search_table(
    sheet_name="销售数据",
    conditions={"col_2": {"$gt": 1000}}  # 第2列 > 1000
)
    """)
    print("=" * 80)
