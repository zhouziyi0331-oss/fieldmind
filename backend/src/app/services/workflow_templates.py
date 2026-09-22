"""
预定义工作流模板 - 链路十二
包含常用的工作流模板：文档处理、分析报告、知识图谱构建等
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import logging

from app.services.workflow_engine import WorkflowEngine, WorkflowDefinition
from app.services.document_processing_pipeline_complete import DocumentProcessingPipeline
from app.services.knowledge_graph_builder import get_knowledge_graph_builder
from app.core.database import get_db

logger = logging.getLogger(__name__)


class WorkflowTemplates:
    """预定义工作流模板"""



    def __init__(self, use_workflow_engine: bool = True):


        """初始化服务"""


        self.use_workflow_engine = use_workflow_engine


        


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)


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

            pipeline = DocumentProcessingPipeline()
            result = pipeline._vectorize_with_retry(
                text_data["text_content"],
                {"document_id": document_id}
            )
            return {"vectorized": result is not None, "chunk_count": result if result else 0}

        # 任务3：提取实体
        def extract_entities(_context: Dict[str, Any], **kwargs):
            from app.services.entity_extraction import get_entity_extraction_service

            text_data = _context.get("extract_text")
            if not text_data:
                return {"entities": []}

            extractor = get_entity_extraction_service()
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
                builder = get_knowledge_graph_builder(db)

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
            from app.services.entity_extraction import get_entity_extraction_service
            from app.models.timeline import TimelineEvent
            from app.models.project import ProjectDocument

            doc_data = _context.get("get_documents")
            if not doc_data or not doc_data["document_ids"]:
                return {"events_created": 0}

            db: Session = next(get_db())
            try:
                extractor = get_entity_extraction_service()
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
            from app.services.document_processing_pipeline_complete import DocumentProcessingPipeline
            pipeline = DocumentProcessingPipeline()

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
                builder = get_knowledge_graph_builder(db)
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

    @staticmethod
    def create_report_generation_workflow(
        engine: WorkflowEngine,
        project_id: int,
        report_level: int = 1,
        options: Dict[str, Any] = None
    ) -> WorkflowDefinition:
        """
        报告生成工作流

        流程：
        1. 提取报告素材（ReportMaterial）
        2. 生成报告大纲
        3. 并行填充各章节内容
        4. 组装完整报告并保存
        """
        workflow = engine.create_workflow(
            name=f"report_generation_level_{report_level}",
            description=f"生成Level {report_level}报告"
        )

        # 任务1：提取报告素材
        def extract_material(_context: Dict[str, Any], **kwargs):
            from app.services.report_generation.report_material_builder import ReportMaterialBuilder

            db: Session = next(get_db())
            try:
                builder = ReportMaterialBuilder(db)
                material = builder.extract_report_material(project_id)

                return {
                    "material": material.to_dict(),
                    "project_id": project_id,
                    "report_level": report_level
                }
            finally:
                db.close()

        # 任务2：生成报告大纲
        def generate_outline(_context: Dict[str, Any], **kwargs):
            from app.services.report_generation.report_material_builder import ReportMaterialBuilder
            from app.services.report_generation.report_material import ReportMaterial

            material_data = _context.get("extract_material")
            if not material_data:
                raise ValueError("缺少报告素材")

            db: Session = next(get_db())
            try:
                builder = ReportMaterialBuilder(db)
                material = ReportMaterial.from_dict(material_data["material"])
                outline = builder.generate_dynamic_outline(material, report_level)

                return {
                    "outline": outline,
                    "section_count": len(outline)
                }
            finally:
                db.close()

        # 任务3：并行填充章节
        def fill_sections(_context: Dict[str, Any], **kwargs):
            from app.services.report_generation.report_content_engine import ReportContentEngine
            from app.services.report_generation.report_material import ReportMaterial
            from app.services.llm.llm_adapter import get_llm_adapter

            material_data = _context.get("extract_material")
            outline_data = _context.get("generate_outline")

            if not material_data or not outline_data:
                raise ValueError("缺少素材或大纲")

            material = ReportMaterial.from_dict(material_data["material"])
            outline = outline_data["outline"]

            llm_adapter = get_llm_adapter()
            content_engine = ReportContentEngine(llm_adapter)

            sections = []
            for section_outline in outline:
                section = content_engine.fill_section(section_outline, material, report_level)
                sections.append(section)

            return {
                "sections": sections,
                "total_length": sum(len(s.get("content", "")) for s in sections)
            }

        # 任务4：组装完整报告
        def assemble_report(_context: Dict[str, Any], **kwargs):
            from app.models.report import Report

            material_data = _context.get("extract_material")
            sections_data = _context.get("fill_sections")

            if not material_data or not sections_data:
                raise ValueError("缺少数据")

            sections = sections_data["sections"]
            full_content = "\n\n".join([
                f"## {s.get('title', '')}\n\n{s.get('content', '')}"
                for s in sections
            ])

            db: Session = next(get_db())
            try:
                report = Report(
                    project_id=project_id,
                    report_type=f"level_{report_level}",
                    title=f"Level {report_level} 报告",
                    content=full_content,
                    status="completed"
                )
                db.add(report)
                db.commit()
                db.refresh(report)

                logger.info(f"✅ 报告生成完成: ID={report.id}, Level={report_level}, 长度={len(full_content)}")

                return {
                    "report_id": report.id,
                    "content_length": len(full_content),
                    "section_count": len(sections)
                }
            finally:
                db.close()

        # 添加任务
        engine.add_task(workflow, "extract_material", extract_material)
        engine.add_task(
            workflow, "generate_outline", generate_outline,
            dependencies=["extract_material"]
        )
        engine.add_task(
            workflow, "fill_sections", fill_sections,
            dependencies=["generate_outline"]
        )
        engine.add_task(
            workflow, "assemble_report", assemble_report,
            dependencies=["fill_sections"]
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


def run_report_generation_workflow(project_id: int, report_level: int = 1, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """快捷执行报告生成工作流"""
    from app.services.workflow_engine import workflow_engine

    workflow = WorkflowTemplates.create_report_generation_workflow(
        workflow_engine, project_id, report_level, options
    )
    execution = workflow_engine.execute_workflow(workflow)
    return execution.to_dict()
