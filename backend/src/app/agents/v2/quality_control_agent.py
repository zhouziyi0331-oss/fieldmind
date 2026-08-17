"""
Quality Control Agent - 质量控制智能体
自动验证处理结果的质量，检测并修复常见问题
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import re
import json
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class QualityLevel(str, Enum):
    """质量等级"""
    EXCELLENT = "excellent"  # 优秀 (≥95分)
    GOOD = "good"  # 良好 (80-94分)
    ACCEPTABLE = "acceptable"  # 可接受 (60-79分)
    POOR = "poor"  # 差 (40-59分)
    FAILED = "failed"  # 失败 (<40分)


class IssueType(str, Enum):
    """问题类型"""
    # 文档转换问题
    EMPTY_CONTENT = "empty_content"  # 空内容
    ENCODING_ERROR = "encoding_error"  # 编码错误
    FORMAT_BROKEN = "format_broken"  # 格式损坏
    MISSING_METADATA = "missing_metadata"  # 缺失元数据

    # OCR问题
    LOW_CONFIDENCE = "low_confidence"  # 低置信度
    GARBLED_TEXT = "garbled_text"  # 乱码文本
    LAYOUT_BROKEN = "layout_broken"  # 布局错误

    # 实体识别问题
    NO_ENTITIES = "no_entities"  # 无实体
    DUPLICATE_ENTITIES = "duplicate_entities"  # 重复实体
    INVALID_ENTITY_TYPE = "invalid_entity_type"  # 无效实体类型

    # 向量化问题
    EMPTY_EMBEDDING = "empty_embedding"  # 空向量
    DIMENSION_MISMATCH = "dimension_mismatch"  # 维度不匹配
    LOW_DIVERSITY = "low_diversity"  # 低多样性

    # 知识图谱问题
    ISOLATED_NODE = "isolated_node"  # 孤立节点
    MISSING_RELATIONSHIP = "missing_relationship"  # 缺失关系
    INVALID_TRIPLE = "invalid_triple"  # 无效三元组

    # 全文检索问题
    INDEX_FAILED = "index_failed"  # 索引失败
    EMPTY_INDEX = "empty_index"  # 空索引

    # 通用问题
    PROCESSING_TIMEOUT = "processing_timeout"  # 处理超时
    RESOURCE_ERROR = "resource_error"  # 资源错误


class QualityIssue:
    """质量问题"""

    def __init__(
        self,
        issue_type: IssueType,
        severity: str,  # critical, high, medium, low
        description: str,
        location: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
        auto_fixable: bool = False
    ):
        self.issue_type = issue_type
        self.severity = severity
        self.description = description
        self.location = location
        self.details = details or {}
        self.suggestion = suggestion
        self.auto_fixable = auto_fixable
        self.detected_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "issue_type": self.issue_type.value,
            "severity": self.severity,
            "description": self.description,
            "location": self.location,
            "details": self.details,
            "suggestion": self.suggestion,
            "auto_fixable": self.auto_fixable,
            "detected_at": self.detected_at.isoformat()
        }


class QualityReport:
    """质量报告"""

    def __init__(self, task_id: str, task_type: str):
        self.task_id = task_id
        self.task_type = task_type
        self.overall_score: float = 0.0  # 总分 (0-100)
        self.quality_level: QualityLevel = QualityLevel.FAILED
        self.issues: List[QualityIssue] = []
        self.metrics: Dict[str, Any] = {}
        self.auto_fixed: List[str] = []  # 自动修复的问题
        self.manual_review_required: bool = False
        self.passed: bool = False
        self.created_at = datetime.utcnow()

    def add_issue(self, issue: QualityIssue):
        """添加问题"""
        self.issues.append(issue)
        # 严重问题需要人工审核
        if issue.severity in ["critical", "high"]:
            self.manual_review_required = True

    def calculate_score(self):
        """计算总分"""
        if not self.issues:
            self.overall_score = 100.0
            self.quality_level = QualityLevel.EXCELLENT
            self.passed = True
            return

        # 扣分规则
        deduction = 0
        has_critical = False
        has_high = False

        for issue in self.issues:
            if issue.severity == "critical":
                deduction += 30
                has_critical = True
            elif issue.severity == "high":
                deduction += 15
                has_high = True
            elif issue.severity == "medium":
                deduction += 5
            elif issue.severity == "low":
                deduction += 2

        self.overall_score = max(0, 100 - deduction)

        # 确定质量等级
        if self.overall_score >= 95:
            self.quality_level = QualityLevel.EXCELLENT
        elif self.overall_score >= 80:
            self.quality_level = QualityLevel.GOOD
        elif self.overall_score >= 60:
            self.quality_level = QualityLevel.ACCEPTABLE
        elif self.overall_score >= 40:
            self.quality_level = QualityLevel.POOR
        else:
            self.quality_level = QualityLevel.FAILED

        # 判定是否通过：
        # 1. 有严重问题(critical)直接失败
        # 2. 有高危问题(high)且分数不高于80分失败
        # 3. 否则60分以上通过
        if has_critical:
            self.passed = False
        elif has_high and self.overall_score <= 80:
            self.passed = False
        else:
            self.passed = self.overall_score >= 60

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "overall_score": round(self.overall_score, 2),
            "quality_level": self.quality_level.value,
            "passed": self.passed,
            "issues": [issue.to_dict() for issue in self.issues],
            "issues_count": {
                "critical": len([i for i in self.issues if i.severity == "critical"]),
                "high": len([i for i in self.issues if i.severity == "high"]),
                "medium": len([i for i in self.issues if i.severity == "medium"]),
                "low": len([i for i in self.issues if i.severity == "low"])
            },
            "metrics": self.metrics,
            "auto_fixed": self.auto_fixed,
            "manual_review_required": self.manual_review_required,
            "created_at": self.created_at.isoformat()
        }


class QualityControlAgent:
    """质量控制智能体"""

    def __init__(self):
        self.validation_rules = self._load_validation_rules()
        self.auto_fix_enabled = True
        self.statistics = {
            "total_checks": 0,
            "passed": 0,
            "failed": 0,
            "auto_fixed": 0
        }

    def _load_validation_rules(self) -> Dict[str, Any]:
        """加载验证规则"""
        return {
            # 文档转换规则
            "document": {
                "min_content_length": 10,  # 最小内容长度
                "required_metadata": ["title", "created_at"],
                "max_file_size_mb": 100
            },
            # OCR规则
            "ocr": {
                "min_confidence": 0.7,  # 最小置信度
                "max_garbled_ratio": 0.1,  # 最大乱码比例
                "min_blocks": 1
            },
            # 实体识别规则
            "entity": {
                "min_entities": 1,  # 至少识别1个实体
                "valid_types": ["PERSON", "LOCATION", "ORGANIZATION", "DATE", "TIME"],
                "max_duplicate_ratio": 0.3
            },
            # 向量化规则
            "embedding": {
                "expected_dimension": 768,  # 期望维度
                "min_diversity": 0.1,  # 最小多样性
                "max_zero_ratio": 0.5  # 最大零值比例
            },
            # 知识图谱规则
            "graph": {
                "min_nodes": 1,
                "min_relationships": 0,
                "max_isolated_ratio": 0.5
            }
        }

    # ==================== 文档转换质量检查 ====================

    def validate_document(self, document_data: Dict[str, Any]) -> QualityReport:
        """验证文档转换质量"""
        report = QualityReport(
            task_id=document_data.get("id", "unknown"),
            task_type="document_conversion"
        )

        # 1. 检查内容是否为空
        content = document_data.get("content", "")
        if not content or len(content.strip()) < self.validation_rules["document"]["min_content_length"]:
            report.add_issue(QualityIssue(
                issue_type=IssueType.EMPTY_CONTENT,
                severity="critical",
                description="文档内容为空或过短",
                details={"content_length": len(content)},
                suggestion="检查文档是否正确转换，可能需要重新处理",
                auto_fixable=False
            ))

        # 2. 检查编码
        try:
            # 尝试编码为UTF-8
            content.encode('utf-8')
        except UnicodeEncodeError as e:
            report.add_issue(QualityIssue(
                issue_type=IssueType.ENCODING_ERROR,
                severity="high",
                description="文档包含编码错误",
                details={"error": str(e)},
                suggestion="使用正确的编码重新读取文档",
                auto_fixable=True
            ))

            # 自动修复：移除无法编码的字符
            if self.auto_fix_enabled:
                fixed_content = content.encode('utf-8', errors='ignore').decode('utf-8')
                document_data["content"] = fixed_content
                report.auto_fixed.append("encoding_error")

        # 3. 检查元数据
        metadata = document_data.get("metadata", {})
        missing_fields = []
        for field in self.validation_rules["document"]["required_metadata"]:
            if field not in metadata or not metadata[field]:
                missing_fields.append(field)

        if missing_fields:
            report.add_issue(QualityIssue(
                issue_type=IssueType.MISSING_METADATA,
                severity="medium",
                description="缺少必需的元数据字段",
                details={"missing_fields": missing_fields},
                suggestion=f"添加缺失的字段: {', '.join(missing_fields)}",
                auto_fixable=True
            ))

            # 自动修复：添加默认元数据
            if self.auto_fix_enabled:
                if "metadata" not in document_data:
                    document_data["metadata"] = {}
                for field in missing_fields:
                    if field == "title":
                        document_data["metadata"]["title"] = "Untitled"
                    elif field == "created_at":
                        document_data["metadata"]["created_at"] = datetime.utcnow().isoformat()
                report.auto_fixed.append("missing_metadata")

        # 4. 检查格式
        if document_data.get("format") == "markdown":
            # 检查markdown基本语法
            if not re.search(r'[#*\-\[\]]', content):
                report.add_issue(QualityIssue(
                    issue_type=IssueType.FORMAT_BROKEN,
                    severity="low",
                    description="Markdown格式可能损坏，未发现常见语法标记",
                    suggestion="检查转换过程是否正确保留了格式",
                    auto_fixable=False
                ))

        # 计算指标
        report.metrics = {
            "content_length": len(content),
            "word_count": len(content.split()),
            "metadata_completeness": 1 - len(missing_fields) / len(self.validation_rules["document"]["required_metadata"])
        }

        report.calculate_score()
        self._update_statistics(report)

        return report

    # ==================== OCR质量检查 ====================

    def validate_ocr_result(self, ocr_result: Dict[str, Any]) -> QualityReport:
        """验证OCR识别质量"""
        report = QualityReport(
            task_id=ocr_result.get("task_id", "unknown"),
            task_type="ocr_recognition"
        )

        text = ocr_result.get("text", "")
        confidence = ocr_result.get("confidence", 0.0)
        text_blocks = ocr_result.get("text_blocks", [])

        # 1. 检查置信度
        if confidence < self.validation_rules["ocr"]["min_confidence"]:
            report.add_issue(QualityIssue(
                issue_type=IssueType.LOW_CONFIDENCE,
                severity="high" if confidence <= 0.5 else "medium",
                description=f"OCR置信度过低: {confidence:.2%}",
                details={"confidence": confidence},
                suggestion="考虑提高图像质量或使用其他OCR引擎",
                auto_fixable=False
            ))

        # 2. 检查乱码
        garbled_pattern = re.compile(r'[^\w\s一-鿿　-〿＀-￯.,!?;:\'"()\-]')
        garbled_chars = len(garbled_pattern.findall(text))
        garbled_ratio = garbled_chars / len(text) if text else 0

        if garbled_ratio > self.validation_rules["ocr"]["max_garbled_ratio"]:
            report.add_issue(QualityIssue(
                issue_type=IssueType.GARBLED_TEXT,
                severity="high",
                description=f"文本包含过多乱码字符: {garbled_ratio:.2%}",
                details={"garbled_ratio": garbled_ratio},
                suggestion="检查图像质量，或使用正确的语言模型",
                auto_fixable=True
            ))

            # 自动修复：移除乱码
            if self.auto_fix_enabled:
                cleaned_text = garbled_pattern.sub('', text)
                ocr_result["text"] = cleaned_text
                report.auto_fixed.append("garbled_text")

        # 3. 检查文本块数量
        if len(text_blocks) < self.validation_rules["ocr"]["min_blocks"]:
            report.add_issue(QualityIssue(
                issue_type=IssueType.LAYOUT_BROKEN,
                severity="medium",
                description="未检测到文本块，可能是布局识别失败",
                details={"blocks_count": len(text_blocks)},
                suggestion="检查图像是否包含可识别的文本",
                auto_fixable=False
            ))

        # 4. 检查空内容
        if not text or len(text.strip()) < 5:
            report.add_issue(QualityIssue(
                issue_type=IssueType.EMPTY_CONTENT,
                severity="critical",
                description="OCR未识别到有效文本",
                suggestion="检查图像是否清晰，是否使用了正确的语言模型",
                auto_fixable=False
            ))

        # 计算指标
        report.metrics = {
            "confidence": confidence,
            "text_length": len(text),
            "blocks_count": len(text_blocks),
            "garbled_ratio": garbled_ratio,
            "avg_block_confidence": sum(b.get("confidence", 0) for b in text_blocks) / len(text_blocks) if text_blocks else 0
        }

        report.calculate_score()
        self._update_statistics(report)

        return report

    # ==================== 实体识别质量检查 ====================

    def validate_entities(self, entity_data: Dict[str, Any]) -> QualityReport:
        """验证实体识别质量"""
        report = QualityReport(
            task_id=entity_data.get("document_id", "unknown"),
            task_type="entity_recognition"
        )

        entities = entity_data.get("entities", [])

        # 1. 检查是否识别到实体
        if len(entities) < self.validation_rules["entity"]["min_entities"]:
            report.add_issue(QualityIssue(
                issue_type=IssueType.NO_ENTITIES,
                severity="medium",
                description="未识别到任何实体",
                details={"entities_count": len(entities)},
                suggestion="检查文本内容是否包含命名实体，或调整识别参数",
                auto_fixable=False
            ))

        # 2. 检查实体类型
        valid_types = set(self.validation_rules["entity"]["valid_types"])
        invalid_entities = []
        for entity in entities:
            entity_type = entity.get("type", "")
            if entity_type not in valid_types:
                invalid_entities.append(entity)

        if invalid_entities:
            report.add_issue(QualityIssue(
                issue_type=IssueType.INVALID_ENTITY_TYPE,
                severity="low",
                description=f"发现{len(invalid_entities)}个无效的实体类型",
                details={"invalid_types": list(set(e.get("type") for e in invalid_entities))},
                suggestion="检查实体类型映射是否正确",
                auto_fixable=True
            ))

            # 自动修复：移除无效实体
            if self.auto_fix_enabled:
                entity_data["entities"] = [e for e in entities if e.get("type") in valid_types]
                report.auto_fixed.append("invalid_entity_type")

        # 3. 检查重复实体
        entity_texts = [e.get("text", "") for e in entities]
        unique_entities = set(entity_texts)
        duplicate_ratio = 1 - len(unique_entities) / len(entity_texts) if entity_texts else 0

        if duplicate_ratio > self.validation_rules["entity"]["max_duplicate_ratio"]:
            report.add_issue(QualityIssue(
                issue_type=IssueType.DUPLICATE_ENTITIES,
                severity="low",
                description=f"重复实体比例过高: {duplicate_ratio:.2%}",
                details={"duplicate_ratio": duplicate_ratio},
                suggestion="考虑去重或合并相同实体",
                auto_fixable=True
            ))

            # 自动修复：去重
            if self.auto_fix_enabled:
                seen = set()
                deduped = []
                for entity in entities:
                    key = (entity.get("text"), entity.get("type"))
                    if key not in seen:
                        seen.add(key)
                        deduped.append(entity)
                entity_data["entities"] = deduped
                report.auto_fixed.append("duplicate_entities")

        # 计算指标
        report.metrics = {
            "entities_count": len(entities),
            "unique_entities": len(unique_entities),
            "duplicate_ratio": duplicate_ratio,
            "type_distribution": {t: len([e for e in entities if e.get("type") == t]) for t in valid_types}
        }

        report.calculate_score()
        self._update_statistics(report)

        return report

    # ==================== 向量化质量检查 ====================

    def validate_embedding(self, embedding_data: Dict[str, Any]) -> QualityReport:
        """验证向量化质量"""
        report = QualityReport(
            task_id=embedding_data.get("document_id", "unknown"),
            task_type="vectorization"
        )

        embedding = embedding_data.get("embedding", [])

        # 1. 检查是否为空
        if not embedding:
            report.add_issue(QualityIssue(
                issue_type=IssueType.EMPTY_EMBEDDING,
                severity="critical",
                description="向量为空",
                suggestion="检查向量化模型是否正常加载",
                auto_fixable=False
            ))
            report.calculate_score()
            self._update_statistics(report)
            return report

        # 2. 检查维度
        expected_dim = self.validation_rules["embedding"]["expected_dimension"]
        if len(embedding) != expected_dim:
            report.add_issue(QualityIssue(
                issue_type=IssueType.DIMENSION_MISMATCH,
                severity="critical",
                description=f"向量维度不匹配: 期望{expected_dim}, 实际{len(embedding)}",
                details={"expected": expected_dim, "actual": len(embedding)},
                suggestion="检查使用的向量模型是否正确",
                auto_fixable=False
            ))

        # 3. 检查多样性
        embedding_array = np.array(embedding)
        std_dev = np.std(embedding_array)

        if std_dev < self.validation_rules["embedding"]["min_diversity"]:
            report.add_issue(QualityIssue(
                issue_type=IssueType.LOW_DIVERSITY,
                severity="medium",
                description=f"向量多样性过低 (std={std_dev:.4f})",
                details={"std_dev": float(std_dev)},
                suggestion="检查输入文本是否有效，或模型是否正常",
                auto_fixable=False
            ))

        # 4. 检查零值比例
        zero_count = np.sum(embedding_array == 0)
        zero_ratio = zero_count / len(embedding_array)

        if zero_ratio > self.validation_rules["embedding"]["max_zero_ratio"]:
            report.add_issue(QualityIssue(
                issue_type=IssueType.LOW_DIVERSITY,
                severity="medium",
                description=f"向量包含过多零值: {zero_ratio:.2%}",
                details={"zero_ratio": zero_ratio},
                suggestion="检查向量化过程是否正常",
                auto_fixable=False
            ))

        # 计算指标
        report.metrics = {
            "dimension": len(embedding),
            "mean": float(np.mean(embedding_array)),
            "std": float(std_dev),
            "min": float(np.min(embedding_array)),
            "max": float(np.max(embedding_array)),
            "zero_ratio": zero_ratio
        }

        report.calculate_score()
        self._update_statistics(report)

        return report

    # ==================== 知识图谱质量检查 ====================

    def validate_knowledge_graph(self, graph_data: Dict[str, Any]) -> QualityReport:
        """验证知识图谱质量"""
        report = QualityReport(
            task_id=graph_data.get("document_id", "unknown"),
            task_type="knowledge_graph"
        )

        nodes = graph_data.get("nodes", [])
        relationships = graph_data.get("relationships", [])

        # 1. 检查节点数量
        if len(nodes) < self.validation_rules["graph"]["min_nodes"]:
            report.add_issue(QualityIssue(
                issue_type=IssueType.ISOLATED_NODE,
                severity="medium",
                description="图谱节点数量过少",
                details={"nodes_count": len(nodes)},
                suggestion="检查实体识别和关系抽取是否正常",
                auto_fixable=False
            ))

        # 2. 检查孤立节点
        connected_nodes = set()
        for rel in relationships:
            connected_nodes.add(rel.get("source"))
            connected_nodes.add(rel.get("target"))

        isolated_nodes = [n for n in nodes if n.get("id") not in connected_nodes]
        isolated_ratio = len(isolated_nodes) / len(nodes) if nodes else 0

        if isolated_ratio > self.validation_rules["graph"]["max_isolated_ratio"]:
            report.add_issue(QualityIssue(
                issue_type=IssueType.ISOLATED_NODE,
                severity="medium",
                description=f"孤立节点比例过高: {isolated_ratio:.2%}",
                details={"isolated_count": len(isolated_nodes), "total_nodes": len(nodes)},
                suggestion="检查关系抽取逻辑，可能需要增加关系类型",
                auto_fixable=False
            ))

        # 3. 检查无效三元组
        invalid_triples = []
        for rel in relationships:
            if not rel.get("source") or not rel.get("target") or not rel.get("type"):
                invalid_triples.append(rel)

        if invalid_triples:
            report.add_issue(QualityIssue(
                issue_type=IssueType.INVALID_TRIPLE,
                severity="high",
                description=f"发现{len(invalid_triples)}个无效三元组",
                details={"invalid_count": len(invalid_triples)},
                suggestion="检查关系抽取结果，确保所有字段完整",
                auto_fixable=True
            ))

            # 自动修复：移除无效三元组
            if self.auto_fix_enabled:
                graph_data["relationships"] = [
                    r for r in relationships
                    if r.get("source") and r.get("target") and r.get("type")
                ]
                report.auto_fixed.append("invalid_triple")

        # 计算指标
        report.metrics = {
            "nodes_count": len(nodes),
            "relationships_count": len(relationships),
            "isolated_nodes": len(isolated_nodes),
            "isolated_ratio": isolated_ratio,
            "avg_degree": len(relationships) * 2 / len(nodes) if nodes else 0
        }

        report.calculate_score()
        self._update_statistics(report)

        return report

    # ==================== 统计和工具方法 ====================

    def _update_statistics(self, report: QualityReport):
        """更新统计信息"""
        self.statistics["total_checks"] += 1
        if report.passed:
            self.statistics["passed"] += 1
        else:
            self.statistics["failed"] += 1
        if report.auto_fixed:
            self.statistics["auto_fixed"] += 1

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = self.statistics["total_checks"]
        return {
            "total_checks": total,
            "passed": self.statistics["passed"],
            "failed": self.statistics["failed"],
            "pass_rate": self.statistics["passed"] / total if total > 0 else 0,
            "auto_fixed": self.statistics["auto_fixed"],
            "auto_fix_rate": self.statistics["auto_fixed"] / total if total > 0 else 0
        }

    def reset_statistics(self):
        """重置统计"""
        self.statistics = {
            "total_checks": 0,
            "passed": 0,
            "failed": 0,
            "auto_fixed": 0
        }


# 全局单例
_quality_control_agent: Optional[QualityControlAgent] = None


def get_quality_control_agent() -> QualityControlAgent:
    """获取质量控制Agent单例"""
    global _quality_control_agent
    if _quality_control_agent is None:
        _quality_control_agent = QualityControlAgent()
    return _quality_control_agent
