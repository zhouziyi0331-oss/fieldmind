"""
DLT 数据管道集成
优化文档处理流程，添加数据验证和增量加载
"""

import dlt
from typing import Iterator, Dict, Any, List
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


# ===== DLT Pipeline 定义 =====


@dlt.resource(name="documents", write_disposition="merge", primary_key="document_id")
def extract_documents(project_id: int) -> Iterator[Dict[str, Any]]:
    """
    提取文档数据

    使用 dlt 的增量加载机制，只处理新文档或更新的文档
    """
    from app.models.project import ProjectDocument
    from app.core.database import SessionLocal

    db = SessionLocal()

    try:
        # 使用 dlt 的状态管理实现增量加载
        last_processed = dlt.current.resource_state().get("last_processed_at")

        query = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        )

        if last_processed:
            # 只获取上次处理后的新文档
            query = query.filter(ProjectDocument.created_at > last_processed)

        documents = query.all()

        logger.info(f"提取了 {len(documents)} 个待处理文档")

        for doc in documents:
            yield {
                "document_id": doc.id,
                "project_id": doc.project_id,
                "file_path": doc.file_path,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "status": doc.status,
                "created_at": doc.created_at,
                "updated_at": doc.updated_at,
            }

        # 更新状态
        dlt.current.resource_state()["last_processed_at"] = datetime.now()

    finally:
        db.close()


