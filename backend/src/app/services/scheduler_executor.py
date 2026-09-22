"""定时任务执行器"""
import asyncio
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.scheduled_task import ScheduledTask
import logging

if TYPE_CHECKING:
    from app.services.scheduler import SchedulerService

logger = logging.getLogger(__name__)


class SchedulerExecutor:
    """任务执行器"""



    def __init__(self, use_workflow_engine: bool = True):


        """初始化服务"""


        self.use_workflow_engine = use_workflow_engine


        


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)


    async def execute_task(self, task_id: int, db_factory):
        """执行定时任务"""
        from app.services.scheduler import SchedulerService

        db: Session = db_factory()
        try:
            task = SchedulerService.get_task_by_id(db, task_id)
            if not task:
                logger.error(f"任务不存在: ID={task_id}")
                return

            logger.info(f"开始执行任务: {task.name} (类型: {task.task_type})")

            # 创建执行记录
            execution = SchedulerService.create_execution(db, task.id)

            try:
                # 根据任务类型执行不同的逻辑
                if task.task_type == "crawler":
                    result = await self._execute_crawler(db, task)
                elif task.task_type == "report":
                    result = await self._execute_report(db, task)
                elif task.task_type == "quality_check":
                    result = await self._execute_quality_check(db, task)
                elif task.task_type == "export":
                    result = await self._execute_export(db, task)
                elif task.task_type == "cleanup":
                    result = await self._execute_cleanup(db, task)
                else:
                    raise ValueError(f"未知的任务类型: {task.task_type}")

                # 更新执行成功
                SchedulerService.update_execution(
                    db, execution.id, "success", result=result
                )

                # 更新任务最后运行时间
                task.last_run_at = datetime.utcnow()
                db.commit()

                logger.info(f"任务执行成功: {task.name}")

            except Exception as e:
                # 更新执行失败
                error_msg = str(e)
                logger.error(f"任务执行失败: {task.name}, 错误: {error_msg}")
                SchedulerService.update_execution(
                    db, execution.id, "failed", error_message=error_msg
                )

        except Exception as e:
            logger.error(f"执行任务时发生异常: {str(e)}")
        finally:
            db.close()

    async def _execute_crawler(self, db: Session, task: ScheduledTask) -> Dict[str, Any]:
        """执行爬虫任务"""
        from app.services.crawler import WebCrawler

        config = task.config
        urls = config.get("urls", [])
        max_depth = config.get("max_depth", 1)
        max_pages = config.get("max_pages", 10)

        if not urls:
            raise ValueError("爬虫任务缺少URLs配置")

        crawler = WebCrawler()
        results = []

        for url in urls:
            try:
                crawled_data = await crawler.crawl(
                    url=url,
                    max_depth=max_depth,
                    max_pages=max_pages
                )
                results.append({
                    "url": url,
                    "status": "success",
                    "pages_crawled": len(crawled_data)
                })

                # 如果配置了项目ID，自动创建文档
                if task.project_id and config.get("auto_create_documents", False):
                    from app.services.document import DocumentService
                    for page in crawled_data:
                        DocumentService.create_document(
                            db=db,
                            project_id=task.project_id,
                            name=page.get("title", url),
                            content=page.get("content", ""),
                            metadata={"source": "scheduled_crawler", "url": url}
                        )

            except Exception as e:
                results.append({
                    "url": url,
                    "status": "failed",
                    "error": str(e)
                })

        return {
            "total_urls": len(urls),
            "results": results
        }

    async def _execute_report(self, db: Session, task: ScheduledTask) -> Dict[str, Any]:
        """执行报告生成任务"""
        from app.services.report import ReportService

        config = task.config
        report_type = config.get("report_type", "summary")
        recipients = config.get("recipients", [])

        if not task.project_id:
            raise ValueError("报告任务需要指定项目ID")

        # 生成报告
        report_service = ReportService()
        report = await report_service.generate_report(
            db=db,
            project_id=task.project_id,
            report_type=report_type,
            config=config
        )

        # 发送报告（如果配置了收件人）
        sent_count = 0
        if recipients and config.get("auto_send", False):
            for recipient in recipients:
                try:
                    await report_service.send_report(recipient, report)
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"发送报告失败: {recipient}, 错误: {str(e)}")

        return {
            "report_type": report_type,
            "report_id": report.get("id"),
            "recipients": len(recipients),
            "sent": sent_count
        }

    async def _execute_quality_check(self, db: Session, task: ScheduledTask) -> Dict[str, Any]:
        """执行质量检查任务"""
        from app.services.quality import QualityAgent
        from app.models.document import Document

        if not task.project_id:
            raise ValueError("质量检查任务需要指定项目ID")

        config = task.config
        check_all = config.get("check_all", False)
        document_ids = config.get("document_ids", [])

        quality_agent = QualityAgent()
        results = []

        if check_all:
            # 检查项目下所有文档
            documents = db.query(Document).filter(
                Document.project_id == task.project_id
            ).all()
        elif document_ids:
            # 检查指定文档
            documents = db.query(Document).filter(
                Document.id.in_(document_ids)
            ).all()
        else:
            raise ValueError("质量检查任务需要指定check_all或document_ids")

        for doc in documents:
            try:
                validation_result = quality_agent.validate_all(doc)
                results.append({
                    "document_id": doc.id,
                    "status": "success",
                    "validation": validation_result
                })
            except Exception as e:
                results.append({
                    "document_id": doc.id,
                    "status": "failed",
                    "error": str(e)
                })

        return {
            "total_documents": len(documents),
            "results": results
        }

    async def _execute_export(self, db: Session, task: ScheduledTask) -> Dict[str, Any]:
        """执行导出任务"""
        from app.services.export import ExportService

        if not task.project_id:
            raise ValueError("导出任务需要指定项目ID")

        config = task.config
        export_format = config.get("format", "json")
        export_path = config.get("path")

        if not export_path:
            raise ValueError("导出任务需要指定导出路径")

        export_service = ExportService()
        result = await export_service.export_project(
            db=db,
            project_id=task.project_id,
            format=export_format,
            path=export_path,
            config=config
        )

        return {
            "format": export_format,
            "path": export_path,
            "size": result.get("size"),
            "items_exported": result.get("items_exported")
        }

    async def _execute_cleanup(self, db: Session, task: ScheduledTask) -> Dict[str, Any]:
        """执行清理任务"""
        from app.models.document import Document
        from app.models.batch_operation import BatchOperation
        from app.models.scheduled_task import ScheduledTaskExecution
        from datetime import timedelta

        config = task.config
        cleanup_type = config.get("cleanup_type", "old_executions")
        days_to_keep = config.get("days_to_keep", 30)

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted_count = 0

        if cleanup_type == "old_executions":
            # 清理旧的执行记录
            old_executions = db.query(ScheduledTaskExecution).filter(
                ScheduledTaskExecution.completed_at < cutoff_date
            ).all()
            deleted_count = len(old_executions)
            for execution in old_executions:
                db.delete(execution)

        elif cleanup_type == "old_batch_operations":
            # 清理旧的批处理记录
            old_batches = db.query(BatchOperation).filter(
                BatchOperation.completed_at < cutoff_date,
                BatchOperation.status.in_(["completed", "failed", "cancelled"])
            ).all()
            deleted_count = len(old_batches)
            for batch in old_batches:
                db.delete(batch)

        elif cleanup_type == "deleted_documents":
            # 清理标记为删除的文档
            deleted_docs = db.query(Document).filter(
                Document.status == "deleted",
                Document.updated_at < cutoff_date
            ).all()
            deleted_count = len(deleted_docs)
            for doc in deleted_docs:
                db.delete(doc)

        else:
            raise ValueError(f"未知的清理类型: {cleanup_type}")

        db.commit()

        return {
            "cleanup_type": cleanup_type,
            "days_to_keep": days_to_keep,
            "deleted_count": deleted_count
        }

    async def execute_task_manually(self, db: Session, task_id: str) -> Dict[str, Any]:
        """手动执行任务（立即执行）"""
        task = db.query(ScheduledTask).filter(ScheduledTask.task_id == task_id).first()
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        logger.info(f"手动执行任务: {task.name}")

        # 创建执行记录
        execution = SchedulerService.create_execution(db, task.id)

        try:
            # 根据任务类型执行
            if task.task_type == "crawler":
                result = await self._execute_crawler(db, task)
            elif task.task_type == "report":
                result = await self._execute_report(db, task)
            elif task.task_type == "quality_check":
                result = await self._execute_quality_check(db, task)
            elif task.task_type == "export":
                result = await self._execute_export(db, task)
            elif task.task_type == "cleanup":
                result = await self._execute_cleanup(db, task)
            else:
                raise ValueError(f"未知的任务类型: {task.task_type}")

            # 更新执行成功
            SchedulerService.update_execution(db, execution.id, "success", result=result)

            # 更新任务最后运行时间
            task.last_run_at = datetime.utcnow()
            db.commit()

            return {
                "execution_id": execution.id,
                "status": "success",
                "result": result
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"手动执行任务失败: {task.name}, 错误: {error_msg}")
            SchedulerService.update_execution(db, execution.id, "failed", error_message=error_msg)
            raise


# 全局执行器实例
executor = SchedulerExecutor()
