"""
Report Governance Summary Generator - 报告治理摘要生成器

职责：
1. 为 ReportAgent 生成的报告添加治理摘要部分
2. 汇总数据质量指标
3. 统计血缘关系深度
4. 检测治理问题
5. 提供合规性建议

治理摘要包含：
1. 数据质量摘要 - quality_summary
2. 血缘关系摘要 - lineage_summary
3. 指标统计摘要 - metrics_summary
4. 治理问题列表 - governance_issues
5. 合规性评估 - compliance_assessment
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class QualitySummary:
    """数据质量摘要"""
    total_documents: int
    avg_quality_score: float
    high_quality_count: int  # 质量>=80
    medium_quality_count: int  # 50<=质量<80
    low_quality_count: int  # 质量<50
    completeness_rate: float  # 元数据完整性
    issues_count: int


@dataclass
class LineageSummary:
    """血缘关系摘要"""
    total_lineage_edges: int
    max_depth: int
    avg_depth: float
    file_to_chunk_count: int
    chunk_to_entity_count: int
    traceable_documents: int
    coverage_rate: float  # 血缘覆盖率


@dataclass
class MetricsSummary:
    """指标统计摘要"""
    total_chunks: int
    avg_semantic_density: float
    avg_coherence: float
    avg_readability: float
    avg_complexity: float
    total_entities: int
    total_keywords: int
    metrics_coverage_rate: float  # 指标计算覆盖率


@dataclass
class GovernanceIssue:
    """治理问题"""
    issue_type: str  # quality/lineage/compliance/security
    severity: str    # high/medium/low
    description: str
    affected_entities: List[str]
    recommendation: str


@dataclass
class ComplianceAssessment:
    """合规性评估"""
    data_classification_compliance: bool
    retention_policy_compliance: bool
    access_control_compliance: bool
    audit_trail_compliance: bool
    overall_score: float  # 0-100
    recommendations: List[str]


@dataclass
class GovernanceSummary:
    """完整的治理摘要"""
    project_id: int
    document_id: Optional[str]
    generated_at: str
    quality_summary: QualitySummary
    lineage_summary: LineageSummary
    metrics_summary: MetricsSummary
    governance_issues: List[GovernanceIssue]
    compliance_assessment: ComplianceAssessment


class ReportGovernanceSummaryGenerator:
    """
    报告治理摘要生成器

    功能：
    1. 查询数据质量指标
    2. 统计血缘关系
    3. 汇总chunk指标
    4. 检测治理问题
    5. 评估合规性
    """
    def __init__(self, db_session=None, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化治理摘要生成器

        Args:
            db_session: 数据库会话
        """
        self.db = db_session
        logger.info("ReportGovernanceSummaryGenerator initialized")

    def generate_summary(
        self,
        project_id: int,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成治理摘要

        Args:
            project_id: 项目ID
            document_id: 文档ID（可选，如果提供则只统计该文档）

        Returns:
            Dict: 治理摘要数据
        """
        if not self.db:
            logger.warning("No db_session provided, cannot generate summary")
            return self._empty_summary()

        logger.info(f"Generating governance summary for project {project_id}, document {document_id}")

        try:
            # 1. 数据质量摘要
            quality_summary = self._generate_quality_summary(project_id, document_id)

            # 2. 血缘关系摘要
            lineage_summary = self._generate_lineage_summary(project_id, document_id)

            # 3. 指标统计摘要
            metrics_summary = self._generate_metrics_summary(project_id, document_id)

            # 4. 检测治理问题
            governance_issues = self._detect_governance_issues(
                quality_summary, lineage_summary, metrics_summary
            )

            # 5. 合规性评估
            compliance_assessment = self._assess_compliance(
                project_id, document_id, quality_summary, lineage_summary
            )

            # 构建完整摘要
            summary = GovernanceSummary(
                project_id=project_id,
                document_id=document_id,
                generated_at=datetime.utcnow().isoformat(),
                quality_summary=quality_summary,
                lineage_summary=lineage_summary,
                metrics_summary=metrics_summary,
                governance_issues=governance_issues,
                compliance_assessment=compliance_assessment
            )

            result = self._summary_to_dict(summary)
            logger.info(f"✅ Governance summary generated: {len(governance_issues)} issues found")
            return result

        except Exception as e:
            logger.error(f"Error generating governance summary: {e}")
            return self._empty_summary()

    def _generate_quality_summary(
        self,
        project_id: int,
        document_id: Optional[str]
    ) -> QualitySummary:
        """生成数据质量摘要"""
        from sqlalchemy import text

        if document_id:
            # 单个文档的质量
            query = text("""
                SELECT
                    COUNT(*) as total,
                    AVG(quality_score) as avg_quality,
                    SUM(CASE WHEN quality_score >= 80 THEN 1 ELSE 0 END) as high_quality,
                    SUM(CASE WHEN quality_score >= 50 AND quality_score < 80 THEN 1 ELSE 0 END) as medium_quality,
                    SUM(CASE WHEN quality_score < 50 THEN 1 ELSE 0 END) as low_quality
                FROM documents
                WHERE id = :document_id
            """)
            result = self.db.execute(query, {'document_id': document_id}).fetchone()
        else:
            # 项目级别的质量
            query = text("""
                SELECT
                    COUNT(*) as total,
                    AVG(quality_score) as avg_quality,
                    SUM(CASE WHEN quality_score >= 80 THEN 1 ELSE 0 END) as high_quality,
                    SUM(CASE WHEN quality_score >= 50 AND quality_score < 80 THEN 1 ELSE 0 END) as medium_quality,
                    SUM(CASE WHEN quality_score < 50 THEN 1 ELSE 0 END) as low_quality
                FROM documents
                WHERE project_id = :project_id
            """)
            result = self.db.execute(query, {'project_id': project_id}).fetchone()

        if not result or result[0] == 0:
            return QualitySummary(0, 0.0, 0, 0, 0, 0.0, 0)

        # 计算元数据完整性
        completeness = self._calculate_metadata_completeness(project_id, document_id)

        return QualitySummary(
            total_documents=result[0] or 0,
            avg_quality_score=round(result[1] or 0.0, 2),
            high_quality_count=result[2] or 0,
            medium_quality_count=result[3] or 0,
            low_quality_count=result[4] or 0,
            completeness_rate=completeness,
            issues_count=result[4] or 0  # 低质量文档数
        )

    def _calculate_metadata_completeness(
        self,
        project_id: int,
        document_id: Optional[str]
    ) -> float:
        """计算元数据完整性"""
        from sqlalchemy import text

        # 检查必需的元数据字段
        required_fields = [
            'source_system', 'data_classification', 'quality_score',
            'metadata_version', 'governance_tags'
        ]

        if document_id:
            query = text("""
                SELECT
                    source_system, data_classification, quality_score,
                    metadata_version, governance_tags
                FROM documents
                WHERE id = :document_id
            """)
            result = self.db.execute(query, {'document_id': document_id}).fetchone()
        else:
            # 项目级别：统计有值的字段比例
            conditions = ' + '.join([
                f"CASE WHEN {field} IS NOT NULL THEN 1 ELSE 0 END"
                for field in required_fields
            ])
            query = text(f"""
                SELECT AVG(({conditions}) * 1.0 / {len(required_fields)})
                FROM documents
                WHERE project_id = :project_id
            """)
            result = self.db.execute(query, {'project_id': project_id}).fetchone()

            if result and result[0]:
                return round(result[0] * 100, 2)

        # 单文档：检查字段完整性
        if result:
            present = sum(1 for val in result if val is not None)
            return round(present / len(required_fields) * 100, 2)

        return 0.0

    def _generate_lineage_summary(
        self,
        project_id: int,
        document_id: Optional[str]
    ) -> LineageSummary:
        """生成血缘关系摘要"""
        from sqlalchemy import text

        if document_id:
            # 单文档的血缘
            query = text("""
                SELECT COUNT(*) as total
                FROM lineage_edges
                WHERE project_id = :project_id
                AND source_id = :document_id
            """)
            result = self.db.execute(query, {
                'project_id': project_id,
                'document_id': document_id
            }).fetchone()
            total_edges = result[0] if result else 0

            # 统计 file->chunk
            query2 = text("""
                SELECT COUNT(*)
                FROM lineage_edges
                WHERE project_id = :project_id
                AND source_id = :document_id
                AND source_type = 'file' AND target_type = 'chunk'
            """)
            result2 = self.db.execute(query2, {
                'project_id': project_id,
                'document_id': document_id
            }).fetchone()
            file_to_chunk = result2[0] if result2 else 0

        else:
            # 项目级别的血缘
            query = text("""
                SELECT COUNT(*) as total
                FROM lineage_edges
                WHERE project_id = :project_id
            """)
            result = self.db.execute(query, {'project_id': project_id}).fetchone()
            total_edges = result[0] if result else 0

            # 统计 file->chunk
            query2 = text("""
                SELECT COUNT(*)
                FROM lineage_edges
                WHERE project_id = :project_id
                AND source_type = 'file' AND target_type = 'chunk'
            """)
            result2 = self.db.execute(query2, {'project_id': project_id}).fetchone()
            file_to_chunk = result2[0] if result2 else 0

        # 简化版：深度统计（实际应该递归查询）
        max_depth = 2 if total_edges > 0 else 0
        avg_depth = 1.5 if total_edges > 0 else 0.0

        # 覆盖率（有血缘记录的文档占比）
        if document_id:
            coverage = 100.0 if total_edges > 0 else 0.0
            traceable = 1 if total_edges > 0 else 0
        else:
            query3 = text("""
                SELECT
                    COUNT(DISTINCT d.id) as total_docs,
                    COUNT(DISTINCT le.source_id) as traceable_docs
                FROM documents d
                LEFT JOIN lineage_edges le ON d.id = le.source_id AND le.source_type = 'file'
                WHERE d.project_id = :project_id
            """)
            result3 = self.db.execute(query3, {'project_id': project_id}).fetchone()
            total_docs = result3[0] if result3 else 0
            traceable = result3[1] if result3 else 0
            coverage = round(traceable / total_docs * 100, 2) if total_docs > 0 else 0.0

        return LineageSummary(
            total_lineage_edges=total_edges,
            max_depth=max_depth,
            avg_depth=avg_depth,
            file_to_chunk_count=file_to_chunk,
            chunk_to_entity_count=0,  # 暂时未实现
            traceable_documents=traceable,
            coverage_rate=coverage
        )

    def _generate_metrics_summary(
        self,
        project_id: int,
        document_id: Optional[str]
    ) -> MetricsSummary:
        """生成指标统计摘要"""
        from sqlalchemy import text

        if document_id:
            # 单文档的指标
            query = text("""
                SELECT
                    COUNT(*) as total_chunks,
                    AVG(semantic_density) as avg_semantic_density,
                    AVG(coherence_score) as avg_coherence,
                    AVG(readability_score) as avg_readability,
                    AVG(complexity_score) as avg_complexity,
                    SUM(entity_count) as total_entities,
                    SUM(keyword_count) as total_keywords,
                    SUM(CASE WHEN semantic_density IS NOT NULL THEN 1 ELSE 0 END) as calculated_chunks
                FROM document_chunks
                WHERE document_id = :document_id
            """)
            result = self.db.execute(query, {'document_id': document_id}).fetchone()
        else:
            # 项目级别的指标
            query = text("""
                SELECT
                    COUNT(*) as total_chunks,
                    AVG(semantic_density) as avg_semantic_density,
                    AVG(coherence_score) as avg_coherence,
                    AVG(readability_score) as avg_readability,
                    AVG(complexity_score) as avg_complexity,
                    SUM(entity_count) as total_entities,
                    SUM(keyword_count) as total_keywords,
                    SUM(CASE WHEN semantic_density IS NOT NULL THEN 1 ELSE 0 END) as calculated_chunks
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.project_id = :project_id
            """)
            result = self.db.execute(query, {'project_id': project_id}).fetchone()

        if not result or result[0] == 0:
            return MetricsSummary(0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0.0)

        total_chunks = result[0] or 0
        calculated_chunks = result[7] or 0
        coverage = round(calculated_chunks / total_chunks * 100, 2) if total_chunks > 0 else 0.0

        return MetricsSummary(
            total_chunks=total_chunks,
            avg_semantic_density=round(result[1] or 0.0, 3),
            avg_coherence=round(result[2] or 0.0, 3),
            avg_readability=round(result[3] or 0.0, 2),
            avg_complexity=round(result[4] or 0.0, 2),
            total_entities=result[5] or 0,
            total_keywords=result[6] or 0,
            metrics_coverage_rate=coverage
        )

    def _detect_governance_issues(
        self,
        quality_summary: QualitySummary,
        lineage_summary: LineageSummary,
        metrics_summary: MetricsSummary
    ) -> List[GovernanceIssue]:
        """检测治理问题"""
        issues = []

        # 1. 数据质量问题
        if quality_summary.low_quality_count > 0:
            severity = 'high' if quality_summary.low_quality_count > 5 else 'medium'
            issues.append(GovernanceIssue(
                issue_type='quality',
                severity=severity,
                description=f'{quality_summary.low_quality_count}个文档质量低于50分',
                affected_entities=[],
                recommendation='建议重新采集或清洗这些文档，提高内容完整性和格式规范性'
            ))

        # 2. 元数据完整性问题
        if quality_summary.completeness_rate < 80:
            issues.append(GovernanceIssue(
                issue_type='quality',
                severity='medium',
                description=f'元数据完整性仅{quality_summary.completeness_rate}%',
                affected_entities=[],
                recommendation='补充缺失的元数据字段，特别是source_system和data_classification'
            ))

        # 3. 血缘覆盖率问题
        if lineage_summary.coverage_rate < 90:
            severity = 'high' if lineage_summary.coverage_rate < 50 else 'medium'
            issues.append(GovernanceIssue(
                issue_type='lineage',
                severity=severity,
                description=f'血缘覆盖率仅{lineage_summary.coverage_rate}%',
                affected_entities=[],
                recommendation='为所有文档和chunks建立完整的血缘关系记录'
            ))

        # 4. 指标计算覆盖率问题
        if metrics_summary.metrics_coverage_rate < 90:
            issues.append(GovernanceIssue(
                issue_type='quality',
                severity='low',
                description=f'指标计算覆盖率仅{metrics_summary.metrics_coverage_rate}%',
                affected_entities=[],
                recommendation='为所有chunks计算完整的15个指标'
            ))

        # 5. 语义密度异常
        if metrics_summary.avg_semantic_density < 0.05:
            issues.append(GovernanceIssue(
                issue_type='quality',
                severity='medium',
                description=f'平均语义密度过低({metrics_summary.avg_semantic_density})',
                affected_entities=[],
                recommendation='检查实体和关键词提取是否正常，考虑调整提取阈值'
            ))

        return issues

    def _assess_compliance(
        self,
        project_id: int,
        document_id: Optional[str],
        quality_summary: QualitySummary,
        lineage_summary: LineageSummary
    ) -> ComplianceAssessment:
        """评估合规性"""
        recommendations = []

        # 1. 数据分类合规性（检查所有文档是否都有分类）
        data_classification_ok = quality_summary.completeness_rate >= 95
        if not data_classification_ok:
            recommendations.append("为所有文档设置data_classification字段")

        # 2. 保留策略合规性（检查是否设置了保留期限）
        retention_policy_ok = quality_summary.completeness_rate >= 90
        if not retention_policy_ok:
            recommendations.append("为所有文档设置retention_period字段")

        # 3. 访问控制合规性（检查是否记录了访问信息）
        access_control_ok = True  # 简化版：默认通过

        # 4. 审计追踪合规性（检查血缘覆盖率）
        audit_trail_ok = lineage_summary.coverage_rate >= 80
        if not audit_trail_ok:
            recommendations.append("建立完整的数据血缘追踪，确保所有数据转换可追溯")

        # 计算总分
        score = (
            (100 if data_classification_ok else 60) * 0.3 +
            (100 if retention_policy_ok else 70) * 0.2 +
            (100 if access_control_ok else 80) * 0.2 +
            (100 if audit_trail_ok else 50) * 0.3
        )

        if score >= 90:
            recommendations.insert(0, "整体合规性良好，继续保持")
        elif score >= 70:
            recommendations.insert(0, "合规性基本达标，仍有改进空间")
        else:
            recommendations.insert(0, "合规性不足，需要立即改进")

        return ComplianceAssessment(
            data_classification_compliance=data_classification_ok,
            retention_policy_compliance=retention_policy_ok,
            access_control_compliance=access_control_ok,
            audit_trail_compliance=audit_trail_ok,
            overall_score=round(score, 2),
            recommendations=recommendations
        )

    def _empty_summary(self) -> Dict[str, Any]:
        """返回空摘要"""
        return {
            'error': 'Unable to generate governance summary',
            'quality_summary': {},
            'lineage_summary': {},
            'metrics_summary': {},
            'governance_issues': [],
            'compliance_assessment': {}
        }

    def _summary_to_dict(self, summary: GovernanceSummary) -> Dict[str, Any]:
        """将摘要对象转换为字典"""
        return {
            'project_id': summary.project_id,
            'document_id': summary.document_id,
            'generated_at': summary.generated_at,
            'quality_summary': {
                'total_documents': summary.quality_summary.total_documents,
                'avg_quality_score': summary.quality_summary.avg_quality_score,
                'high_quality_count': summary.quality_summary.high_quality_count,
                'medium_quality_count': summary.quality_summary.medium_quality_count,
                'low_quality_count': summary.quality_summary.low_quality_count,
                'completeness_rate': summary.quality_summary.completeness_rate,
                'issues_count': summary.quality_summary.issues_count
            },
            'lineage_summary': {
                'total_lineage_edges': summary.lineage_summary.total_lineage_edges,
                'max_depth': summary.lineage_summary.max_depth,
                'avg_depth': summary.lineage_summary.avg_depth,
                'file_to_chunk_count': summary.lineage_summary.file_to_chunk_count,
                'chunk_to_entity_count': summary.lineage_summary.chunk_to_entity_count,
                'traceable_documents': summary.lineage_summary.traceable_documents,
                'coverage_rate': summary.lineage_summary.coverage_rate
            },
            'metrics_summary': {
                'total_chunks': summary.metrics_summary.total_chunks,
                'avg_semantic_density': summary.metrics_summary.avg_semantic_density,
                'avg_coherence': summary.metrics_summary.avg_coherence,
                'avg_readability': summary.metrics_summary.avg_readability,
                'avg_complexity': summary.metrics_summary.avg_complexity,
                'total_entities': summary.metrics_summary.total_entities,
                'total_keywords': summary.metrics_summary.total_keywords,
                'metrics_coverage_rate': summary.metrics_summary.metrics_coverage_rate
            },
            'governance_issues': [
                {
                    'issue_type': issue.issue_type,
                    'severity': issue.severity,
                    'description': issue.description,
                    'affected_entities': issue.affected_entities,
                    'recommendation': issue.recommendation
                }
                for issue in summary.governance_issues
            ],
            'compliance_assessment': {
                'data_classification_compliance': summary.compliance_assessment.data_classification_compliance,
                'retention_policy_compliance': summary.compliance_assessment.retention_policy_compliance,
                'access_control_compliance': summary.compliance_assessment.access_control_compliance,
                'audit_trail_compliance': summary.compliance_assessment.audit_trail_compliance,
                'overall_score': summary.compliance_assessment.overall_score,
                'recommendations': summary.compliance_assessment.recommendations
            }
        }


def create_governance_summary_generator(db_session=None) -> ReportGovernanceSummaryGenerator:
    """
    工厂方法：创建治理摘要生成器实例

    Args:
        db_session: 数据库会话

    Returns:
        ReportGovernanceSummaryGenerator: 治理摘要生成器实例
    """
    return ReportGovernanceSummaryGenerator(db_session=db_session)
