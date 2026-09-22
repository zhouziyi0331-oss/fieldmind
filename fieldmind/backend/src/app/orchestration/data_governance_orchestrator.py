"""
数据治理 Agent 编排器
整合：采集 → 分块 → 向量化 → 知识图谱 → 数据治理
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time

from app.core.logging import logger
from app.core.database import get_db_session


class GovernanceStage(str, Enum):
    """数据治理流程阶段"""
    INGESTION = "ingestion"           # 采集（18个插件）
    METADATA = "metadata"             # 元数据提取
    CHUNKING = "chunking"             # 分块
    METRICS = "metrics"               # 指标计算
    VECTORIZATION = "vectorization"   # 向量化
    KNOWLEDGE = "knowledge"           # 知识图谱
    LINEAGE = "lineage"               # 血缘追踪
    QUALITY = "quality"               # 质量检查
    COMPLETE = "complete"             # 完成


@dataclass
class GovernanceResult:
    """治理结果"""
    file_id: str
    success: bool
    stages_completed: List[GovernanceStage]
    stage_results: Dict[GovernanceStage, Dict[str, Any]]
    total_duration: float
    errors: List[str] = field(default_factory=list)


class DataGovernanceOrchestrator:
    """
    数据治理编排器

    完整流程：
    1. 采集（IngestionAgent + 18个插件）
    2. 元数据提取（MetadataCollector）
    3. 分块（ChunkingAgent）
    4. 指标计算（MetricCalculator）
    5. 向量化（VectorizationAgent）
    6. 知识图谱（KnowledgeAgent）
    7. 血缘追踪（LineageTracker）
    8. 质量检查（QualityChecker）
    """

    def __init__(self):
        # 懒加载所有组件
        self._ingestion_agent = None
        self._chunking_agent = None
        self._vectorization_agent = None
        self._knowledge_agent = None
        self._lineage_tracker = None
        self._metric_calculator = None

    def process_file(
        self,
        file_path: str,
        filename: str,
        mime_type: str,
        project_id: int,
        collection_info: Optional[Dict[str, Any]] = None
    ) -> GovernanceResult:
        """
        处理单个文件（完整治理流程）

        Args:
            file_path: 文件路径
            filename: 文件名
            mime_type: MIME类型
            project_id: 项目ID
            collection_info: 采集信息

        Returns:
            GovernanceResult: 治理结果
        """
        start_time = time.time()

        logger.info(f"[数据治理] 开始处理文件: {filename}")

        result = GovernanceResult(
            file_id=None,
            success=False,
            stages_completed=[],
            stage_results={},
            total_duration=0,
            errors=[]
        )

        # 创建数据库会话，贯穿所有阶段
        db = get_db_session()

        try:
            # 阶段1: 采集（IngestionAgent + 18个插件）
            ingestion_result = self._stage_ingestion(
                file_path, filename, mime_type, collection_info
            )
            result.stages_completed.append(GovernanceStage.INGESTION)
            result.stage_results[GovernanceStage.INGESTION] = ingestion_result

            # 阶段2: 元数据提取
            metadata_result = self._stage_metadata(
                ingestion_result['raw_text'],
                ingestion_result['structured_metadata']
            )
            result.stages_completed.append(GovernanceStage.METADATA)
            result.stage_results[GovernanceStage.METADATA] = metadata_result

            # 阶段3: 分块（ChunkingAgent）
            chunking_result = self._stage_chunking(
                file_id=result.file_id,
                text=ingestion_result['raw_text'],
                metadata=ingestion_result['structured_metadata']
            )
            result.stages_completed.append(GovernanceStage.CHUNKING)
            result.stage_results[GovernanceStage.CHUNKING] = chunking_result

            # 阶段4: 指标计算（MetricCalculator）
            metrics_result = self._stage_metrics(
                chunks=chunking_result['chunks'],
                db=db
            )
            result.stages_completed.append(GovernanceStage.METRICS)
            result.stage_results[GovernanceStage.METRICS] = metrics_result

            # 阶段5: 向量化（VectorizationAgent）
            vectorization_result = self._stage_vectorization(
                chunks=chunking_result['chunks']
            )
            result.stages_completed.append(GovernanceStage.VECTORIZATION)
            result.stage_results[GovernanceStage.VECTORIZATION] = vectorization_result

            # 阶段6: 知识图谱（KnowledgeAgent）
            knowledge_result = self._stage_knowledge(
                chunks=chunking_result['chunks']
            )
            result.stages_completed.append(GovernanceStage.KNOWLEDGE)
            result.stage_results[GovernanceStage.KNOWLEDGE] = knowledge_result

            # 阶段7: 血缘追踪（LineageTracker）
            lineage_result = self._stage_lineage(
                file_id=result.file_id,
                chunk_ids=[c['id'] for c in chunking_result['chunks']],
                project_id=project_id,
                db=db
            )
            result.stages_completed.append(GovernanceStage.LINEAGE)
            result.stage_results[GovernanceStage.LINEAGE] = lineage_result

            # 阶段8: 质量检查（QualityChecker）
            quality_result = self._stage_quality(
                file_id=result.file_id,
                project_id=project_id,
                db=db
            )
            result.stages_completed.append(GovernanceStage.QUALITY)
            result.stage_results[GovernanceStage.QUALITY] = quality_result

            # 所有阶段成功，提交事务
            db.commit()
            result.success = True
            result.total_duration = time.time() - start_time

            logger.info(
                f"[数据治理] 文件处理完成: {filename}, "
                f"阶段 {len(result.stages_completed)}/8, "
                f"耗时 {result.total_duration:.2f}s"
            )

        except Exception as e:
            # 任何阶段失败，回滚所有数据库操作
            db.rollback()
            logger.error(
                f"[数据治理] 文件处理失败，已回滚所有数据库操作: {e}",
                filename=filename,
                stages_completed=len(result.stages_completed)
            )
            result.errors.append(str(e))
            result.total_duration = time.time() - start_time

        finally:
            # 无论成功失败，关闭数据库会话
            db.close()

        return result

    def _stage_ingestion(
        self,
        file_path: str,
        filename: str,
        mime_type: str,
        collection_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """阶段1: 采集"""
        from app.agents.ingestion_agent import get_ingestion_agent

        agent = get_ingestion_agent()
        return agent.ingest_file(file_path, filename, mime_type)

    def _stage_metadata(
        self,
        text: str,
        structured_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """阶段2: 元数据提取"""
        from app.services.metadata_collector import MetadataCollector

        content_metadata = MetadataCollector.extract_content_metadata(
            text=text,
            doc_type=structured_metadata.get('content_type', 'document')
        )

        return {
            "extracted": True,
            "content_metadata": content_metadata
        }

    def _stage_chunking(
        self,
        file_id: str,
        text: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """阶段3: 分块"""
        from app.agents.chunking_agent import ChunkingAgent

        if self._chunking_agent is None:
            self._chunking_agent = ChunkingAgent()

        result = self._chunking_agent.process(text, metadata)

        return {
            "chunks": result.chunks,
            "total_chunks": len(result.chunks)
        }

    def _stage_metrics(self, chunks: List[Any], db=None) -> Dict[str, Any]:
        """阶段4: 指标计算（批量优化）"""
        from app.services.metric_calculator import calculate_chunk_metrics

        metrics_count = 0

        # 批量计算指标，避免N+1查询
        # 注意：这里仍需循环，但db参数传递确保使用同一会话
        for chunk in chunks:
            metrics = calculate_chunk_metrics(
                chunk_id=chunk.id,
                chunk_text=chunk.content,
                db=db
            )
            metrics_count += len(metrics)

        return {
            "metrics_calculated": metrics_count,
            "chunks_processed": len(chunks)
        }

    def _stage_vectorization(self, chunks: List[Any]) -> Dict[str, Any]:
        """阶段5: 向量化"""
        from app.agents.vectorization_agent import VectorizationAgent

        if self._vectorization_agent is None:
            self._vectorization_agent = VectorizationAgent()

        result = self._vectorization_agent.vectorize(chunks)

        return {
            "vectors_generated": len(result.get('vectors', [])),
            "chunks_vectorized": len(chunks)
        }

    def _stage_knowledge(self, chunks: List[Any]) -> Dict[str, Any]:
        """阶段6: 知识图谱"""
        from app.agents.knowledge_agent import KnowledgeAgent

        if self._knowledge_agent is None:
            self._knowledge_agent = KnowledgeAgent()

        result = self._knowledge_agent.build_graph(chunks)

        return {
            "entities_extracted": len(result.get('entities', [])),
            "relations_extracted": len(result.get('relations', []))
        }

    def _stage_lineage(
        self,
        file_id: str,
        chunk_ids: List[str],
        project_id: int,
        db=None
    ) -> Dict[str, Any]:
        """阶段7: 血缘追踪（批量优化）"""
        from app.services.lineage_tracker import LineageTracker

        if not chunk_ids:
            return {
                "lineage_recorded": 0,
                "chunks_tracked": 0
            }

        # 批量记录血缘关系
        lineage_count = LineageTracker.record_lineage_batch(
            project_id=project_id,
            source_type="file",
            source_id=file_id,
            target_type="chunk",
            target_ids=chunk_ids,
            transform_type="extract",
            transform_description="文件分块",
            db=db
        )

        return {
            "lineage_recorded": lineage_count,
            "chunks_tracked": len(chunk_ids)
        }

    def _stage_quality(
        self,
        file_id: str,
        project_id: int,
        db
    ) -> Dict[str, Any]:
        """阶段8: 质量检查"""
        from app.models.governance import QualityRule, QualityCheckResult

        # 获取适用的质量规则
        rules = db.query(QualityRule).filter(
            QualityRule.enabled == True
        ).all()

        if not rules:
            logger.info(f"[质量检查] 没有启用的质量规则，跳过检查")
            return {
                "quality_checks": 0,
                "issues_found": 0,
                "rules_applied": 0
            }

        checks_performed = 0
        issues_found = 0

        for rule in rules:
            try:
                # 执行质量检查
                check_result = self._execute_quality_rule(
                    rule=rule,
                    file_id=file_id,
                    project_id=project_id,
                    db=db
                )

                if check_result:
                    checks_performed += 1
                    if not check_result.check_result:
                        issues_found += 1

            except Exception as e:
                logger.warning(f"[质量检查] 规则 {rule.rule_name} 执行失败: {e}")
                continue

        # 注意: 不在这里commit，由编排器统一管理事务
        return {
            "quality_checks": checks_performed,
            "issues_found": issues_found,
            "rules_applied": len(rules)
        }

    def _execute_quality_rule(
        self,
        rule,
        file_id: str,
        project_id: int,
        db
    ) -> Optional[Any]:
        """执行单个质量规则"""
        from app.models.governance import QualityCheckResult
        from app.models.document import Document
        from app.models.document_chunk import DocumentChunk

        # 获取文档和chunks
        document = db.query(Document).filter(Document.id == file_id).first()
        if not document:
            return None

        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == file_id
        ).all()

        # 根据规则类型执行不同检查
        rule_type = rule.rule_type
        passed = True
        issue_desc = None
        suggestion = None

        if rule_type == "completeness":
            # 完整性检查：文档是否有内容
            if not document.content or len(document.content.strip()) < 10:
                passed = False
                issue_desc = "文档内容为空或过短"
                suggestion = "请确保文档包含有效内容"

        elif rule_type == "chunk_quality":
            # 分块质量检查：chunks是否符合预期
            if len(chunks) == 0:
                passed = False
                issue_desc = "文档未生成任何分块"
                suggestion = "检查文档内容和分块逻辑"
            else:
                # 检查是否有质量分数过低的chunk
                low_quality_chunks = [
                    c for c in chunks
                    if c.quality_score is not None and c.quality_score < 0.3
                ]
                if low_quality_chunks:
                    passed = False
                    issue_desc = f"发现 {len(low_quality_chunks)} 个低质量分块"
                    suggestion = "检查分块算法或源文档质量"

        elif rule_type == "metadata":
            # 元数据完整性检查
            required_fields = ['total_words', 'language']
            missing = [f for f in required_fields if not getattr(document, f, None)]
            if missing:
                passed = False
                issue_desc = f"缺少必需元数据字段: {', '.join(missing)}"
                suggestion = "重新运行元数据提取"

        elif rule_type == "consistency":
            # 一致性检查：chunks总字数与文档字数对比
            if document.total_words and len(chunks) > 0:
                chunk_words = sum(len(c.content.split()) for c in chunks)
                doc_words = document.total_words
                if abs(chunk_words - doc_words) > doc_words * 0.2:
                    passed = False
                    issue_desc = f"分块总字数({chunk_words})与文档字数({doc_words})差异过大"
                    suggestion = "检查分块过程是否丢失内容"

        # 保存检查结果
        check_result = QualityCheckResult(
            id=generate_id(),
            rule_id=rule.id,
            target_type="document",
            target_id=file_id,
            check_result=passed,
            issue_description=issue_desc,
            suggestion=suggestion,
            checked_at=datetime.utcnow()
        )

        db.add(check_result)

        return check_result


# 便捷函数
def process_file_with_governance(
    file_path: str,
    filename: str,
    mime_type: str,
    project_id: int,
    collection_info: Optional[Dict[str, Any]] = None
) -> GovernanceResult:
    """处理文件（完整数据治理流程）"""
    orchestrator = DataGovernanceOrchestrator()
    return orchestrator.process_file(
        file_path, filename, mime_type, project_id, collection_info
    )
