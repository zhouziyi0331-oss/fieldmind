"""
蒸馏服务

业务逻辑层，协调蒸馏流程和数据持久化
"""

import os
import uuid
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.distillation import (
    DistillationJob,
    DistillationStatus,
    ExtractedKnowledge,
    ExtractedMethod,
    ProductionSnapshot,
)
from app.distillation.types import SourceMetadata, InputMode, SourceKind, SourceMode
from app.distillation.pipeline import DistillationPipeline, DistillationResult
from app.core.config import settings


class DistillationService:
    """蒸馏服务"""

    def __init__(self, db: Session, llm_service=None):
        self.db = db
        self.llm_service = llm_service
        self.output_dir = getattr(
            settings, "DISTILLATION_OUTPUT_DIR", "/tmp/fieldmind_distillation"
        )

    async def create_job_from_file(
        self,
        file_path: str,
        source_kind: SourceKind,
        title: str,
        author: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> DistillationJob:
        """
        从文件创建蒸馏任务

        Args:
            file_path: 文件路径
            source_kind: 来源类型
            title: 标题
            author: 作者
            additional_metadata: 额外元数据

        Returns:
            DistillationJob: 创建的任务
        """
        # 计算文件哈希
        import hashlib

        with open(file_path, "rb") as f:
            file_sha256 = hashlib.sha256(f.read()).hexdigest()

        # 检测文件格式
        file_format = Path(file_path).suffix.lstrip(".")

        # 构建元数据
        metadata = SourceMetadata(
            input_mode=InputMode.FILE,
            source_kind=source_kind,
            source_mode=SourceMode.EMBEDDED,
            title=title,
            author=author,
            file_path=file_path,
            file_format=file_format,
            file_sha256=f"sha256:{file_sha256}",
        )

        if additional_metadata:
            for key, value in additional_metadata.items():
                setattr(metadata, key, value)

        # 创建任务
        job = DistillationJob(
            id=f"job-{uuid.uuid4().hex[:8]}",
            generation_id=f"gen-{uuid.uuid4()}",
            input_mode=metadata.input_mode.value,
            source_kind=metadata.source_kind.value,
            source_mode=metadata.source_mode.value,
            source_metadata={
                "title": metadata.title,
                "author": metadata.author,
                "file_path": metadata.file_path,
                "file_format": metadata.file_format,
                "file_sha256": metadata.file_sha256,
            },
            status=DistillationStatus.PENDING,
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        return job

    async def create_job_from_url(
        self,
        url: str,
        source_kind: SourceKind,
        title: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> DistillationJob:
        """
        从 URL 创建蒸馏任务

        Args:
            url: URL 地址
            source_kind: 来源类型
            title: 标题（可选，会自动提取）
            additional_metadata: 额外元数据

        Returns:
            DistillationJob: 创建的任务
        """
        # 构建元数据
        metadata = SourceMetadata(
            input_mode=InputMode.URL,
            source_kind=source_kind,
            source_mode=SourceMode.EXTERNAL_MEDIA_BOUND,
            title=title or "未知标题",
            original_url=url,
        )

        if additional_metadata:
            for key, value in additional_metadata.items():
                setattr(metadata, key, value)

        # 创建任务
        job = DistillationJob(
            id=f"job-{uuid.uuid4().hex[:8]}",
            generation_id=f"gen-{uuid.uuid4()}",
            input_mode=metadata.input_mode.value,
            source_kind=metadata.source_kind.value,
            source_mode=metadata.source_mode.value,
            source_metadata={
                "title": metadata.title,
                "original_url": metadata.original_url,
            },
            status=DistillationStatus.PENDING,
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        return job

    async def start_distillation(self, job_id: str) -> bool:
        """
        启动蒸馏流程

        Args:
            job_id: 任务 ID

        Returns:
            bool: 是否成功启动
        """
        job = self.db.query(DistillationJob).filter_by(id=job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.status != DistillationStatus.PENDING:
            raise ValueError(f"Job {job_id} is not in PENDING status")

        # 更新状态
        job.status = DistillationStatus.NORMALIZING
        job.started_at = datetime.utcnow()
        self.db.commit()

        # 异步执行蒸馏 - 传递job_id而不是job对象
        asyncio.create_task(self._execute_distillation(job_id))

        return True

    async def _execute_distillation(self, job_id: str):
        """
        执行蒸馏流程（内部方法）

        Args:
            job_id: 蒸馏任务ID
        """
        # 创建新的数据库会话
        from app.core.database import SessionLocal
        db = SessionLocal()

        try:
            # 查询job对象
            job = db.query(DistillationJob).filter_by(id=job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")

            # 重新构建 SourceMetadata
            metadata = SourceMetadata(
                input_mode=InputMode(job.input_mode),
                source_kind=SourceKind(job.source_kind),
                source_mode=SourceMode(job.source_mode),
                **job.source_metadata,
            )

            # 创建流水线
            pipeline = DistillationPipeline(
                llm_service=self.llm_service, output_dir=self.output_dir
            )

            # 执行蒸馏
            result = await pipeline.execute(
                metadata, user_confirmation_callback=self._user_confirmation_callback
            )

            if result.success:
                # 保存结果到数据库
                await self._save_result_to_db(job, result, db)

                # 更新任务状态
                job.status = DistillationStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                job.knowledge_count = len(result.knowledge_units)
                job.method_count = len(result.methods)
            else:
                job.status = DistillationStatus.FAILED
                job.error_message = result.error_message

            db.commit()

        except Exception as e:
            import traceback

            job = db.query(DistillationJob).filter_by(id=job_id).first()
            if job:
                job.status = DistillationStatus.FAILED
                job.error_message = str(e)
                job.error_traceback = traceback.format_exc()
                db.commit()

            raise
        finally:
            db.close()

    async def _user_confirmation_callback(
        self, stage_name: str, data: Any
    ) -> bool:
        """
        用户确认回调

        Args:
            stage_name: 阶段名称
            data: 需要确认的数据

        Returns:
            bool: 用户是否确认
        """
        # TODO: 实现真实的用户确认机制
        # 可以通过 WebSocket 推送给前端，等待用户确认
        print(f"等待用户确认：{stage_name}")
        print(f"数据：{data}")

        # 暂时自动确认
        return True

    async def _save_result_to_db(
        self, job: DistillationJob, result: DistillationResult, db: Session
    ):
        """
        保存蒸馏结果到数据库

        Args:
            job: 蒸馏任务
            result: 蒸馏结果
            db: 数据库会话
        """
        # 保存知识单元
        for ku in result.knowledge_units:
            extracted_knowledge = ExtractedKnowledge(
                id=ku.id,
                job_id=job.id,
                generation_id=result.generation_id,
                type=ku.type.value,
                title=ku.title,
                statement=ku.statement,
                explanation=ku.explanation,
                why_it_matters=ku.why_it_matters,
                scope=ku.scope,
                conditions=ku.conditions,
                boundaries=ku.boundaries,
                counterexamples=ku.counterexamples,
                evidence_anchors=[
                    {
                        "chapter_id": anchor.chapter_id,
                        "quote": anchor.quote,
                        "byte_start": anchor.byte_start,
                        "byte_end": anchor.byte_end,
                    }
                    for anchor in ku.evidence_anchors
                ],
                evidence_route=ku.evidence_route,
                source_certainty=ku.source_certainty.value,
                claim_attribution=ku.claim_attribution.value,
                extraction_certainty=ku.extraction_certainty,
                external_verification_status=ku.external_verification_status,
                tags=ku.tags,
            )
            db.add(extracted_knowledge)

        # 保存方法单元
        for method in result.methods:
            extracted_method = ExtractedMethod(
                id=method.id,
                job_id=job.id,
                generation_id=result.generation_id,
                name=method.name,
                display_name=method.display_name,
                description=method.description,
                reading_quote=method.reading_quote,
                reading_source=method.reading_source,
                interpretation=method.interpretation,
                past_applications=method.past_applications,
                trigger_scenarios=method.trigger_scenarios,
                trigger_language_signals=method.trigger_language_signals,
                distinction_from_neighbors=method.distinction_from_neighbors,
                execution_steps=method.execution_steps,
                boundary_anti_scenarios=method.boundary_anti_scenarios,
                boundary_failure_modes=method.boundary_failure_modes,
                boundary_author_blindspots=method.boundary_author_blindspots,
                boundary_confusion_risks=method.boundary_confusion_risks,
                source_book=method.source_book,
                source_chapter=method.source_chapter,
                tags=method.tags,
                related_methods=method.related_methods,
                canonical_sha256=method.canonical_sha256,
            )
            db.add(extracted_method)

        db.commit()

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        获取任务状态

        Args:
            job_id: 任务 ID

        Returns:
            Dict: 任务状态信息
        """
        job = self.db.query(DistillationJob).filter_by(id=job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        return {
            "id": job.id,
            "generation_id": job.generation_id,
            "status": job.status.value,
            "current_stage": job.current_stage,
            "progress": job.progress,
            "knowledge_count": job.knowledge_count,
            "method_count": job.method_count,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
        }

    async def get_extracted_knowledge(
        self, job_id: str
    ) -> List[Dict[str, Any]]:
        """
        获取提取的知识单元

        Args:
            job_id: 任务 ID

        Returns:
            List[Dict]: 知识单元列表
        """
        knowledge_units = (
            self.db.query(ExtractedKnowledge).filter_by(job_id=job_id).all()
        )

        return [
            {
                "id": ku.id,
                "type": ku.type,
                "title": ku.title,
                "statement": ku.statement,
                "explanation": ku.explanation,
                "evidence_anchors": ku.evidence_anchors,
                "tags": ku.tags,
            }
            for ku in knowledge_units
        ]

    async def get_extracted_methods(self, job_id: str) -> List[Dict[str, Any]]:
        """
        获取提取的方法单元

        Args:
            job_id: 任务 ID

        Returns:
            List[Dict]: 方法单元列表
        """
        methods = self.db.query(ExtractedMethod).filter_by(job_id=job_id).all()

        return [
            {
                "id": method.id,
                "name": method.name,
                "display_name": method.display_name,
                "description": method.description,
                "trigger_scenarios": method.trigger_scenarios,
                "execution_steps": method.execution_steps,
                "tags": method.tags,
            }
            for method in methods
        ]

    async def list_jobs(
        self,
        status: Optional[DistillationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        列出蒸馏任务

        Args:
            status: 过滤状态
            limit: 限制数量
            offset: 偏移量

        Returns:
            List[Dict]: 任务列表
        """
        query = self.db.query(DistillationJob)

        if status:
            query = query.filter_by(status=status)

        query = query.order_by(DistillationJob.created_at.desc())
        query = query.limit(limit).offset(offset)

        jobs = query.all()

        return [
            {
                "id": job.id,
                "generation_id": job.generation_id,
                "status": job.status.value,
                "source_metadata": job.source_metadata,
                "knowledge_count": job.knowledge_count,
                "method_count": job.method_count,
                "created_at": job.created_at.isoformat() if job.created_at else None,
            }
            for job in jobs
        ]

    async def delete_job(self, job_id: str) -> bool:
        """
        删除蒸馏任务

        Args:
            job_id: 任务 ID

        Returns:
            bool: 是否成功删除
        """
        job = self.db.query(DistillationJob).filter_by(id=job_id).first()
        if not job:
            return False

        self.db.delete(job)
        self.db.commit()

        return True