@dlt.transformer(name="process_documents", primary_key="document_id")
def process_documents(documents: Iterator[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
    """
    处理文档数据

    添加数据验证和转换
    """
    from app.services.document_converter import DocumentConverter

    converter = DocumentConverter()

    for doc in documents:
        try:
            # 数据验证
            if not _validate_document(doc):
                logger.error(f"文档 {doc['document_id']} 验证失败")
                continue

            # 提取内容
            file_path = doc["file_path"]
            if Path(file_path).exists():
                content = converter.convert(file_path, doc["file_type"])

                doc["content"] = content
                doc["content_length"] = len(content) if content else 0
                doc["processed_at"] = datetime.now()
                doc["processing_status"] = "success"

                yield doc
            else:
                logger.error(f"文件不存在: {file_path}")
                doc["processing_status"] = "file_not_found"
                yield doc

        except Exception as e:
            logger.error(f"处理文档 {doc['document_id']} 失败: {e}")
            doc["processing_status"] = "error"
            doc["error_message"] = str(e)
            yield doc


def _validate_document(doc: Dict[str, Any]) -> bool:
    """
    验证文档数据

    使用 dlt 的内置验证功能
    """
    required_fields = ["document_id", "project_id", "file_path", "file_type"]

    # 检查必需字段
    for field in required_fields:
        if field not in doc or doc[field] is None:
            logger.error(f"缺少必需字段: {field}")
            return False

    # 验证文件大小
    if doc.get("file_size", 0) > 100 * 1024 * 1024:  # 100MB
        logger.error(f"文件过大: {doc['file_size']} bytes")
        return False

    # 验证文件类型
    allowed_types = ["pdf", "docx", "txt", "md", "jpg", "png", "mp3", "mp4"]
    if doc.get("file_type") not in allowed_types:
        logger.error(f"不支持的文件类型: {doc['file_type']}")
        return False

    return True


# ===== DLT Pipeline 主函数 =====


def run_document_pipeline(project_id: int, destination: str = "duckdb") -> dict:
    """
    运行文档处理管道

    Args:
        project_id: 项目 ID
        destination: 数据目标（duckdb/postgres/bigquery）

    Returns:
        Pipeline 执行结果
    """
    # 创建 pipeline
    pipeline = dlt.pipeline(
        pipeline_name="fieldmind_documents",
        destination=destination,
        dataset_name=f"project_{project_id}",
    )

    # 运行 pipeline
    logger.info(f"开始运行文档处理 Pipeline (project_id={project_id})")

    load_info = pipeline.run(
        extract_documents(project_id) | process_documents(),
        write_disposition="merge",
    )

    logger.info(f"Pipeline 完成: {load_info}")

    return {
        "pipeline_name": pipeline.pipeline_name,
        "dataset_name": pipeline.dataset_name,
        "loads": load_info.loads_ids,
        "status": "success" if load_info.has_failed_jobs == False else "failed",
    }


# ===== 增量更新函数 =====


def incremental_update_documents(project_id: int) -> dict:
    """
    增量更新文档

    只处理新增或修改的文档
    """
    logger.info(f"开始增量更新 (project_id={project_id})")

    result = run_document_pipeline(project_id)

    logger.info(f"增量更新完成: {result}")

    return result


# ===== 完整重建函数 =====


def full_rebuild_documents(project_id: int) -> dict:
    """
    完整重建文档数据

    重新处理所有文档
    """
    logger.info(f"开始完整重建 (project_id={project_id})")

    # 重置状态
    pipeline = dlt.pipeline(
        pipeline_name="fieldmind_documents",
        destination="duckdb",
        dataset_name=f"project_{project_id}",
    )

    # 清除状态
    pipeline.drop()

    # 重新运行
    result = run_document_pipeline(project_id)

    logger.info(f"完整重建完成: {result}")

    return result


# ===== 数据质量检查 =====


@dlt.source
def data_quality_checks(project_id: int):
    """
    数据质量检查

    检查处理结果的质量
    """

    @dlt.resource
    def check_completeness():
        """检查完整性"""
        from app.core.database import SessionLocal
        from app.models.project import ProjectDocument

        db = SessionLocal()

        try:
            total = (
                db.query(ProjectDocument)
                .filter(ProjectDocument.project_id == project_id)
                .count()
            )

            processed = (
                db.query(ProjectDocument)
                .filter(
                    ProjectDocument.project_id == project_id,
                    ProjectDocument.status == "completed",
                )
                .count()
            )

            return [
                {
                    "check": "completeness",
                    "total_documents": total,
                    "processed_documents": processed,
                    "completion_rate": processed / total if total > 0 else 0,
                    "passed": processed / total > 0.95 if total > 0 else False,
                }
            ]

        finally:
            db.close()

    @dlt.resource
    def check_content_quality():
        """检查内容质量"""
        from app.core.database import SessionLocal
        from app.models.project import ProjectDocument

        db = SessionLocal()

        try:
            docs_with_content = (
                db.query(ProjectDocument)
                .filter(
                    ProjectDocument.project_id == project_id,
                    ProjectDocument.text_content != None,
                    ProjectDocument.text_content != "",
                )
                .count()
            )

            total_processed = (
                db.query(ProjectDocument)
                .filter(
                    ProjectDocument.project_id == project_id,
                    ProjectDocument.status == "completed",
                )
                .count()
            )

            return [
                {
                    "check": "content_quality",
                    "documents_with_content": docs_with_content,
                    "total_processed": total_processed,
                    "content_extraction_rate": (
                        docs_with_content / total_processed
                        if total_processed > 0
                        else 0
                    ),
                    "passed": (
                        docs_with_content / total_processed > 0.90
                        if total_processed > 0
                        else False
                    ),
                }
            ]

        finally:
            db.close()

    return check_completeness, check_content_quality


# ===== API 接口 =====


def get_pipeline_status(project_id: int) -> dict:
    """
    获取 Pipeline 状态

    Returns:
        Pipeline 运行状态和统计信息
    """
    pipeline = dlt.pipeline(
        pipeline_name="fieldmind_documents",
        destination="duckdb",
        dataset_name=f"project_{project_id}",
    )

    try:
        # 获取最后一次运行信息
        last_trace = pipeline.last_trace

        if last_trace:
            return {
                "pipeline_name": pipeline.pipeline_name,
                "dataset_name": pipeline.dataset_name,
                "last_run": last_trace.started_at,
                "status": "success" if not last_trace.finished_at else "running",
                "duration": (
                    (last_trace.finished_at - last_trace.started_at).total_seconds()
                    if last_trace.finished_at
                    else None
                ),
            }
        else:
            return {
                "pipeline_name": pipeline.pipeline_name,
                "status": "not_run",
            }

    except Exception as e:
        logger.error(f"获取 Pipeline 状态失败: {e}")
        return {
            "status": "error",
            "error": str(e),
        }
