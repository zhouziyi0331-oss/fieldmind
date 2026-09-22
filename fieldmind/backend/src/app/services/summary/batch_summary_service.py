"""
批量缩影生成服务
Batch Summary Generation Service

功能：
1. 批量生成项目所有文档的缩影
2. 进度跟踪
3. 错误处理
4. 统计报告
"""

from sqlalchemy.orm import Session
import logging
from typing import List, Dict, Any
import time

from app.models.project import ProjectDocument
from app.services.summary.enhanced_summary_generator import EnhancedSummaryGenerator

logger = logging.getLogger(__name__)


class BatchSummaryGenerationService:
    """批量缩影生成服务"""

    def __init__(self, db: Session):
        self.db = db
        self.generator = EnhancedSummaryGenerator(db)

    def generate_for_project(
        self,
        project_id: int,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        为项目生成所有文档的缩影

        Args:
            project_id: 项目 ID
            force_regenerate: 是否强制重新生成

        Returns:
            批量生成结果
        """
        logger.info(f"🚀 批量生成缩影 - 项目 {project_id}")

        start_time = time.time()

        # 获取项目下所有文档
        documents = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == 'completed'
        ).all()

        total_docs = len(documents)
        logger.info(f"📋 找到 {total_docs} 个文档")

        results = []
        success_count = 0
        failed_count = 0
        skipped_count = 0

        for i, doc in enumerate(documents, 1):
            logger.info(f"[{i}/{total_docs}] 处理文档: {doc.original_filename}")

            try:
                # 检查是否已有缩影
                if not force_regenerate:
                    from app.models.project import FileSummary
                    existing = self.db.query(FileSummary).filter(
                        FileSummary.document_id == doc.id
                    ).first()

                    if existing and existing.knowledge_graph_node_id:
                        logger.info(f"  ⏭️  已有增强版缩影，跳过")
                        skipped_count += 1
                        results.append({
                            'document_id': doc.id,
                            'filename': doc.original_filename,
                            'status': 'skipped',
                            'reason': '已有增强版缩影'
                        })
                        continue

                # 生成缩影
                result = self.generator.generate_enhanced_summary(doc.id)

                if result['success']:
                    success_count += 1
                    logger.info(f"  ✅ 成功")
                else:
                    failed_count += 1
                    logger.warning(f"  ❌ 失败: {result.get('message')}")

                results.append({
                    'document_id': doc.id,
                    'filename': doc.original_filename,
                    'status': 'success' if result['success'] else 'failed',
                    'result': result
                })

            except Exception as e:
                failed_count += 1
                logger.error(f"  ❌ 异常: {e}", exc_info=True)
                results.append({
                    'document_id': doc.id,
                    'filename': doc.original_filename,
                    'status': 'error',
                    'error': str(e)
                })

        elapsed_time = time.time() - start_time

        summary_result = {
            'success': True,
            'project_id': project_id,
            'total_documents': total_docs,
            'success_count': success_count,
            'failed_count': failed_count,
            'skipped_count': skipped_count,
            'elapsed_time': round(elapsed_time, 2),
            'results': results
        }

        logger.info(
            f"✅ 批量生成完成 - 项目 {project_id}, "
            f"成功: {success_count}, 失败: {failed_count}, 跳过: {skipped_count}, "
            f"耗时: {elapsed_time:.2f}秒"
        )

        return summary_result

    def generate_for_documents(
        self,
        document_ids: List[int]
    ) -> Dict[str, Any]:
        """
        为指定文档生成缩影

        Args:
            document_ids: 文档 ID 列表

        Returns:
            批量生成结果
        """
        logger.info(f"🚀 批量生成缩影 - {len(document_ids)} 个文档")

        start_time = time.time()
        results = []
        success_count = 0
        failed_count = 0

        for i, doc_id in enumerate(document_ids, 1):
            logger.info(f"[{i}/{len(document_ids)}] 处理文档 ID: {doc_id}")

            try:
                result = self.generator.generate_enhanced_summary(doc_id)

                if result['success']:
                    success_count += 1
                else:
                    failed_count += 1

                results.append({
                    'document_id': doc_id,
                    'status': 'success' if result['success'] else 'failed',
                    'result': result
                })

            except Exception as e:
                failed_count += 1
                logger.error(f"  ❌ 异常: {e}", exc_info=True)
                results.append({
                    'document_id': doc_id,
                    'status': 'error',
                    'error': str(e)
                })

        elapsed_time = time.time() - start_time

        return {
            'success': True,
            'total_documents': len(document_ids),
            'success_count': success_count,
            'failed_count': failed_count,
            'elapsed_time': round(elapsed_time, 2),
            'results': results
        }


# ============================================================
# 便捷函数
# ============================================================

def batch_generate_summaries(
    db: Session,
    project_id: int,
    force_regenerate: bool = False
) -> Dict[str, Any]:
    """
    批量生成缩影的便捷函数

    Args:
        db: 数据库会话
        project_id: 项目 ID
        force_regenerate: 是否强制重新生成

    Returns:
        批量生成结果
    """
    service = BatchSummaryGenerationService(db)
    return service.generate_for_project(project_id, force_regenerate)
