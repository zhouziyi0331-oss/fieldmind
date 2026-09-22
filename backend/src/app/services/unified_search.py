"""
统一查询服务
整合全文搜索、向量检索、知识图谱查询
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import text, or_, and_
from app.core.logging import logger
from app.core.database import get_db_session
from app.core.vector_store import get_vector_store
from app.models.document_chunk import DocumentChunk
from app.models.entity import Entity, EntityRelation
from app.processors.vector_generator import get_vector_generator


class UnifiedSearchService:
    """统一搜索服务"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.vector_store = get_vector_store()
        self.vector_generator = get_vector_generator()

    def search(
        self,
        query: str,
        project_id: int,
        search_type: str = "hybrid",
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        统一搜索入口

        Args:
            query: 查询文本
            project_id: 项目ID
            search_type: 搜索类型
                - "keyword": 关键词搜索
                - "semantic": 语义检索
                - "hybrid": 混合检索（推荐）
                - "entity": 实体查询
            top_k: 返回结果数

        Returns:
            Dict: 搜索结果
                {
                    "query": str,
                    "results": List[Dict],
                    "count": int,
                    "search_type": str
                }
        """
        logger.info(f"[统一查询] query='{query}', type={search_type}, project_id={project_id}")

        if search_type == "keyword":
            results = self._keyword_search(query, project_id, top_k)

        elif search_type == "semantic":
            results = self._semantic_search(query, project_id, top_k)

        elif search_type == "hybrid":
            results = self._hybrid_search(query, project_id, top_k)

        elif search_type == "entity":
            results = self._entity_search(query, project_id, top_k)

        else:
            raise ValueError(f"Unsupported search type: {search_type}")

        return {
            "query": query,
            "results": results,
            "count": len(results),
            "search_type": search_type
        }

    def _keyword_search(
        self,
        query: str,
        project_id: int,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """关键词搜索（全文搜索）"""
        db = get_db_session()

        try:
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.project_id == project_id,
                DocumentChunk.text.like(f"%{query}%")
            ).order_by(DocumentChunk.chunk_index).limit(top_k).all()

            return [
                {
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "page_number": chunk.page_number,
                    "speaker": chunk.speaker,
                    "timestamp_start": chunk.timestamp_start,
                    "score": 1.0,
                    "match_type": "keyword"
                }
                for chunk in chunks
            ]

        finally:
            db.close()

    def _semantic_search(
        self,
        query: str,
        project_id: int,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """语义检索（向量搜索）"""
        # 1. 将查询转换为向量
        query_embedding = self.vector_generator.generate_single(query)

        # 2. 向量检索
        vector_results = self.vector_store.search_similar_vectors(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_conditions={"project_id": project_id}
        )

        # 3. 获取chunk详情
        db = get_db_session()

        try:
            results = []
            chunk_ids = [r['chunk_id'] for r in vector_results]

            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.id.in_(chunk_ids)
            ).all()

            chunk_map = {c.id: c for c in chunks}

            for vec_result in vector_results:
                chunk_id = vec_result['chunk_id']
                if chunk_id in chunk_map:
                    chunk = chunk_map[chunk_id]
                    results.append({
                        "chunk_id": chunk.id,
                        "document_id": chunk.document_id,
                        "chunk_index": chunk.chunk_index,
                        "text": chunk.text,
                        "page_number": chunk.page_number,
                        "speaker": chunk.speaker,
                        "timestamp_start": chunk.timestamp_start,
                        "score": vec_result['similarity'],
                        "match_type": "semantic"
                    })

            return results

        finally:
            db.close()

    def _hybrid_search(
        self,
        query: str,
        project_id: int,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """混合检索（关键词 + 语义）"""
        # 1. 关键词检索
        keyword_results = self._keyword_search(query, project_id, top_k)

        # 2. 语义检索
        semantic_results = self._semantic_search(query, project_id, top_k)

        # 3. 融合结果（去重 + 重排序）
        results_map = {}

        # 关键词结果（权重 0.4）
        for result in keyword_results:
            chunk_id = result['chunk_id']
            results_map[chunk_id] = result
            results_map[chunk_id]['score'] = 0.4

        # 语义结果（权重 0.6）
        for result in semantic_results:
            chunk_id = result['chunk_id']
            if chunk_id in results_map:
                # 已存在，累加分数
                results_map[chunk_id]['score'] += 0.6 * result['score']
                results_map[chunk_id]['match_type'] = "hybrid"
            else:
                # 新结果
                results_map[chunk_id] = result
                results_map[chunk_id]['score'] = 0.6 * result['score']

        # 按分数排序
        results = sorted(
            results_map.values(),
            key=lambda x: x['score'],
            reverse=True
        )

        return results[:top_k]

    def _entity_search(
        self,
        query: str,
        project_id: int,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """实体查询"""
        db = get_db_session()

        try:
            # 查找匹配的实体
            entities = db.query(Entity).filter(
                Entity.text.like(f"%{query}%")
            ).limit(top_k).all()

            results = []

            for entity in entities:
                # 获取该实体相关的chunks
                from app.models.entity import DocumentEntity

                doc_entities = db.query(DocumentEntity).filter(
                    DocumentEntity.entity_id == entity.id
                ).limit(3).all()

                related_chunks = []
                for de in doc_entities:
                    chunk = db.query(DocumentChunk).filter(
                        DocumentChunk.document_id == de.document_id
                    ).first()

                    if chunk:
                        related_chunks.append({
                            "chunk_id": chunk.id,
                            "text": chunk.text[:200] + "..."
                        })

                results.append({
                    "entity_id": entity.id,
                    "entity_name": entity.text,
                    "entity_type": entity.type,
                    "occurrences": len(doc_entities),
                    "related_chunks": related_chunks,
                    "match_type": "entity"
                })

            return results

        finally:
            db.close()

    def get_entity_relations(
        self,
        entity_name: str,
        project_id: int
    ) -> Dict[str, Any]:
        """
        获取实体的关系图谱

        Args:
            entity_name: 实体名称
            project_id: 项目ID

        Returns:
            Dict: 关系图谱
                {
                    "entity": Dict,
                    "relations": List[Dict]
                }
        """
        db = get_db_session()

        try:
            # 查找实体
            entity = db.query(Entity).filter(
                Entity.text == entity_name
            ).first()

            if not entity:
                return {
                    "entity": None,
                    "relations": []
                }

            # 查找所有相关关系
            outgoing = db.query(EntityRelation).filter(
                EntityRelation.source_entity_id == entity.id
            ).all()

            incoming = db.query(EntityRelation).filter(
                EntityRelation.target_entity_id == entity.id
            ).all()

            relations = []

            # 出边
            for rel in outgoing:
                target = db.query(Entity).filter(Entity.id == rel.target_entity_id).first()
                relations.append({
                    "source": entity.text,
                    "relation": rel.relation_type,
                    "target": target.text if target else "Unknown",
                    "direction": "outgoing"
                })

            # 入边
            for rel in incoming:
                source = db.query(Entity).filter(Entity.id == rel.source_entity_id).first()
                relations.append({
                    "source": source.text if source else "Unknown",
                    "relation": rel.relation_type,
                    "target": entity.text,
                    "direction": "incoming"
                })

            return {
                "entity": {
                    "id": entity.id,
                    "name": entity.text,
                    "type": entity.type,
                    "occurrences": len(relations)
                },
                "relations": relations
            }

        finally:
            db.close()


# 便捷函数
def search(
    query: str,
    project_id: int,
    search_type: str = "hybrid",
    top_k: int = 10
) -> Dict[str, Any]:
    """统一搜索"""
    service = UnifiedSearchService()
    return service.search(query, project_id, search_type, top_k)


def get_entity_graph(entity_name: str, project_id: int) -> Dict[str, Any]:
    """获取实体关系图"""
    service = UnifiedSearchService()
    return service.get_entity_relations(entity_name, project_id)
