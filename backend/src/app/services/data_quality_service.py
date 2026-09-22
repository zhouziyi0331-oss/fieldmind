"""
数据质量监控服务
实现材料状态机、数据治理看板、质量评分
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DocumentStatus(str, Enum):
    """文档状态枚举"""
    PENDING = "pending"           # 待处理
    UPLOADING = "uploading"       # 上传中
    PROCESSING = "processing"     # 处理中
    COMPLETED = "completed"       # 已完成
    ERROR = "error"              # 错误
    RETRY = "retry"              # 重试中


class ProcessingStep(str, Enum):
    """处理步骤枚举"""
    UPLOAD = "upload"            # 上传
    EXTRACT = "extract"          # 内容提取
    CHUNK = "chunk"              # 切分
    QUANTIFY = "quantify"        # 量化
    ANALYZE = "analyze"          # 分析


class DataQualityService:
    """
    数据质量监控服务

    功能：
    1. 材料状态追踪
    2. 处理进度监控
    3. 数据质量评分
    4. 缺口分析
    """
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        pass

    def get_project_status(self, db: Session, project_id: int) -> Dict[str, Any]:
        """
        获取项目整体状态

        Returns:
            {
                "total_documents": int,
                "status_breakdown": {
                    "pending": int,
                    "processing": int,
                    "completed": int,
                    "error": int
                },
                "processing_progress": float,  # 0-1
                "quality_score": float,  # 0-100
                "data_coverage": {...},
                "gaps": [...]
            }
        """
        from app.models.project import ProjectDocument
        from app.models.chunk import Chunk

        # 1. 获取所有文档
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        total = len(documents)

        if total == 0:
            return {
                "total_documents": 0,
                "status_breakdown": {},
                "processing_progress": 0.0,
                "quality_score": 0.0,
                "message": "项目中没有文档"
            }

        # 2. 统计状态分布
        status_counts = {
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "error": 0
        }

        for doc in documents:
            status = doc.status or "pending"
            if status in status_counts:
                status_counts[status] += 1
            else:
                # 其他状态归类
                if status in ["uploaded", "queued"]:
                    status_counts["pending"] += 1
                elif status == "failed":
                    status_counts["error"] += 1

        # 3. 计算处理进度
        completed = status_counts["completed"]
        processing_progress = completed / total if total > 0 else 0.0

        # 4. 计算质量分数
        quality_score = self._calculate_quality_score(db, project_id, documents)

        # 5. 数据覆盖度分析
        data_coverage = self._analyze_data_coverage(db, project_id)

        # 6. 缺口分析
        gaps = self._identify_gaps(db, project_id, documents)

        return {
            "total_documents": total,
            "status_breakdown": status_counts,
            "processing_progress": round(processing_progress, 2),
            "quality_score": round(quality_score, 1),
            "data_coverage": data_coverage,
            "gaps": gaps,
            "last_updated": datetime.now().isoformat()
        }

    def _calculate_quality_score(
        self,
        db: Session,
        project_id: int,
        documents: List
    ) -> float:
        """
        计算数据质量分数（0-100）

        评分维度：
        - 文档完整性（40分）
        - 处理成功率（30分）
        - 数据覆盖度（20分）
        - 量化指标完整性（10分）
        """
        from app.models.chunk import Chunk

        score = 0.0

        # 1. 文档完整性（40分）
        total_docs = len(documents)
        docs_with_content = sum(1 for d in documents if d.text_content)
        if total_docs > 0:
            score += (docs_with_content / total_docs) * 40

        # 2. 处理成功率（30分）
        completed_docs = sum(1 for d in documents if d.status == "completed")
        if total_docs > 0:
            score += (completed_docs / total_docs) * 30

        # 3. 数据覆盖度（20分）
        # 检查是否有多种类型的文档
        file_types = set(d.file_type for d in documents if d.file_type)
        type_diversity = min(len(file_types) / 5, 1.0)  # 5种类型为满分
        score += type_diversity * 20

        # 4. 量化指标完整性（10分）
        chunks = db.query(Chunk).filter(Chunk.project_id == project_id).all()
        if chunks:
            chunks_with_sentiment = sum(
                1 for c in chunks if c.sentiment_score is not None
            )
            score += (chunks_with_sentiment / len(chunks)) * 10

        return score

    def _analyze_data_coverage(self, db: Session, project_id: int) -> Dict[str, Any]:
        """
        分析数据覆盖度

        Returns:
            {
                "dimensions": {
                    "文化": 45,
                    "经济": 30,
                    ...
                },
                "file_types": {
                    "pdf": 10,
                    "audio": 5,
                    ...
                }
            }
        """
        from app.models.chunk import Chunk
        from app.models.project import ProjectDocument

        # 维度覆盖
        chunks = db.query(Chunk).filter(Chunk.project_id == project_id).all()

        dimension_counts = {}
        for chunk in chunks:
            dim = chunk.dimension_category or "未分类"
            dimension_counts[dim] = dimension_counts.get(dim, 0) + 1

        # 文件类型覆盖
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        file_type_counts = {}
        for doc in documents:
            ftype = doc.file_type or "unknown"
            file_type_counts[ftype] = file_type_counts.get(ftype, 0) + 1

        return {
            "dimensions": dimension_counts,
            "file_types": file_type_counts,
            "total_chunks": len(chunks),
            "total_documents": len(documents)
        }

    def _identify_gaps(
        self,
        db: Session,
        project_id: int,
        documents: List
    ) -> List[Dict[str, Any]]:
        """
        识别数据缺口

        Returns:
            [
                {
                    "type": "missing_dimension",
                    "severity": "high",
                    "message": "缺少'政策'维度的数据",
                    "suggestion": "建议补充政策相关的调研材料"
                }
            ]
        """
        from app.models.chunk import Chunk

        gaps = []

        # 1. 检查维度缺口
        expected_dimensions = ["文化", "经济", "社会", "政策", "历史"]
        chunks = db.query(Chunk).filter(Chunk.project_id == project_id).all()

        existing_dimensions = set(
            c.dimension_category for c in chunks if c.dimension_category
        )

        for dim in expected_dimensions:
            if dim not in existing_dimensions:
                gaps.append({
                    "type": "missing_dimension",
                    "severity": "medium",
                    "message": f"缺少'{dim}'维度的数据",
                    "suggestion": f"建议补充{dim}相关的调研材料"
                })

        # 2. 检查处理错误
        error_docs = [d for d in documents if d.status == "error" or d.status == "failed"]
        if error_docs:
            gaps.append({
                "type": "processing_error",
                "severity": "high",
                "message": f"有 {len(error_docs)} 个文档处理失败",
                "suggestion": "请查看错误日志并重试",
                "affected_documents": [d.id for d in error_docs[:5]]
            })

        # 3. 检查数据量不足
        if len(documents) < 5:
            gaps.append({
                "type": "insufficient_data",
                "severity": "high",
                "message": f"项目文档数量较少（{len(documents)} 个）",
                "suggestion": "建议至少上传 5 个文档以获得更全面的分析"
            })

        # 4. 检查量化指标缺失
        chunks_without_sentiment = [
            c for c in chunks if c.sentiment_score is None
        ]
        if len(chunks_without_sentiment) > len(chunks) * 0.3:
            gaps.append({
                "type": "missing_quantification",
                "severity": "medium",
                "message": "部分文本块缺少量化指标",
                "suggestion": "系统将自动重新量化这些文本块"
            })

        return gaps

    def get_document_detail(
        self,
        db: Session,
        document_id: int
    ) -> Dict[str, Any]:
        """
        获取单个文档的详细状态

        Returns:
            {
                "id": int,
                "filename": str,
                "status": str,
                "processing_steps": [
                    {
                        "step": "upload",
                        "status": "completed",
                        "timestamp": "...",
                        "duration": 1.2
                    }
                ],
                "error_log": [...],
                "quality_metrics": {...}
            }
        """
        from app.models.project import ProjectDocument
        from app.models.chunk import Chunk

        doc = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not doc:
            return {"error": "文档不存在"}

        # 处理步骤（从 extra_data 中提取）
        processing_steps = self._extract_processing_steps(doc)

        # 错误日志
        error_log = []
        if doc.error_message:
            error_log.append({
                "timestamp": doc.updated_at.isoformat() if doc.updated_at else None,
                "message": doc.error_message
            })

        # 质量指标
        chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()

        quality_metrics = {
            "chunk_count": len(chunks),
            "total_words": doc.word_count or 0,
            "has_sentiment": any(c.sentiment_score is not None for c in chunks),
            "avg_sentiment": sum(c.sentiment_score or 0 for c in chunks) / len(chunks) if chunks else 0
        }

        return {
            "id": doc.id,
            "filename": doc.original_filename,
            "status": doc.status,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "upload_time": doc.upload_time.isoformat() if doc.upload_time else None,
            "processing_steps": processing_steps,
            "error_log": error_log,
            "quality_metrics": quality_metrics,
            "can_retry": doc.status in ["error", "failed"]
        }

    def _extract_processing_steps(self, doc) -> List[Dict[str, Any]]:
        """从文档的 extra_data 提取处理步骤"""
        steps = []

        extra_data = doc.extra_data or {}

        # 上传
        if doc.upload_time:
            steps.append({
                "step": "upload",
                "status": "completed",
                "timestamp": doc.upload_time.isoformat()
            })

        # 内容提取
        if extra_data.get("extraction_status"):
            steps.append({
                "step": "extract",
                "status": extra_data["extraction_status"],
                "timestamp": None
            })

        # 切分
        if extra_data.get("chunking_completed"):
            steps.append({
                "step": "chunk",
                "status": "completed",
                "chunks_count": extra_data.get("chunks_count", 0)
            })

        # 量化
        if extra_data.get("quantification_completed"):
            steps.append({
                "step": "quantify",
                "status": "completed"
            })

        return steps


# 全局实例
data_quality_service = DataQualityService()
