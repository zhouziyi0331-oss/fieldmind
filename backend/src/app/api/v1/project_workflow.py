"""
项目工作流API - 端到端编排（使用真实服务）
统一的分析、处理、通知工作流
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import asyncio
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.project import Project, ProjectDocument
from app.models.document import Document
from app.services.ocr_service import OCRService
from app.services.entity_extraction import EntityExtractionService
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.data_quality_checker import DataQualityChecker
from app.services.websocket_manager import ConnectionManager
from app.schemas.response import success_response, error_response

router = APIRouter()
logger = logging.getLogger(__name__)

# 全局连接管理器
connection_manager = ConnectionManager()


class ProjectWorkflowOrchestrator:
    """项目工作流编排器"""

    def __init__(self, db: Session):
        self.db = db
        self.ocr_service = OCRService()
        self.entity_service = EntityExtractionService()
        self.kg_service = KnowledgeGraphService()
        self.qc_service = DataQualityChecker()

    async def analyze_project(self, project_id: int) -> Dict[str, Any]:
        """完整的项目分析工作流"""

        # Step 0: 验证项目存在
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 获取项目所有文档
        documents = self.db.query(Document).join(
            ProjectDocument, Document.id == ProjectDocument.document_id
        ).filter(
            ProjectDocument.project_id == project_id
        ).all()

        if not documents:
            raise HTTPException(status_code=400, detail="项目无文档可分析")

        total_docs = len(documents)
        results = {
            "project_id": project_id,
            "total_documents": total_docs,
            "processed": 0,
            "failed": 0,
            "steps_completed": [],
            "entities_extracted": 0,
            "kg_stats": {},
            "quality_issues": [],
            "start_time": datetime.now().isoformat()
        }

        # 发送开始通知
        await self._broadcast({
            "type": "workflow_start",
            "data": {
                "project_id": project_id,
                "total_documents": total_docs,
                "workflow": "project_analysis"
            }
        })

        # Step 1: OCR处理（如果需要）
        await self._notify_progress(project_id, "ocr_processing", 0, total_docs)
        ocr_count = 0
        for idx, doc in enumerate(documents, 1):
            if doc.file_path and (doc.file_path.endswith('.pdf') or
                                  doc.file_path.endswith('.png') or
                                  doc.file_path.endswith('.jpg')):
                try:
                    # 使用真实的OCR方法
                    if doc.file_path.endswith('.pdf'):
                        ocr_result = self.ocr_service.recognize_pdf(doc.file_path)
                    else:
                        ocr_result = self.ocr_service.recognize_image(doc.file_path)

                    if ocr_result and ocr_result.text:
                        # 更新文档内容
                        doc.content = ocr_result.text
                        self.db.commit()
                        ocr_count += 1
                        results["processed"] += 1
                except Exception as e:
                    logger.error(f"OCR失败: {doc.title} - {e}")
                    results["failed"] += 1

            await self._notify_progress(project_id, "ocr_processing", idx, total_docs)

        results["steps_completed"].append("ocr_processing")
        logger.info(f"OCR处理完成: {ocr_count}/{total_docs}")

        # Step 2: 实体识别
        await self._notify_progress(project_id, "entity_extraction", 0, total_docs)
        all_entities = []
        for idx, doc in enumerate(documents, 1):
            try:
                # 从文档内容提取实体（同步方法）
                content = doc.content or ""
                if content.strip():
                    entities = self.entity_service.extract_entities(content)
                    all_entities.extend(entities)
                    results["entities_extracted"] += len(entities)
            except Exception as e:
                logger.error(f"实体提取失败: {doc.title} - {e}")

            await self._notify_progress(project_id, "entity_extraction", idx, total_docs)

        results["steps_completed"].append("entity_extraction")
        logger.info(f"实体提取完成: {results['entities_extracted']}个实体")

        # Step 3: 构建知识图谱（使用真实方法）
        await self._notify_progress(project_id, "knowledge_graph", 0, 1)
        try:
            kg_stats = self.kg_service.build_cross_document_graph(project_id, self.db)
            results["kg_stats"] = kg_stats
            results["steps_completed"].append("knowledge_graph")
            logger.info(f"知识图谱构建完成: {kg_stats}")
        except Exception as e:
            logger.error(f"知识图谱构建失败: {e}")
            results["kg_stats"] = {"error": str(e)}

        await self._notify_progress(project_id, "knowledge_graph", 1, 1)

        # Step 4: 质量检查
        await self._notify_progress(project_id, "quality_check", 0, total_docs)
        for idx, doc in enumerate(documents, 1):
            try:
                # 使用真实的质量检查方法（传入document对象和db）
                qc_result = self.qc_service.check_document(doc, self.db)
                if qc_result.get("issues"):
                    results["quality_issues"].extend([
                        {
                            "document_id": doc.id,
                            "document_title": doc.title,
                            "score": qc_result.get("score", 0),
                            "issues": qc_result["issues"]
                        }
                    ])
            except Exception as e:
                logger.error(f"质量检查失败: {doc.title} - {e}")

            await self._notify_progress(project_id, "quality_check", idx, total_docs)

        results["steps_completed"].append("quality_check")
        results["end_time"] = datetime.now().isoformat()

        # 发送完成通知
        await self._broadcast({
            "type": "workflow_complete",
            "data": results
        })

        return results

    async def _notify_progress(self, project_id: int, step: str, current: int, total: int):
        """发送进度通知"""
        await self._broadcast({
            "type": "workflow_progress",
            "data": {
                "project_id": project_id,
                "step": step,
                "current": current,
                "total": total,
                "progress": round(current / total * 100, 2) if total > 0 else 0
            }
        })

    async def _broadcast(self, message: Dict[str, Any]):
        """广播消息到所有WebSocket连接"""
        try:
            await connection_manager.broadcast(message)
        except Exception as e:
            logger.error(f"WebSocket广播失败: {e}")


def _run_workflow_sync(project_id: int):
    """同步包装器：在后台线程中运行异步工作流"""
    import asyncio
    from app.core.database import SessionLocal

    # 创建新的数据库会话（后台任务专用）
    db = SessionLocal()

    try:
        orchestrator = ProjectWorkflowOrchestrator(db)

        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(orchestrator.analyze_project(project_id))
            logger.info(f"工作流完成: {result}")
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"工作流执行失败: {e}", exc_info=True)
    finally:
        db.close()


@router.post("/projects/{project_id}/analyze/")
async def analyze_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    统一的项目分析端点
    触发完整工作流：OCR → 实体识别 → 知识图谱 → 质量检查
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 后台执行（不传递db session，任务内部自己创建）
    background_tasks.add_task(_run_workflow_sync, project_id)

    return success_response(
        data={
            "project_id": project_id,
            "status": "processing"
        },
        message="项目分析已启动"
    )


@router.get("/projects/{project_id}/workflow-status/")
async def get_workflow_status(
    project_id: int,
    db: Session = Depends(get_db)
):
    """查询工作流执行状态"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # TODO: 实现状态持久化和查询
    return success_response(
        data={
            "project_id": project_id,
            "status": "状态持久化功能待实现（P1任务）"
        }
    )
