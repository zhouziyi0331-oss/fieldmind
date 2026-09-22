"""
蒸馏系统数据类型定义
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============== 输入类型 ==============

class InputMode(str, Enum):
    """输入模式"""
    FILE = "file"
    URL = "url"
    AUDIO = "audio"


class SourceKind(str, Enum):
    """来源类型"""
    BOOK = "book"
    BLOG = "blog"
    VIDEO = "video"
    PODCAST = "podcast"
    COURSE = "course"
    DOCUMENT = "document"
    FIELDWORK_NOTE = "fieldwork_note"


class SourceMode(str, Enum):
    """来源模式"""
    EMBEDDED = "embedded"
    EXTERNAL_MEDIA_BOUND = "external-media-bound"


@dataclass
class SourceMetadata:
    """来源元信息"""
    input_mode: InputMode
    source_kind: SourceKind
    source_mode: SourceMode

    # 基础元数据
    title: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    publish_date: Optional[str] = None
    language: str = "zh-CN"

    # URL 模式专用
    original_url: Optional[str] = None
    platform: Optional[str] = None

    # 文件模式专用
    file_path: Optional[str] = None
    file_format: Optional[str] = None
    file_sha256: Optional[str] = None

    # OCR/转写信息
    ocr_performed: bool = False
    ocr_tool: Optional[str] = None
    transcription_performed: bool = False
    transcription_model: Optional[str] = None


# ============== 规范化层 ==============

@dataclass
class NormalizedChapter:
    """规范化章节"""
    chapter_id: str
    label: str
    order: int
    content: str
    sha256: str

    # 证据锚点支持
    byte_offset_start: int
    byte_offset_end: int

    # 时间锚点（视频/音频）
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None

    # 原始定位
    source_page: Optional[int] = None
    source_line: Optional[int] = None


@dataclass
class NormalizedSource:
    """规范化源文档"""
    generation_id: str
    source_metadata: SourceMetadata

    chapters: List[NormalizedChapter]
    full_text: str
    full_text_sha256: str

    # 质量标记
    has_missing_pages: bool = False
    has_encoding_errors: bool = False
    has_ocr_uncertainty: bool = False

    normalized_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    normalizer_version: str = "fieldmind-normalizer-1.0.0"


# ============== 知识轨 ==============

class KnowledgeType(str, Enum):
    """知识类型"""
    CONCEPT = "concept"
    CLAIM = "claim"
    PRINCIPLE = "principle"
    MECHANISM = "mechanism"
    REPORTED_FACT = "reportedFact"
    ARGUMENT = "argument"
    BOUNDARY = "boundary"
    COUNTER_EXAMPLE = "counterexample"


class SourceCertainty(str, Enum):
    """来源确定性"""
    EXPLICIT = "explicit"
    IMPLIED = "implied"
    DERIVED = "derived"


class ClaimAttribution(str, Enum):
    """主张归属"""
    AUTHOR_CLAIM = "author-claim"
    REPORTED_BY_AUTHOR = "reported-by-author"
    DISTILLER_INFERENCE = "distiller-inference"


@dataclass
class EvidenceAnchor:
    """证据锚点"""
    chapter_id: str
    quote: str
    byte_start: int
    byte_end: int

    page: Optional[int] = None
    timestamp: Optional[float] = None

    def verify_quote(self, full_text: str) -> bool:
        """验证 quote 是否与 byte 区间完全相等"""
        try:
            actual = full_text.encode('utf-8')[self.byte_start:self.byte_end].decode('utf-8')
            return actual == self.quote
        except Exception:
            return False


@dataclass
class KnowledgeUnit:
    """知识单元"""
    id: str
    type: KnowledgeType

    # 核心内容
    title: str
    statement: str
    explanation: str
    why_it_matters: str

    # 边界
    scope: str
    conditions: List[str]
    boundaries: List[str]
    counterexamples: List[str]

    # 证据
    evidence_anchors: List[EvidenceAnchor]
    evidence_route: str

    # 元数据
    source_certainty: SourceCertainty
    claim_attribution: ClaimAttribution
    extraction_certainty: float
    external_verification_status: str = "not-verified"

    # 生产者
    producer_id: str = "producer:knowledge-distiller"
    generation_id: str = ""

    tags: List[str] = field(default_factory=list)


# ============== 方法轨 ==============

class ExtractorType(str, Enum):
    """提取器类型"""
    FRAMEWORK = "framework"
    PRINCIPLE = "principle"
    CASE = "case"
    COUNTER_EXAMPLE = "counter-example"
    GLOSSARY = "glossary"


@dataclass
class MethodCandidate:
    """方法候选单元"""
    id: str
    title: str
    type: ExtractorType
    source_chapter: str
    source_quote: str
    summary: str
    tags: List[str]

    extracted_by: str
    extraction_context: str = ""


@dataclass
class VerificationResult:
    """验证结果"""
    candidate_id: str

    # V1: 跨域验证
    v1_cross_domain_passed: bool
    v1_evidence: List[Dict[str, str]]
    v1_route: str

    # V2: 预测力测试
    v2_predictive_power_passed: bool
    v2_novel_question: str
    v2_derived_answer: str

    # V3: 独特性检验
    v3_exclusivity_passed: bool
    v3_why_not_common: str

    overall_passed: bool


@dataclass
class MethodUnit:
    """方法单元（RIA++ 六段）"""
    id: str
    name: str
    display_name: str

    # R - Reading
    reading_quote: str
    reading_source: str

    # I - Interpretation
    interpretation: str

    # A1 - Past Application
    past_applications: List[Dict[str, str]]

    # A2 - Future Trigger
    trigger_scenarios: List[str]
    trigger_language_signals: List[str]
    distinction_from_neighbors: Dict[str, str]

    # E - Execution
    execution_steps: List[Dict[str, Any]]

    # B - Boundary
    boundary_anti_scenarios: List[str]
    boundary_failure_modes: List[str]
    boundary_author_blindspots: List[str]
    boundary_confusion_risks: List[str]

    # Frontmatter
    description: str
    source_book: str
    source_chapter: str
    tags: List[str]
    related_methods: List[str] = field(default_factory=list)

    # 元数据
    generation_id: str = ""
    producer_id: str = "producer:skill-distiller"
    canonical_sha256: Optional[str] = None


# ============== 测试 ==============

@dataclass
class TestCase:
    """测试用例"""
    id: str
    type: str  # should_trigger | should_not_trigger | edge_case | sibling_confusion
    prompt: str
    expected_behavior: str
    notes: str


@dataclass
class TestResult:
    """测试结果"""
    test_case_id: str
    would_trigger: bool
    reason: str
    if_triggered_action: str
    passed: bool

    # 测试原件
    output_artifact_path: str
    trace_artifact_path: str
    output_sha256: str
    trace_sha256: str

    # 测试环境
    tested_by_model: str
    tested_at: str
    run_id: str


@dataclass
class PressureTestSuite:
    """压力测试套件"""
    method_id: str
    method_version: str
    test_cases: List[TestCase]

    should_trigger_count: int
    should_not_trigger_count: int
    edge_case_count: int
    sibling_confusion_count: int


# ============== 整书理解 ==============

@dataclass
class BookOverview:
    """整书理解骨架（Adler 分析阅读）"""
    generation_id: str

    # 步骤 1: 结构
    book_type: str
    main_thesis: str
    key_parts: List[Dict[str, str]]
    core_problem: str

    # 步骤 2: 解释
    key_terms: Dict[str, str]
    core_propositions: List[str]
    argument_chain: str

    # 步骤 3: 批判
    era_limitations: List[str]
    author_blindspots: List[str]
    unproven_assumptions: List[str]
    counter_arguments: List[str]

    # 步骤 4: 应用潜力
    skillable_content: List[str]
    non_skillable_content: List[str]
    estimated_skill_count_range: str
    priority_ranking: List[str]

    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    requires_user_confirmation: bool = True


# ============== 审计 ==============

@dataclass
class CandidateCoverageAudit:
    """候选覆盖审计"""
    generation_id: str

    scans: Dict[str, Dict[ExtractorType, str]]
    candidates: List[Dict[str, Any]]

    total_candidates: int = 0
    kept_count: int = 0
    merged_count: int = 0
    rejected_count: int = 0
    pending_count: int = 0


@dataclass
class ProducerSnapshot:
    """生产者快照"""
    producer_id: str
    role: str
    tool: str
    version: str

    run_id: str
    started_at: str
    ended_at: str
    platform: str
    model: str
    interface: str

    inputs: List[str]
    outputs: List[str]

    prompts: List[str]
    config: Dict[str, Any]
    methodology_version: str

    success: bool
    failures: List[str] = field(default_factory=list)
    rework_count: int = 0


@dataclass
class ProductionAudit:
    """生产审计"""
    generation_id: str
    source_sha256: str
    chapters: List[Dict[str, Any]]
    candidates: List[Dict[str, Any]]
    skills: List[Dict[str, Any]]
    version: str = "1.4.3"


# ============== 冻结清单 ==============

@dataclass
class KnowledgeFreezeManifest:
    """知识轨冻结清单"""
    generation_id: str
    source_sha256: str
    knowledge_units: List[Dict[str, str]]
    frozen_at: str
    distiller_version: str
    distiller_model: str


@dataclass
class MethodFreezeManifest:
    """方法轨冻结清单"""
    generation_id: str
    source_sha256: str

    verified_md_sha256: str
    methods: List[Dict[str, str]]

    cangjie_version: str = "v2.0.0"
    cangjie_commit: str = "149cb39f559cafcb82910f8662b3f4e3b9ee5574"
    cangjie_upstream_sha256: str = "e634c0e443e9625fb1f6a9b65dbf8d59087366a893aa16d452691f689f5b002e"

    producer_model: str = ""
    producer_run_id: str = ""
    producer_snapshot_sha256: str = ""

    frozen_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ============== 关系 ==============

@dataclass
class MethodRelation:
    """方法关系"""
    id: str
    source_method_id: str
    target_method_id: str
    relation_type: str  # prerequisite | alternative | complement | conflicts-with
    evidence: str


@dataclass
class KnowledgeMethodRelation:
    """知识-方法关系"""
    id: str
    knowledge_unit_id: str
    method_unit_id: str
    relation_type: str  # supports | explains | contradicts
    evidence_anchors: List[EvidenceAnchor]


# ============== 封装 ==============

@dataclass
class PackageManifest:
    """PACKAGE.json"""
    protocol_version: str = "2.0.0"
    profile: str = "full"
    package_id: str = ""
    package_root_hash: str = ""

    generation_id: str = ""
    source_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    creator: str = "fieldmind-distiller"


@dataclass
class ExportCertificate:
    """EXPORT_CERTIFICATE.json"""
    protocol_version: str = "2.0.0"
    package_id: str = ""
    package_root_hash: str = ""
    manifest_projection_sha256: str = ""

    exported_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    exporter_version: str = "fieldmind-distiller-1.0.0"


@dataclass
class ValidationReport:
    """VALIDATION_REPORT.json"""
    protocol_version: str = "2.0.0"
    package_id: str = ""
    package_root_hash: str = ""

    semantic_validation: str = ""
    ok: bool = False
    errors: List[str] = field(default_factory=list)
    validated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ============== 生产者角色 ==============

class ProducerRole(str, Enum):
    """生产者角色"""
    ORCHESTRATOR = "producer:orchestrator"
    SOURCE_NORMALIZER = "producer:source-normalizer"
    KNOWLEDGE_DISTILLER = "producer:knowledge-distiller"
    SKILL_DISTILLER = "producer:skill-distiller"
    RELATION_BUILDER = "producer:relation-builder"
    ADAPTER_COMPILER = "producer:adapter-compiler"
    TEST_RUNNER = "producer:test-runner"
    VALIDATOR = "producer:validator"


# 权限矩阵
PERMISSION_MATRIX: Dict[str, set] = {
    "generate_or_modify_method_semantic": {ProducerRole.SKILL_DISTILLER},
    "generate_or_modify_knowledge_semantic": {ProducerRole.KNOWLEDGE_DISTILLER},
    "build_knowledge_method_relation": {ProducerRole.RELATION_BUILDER},
    "execute_method_test": {ProducerRole.TEST_RUNNER},
    "generate_runtime_projection": {ProducerRole.ADAPTER_COMPILER},
    "merge_split_rename_method_before_freeze": {ProducerRole.SKILL_DISTILLER},
    "modify_frozen_asset": set(),
}


def check_permission(role: ProducerRole, operation: str) -> bool:
    """检查权限"""
    allowed_roles = PERMISSION_MATRIX.get(operation, set())
    return role in allowed_roles
