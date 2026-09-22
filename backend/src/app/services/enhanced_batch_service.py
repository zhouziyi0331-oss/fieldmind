"""
增强批量文档处理服务

整合WebSocket事件、错误恢复和进度追踪
"""
from typing import List, Dict, Any, Optional, Callable
import asyncio
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from app.services.batch_processor import BatchProcessor
from app.services.event_emitter import get_event_emitter
from app.models.document import Document
from app.models.batch_operation import BatchOperation, BatchOperationStatus

logger = logging.getLogger(__name__)


class EnhancedBatchService:
    """增强批量处理服务"""

    def __init__(self, db: Session, max_workers: int = 3):
        self.db = db
        self.batch_processor = BatchProcessor(max_workers=max_workers)
        self.event_emitter = get_event_emitter()

    async def batch_process_documents(
        self,
        project_id: int,
        document_ids: List[int],
        operation_type: str,
        operation_config: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        批量处理文档

        Args:
            project_id: 项目ID
            document_ids: 文档ID列表
            operation_type: 操作类型（extract, analyze, distill等）
            operation_config: 操作配置
            user_id: 用户ID

        Returns:
            批处理结果
        """
        # 创建批处理记录
        batch_op = BatchOperation(
            project_id=project_id,
            operation_type=operation_type,
            total_items=len(document_ids),
            status=BatchOperationStatus.PENDING,
            config=operation_config or {},
            user_id=user_id
        )
        self.db.add(batch_op)
        self.db.commit()
        self.db.refresh(batch_op)

        batch_id = f"batch_{batch_op.id}"

        # 发射开始事件
        await self.event_emitter.emit("batch.start", {
            "batch_id": batch_id,
            "project_id": project_id,
            "operation_type": operation_type,
            "total_items": len(document_ids)
        })

        # 定义进度回调
        async def on_progress(progress: Dict[str, Any]):
            # 更新数据库
            batch_op.completed_items = progress["completed"]
            batch_op.failed_items = progress["failed"]
            self.db.commit()

            # 发射进度事件
            await self.event_emitter.emit("batch.progress", {
                "batch_id": batch_id,
                "project_id": project_id,
                "progress": progress
            })

        # 定义项目完成回调
        async def on_item_complete(item_result: Dict[str, Any]):
            await self.event_emitter.emit("batch.item.complete", {
                "batch_id": batch_id,
                "project_id": project_id,
                "item": item_result
            })

        try:
            # 获取文档列表
            documents = self.db.query(Document).filter(
                Document.id.in_(document_ids),
                Document.project_id == project_id
            ).all()

            if len(documents) != len(document_ids):
                raise ValueError("部分文档不存在或不属于该项目")

            # 选择处理函数
            process_func = self._get_process_function(operation_type, operation_config)

            # 执行批量处理
            batch_op.status = BatchOperationStatus.RUNNING
            self.db.commit()

            result = await self.batch_processor.process_batch(
                task_id=batch_id,
                process_func=process_func,
                items=documents,
                on_progress=lambda p: asyncio.create_task(on_progress(p))
            )

            # 更新批处理记录
            batch_op.status = BatchOperationStatus.COMPLETED
            batch_op.completed_items = result["completed"]
            batch_op.failed_items = result["failed"]
            batch_op.result_summary = {
                "success_count": len(result["results"]),
                "error_count": len(result["errors"])
            }
            self.db.commit()

            # 发射完成事件
            await self.event_emitter.emit("batch.complete", {
                "batch_id": batch_id,
                "project_id": project_id,
                "completed": result["completed"],
                "failed": result["failed"],
                "total": len(document_ids)
            })

            return {
                "batch_id": batch_id,
                "status": "completed",
                "total": len(document_ids),
                "completed": result["completed"],
                "failed": result["failed"],
                "results": result["results"],
                "errors": result["errors"]
            }

        except Exception as e:
            logger.error(f"批量处理失败: {e}")

            # 更新批处理记录
            batch_op.status = BatchOperationStatus.FAILED
            batch_op.error_message = str(e)
            self.db.commit()

            # 发射错误事件
            await self.event_emitter.emit("batch.error", {
                "batch_id": batch_id,
                "project_id": project_id,
                "error": str(e)
            })

            return {
                "batch_id": batch_id,
                "status": "failed",
                "error": str(e)
            }

    def _get_process_function(
        self,
        operation_type: str,
        config: Optional[Dict[str, Any]]
    ) -> Callable:
        """获取处理函数"""
        if operation_type == "extract":
            return lambda doc: self._extract_document(doc, config)
        elif operation_type == "analyze":
            return lambda doc: self._analyze_document(doc, config)
        elif operation_type == "distill":
            return lambda doc: self._distill_document(doc, config)
        elif operation_type == "index":
            return lambda doc: self._index_document(doc, config)
        else:
            raise ValueError(f"不支持的操作类型: {operation_type}")

    def _extract_document(self, document: Document, config: Optional[Dict]) -> Dict[str, Any]:
        """提取文档内容"""
        # TODO: 实现实际的提取逻辑
        return {
            "document_id": document.id,
            "extracted": True,
            "content_length": len(document.content or "")
        }

    def _analyze_document(self, document: Document, config: Optional[Dict]) -> Dict[str, Any]:
        """分析文档"""
        # TODO: 实现实际的分析逻辑
        return {
            "document_id": document.id,
            "analyzed": True
        }

    def _distill_document(self, document: Document, config: Optional[Dict]) -> Dict[str, Any]:
        """蒸馏文档知识"""
        # TODO: 实现实际的蒸馏逻辑
        return {
            "document_id": document.id,
            "distilled": True
        }

    def _index_document(self, document: Document, config: Optional[Dict]) -> Dict[str, Any]:
        """索引文档"""
        # TODO: 实现实际的索引逻辑
        return {
            "document_id": document.id,
            "indexed": True
        }

    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """获取批处理状态"""
        # 从batch_id提取数据库ID
        try:
            db_id = int(batch_id.replace("batch_", ""))
            batch_op = self.db.query(BatchOperation).filter(
                BatchOperation.id == db_id
            ).first()

            if not batch_op:
                return None

            return {
                "batch_id": batch_id,
                "project_id": batch_op.project_id,
                "operation_type": batch_op.operation_type,
                "status": batch_op.status.value,
                "total_items": batch_op.total_items,
                "completed_items": batch_op.completed_items,
                "failed_items": batch_op.failed_items,
                "created_at": batch_op.created_at.isoformat(),
                "error_message": batch_op.error_message,
                "result_summary": batch_op.result_summary
            }

        except ValueError:
            return None

    def list_batch_operations(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """列出批处理操作"""
        query = self.db.query(BatchOperation)

        if project_id:
            query = query.filter(BatchOperation.project_id == project_id)

        if status:
            try:
                status_enum = BatchOperationStatus(status)
                query = query.filter(BatchOperation.status == status_enum)
            except ValueError:
                pass

        batch_ops = query.order_by(
            BatchOperation.created_at.desc()
        ).limit(limit).all()

        return [
            {
                "batch_id": f"batch_{op.id}",
                "project_id": op.project_id,
                "operation_type": op.operation_type,
                "status": op.status.value,
                "total_items": op.total_items,
                "completed_items": op.completed_items,
                "failed_items": op.failed_items,
                "created_at": op.created_at.isoformat()
            }
            for op in batch_ops
        ]

    async def retry_failed_items(
        self,
        batch_id: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """重试失败的项目"""
        # 获取原始批处理
        try:
            db_id = int(batch_id.replace("batch_", ""))
            original_batch = self.db.query(BatchOperation).filter(
                BatchOperation.id == db_id
            ).first()

            if not original_batch:
                raise ValueError("批处理不存在")

            # TODO: 实现重试逻辑
            # 需要从原始批处理中提取失败的文档ID并重新处理

            return {
                "message": "重试功能开发中",
                "batch_id": batch_id
            }

        except ValueError as e:
            raise ValueError(f"无效的batch_id: {e}")

    def get_batch_progress(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """获取批处理进度"""
        return self.batch_processor.progress.get(batch_id)
