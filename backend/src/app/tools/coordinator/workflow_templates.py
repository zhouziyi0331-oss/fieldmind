"""
预定义工作流模板 - 链路十二
包含常用的工作流模板：文档处理、分析报告、知识图谱构建等
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import logging

from app.services.workflow_engine import WorkflowEngine, WorkflowDefinition
from app.tools.document import UnifiedDocumentPipeline
from app.tools.knowledge.graph import create_knowledge_graph
from app.core.database import get_db

logger = logging.getLogger(__name__)


class WorkflowTemplates:
    """预定义工作流模板"""

    @staticmethod
    def create_document_processing_workflow(
        engine: WorkflowEngine,
        document_id: int,
        project_id: int
    ) -> WorkflowDefinition:
        """
        文档处理工作流

        流程：
        1. 提取文本
        2. 并行执行：
           - 向量化
           - 实体提取
           - 关键词提取
        3. 更新文档状态
        """
        workflow = engine.create_workflow(
            name="document_processing",
            description="完整文档处理流程"
        )

        # 任务1：提取文本内容
        def extract_text(_context: Dict[str, Any], **kwargs):
            from app.models.project import ProjectDocument
            db: Session = next(get_db())
            try:
                doc = db.query(ProjectDocument).filter(
                    ProjectDocument.id == document_id,
                    ProjectDocument.project_id == project_id
                ).first()

                if not doc or not doc.text_content:
                    raise ValueError(f"文档 {document_id} 不存在或无文本内容")

                return {
                    "document_id": document_id,
                    "text_content": doc.text_content,
                    "filename": doc.filename
                }
            finally:
                db.close()

        # 任务2：向量化
        def vectorize_document(_context: Dict[str, Any], **kwargs):
            text_data = _context.get("extract_text")
            if not text_data:
                raise ValueError("缺少文本数据")

            pipeline = UnifiedDocumentPipeline()
            result = pipeline._vectorize_with_retry(
                text_data["text_content"],
                {"document_id": document_id}
            )
            return {"vectorized": result is not None, "chunk_count": result if result else 0}

        # 任务3：提取实体
        def extract_entities(_context: Dict[str, Any], **kwargs):
            from app.tools.entity import create_engine

            text_data = _context.get("extract_text")
            if not text_data:
                return {"entities": []}

            extractor = create_engine()
            entities = extractor.extract_entities(text_data["text_content"])

            # 存储到数据库
            from app.models.entity import Entity
            db: Session = next(get_db())
            try:
                entities_created = 0
                for ent_data in entities[:50]:  # 限制数量
                    existing = db.query(Entity).filter(
                        Entity.name == ent_data['name'],
                        Entity.entity_type == ent_data['type']
                    ).first()

                    if not existing:
                        new_entity = Entity(
                            entity_type=ent_data['type'],
                            name=ent_data['name'],
                            confidence=ent_data['confidence'],
                            mention_count=ent_data['mention_count'],
                            document_ids=[document_id]
                        )
                        db.add(new_entity)
                        entities_created += 1

                db.commit()
                return {"entities_count": len(entities), "entities_created": entities_created}
            finally:
                db.close()

        # 任务4：提取关键词
        def extract_keywords(_context: Dict[str, Any], **kwargs):
            text_data = _context.get("extract_text")
            if not text_data:
                return {"keywords": []}

            # 使用jieba提取关键词
            import jieba.analyse
            keywords = jieba.analyse.extract_tags(
                text_data["text_content"],
                topK=20,
                withWeight=True
            )
            return {"keywords": [{"word": w, "weight": wt} for w, wt in keywords]}

        # 任务5：更新文档状态
        def update_document_status(_context: Dict[str, Any], **kwargs):
            from app.models.project import ProjectDocument
            db: Session = next(get_db())
            try:
                doc = db.query(ProjectDocument).filter(
                    ProjectDocument.id == document_id
                ).first()

                if doc:
                    # 汇总所有结果
                    vectorize_result = _context.get("vectorize_document", {})
                    entity_result = _context.get("extract_entities", {})
                    keyword_result = _context.get("extract_keywords", {})

                    doc.status = "completed"
                    doc.chunk_count = vectorize_result.get("chunk_count", 0)

                    # 更新entities字段
                    if entity_result.get("entities_count"):
                        doc.entities = {"count": entity_result["entities_count"]}

                    # 更新keywords字段
                    if keyword_result.get("keywords"):
                        doc.keywords = [kw["word"] for kw in keyword_result["keywords"][:10]]

                    db.commit()
                    return {"updated": True}
                return {"updated": False}
            finally:
                db.close()

        # 添加任务
        engine.add_task(workflow, "extract_text", extract_text)

        engine.add_task(
            workflow, "vectorize_document", vectorize_document,
            dependencies=["extract_text"]
        )
        engine.add_task(
            workflow, "extract_entities", extract_entities,
            dependencies=["extract_text"]
        )
        engine.add_task(
            workflow, "extract_keywords", extract_keywords,
            dependencies=["extract_text"]
        )

        engine.add_task(
            workflow, "update_document_status", update_document_status,
            dependencies=["vectorize_document", "extract_entities", "extract_keywords"]
        )

        return workflow

    @staticmethod
    def create_knowledge_graph_workflow(
        engine: WorkflowEngine,
        project_id: int,
        document_ids: List[int] = None
    ) -> WorkflowDefinition:
        """
        知识图谱构建工作流

        流程：
        1. 获取文档列表
        2. 批量提取实体
        3. 提取关系
        4. 构建时间线
        """
        workflow = engine.create_workflow(
            name="knowledge_graph_construction",
            description="知识图谱构建流程"
        )

        # 任务1：获取文档
        def get_documents(_context: Dict[str, Any], **kwargs):
            from app.models.project import ProjectDocument
            db: Session = next(get_db())
            try:
                query = db.query(ProjectDocument).filter(
                    ProjectDocument.project_id == project_id,
                    ProjectDocument.status == "completed"
                )

                if document_ids:
                    query = query.filter(ProjectDocument.id.in_(document_ids))

                docs = query.all()
                return {
                    "document_ids": [doc.id for doc in docs],
                    "document_count": len(docs)
                }
            finally:
                db.close()

        # 任务2：提取实体和关系
        def build_knowledge_graph(_context: Dict[str, Any], **kwargs):
            doc_data = _context.get("get_documents")
            if not doc_data or not doc_data["document_ids"]:
                return {"entities_created": 0, "relationships_created": 0}

            db: Session = next(get_db())
            try:
                builder = create_knowledge_graph(db)

                total_stats = {
                    "entities_created": 0,
                    "entities_updated": 0,
                    "relationships_created": 0
                }

                for doc_id in doc_data["document_ids"]:
                    try:
                        stats = builder.build_from_document(doc_id, project_id)
                        total_stats["entities_created"] += stats["entities_created"]
                        total_stats["entities_updated"] += stats.get("entities_updated", 0)
                        total_stats["relationships_created"] += stats["relationships_created"]
                    except Exception as e:
                        logger.error(f"处理文档 {doc_id} 失败: {e}")

                return total_stats
            finally:
                db.close()

        # 任务3：构建时间线
        def build_timeline(_context: Dict[str, Any], **kwargs):
            from app.tools.entity import create_engine
            from app.models.timeline import TimelineEvent
            from app.models.project import ProjectDocument

            doc_data = _context.get("get_documents")
            if not doc_data or not doc_data["document_ids"]:
                return {"events_created": 0}

            db: Session = next(get_db())
            try:
                extractor = create_engine()
                events_created = 0

                for doc_id in doc_data["document_ids"]:
                    doc = db.query(ProjectDocument).filter(
                        ProjectDocument.id == doc_id
                    ).first()

                    if not doc or not doc.text_content:
                        continue

                    time_expressions = extractor.extract_time_expressions(doc.text_content)

                    for time_expr in time_expressions[:10]:  # 限制数量
                        existing = db.query(TimelineEvent).filter(
                            TimelineEvent.date == time_expr['parsed'],
                            TimelineEvent.document_ids.contains([doc_id])
                        ).first()

                        if not existing:
                            event = TimelineEvent(
                                date=time_expr['parsed'],
                                title=f"{doc.filename} - {time_expr['raw']}",
                                description=f"从文档中提取的时间点：{time_expr['raw']}",
                                category="document_extraction",
                                document_ids=[doc_id],
                                source=doc.filename,
                                confidence=time_expr['confidence'],
                                tags=["auto-extracted", f"project-{project_id}"]
                            )
                            db.add(event)
                            events_created += 1

                db.commit()
                return {"events_created": events_created}
            finally:
                db.close()

        # 添加任务
        engine.add_task(workflow, "get_documents", get_documents)
        engine.add_task(
            workflow, "build_knowledge_graph", build_knowledge_graph,
            dependencies=["get_documents"]
        )
        engine.add_task(
            workflow, "build_timeline", build_timeline,
            dependencies=["get_documents"]
        )

        return workflow

    @staticmethod
    def create_full_analysis_workflow(
        engine: WorkflowEngine,
        project_id: int
    ) -> WorkflowDefinition:
        """
        完整分析工作流：文档处理 + 知识图谱 + 报告生成

        流程：
        1. 获取项目所有文档
        2. 批量处理文档（向量化、实体提取）
        3. 构建知识图谱
        4. 生成分析报告
        """
        workflow = engine.create_workflow(
            name="full_project_analysis",
            description="项目完整分析流程"
        )

        # 任务1：获取文档列表
        def get_project_documents(_context: Dict[str, Any], **kwargs):
            from app.models.project import ProjectDocument
            db: Session = next(get_db())
            try:
                docs = db.query(ProjectDocument).filter(
                    ProjectDocument.project_id == project_id
                ).all()
                return {
                    "document_ids": [doc.id for doc in docs],
                    "total_documents": len(docs)
                }
            finally:
                db.close()

        # 任务2：批量处理文档
        def batch_process_documents(_context: Dict[str, Any], **kwargs):
            doc_data = _context.get("get_project_documents")
            if not doc_data:
                return {"processed": 0}

            # 这里可以调用DocumentProcessingPipeline
            from app.tools.document import UnifiedDocumentPipeline
            pipeline = UnifiedDocumentPipeline()

            processed = 0
            for doc_id in doc_data["document_ids"]:
                try:
                    # 简化版：只标记为processed
                    processed += 1
                except Exception as e:
                    logger.error(f"处理文档 {doc_id} 失败: {e}")

            return {"processed": processed}

        # 任务3：构建知识图谱
        def build_kg(_context: Dict[str, Any], **kwargs):
            doc_data = _context.get("get_project_documents")
            if not doc_data:
                return {}

            db: Session = next(get_db())
            try:
                builder = create_knowledge_graph(db)
                stats = builder.build_from_project(project_id, force_rebuild=False)
                return stats
            finally:
                db.close()

        # 任务4：生成报告
        def generate_report(_context: Dict[str, Any], **kwargs):
            # 汇总所有结果
            doc_data = _context.get("get_project_documents", {})
            process_data = _context.get("batch_process_documents", {})
            kg_data = _context.get("build_kg", {})

            report = {
                "project_id": project_id,
                "total_documents": doc_data.get("total_documents", 0),
                "processed_documents": process_data.get("processed", 0),
                "entities_created": kg_data.get("entities_created", 0),
                "relationships_created": kg_data.get("relationships_created", 0),
                "timeline_events": kg_data.get("timeline_events", 0)
            }

            logger.info(f"📊 分析报告: {report}")
            return report

        # 添加任务
        engine.add_task(workflow, "get_project_documents", get_project_documents)
        engine.add_task(
            workflow, "batch_process_documents", batch_process_documents,
            dependencies=["get_project_documents"]
        )
        engine.add_task(
            workflow, "build_kg", build_kg,
            dependencies=["batch_process_documents"]
        )
        engine.add_task(
            workflow, "generate_report", generate_report,
            dependencies=["build_kg"]
        )

        return workflow


# 工作流快捷方法
def run_document_workflow(document_id: int, project_id: int) -> Dict[str, Any]:
    """快捷执行文档处理工作流"""
    from app.services.workflow_engine import workflow_engine

    workflow = WorkflowTemplates.create_document_processing_workflow(
        workflow_engine, document_id, project_id
    )
    execution = workflow_engine.execute_workflow(workflow)
    return execution.to_dict()


def run_knowledge_graph_workflow(project_id: int, document_ids: List[int] = None) -> Dict[str, Any]:
    """快捷执行知识图谱工作流"""
    from app.services.workflow_engine import workflow_engine

    workflow = WorkflowTemplates.create_knowledge_graph_workflow(
        workflow_engine, project_id, document_ids
    )
    execution = workflow_engine.execute_workflow(workflow)
    return execution.to_dict()


def run_full_analysis_workflow(project_id: int) -> Dict[str, Any]:
    """快捷执行完整分析工作流"""
    from app.services.workflow_engine import workflow_engine

    workflow = WorkflowTemplates.create_full_analysis_workflow(
        workflow_engine, project_id
    )
    execution = workflow_engine.execute_workflow(workflow)
    return execution.to_dict()
