"""
Quality Control Tasks - 质量控制Celery任务
自动化质量检查流程，集成到工作流中
"""
from celery import Task, group, chain
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.celery_app import celery_app
from app.agents.quality_control_agent import get_quality_control_agent

logger = logging.getLogger(__name__)


class QualityCheckTask(Task):
    """质量检查任务基类"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败处理"""
        logger.error(f"Quality check task {task_id} failed: {exc}")

    def on_success(self, retval, task_id, args, kwargs):
        """任务成功处理"""
        logger.info(f"Quality check task {task_id} completed successfully")


@celery_app.task(
    base=QualityCheckTask,
    name="quality.check_document",
    bind=True,
    max_retries=2
)
def check_document_quality(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    检查文档转换质量

    Args:
        document_data: 文档数据，包含id, content, format, metadata

    Returns:
        质量报告字典
    """
    try:
        logger.info(f"Starting document quality check for: {document_data.get('id')}")

        agent = get_quality_control_agent()
        report = agent.validate_document(document_data)

        logger.info(f"Document quality check completed: score={report.overall_score}, passed={report.passed}")

        return report.to_dict()

    except Exception as e:
        logger.error(f"Document quality check error: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(
    base=QualityCheckTask,
    name="quality.check_ocr",
    bind=True,
    max_retries=2
)
def check_ocr_quality(self, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    检查OCR识别质量

    Args:
        ocr_result: OCR结果，包含task_id, text, confidence, text_blocks

    Returns:
        质量报告字典
    """
    try:
        logger.info(f"Starting OCR quality check for: {ocr_result.get('task_id')}")

        agent = get_quality_control_agent()
        report = agent.validate_ocr_result(ocr_result)

        logger.info(f"OCR quality check completed: score={report.overall_score}, passed={report.passed}")

        return report.to_dict()

    except Exception as e:
        logger.error(f"OCR quality check error: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(
    base=QualityCheckTask,
    name="quality.check_entities",
    bind=True,
    max_retries=2
)
def check_entity_quality(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    检查实体识别质量

    Args:
        entity_data: 实体数据，包含document_id, entities

    Returns:
        质量报告字典
    """
    try:
        logger.info(f"Starting entity quality check for: {entity_data.get('document_id')}")

        agent = get_quality_control_agent()
        report = agent.validate_entities(entity_data)

        logger.info(f"Entity quality check completed: score={report.overall_score}, passed={report.passed}")

        return report.to_dict()

    except Exception as e:
        logger.error(f"Entity quality check error: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(
    base=QualityCheckTask,
    name="quality.check_embedding",
    bind=True,
    max_retries=2
)
def check_embedding_quality(self, embedding_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    检查向量化质量

    Args:
        embedding_data: 向量数据，包含document_id, embedding

    Returns:
        质量报告字典
    """
    try:
        logger.info(f"Starting embedding quality check for: {embedding_data.get('document_id')}")

        agent = get_quality_control_agent()
        report = agent.validate_embedding(embedding_data)

        logger.info(f"Embedding quality check completed: score={report.overall_score}, passed={report.passed}")

        return report.to_dict()

    except Exception as e:
        logger.error(f"Embedding quality check error: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(
    base=QualityCheckTask,
    name="quality.check_graph",
    bind=True,
    max_retries=2
)
def check_graph_quality(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    检查知识图谱质量

    Args:
        graph_data: 图谱数据，包含document_id, nodes, relationships

    Returns:
        质量报告字典
    """
    try:
        logger.info(f"Starting graph quality check for: {graph_data.get('document_id')}")

        agent = get_quality_control_agent()
        report = agent.validate_knowledge_graph(graph_data)

        logger.info(f"Graph quality check completed: score={report.overall_score}, passed={report.passed}")

        return report.to_dict()

    except Exception as e:
        logger.error(f"Graph quality check error: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(
    name="quality.batch_check",
    bind=True
)
def batch_quality_check(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    批量质量检查

    Args:
        tasks: 任务列表，每个任务包含type和data字段

    Returns:
        批量检查结果
    """
    try:
        logger.info(f"Starting batch quality check for {len(tasks)} tasks")

        # 创建并行任务组
        job_group = []
        for task in tasks:
            task_type = task.get("type")
            task_data = task.get("data", {})

            if task_type == "document":
                job_group.append(check_document_quality.s(task_data))
            elif task_type == "ocr":
                job_group.append(check_ocr_quality.s(task_data))
            elif task_type == "entity":
                job_group.append(check_entity_quality.s(task_data))
            elif task_type == "embedding":
                job_group.append(check_embedding_quality.s(task_data))
            elif task_type == "graph":
                job_group.append(check_graph_quality.s(task_data))

        # 并行执行
        result = group(job_group).apply_async()
        reports = result.get()

        # 统计结果
        passed = sum(1 for r in reports if r.get("passed", False))
        failed = len(reports) - passed

        logger.info(f"Batch quality check completed: {passed} passed, {failed} failed")

        return {
            "total": len(reports),
            "passed": passed,
            "failed": failed,
            "reports": reports,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Batch quality check error: {e}")
        raise


@celery_app.task(
    name="quality.full_pipeline_check",
    bind=True
)
def full_pipeline_quality_check(
    self,
    document_id: str,
    document_data: Optional[Dict[str, Any]] = None,
    entity_data: Optional[Dict[str, Any]] = None,
    embedding_data: Optional[Dict[str, Any]] = None,
    graph_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    完整流水线质量检查

    检查文档处理的所有环节：文档转换 → 实体识别 → 向量化 → 知识图谱

    Args:
        document_id: 文档ID
        document_data: 文档数据（可选）
        entity_data: 实体数据（可选）
        embedding_data: 向量数据（可选）
        graph_data: 图谱数据（可选）

    Returns:
        完整流水线质量报告
    """
    try:
        logger.info(f"Starting full pipeline quality check for document: {document_id}")

        reports = {}

        # 1. 文档质量检查
        if document_data:
            doc_report = check_document_quality(document_data)
            reports["document"] = doc_report

        # 2. 实体质量检查
        if entity_data:
            entity_report = check_entity_quality(entity_data)
            reports["entity"] = entity_report

        # 3. 向量质量检查
        if embedding_data:
            emb_report = check_embedding_quality(embedding_data)
            reports["embedding"] = emb_report

        # 4. 图谱质量检查
        if graph_data:
            graph_report = check_graph_quality(graph_data)
            reports["graph"] = graph_report

        # 计算总体评分
        scores = [r.get("overall_score", 0) for r in reports.values()]
        overall_score = sum(scores) / len(scores) if scores else 0

        # 判断是否通过
        all_passed = all(r.get("passed", False) for r in reports.values())

        # 汇总问题
        all_issues = []
        for report in reports.values():
            all_issues.extend(report.get("issues", []))

        # 需要人工审核？
        manual_review = any(r.get("manual_review_required", False) for r in reports.values())

        result = {
            "document_id": document_id,
            "overall_score": round(overall_score, 2),
            "passed": all_passed,
            "reports": reports,
            "total_issues": len(all_issues),
            "critical_issues": len([i for i in all_issues if i.get("severity") == "critical"]),
            "manual_review_required": manual_review,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"Full pipeline quality check completed: score={overall_score}, passed={all_passed}")

        return result

    except Exception as e:
        logger.error(f"Full pipeline quality check error: {e}")
        raise


@celery_app.task(
    name="quality.get_statistics",
    bind=True
)
def get_quality_statistics(self) -> Dict[str, Any]:
    """
    获取质量控制统计信息

    Returns:
        统计信息字典
    """
    try:
        agent = get_quality_control_agent()
        stats = agent.get_statistics()

        return {
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Get quality statistics error: {e}")
        raise


@celery_app.task(
    name="quality.reset_statistics",
    bind=True
)
def reset_quality_statistics(self) -> Dict[str, Any]:
    """
    重置质量控制统计

    Returns:
        重置确认
    """
    try:
        agent = get_quality_control_agent()
        agent.reset_statistics()

        return {
            "message": "Statistics reset successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Reset quality statistics error: {e}")
        raise
