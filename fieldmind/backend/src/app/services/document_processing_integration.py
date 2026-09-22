"""
Document Processing Integration - 文档处理集成

将 TF-IDF 和聚类功能集成到现有的文档处理流程中
"""

import logging
import sqlite3
from typing import List, Dict, Any, Optional

from app.core.database import get_sqlite_database_path

logger = logging.getLogger(__name__)


class DocumentProcessingIntegration:
    """文档处理集成器"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_sqlite_database_path()

    def post_process_chunks(self, project_id: int, document_id: str = None):
        """
        在 chunks 保存后执行后处理

        包括：
        1. TF-IDF 关键词提取
        2. 业务维度分类
        3. 聚类分析（如果 chunks 足够多）

        Args:
            project_id: 项目ID
            document_id: 文档ID（可选，如果提供则只处理该文档的chunks）
        """
        logger.info(f"开始后处理项目 {project_id} 的 chunks")

        # 1. 检查 chunks 数量
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if document_id:
            cursor.execute("""
                SELECT COUNT(*) FROM document_chunks
                WHERE project_id = ? AND document_id = ?
            """, (project_id, document_id))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM document_chunks WHERE project_id = ?
            """, (project_id,))

        chunk_count = cursor.fetchone()[0]
        conn.close()

        logger.info(f"项目 {project_id} 有 {chunk_count} 个 chunks")

        if chunk_count == 0:
            logger.warning(f"项目 {project_id} 没有 chunks，跳过后处理")
            return

        # 2. TF-IDF 关键词提取
        try:
            logger.info("开始 TF-IDF 关键词提取...")
            from app.services.tfidf_keyword_extractor import create_extractor
            extractor = create_extractor(self.db_path)
            extractor.batch_extract_for_project(project_id, top_n=5)
            logger.info("✅ TF-IDF 关键词提取完成")
        except Exception as e:
            logger.error(f"TF-IDF 提取失败: {e}", exc_info=True)

        # 3. 聚类分析（只有当 chunks >= 5 时）
        if chunk_count >= 5:
            try:
                logger.info("开始聚类分析...")
                from app.services.topic_clustering_service import create_clustering_service
                clustering_service = create_clustering_service(self.db_path)
                result = clustering_service.auto_cluster_chunks(project_id)

                if 'error' not in result:
                    logger.info(f"✅ 聚类完成：{result['n_clusters']} 个聚类")
                else:
                    logger.error(f"聚类失败: {result['error']}")
            except Exception as e:
                logger.error(f"聚类分析失败: {e}", exc_info=True)
        else:
            logger.info(f"Chunks 数量不足（{chunk_count} < 5），跳过聚类")

        logger.info("✅ 后处理完成")


def integrate_into_pipeline():
    """
    集成到现有的文档处理流程

    使用方式：
    在 document_processing_pipeline_complete.py 的 process_document 方法最后添加：

    ```python
    # ⭐ 新增：后处理
    from app.services.document_processing_integration import DocumentProcessingIntegration
    integrator = DocumentProcessingIntegration()
    integrator.post_process_chunks(project_id, document_id)
    ```
    """
    pass


# 便捷函数
def process_existing_project(project_id: int):
    """
    对已有项目重新执行后处理

    用于对已上传但未处理的数据执行 TF-IDF 和聚类
    """
    integrator = DocumentProcessingIntegration()
    integrator.post_process_chunks(project_id)


if __name__ == "__main__":
    # 测试：对现有项目执行后处理
    import sys

    if len(sys.argv) > 1:
        project_id = int(sys.argv[1])
        print(f"\n对项目 {project_id} 执行后处理...")
        process_existing_project(project_id)
    else:
        print("用法: python document_processing_integration.py <project_id>")
