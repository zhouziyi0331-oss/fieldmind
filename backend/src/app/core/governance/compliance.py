"""
合规性检查系统

提供企业级的合规性检查和治理能力：
- 数据合规检查（GDPR、CCPA等）
- AI 使用合规检查
- 安全合规检查
- 操作合规检查
- 合规报告生成
- 合规审计追踪
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import re
import logging

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Boolean, Index
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()


class ComplianceType(str, Enum):
    """合规类型"""
    DATA_PRIVACY = "data_privacy"  # 数据隐私（GDPR、CCPA）
    AI_ETHICS = "ai_ethics"  # AI 伦理
    SECURITY = "security"  # 安全合规
    AUDIT = "audit"  # 审计合规
    OPERATIONAL = "operational"  # 操作合规


class ComplianceStatus(str, Enum):
    """合规状态"""
    COMPLIANT = "compliant"  # 合规
    NON_COMPLIANT = "non_compliant"  # 不合规
    PARTIAL = "partial"  # 部分合规
    UNKNOWN = "unknown"  # 未知


class ViolationSeverity(str, Enum):
    """违规严重程度"""
    CRITICAL = "critical"  # 严重
    HIGH = "high"  # 高
    MEDIUM = "medium"  # 中
    LOW = "low"  # 低
    INFO = "info"  # 信息


# ==================== 数据库模型 ====================

class ComplianceCheck(Base):
    """合规检查记录表"""
    __tablename__ = "compliance_checks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    check_id = Column(String(64), unique=True, nullable=False, index=True)

    compliance_type = Column(String(32), nullable=False, index=True)
    check_name = Column(String(128), nullable=False)
    check_description = Column(Text)

    status = Column(String(32), nullable=False)
    violations_count = Column(Integer, default=0)

    checked_at = Column(DateTime, default=datetime.utcnow, index=True)
    checked_by = Column(Integer)

    project_id = Column(Integer, index=True)
    resource_type = Column(String(64))
    resource_id = Column(String(128))

    details = Column(JSON)
    metadata = Column(JSON)

    __table_args__ = (
        Index("idx_compliance_project", "project_id", "compliance_type"),
    )


class ComplianceViolation(Base):
    """合规违规记录表"""
    __tablename__ = "compliance_violations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    violation_id = Column(String(64), unique=True, nullable=False, index=True)

    check_id = Column(String(64), nullable=False, index=True)
    compliance_type = Column(String(32), nullable=False)

    rule_name = Column(String(128), nullable=False)
    rule_description = Column(Text)

    severity = Column(String(32), nullable=False, index=True)
    violation_message = Column(Text, nullable=False)

    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime)
    is_resolved = Column(Boolean, default=False)

    project_id = Column(Integer, index=True)
    resource_type = Column(String(64))
    resource_id = Column(String(128))

    remediation_steps = Column(JSON)
    context = Column(JSON)

    __table_args__ = (
        Index("idx_violation_status", "is_resolved", "severity"),
    )


class CompliancePolicy(Base):
    """合规策略表"""
    __tablename__ = "compliance_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(String(64), unique=True, nullable=False, index=True)

    policy_name = Column(String(128), nullable=False)
    compliance_type = Column(String(32), nullable=False)

    rules = Column(JSON, nullable=False)
    enabled = Column(Boolean, default=True)

    scope = Column(String(32))  # global, project, user
    scope_id = Column(String(64))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    metadata = Column(JSON)


# ==================== 合规规则定义 ====================

@dataclass
class ComplianceRule:
    """合规规则"""
    name: str
    description: str
    check_func: Callable
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    remediation_steps: List[str] = field(default_factory=list)


# ==================== 数据隐私合规规则 ====================

class DataPrivacyRules:
    """数据隐私合规规则（GDPR、CCPA）"""

    @staticmethod
    def check_pii_detection(data: Dict[str, Any]) -> List[str]:
        """检查是否包含个人身份信息（PII）"""
        pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        }

        violations = []
        data_str = str(data)

        for pii_type, pattern in pii_patterns.items():
            if re.search(pattern, data_str):
                violations.append(f"检测到 {pii_type} 信息")

        return violations

    @staticmethod
    def check_consent_required(data: Dict[str, Any]) -> bool:
        """检查是否需要用户同意"""
        # 如果处理个人数据，需要用户同意
        return "user_consent" not in data or not data.get("user_consent")

    @staticmethod
    def check_data_retention(data: Dict[str, Any], max_days: int = 365) -> bool:
        """检查数据保留期限"""
        if "created_at" in data:
            created_at = datetime.fromisoformat(str(data["created_at"]))
            age = (datetime.utcnow() - created_at).days
            return age > max_days
        return False

    @staticmethod
    def check_data_encryption(data: Dict[str, Any]) -> bool:
        """检查敏感数据是否加密"""
        sensitive_fields = ["password", "ssn", "credit_card", "api_key", "token"]
        for field in sensitive_fields:
            if field in data and not str(data[field]).startswith("***"):
                return False
        return True


# ==================== AI 伦理合规规则 ====================

class AIEthicsRules:
    """AI 伦理合规规则"""

    @staticmethod
    def check_bias_detection(model_output: Dict[str, Any]) -> bool:
        """检查模型输出是否存在偏见"""
        # 简化版本，实际应该使用专门的偏见检测工具
        biased_keywords = [
            "discriminate", "bias", "unfair", "prejudice",
            "stereotype", "racist", "sexist"
        ]

        output_text = str(model_output).lower()
        return any(keyword in output_text for keyword in biased_keywords)

    @staticmethod
    def check_explainability(ai_result: Dict[str, Any]) -> bool:
        """检查 AI 结果是否可解释"""
        # AI 输出应包含解释信息
        return "explanation" in ai_result or "reasoning" in ai_result

    @staticmethod
    def check_human_oversight(operation: Dict[str, Any]) -> bool:
        """检查是否有人工监督"""
        critical_operations = ["delete", "transfer", "approve", "reject"]
        if operation.get("type") in critical_operations:
            return operation.get("human_reviewed", False)
        return True

    @staticmethod
    def check_transparency(ai_usage: Dict[str, Any]) -> bool:
        """检查 AI 使用透明度"""
        required_fields = ["model_name", "model_version", "timestamp"]
        return all(field in ai_usage for field in required_fields)


# ==================== 安全合规规则 ====================

class SecurityRules:
    """安全合规规则"""

    @staticmethod
    def check_authentication(request: Dict[str, Any]) -> bool:
        """检查是否已认证"""
        return "user_id" in request and request["user_id"] is not None

    @staticmethod
    def check_authorization(request: Dict[str, Any]) -> bool:
        """检查是否已授权"""
        return "permissions" in request and len(request.get("permissions", [])) > 0

    @staticmethod
    def check_input_validation(data: Dict[str, Any]) -> List[str]:
        """检查输入验证"""
        violations = []

        # 检查 SQL 注入
        sql_patterns = [r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE)\b)", r"(;|\-\-|\/\*)"]
        data_str = str(data)
        for pattern in sql_patterns:
            if re.search(pattern, data_str, re.IGNORECASE):
                violations.append("检测到潜在的 SQL 注入")
                break

        # 检查 XSS
        xss_patterns = [r"<script", r"javascript:", r"onerror=", r"onload="]
        for pattern in xss_patterns:
            if re.search(pattern, data_str, re.IGNORECASE):
                violations.append("检测到潜在的 XSS 攻击")
                break

        return violations

    @staticmethod
    def check_secure_communication(request: Dict[str, Any]) -> bool:
        """检查是否使用安全通信"""
        return request.get("protocol", "").lower() == "https"


# ==================== 合规检查服务 ====================

class ComplianceService:
    """合规检查服务"""

    def __init__(self, db: Session):
        self.db = db
        self._rules = self._initialize_rules()

    def _initialize_rules(self) -> Dict[ComplianceType, List[ComplianceRule]]:
        """初始化合规规则"""
        return {
            ComplianceType.DATA_PRIVACY: [
                ComplianceRule(
                    name="PII Detection",
                    description="检测个人身份信息",
                    check_func=DataPrivacyRules.check_pii_detection,
                    severity=ViolationSeverity.HIGH,
                    remediation_steps=[
                        "识别并标记 PII 数据",
                        "对 PII 数据进行加密",
                        "获取用户同意"
                    ]
                ),
                ComplianceRule(
                    name="Data Encryption",
                    description="检查敏感数据加密",
                    check_func=DataPrivacyRules.check_data_encryption,
                    severity=ViolationSeverity.CRITICAL,
                    remediation_steps=[
                        "对敏感字段进行加密",
                        "使用安全的加密算法"
                    ]
                )
            ],
            ComplianceType.AI_ETHICS: [
                ComplianceRule(
                    name="AI Explainability",
                    description="检查 AI 结果可解释性",
                    check_func=AIEthicsRules.check_explainability,
                    severity=ViolationSeverity.MEDIUM,
                    remediation_steps=[
                        "添加 AI 决策解释",
                        "提供推理过程说明"
                    ]
                ),
                ComplianceRule(
                    name="Human Oversight",
                    description="检查人工监督",
                    check_func=AIEthicsRules.check_human_oversight,
                    severity=ViolationSeverity.HIGH,
                    remediation_steps=[
                        "关键操作需要人工审核",
                        "建立人工监督流程"
                    ]
                )
            ],
            ComplianceType.SECURITY: [
                ComplianceRule(
                    name="Authentication Check",
                    description="检查用户认证",
                    check_func=SecurityRules.check_authentication,
                    severity=ViolationSeverity.CRITICAL,
                    remediation_steps=[
                        "要求用户登录",
                        "验证用户身份"
                    ]
                ),
                ComplianceRule(
                    name="Input Validation",
                    description="检查输入验证",
                    check_func=SecurityRules.check_input_validation,
                    severity=ViolationSeverity.HIGH,
                    remediation_steps=[
                        "实施输入验证",
                        "过滤危险字符"
                    ]
                )
            ]
        }

    def run_compliance_check(
        self,
        compliance_type: ComplianceType,
        data: Dict[str, Any],
        project_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        checked_by: Optional[int] = None
    ) -> ComplianceCheck:
        """
        执行合规检查

        Args:
            compliance_type: 合规类型
            data: 待检查的数据
            project_id: 项目ID
            resource_type: 资源类型
            resource_id: 资源ID
            checked_by: 检查人

        Returns:
            ComplianceCheck 记录
        """
        import uuid

        check_id = f"check_{uuid.uuid4().hex[:12]}"
        violations = []

        # 执行规则检查
        rules = self._rules.get(compliance_type, [])
        for rule in rules:
            try:
                result = rule.check_func(data)

                # 处理检查结果
                if isinstance(result, bool):
                    if not result:
                        violations.append(self._create_violation(
                            check_id=check_id,
                            rule=rule,
                            compliance_type=compliance_type,
                            project_id=project_id,
                            resource_type=resource_type,
                            resource_id=resource_id
                        ))
                elif isinstance(result, list) and len(result) > 0:
                    for violation_msg in result:
                        violations.append(self._create_violation(
                            check_id=check_id,
                            rule=rule,
                            compliance_type=compliance_type,
                            project_id=project_id,
                            resource_type=resource_type,
                            resource_id=resource_id,
                            message=violation_msg
                        ))

            except Exception as e:
                logger.error(f"规则检查失败: {rule.name} - {e}")

        # 确定合规状态
        if len(violations) == 0:
            status = ComplianceStatus.COMPLIANT
        elif len(violations) < len(rules) / 2:
            status = ComplianceStatus.PARTIAL
        else:
            status = ComplianceStatus.NON_COMPLIANT

        # 创建检查记录
        check = ComplianceCheck(
            check_id=check_id,
            compliance_type=compliance_type.value,
            check_name=f"{compliance_type.value}_check",
            check_description=f"合规检查: {compliance_type.value}",
            status=status.value,
            violations_count=len(violations),
            checked_by=checked_by,
            project_id=project_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details={
                "rules_checked": len(rules),
                "violations": [v.violation_id for v in violations]
            }
        )

        self.db.add(check)
        self.db.commit()
        self.db.refresh(check)

        logger.info(
            f"✅ 合规检查完成: {compliance_type.value} - "
            f"状态={status.value}, 违规={len(violations)}"
        )

        return check

    def _create_violation(
        self,
        check_id: str,
        rule: ComplianceRule,
        compliance_type: ComplianceType,
        project_id: Optional[int],
        resource_type: Optional[str],
        resource_id: Optional[str],
        message: Optional[str] = None
    ) -> ComplianceViolation:
        """创建违规记录"""
        import uuid

        violation = ComplianceViolation(
            violation_id=f"viol_{uuid.uuid4().hex[:12]}",
            check_id=check_id,
            compliance_type=compliance_type.value,
            rule_name=rule.name,
            rule_description=rule.description,
            severity=rule.severity.value,
            violation_message=message or f"违反规则: {rule.name}",
            project_id=project_id,
            resource_type=resource_type,
            resource_id=resource_id,
            remediation_steps=rule.remediation_steps
        )

        self.db.add(violation)
        return violation

    def get_compliance_report(
        self,
        project_id: Optional[int] = None,
        compliance_type: Optional[ComplianceType] = None,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """
        生成合规报告

        Returns:
            {
                "summary": {...},
                "checks": [...],
                "violations": [...],
                "trends": {...}
            }
        """
        cutoff_time = datetime.utcnow() - timedelta(days=time_range_days)

        # 查询检查记录
        checks_query = self.db.query(ComplianceCheck).filter(
            ComplianceCheck.checked_at >= cutoff_time
        )
        if project_id:
            checks_query = checks_query.filter(ComplianceCheck.project_id == project_id)
        if compliance_type:
            checks_query = checks_query.filter(
                ComplianceCheck.compliance_type == compliance_type.value
            )

        checks = checks_query.all()

        # 查询违规记录
        violations_query = self.db.query(ComplianceViolation).filter(
            ComplianceViolation.detected_at >= cutoff_time
        )
        if project_id:
            violations_query = violations_query.filter(
                ComplianceViolation.project_id == project_id
            )

        violations = violations_query.all()

        # 统计汇总
        total_checks = len(checks)
        compliant_checks = sum(1 for c in checks if c.status == ComplianceStatus.COMPLIANT.value)
        total_violations = len(violations)
        resolved_violations = sum(1 for v in violations if v.is_resolved)

        # 按严重程度分组
        severity_counts = {}
        for v in violations:
            severity_counts[v.severity] = severity_counts.get(v.severity, 0) + 1

        return {
            "summary": {
                "total_checks": total_checks,
                "compliant_checks": compliant_checks,
                "compliance_rate": compliant_checks / total_checks if total_checks > 0 else 0,
                "total_violations": total_violations,
                "resolved_violations": resolved_violations,
                "resolution_rate": resolved_violations / total_violations if total_violations > 0 else 0,
                "severity_distribution": severity_counts
            },
            "checks": [
                {
                    "check_id": c.check_id,
                    "type": c.compliance_type,
                    "status": c.status,
                    "violations_count": c.violations_count,
                    "checked_at": c.checked_at.isoformat()
                }
                for c in checks
            ],
            "violations": [
                {
                    "violation_id": v.violation_id,
                    "rule_name": v.rule_name,
                    "severity": v.severity,
                    "message": v.violation_message,
                    "is_resolved": v.is_resolved,
                    "detected_at": v.detected_at.isoformat()
                }
                for v in violations
            ],
            "time_range_days": time_range_days
        }

    def resolve_violation(
        self,
        violation_id: str,
        resolved_by: Optional[int] = None
    ) -> bool:
        """标记违规为已解决"""
        violation = self.db.query(ComplianceViolation).filter(
            ComplianceViolation.violation_id == violation_id
        ).first()

        if not violation:
            return False

        violation.is_resolved = True
        violation.resolved_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"✅ 违规已解决: {violation_id}")
        return True
