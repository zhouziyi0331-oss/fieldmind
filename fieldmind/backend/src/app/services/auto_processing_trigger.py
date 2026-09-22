"""
自动处理触发器 - 文档上传后自动开始处理
"""

from typing import Optional
from sqlalchemy.orm import Session
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.services.document_processing_pipeline import DocumentProcessingPipeline

logger = logging.getLogger(__name__)

# 线程池用于异步处理
executor = ThreadPoolExecutor(max_workers=4)


class AutoProcessingTrigger:
    """自动处理触发器"""

    def __init__(self):
        self.processing_tasks = {}  # document_id -> task

    async def trigger_processing(
        self,
        document_id: int,
        file_path: str,
        project_id: int,
        db: Session
    ):
        """
        触发文档自动处理

        Args:
            document_id: 文档ID
            file_path: 文件路径
            project_id: 项目ID
            db: 数据库会话
        """
        logger.info(f"自动触发文档处理: document_id={document_id}")

        try:
            # 创建异步任务
            loop = asyncio.get_event_loop()
            task = loop.run_in_executor(
                executor,
                self._process_document_sync,
                document_id,
                file_path,
                project_id
            )

            # 保存任务引用
            self.processing_tasks[document_id] = task

            logger.info(f"文档 {document_id} 已加入处理队列")

            return {
                'status': 'queued',
                'document_id': document_id,
                'message': '文档已加入处理队列，将自动开始处理'
            }

        except Exception as e:
            logger.error(f"触发处理失败: {e}")
            return {
                'status': 'error',
                'document_id': document_id,
                'error': str(e)
            }

    def _process_document_sync(
        self,
        document_id: int,
        file_path: str,
        project_id: int
    ):
        """
        同步处理文档（在线程池中执行）
        """
        from app.core.database import SessionLocal

        db = SessionLocal()

        try:
            pipeline = DocumentProcessingPipeline()

            logger.info(f"开始处理文档 {document_id}")

            result = pipeline.process_document(
                document_id=document_id,
                file_path=file_path,
                project_id=project_id,
                db=db
            )

            if result['success']:
                logger.info(f"文档 {document_id} 处理成功")
            else:
                logger.error(f"文档 {document_id} 处理失败: {result.get('error')}")

            return result

        except Exception as e:
            logger.error(f"文档 {document_id} 处理异常: {e}")
            return {
                'success': False,
                'error': str(e)
            }

        finally:
            db.close()
            # 清理任务引用
            if document_id in self.processing_tasks:
                del self.processing_tasks[document_id]

    def get_task_status(self, document_id: int) -> Optional[dict]:
        """获取处理任务状态"""
        if document_id in self.processing_tasks:
            task = self.processing_tasks[document_id]
            if task.done():
                return {
                    'status': 'completed',
                    'result': task.result()
                }
            else:
                return {
                    'status': 'processing'
                }
        return None


# 全局触发器实例
auto_trigger = AutoProcessingTrigger()
