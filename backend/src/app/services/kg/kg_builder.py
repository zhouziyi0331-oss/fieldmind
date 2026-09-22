"""
知识图谱自动构建服务

整合 GraphRAG 和 Neo4j，提供：
- 从文档自动提取实体和关系
- 自动构建知识图谱
- 图谱查询和推理
- 社区检测
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class GraphRAGService:
    """
    GraphRAG 服务

    使用 Microsoft GraphRAG 进行图谱自动构建
    """
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self._graphrag = None
        self._initialized = False

        try:
            # 尝试导入 GraphRAG
            import graphrag
            self._graphrag = graphrag
            self._initialized = True
            logger.info("✅ GraphRAG 服务初始化成功")
        except ImportError:
            logger.warning("⚠️ GraphRAG 未安装，请运行: pip install graphrag")
        except Exception as e:
            logger.error(f"❌ GraphRAG 初始化失败: {e}")

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self._initialized and self._graphrag is not None

    def extract_entities_and_relations(
        self,
        text: str,
        entity_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        从文本提取实体和关系

        Args:
            text: 输入文本
            entity_types: 要提取的实体类型列表

        Returns:
            {
                "entities": [{"name": "实体", "type": "类型", "description": "描述"}],
                "relations": [{"source": "实体1", "target": "实体2", "type": "关系"}]
            }
        """
        if not self.is_available():
            logger.warning("GraphRAG 不可用，使用简单提取")
            return self._simple_extract(text)

        try:
            # TODO: 使用 GraphRAG 提取
            # 这里需要根据实际的 GraphRAG API 调整
            logger.warning("GraphRAG 提取功能待完善")
            return self._simple_extract(text)

        except Exception as e:
            logger.error(f"GraphRAG 提取失败: {e}")
            return self._simple_extract(text)

    def _simple_extract(self, text: str) -> Dict[str, Any]:
        """简单的实体关系提取（降级方案）"""
        # 使用 HanLP 进行实体识别
        try:
            from app.services.nlp.hanlp_service import get_hanlp_service
            hanlp = get_hanlp_service()

            entities_raw = hanlp.recognize_entities(text)

            # 转换格式
            entities = []
            for ent in entities_raw:
                entities.append({
                    "name": ent["text"],
                    "type": ent["type"],
                    "description": f"{ent['type']} 实体"
                })

            # 简单的关系提取（基于共现）
            relations = []
            for i in range(len(entities) - 1):
                relations.append({
                    "source": entities[i]["name"],
                    "target": entities[i + 1]["name"],
                    "type": "related_to"
                })

            return {
                "entities": entities,
                "relations": relations
            }

        except Exception as e:
            logger.error(f"简单提取失败: {e}")
            return {"entities": [], "relations": []}


