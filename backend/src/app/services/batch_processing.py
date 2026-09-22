"""批量处理服务"""
import uuid
import logging
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.batch_operation import BatchOperation
from app.models.project import ProjectDocument
from app.services.background_tasks import submit_task

logger = logging.getLogger(__name__)


class BatchProcessingService:
    """批量处理服务 - 管理批量操作"""



    def __init__(self, use_workflow_engine: bool = True):


        """初始化服务"""


        self.use_workflow_engine = use_workflow_engine


        


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)


    @staticmethod
    def create_batch_operation(
        db: Session,
        project_id: int,
        operation_type: str,
        total_items: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> BatchOperation:
        """
        创建批次操作记录

        Args:
            db: 数据库会话
            project_id: 项目ID
            operation_type: 操作类型 (upload, delete, reprocess, quality_check)
            total_items: 总项目数
            metadata: 元数据

        Returns:
            BatchOperation对象
        """
        batch_id = str(uuid.uuid4())

        batch_op = BatchOperation(
            batch_id=batch_id,
            project_id=project_id,
            operation_type=operation_type,
            total_items=total_items,
            completed_items=0,
            failed_items=0,
            status="pending",
            metadata=metadata or {}
        )

        db.add(batch_op)
        db.commit()
        db.refresh(batch_op)

        logger.info(f"创建批次操作: {batch_id}, 类型={operation_type}, 项目数={total_items}")

        return batch_op

    @staticmethod
    def update_batch_progress(
        db: Session,
        batch_id: str,
        completed: int = 0,
        failed: int = 0,
        status: Optional[str] = None
    ):
        """
        更新批次进度

        Args:
            db: 数据库会话
            batch_id: 批次ID
            completed: 完成数增量
            failed: 失败数增量
            status: 新状态
        """
        batch_op = db.query(BatchOperation).filter(
            BatchOperation.batch_id == batch_id
        ).first()

        if not batch_op:
            logger.error(f"批次操作不存在: {batch_id}")
            return

        # 更新计数
        if completed > 0:
            batch_op.completed_items += completed
        if failed > 0:
            batch_op.failed_items += failed

        # 更新状态
        if status:
            batch_op.status = status
        else:
            # 自动判断状态
            total_processed = batch_op.completed_items + batch_op.failed_items
            if total_processed >= batch_op.total_items:
                batch_op.status = "completed"
                batch_op.completed_at = datetime.utcnow()
            elif batch_op.status == "pending":
                batch_op.status = "processing"

        db.commit()

        logger.info(
            f"批次进度更新: {batch_id}, "
            f"完成={batch_op.completed_items}/{batch_op.total_items}, "
            f"失败={batch_op.failed_items}, 状态={batch_op.status}"
        )

    @staticmethod
    async def batch_submit_documents(
        db: Session,
        document_ids: List[int],
        project_id: int,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        批量提交文档处理任务

        Args:
            db: 数据库会话
            document_ids: 文档ID列表
            project_id: 项目ID
            max_concurrent: 最大并发数

        Returns:
            结果字典
        """
        # 创建批次记录
        batch_op = BatchProcessingService.create_batch_operation(
            db=db,
            project_id=project_id,
            operation_type="reprocess",
            total_items=len(document_ids),
            metadata={"document_ids": document_ids}
        )

        batch_id = batch_op.batch_id

        # 更新状态为processing
        batch_op.status = "processing"
        db.commit()

        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_limit(doc_id: int):
            async with semaphore:
                try:
                    # 提交到后台处理
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        submit_task,
                        doc_id
                    )
                    BatchProcessingService.update_batch_progress(
                        db, batch_id, completed=1
                    )
                    return {"document_id": doc_id, "status": "submitted"}
                except Exception as e:
                    logger.error(f"提交文档 {doc_id} 失败: {e}")
                    BatchProcessingService.update_batch_progress(
                        db, batch_id, failed=1
                    )
                    return {"document_id": doc_id, "status": "failed", "error": str(e)}

        # 并发处理所有文档
        results = await asyncio.gather(
            *[process_with_limit(doc_id) for doc_id in document_ids],
            return_exceptions=True
        )

        # 统计结果
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "submitted")
        failed = len(results) - successful

        logger.info(f"批量提交完成: 批次={batch_id}, 成功={successful}, 失败={failed}")

        return {
            "batch_id": batch_id,
            "total": len(document_ids),
            "successful": successful,
            "failed": failed,
            "results": results
        }

    @staticmethod
    def batch_delete_documents(
        db: Session,
        document_ids: List[int],
        project_id: int
    ) -> Dict[str, Any]:
        """
        批量删除文档

        Args:
            db: 数据库会话
            document_ids: 文档ID列表
            project_id: 项目ID

        Returns:
            结果字典
        """
        # 创建批次记录
        batch_op = BatchProcessingService.create_batch_operation(
            db=db,
            project_id=project_id,
            operation_type="delete",
            total_items=len(document_ids),
            metadata={"document_ids": document_ids}
        )

        batch_id = batch_op.batch_id
        batch_op.status = "processing"
        db.commit()

        successful = 0
        failed = 0
        errors = []

        for doc_id in document_ids:
            try:
                # 查询文档
                doc = db.query(ProjectDocument).filter(
                    ProjectDocument.id == doc_id,
                    ProjectDocument.project_id == project_id
                ).first()

                if not doc:
                    failed += 1
                    errors.append({
                        "document_id": doc_id,
                        "error": "Document not found"
                    })
                    continue

                # 删除文件
                import os
                if doc.file_path and os.path.exists(doc.file_path):
                    try:
                        os.remove(doc.file_path)
                    except Exception as e:
                        logger.warning(f"删除文件失败: {doc.file_path}, 错误: {e}")

                # 删除数据库记录
                db.delete(doc)
                db.commit()

                successful += 1
                logger.info(f"删除文档成功: {doc_id}")

            except Exception as e:
                failed += 1
                errors.append({
                    "document_id": doc_id,
                    "error": str(e)
                })
                logger.error(f"删除文档失败: {doc_id}, 错误: {e}")
                db.rollback()

        # 更新批次状态
        batch_op.completed_items = successful
        batch_op.failed_items = failed
        batch_op.status = "completed"
        batch_op.completed_at = datetime.utcnow()
        batch_op.metadata["errors"] = errors
        db.commit()

        logger.info(f"批量删除完成: 批次={batch_id}, 成功={successful}, 失败={failed}")

        return {
            "batch_id": batch_id,
            "total": len(document_ids),
            "successful": successful,
            "failed": failed,
            "errors": errors
        }

    @staticmethod
    def get_batch_status(db: Session, batch_id: str) -> Optional[BatchOperation]:
        """
        获取批次状态

        Args:
            db: 数据库会话
            batch_id: 批次ID

        Returns:
            BatchOperation对象或None
        """
        return db.query(BatchOperation).filter(
            BatchOperation.batch_id == batch_id
        ).first()

    @staticmethod
    def list_batch_operations(
        db: Session,
        project_id: Optional[int] = None,
        operation_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[BatchOperation]:
        """
        列出批次操作

        Args:
            db: 数据库会话
            project_id: 项目ID过滤
            operation_type: 操作类型过滤
            status: 状态过滤
            limit: 限制数量
            offset: 偏移量

        Returns:
            BatchOperation列表
        """
        query = db.query(BatchOperation)

        if project_id:
            query = query.filter(BatchOperation.project_id == project_id)
        if operation_type:
            query = query.filter(BatchOperation.operation_type == operation_type)
        if status:
            query = query.filter(BatchOperation.status == status)

        return query.order_by(
            BatchOperation.created_at.desc()
        ).offset(offset).limit(limit).all()

    @staticmethod
    def cancel_batch_operation(db: Session, batch_id: str) -> bool:
        """
        取消批次操作

        Args:
            db: 数据库会话
            batch_id: 批次ID

        Returns:
            是否成功
        """
        batch_op = db.query(BatchOperation).filter(
            BatchOperation.batch_id == batch_id
        ).first()

        if not batch_op:
            return False

        if batch_op.status in ["completed", "failed", "cancelled"]:
            logger.warning(f"批次 {batch_id} 已经结束，无法取消")
            return False

        batch_op.status = "cancelled"
        batch_op.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"取消批次操作: {batch_id}")
        return True


# 创建全局实例
batch_service = BatchProcessingService()
