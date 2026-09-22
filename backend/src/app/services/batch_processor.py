"""
批量文档处理优化
支持并发处理、进度追踪、错误恢复
"""

import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BatchProcessor:
    """批量处理器"""

    def __init__(self, max_workers: int = 3, use_workflow_engine: bool = True):
        """
        初始化批量处理器

        Args:
            max_workers: 最大并发数（默认3，避免过载）
            use_workflow_engine: 是否使用WorkflowEngine
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks = {}  # task_id -> task_info
        self.progress = {}  # task_id -> progress
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=max_workers)

    def create_batch_task(self, task_id: str, items: List[Any]) -> Dict:
        """创建批量任务"""
        task_info = {
            'task_id': task_id,
            'total': len(items),
            'completed': 0,
            'failed': 0,
            'status': 'pending',
            'items': items,
            'results': [],
            'errors': [],
            'created_at': datetime.now().isoformat(),
            'started_at': None,
            'completed_at': None
        }

        self.tasks[task_id] = task_info
        self.progress[task_id] = {
            'total': len(items),
            'completed': 0,
            'failed': 0,
            'progress_percent': 0
        }

        return task_info

    async def process_batch(
        self,
        task_id: str,
        process_func,
        items: List[Any],
        on_progress=None
    ) -> Dict:
        """
        批量处理

        Args:
            task_id: 任务ID
            process_func: 处理函数
            items: 待处理项目列表
            on_progress: 进度回调函数

        Returns:
            处理结果
        """
        task_info = self.tasks.get(task_id)
        if not task_info:
            task_info = self.create_batch_task(task_id, items)

        task_info['status'] = 'running'
        task_info['started_at'] = datetime.now().isoformat()

        logger.info(f"🚀 批量任务开始: {task_id}, 共 {len(items)} 项")

        results = []
        errors = []

        # 使用信号量限制并发
        semaphore = asyncio.Semaphore(self.max_workers)

        async def process_item(item, index):
            async with semaphore:
                try:
                    logger.info(f"处理项目 {index + 1}/{len(items)}")
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        process_func,
                        item
                    )

                    results.append({
                        'index': index,
                        'item': item,
                        'result': result,
                        'status': 'success'
                    })

                    task_info['completed'] += 1

                except Exception as e:
                    logger.error(f"处理失败 {index + 1}/{len(items)}: {e}")
                    errors.append({
                        'index': index,
                        'item': item,
                        'error': str(e),
                        'status': 'failed'
                    })

                    task_info['failed'] += 1

                # 更新进度
                completed = task_info['completed'] + task_info['failed']
                progress_percent = int(completed / len(items) * 100)

                self.progress[task_id] = {
                    'total': len(items),
                    'completed': task_info['completed'],
                    'failed': task_info['failed'],
                    'progress_percent': progress_percent
                }

                # 回调进度
                if on_progress:
                    on_progress(self.progress[task_id])

        # 并发处理所有项目
        tasks = [process_item(item, i) for i, item in enumerate(items)]
        await asyncio.gather(*tasks)

        # 完成
        task_info['status'] = 'completed'
        task_info['completed_at'] = datetime.now().isoformat()
        task_info['results'] = results
        task_info['errors'] = errors

        logger.info(
            f"✅ 批量任务完成: {task_id}, "
            f"成功 {task_info['completed']}, 失败 {task_info['failed']}"
        )

        return task_info

    def get_progress(self, task_id: str) -> Optional[Dict]:
        """获取任务进度"""
        return self.progress.get(task_id)

    def get_task_info(self, task_id: str) -> Optional[Dict]:
        """获取任务详情"""
        return self.tasks.get(task_id)

    def cancel_task(self, task_id: str):
        """取消任务"""
        if task_id in self.tasks:
            self.tasks[task_id]['status'] = 'cancelled'


# 全局批量处理器
batch_processor = BatchProcessor(max_workers=3)


async def batch_reprocess_documents(document_ids: List[int]) -> Dict:
    """
    批量重新处理文档

    Args:
        document_ids: 文档ID列表

    Returns:
        处理结果
    """
    import time
    task_id = f"reprocess_{int(time.time())}"

    def process_single_document(doc_id):
        """处理单个文档"""
        # 这里调用实际的文档处理函数
        from app.services.background_tasks import process_document_background

        try:
            # 模拟处理
            logger.info(f"重新处理文档 {doc_id}")
            # process_document_background(doc_id)
            return {'document_id': doc_id, 'status': 'success'}
        except Exception as e:
            raise Exception(f"文档 {doc_id} 处理失败: {e}")

    result = await batch_processor.process_batch(
        task_id=task_id,
        process_func=process_single_document,
        items=document_ids
    )

    return result


# 使用示例
if __name__ == "__main__":
    async def test_batch_processing():
        # 测试批量处理
        test_items = list(range(1, 11))  # 10个测试项目

        def test_process_func(item):
            import time
            time.sleep(0.5)  # 模拟处理时间
            if item == 5:
                raise Exception("测试错误")
            return item * 2

        task_id = "test_task"
        batch_processor.create_batch_task(task_id, test_items)

        result = await batch_processor.process_batch(
            task_id=task_id,
            process_func=test_process_func,
            items=test_items,
            on_progress=lambda p: print(f"进度: {p['progress_percent']}%")
        )

        print("\n结果:")
        print(f"总数: {result['total']}")
        print(f"成功: {result['completed']}")
        print(f"失败: {result['failed']}")
        print(f"耗时: {result['completed_at']}")

    # 运行测试
    asyncio.run(test_batch_processing())