class KnowledgeGraphBuilder:
    """
    知识图谱构建器

    整合 GraphRAG 和 Neo4j
    """

    def __init__(self, db=None):
        self.db = db
        self.graphrag = GraphRAGService()

        logger.info("🕸️ 知识图谱构建器已初始化")

    def build_from_documents(
        self,
        document_ids: List[int],
        project_id: int,
        use_graphrag: bool = True
    ) -> Dict[str, Any]:
        """
        从文档构建知识图谱

        Args:
            document_ids: 文档ID列表
            project_id: 项目ID
            use_graphrag: 是否使用 GraphRAG

        Returns:
            构建结果
        """
        if not self.db:
            raise ValueError("数据库连接不可用")

        try:
            # 获取文档内容
            documents = self._get_documents(document_ids)

            total_entities = 0
            total_relations = 0

            for doc in documents:
                # 提取实体和关系
                if use_graphrag and self.graphrag.is_available():
                    result = self.graphrag.extract_entities_and_relations(
                        doc["content"]
                    )
                else:
                    result = self.graphrag._simple_extract(doc["content"])

                # 保存到数据库
                entities_count = self._save_entities(
                    result["entities"],
                    project_id,
                    doc["id"]
                )
                relations_count = self._save_relations(
                    result["relations"],
                    project_id,
                    doc["id"]
                )

                total_entities += entities_count
                total_relations += relations_count

            logger.info(
                f"✅ 知识图谱构建完成: "
                f"{total_entities} 个实体, {total_relations} 个关系"
            )

            return {
                "status": "success",
                "documents_processed": len(documents),
                "entities_created": total_entities,
                "relations_created": total_relations
            }

        except Exception as e:
            logger.error(f"知识图谱构建失败: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def _get_documents(self, document_ids: List[int]) -> List[Dict[str, Any]]:
        """获取文档内容"""
        from app.models.document import Document

        documents = []
        for doc_id in document_ids:
            doc = self.db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                documents.append({
                    "id": doc.id,
                    "title": doc.title or "",
                    "content": doc.content or ""
                })

        return documents

    def _save_entities(
        self,
        entities: List[Dict[str, Any]],
        project_id: int,
        document_id: int
    ) -> int:
        """保存实体到数据库"""
        from app.models.knowledge_graph import Entity

        saved_count = 0

        for entity_data in entities:
            try:
                # 检查是否已存在
                existing = self.db.query(Entity).filter(
                    Entity.name == entity_data["name"],
                    Entity.project_id == project_id
                ).first()

                if not existing:
                    entity = Entity(
                        name=entity_data["name"],
                        type=entity_data.get("type", "Unknown"),
                        description=entity_data.get("description", ""),
                        project_id=project_id,
                        properties={"source_document": document_id}
                    )
                    self.db.add(entity)
                    saved_count += 1

            except Exception as e:
                logger.warning(f"保存实体失败: {e}")

        self.db.commit()
        return saved_count

    def _save_relations(
        self,
        relations: List[Dict[str, Any]],
        project_id: int,
        document_id: int
    ) -> int:
        """保存关系到数据库"""
        from app.models.knowledge_graph import Entity, Relation

        saved_count = 0

        for relation_data in relations:
            try:
                # 查找源实体和目标实体
                source = self.db.query(Entity).filter(
                    Entity.name == relation_data["source"],
                    Entity.project_id == project_id
                ).first()

                target = self.db.query(Entity).filter(
                    Entity.name == relation_data["target"],
                    Entity.project_id == project_id
                ).first()

                if source and target:
                    # 检查关系是否已存在
                    existing = self.db.query(Relation).filter(
                        Relation.source_id == source.id,
                        Relation.target_id == target.id,
                        Relation.type == relation_data["type"]
                    ).first()

                    if not existing:
                        relation = Relation(
                            source_id=source.id,
                            target_id=target.id,
                            type=relation_data.get("type", "related_to"),
                            properties={"source_document": document_id}
                        )
                        self.db.add(relation)
                        saved_count += 1

            except Exception as e:
                logger.warning(f"保存关系失败: {e}")

        self.db.commit()
        return saved_count

    def query_graph(
        self,
        query: str,
        project_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        查询知识图谱

        Args:
            query: 查询语句或自然语言
            project_id: 项目ID
            limit: 结果数量

        Returns:
            查询结果
        """
        from app.models.knowledge_graph import Entity

        try:
            # 简单的关键词匹配
            entities = self.db.query(Entity).filter(
                Entity.project_id == project_id,
                Entity.name.contains(query)
            ).limit(limit).all()

            results = []
            for entity in entities:
                results.append({
                    "id": entity.id,
                    "name": entity.name,
                    "type": entity.type,
                    "description": entity.description
                })

            return results

        except Exception as e:
            logger.error(f"图谱查询失败: {e}")
            return []

    def get_entity_neighbors(
        self,
        entity_id: int,
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        获取实体的邻居节点

        Args:
            entity_id: 实体ID
            depth: 深度

        Returns:
            邻居信息
        """
        from app.models.knowledge_graph import Entity, Relation

        try:
            entity = self.db.query(Entity).filter(Entity.id == entity_id).first()
            if not entity:
                return {"nodes": [], "edges": []}

            # 获取直接邻居
            outgoing = self.db.query(Relation).filter(
                Relation.source_id == entity_id
            ).all()

            incoming = self.db.query(Relation).filter(
                Relation.target_id == entity_id
            ).all()

            nodes = [{"id": entity.id, "name": entity.name, "type": entity.type}]
            edges = []

            # 添加邻居节点
            for rel in outgoing:
                target = self.db.query(Entity).filter(Entity.id == rel.target_id).first()
                if target:
                    nodes.append({
                        "id": target.id,
                        "name": target.name,
                        "type": target.type
                    })
                    edges.append({
                        "source": entity.id,
                        "target": target.id,
                        "type": rel.type
                    })

            for rel in incoming:
                source = self.db.query(Entity).filter(Entity.id == rel.source_id).first()
                if source:
                    nodes.append({
                        "id": source.id,
                        "name": source.name,
                        "type": source.type
                    })
                    edges.append({
                        "source": source.id,
                        "target": entity.id,
                        "type": rel.type
                    })

            return {
                "nodes": nodes,
                "edges": edges
            }

        except Exception as e:
            logger.error(f"获取邻居失败: {e}")
            return {"nodes": [], "edges": []}


# ==================== 全局单例 ====================

_kg_builder: Optional[KnowledgeGraphBuilder] = None


def get_kg_builder(db=None) -> KnowledgeGraphBuilder:
    """获取知识图谱构建器单例"""
    global _kg_builder

    if _kg_builder is None or (_kg_builder.db is None and db is not None):
        _kg_builder = KnowledgeGraphBuilder(db)

    return _kg_builder
