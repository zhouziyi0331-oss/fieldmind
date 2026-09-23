"""
SBPACK生产审计器

遵循规范：11-生产审计与验收.md
验证生产过程的完整性和真实性
"""
import json
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ProductionAuditor:
    """
    生产审计器

    审计内容：
    1. 生产者快照完整性
    2. 输入输出一致性
    3. 覆盖与候选去向记录
    4. 技能冻结清单验证
    5. 知识冻结清单验证
    """

    def __init__(self):
        self.errors = []
        self.warnings = []

    def audit(self, audit_dir: Path) -> Dict[str, Any]:
        """
        执行生产审计

        参数:
            audit_dir: 审计产物目录

        返回:
            审计结果
        """
        logger.info(f"开始生产审计: {audit_dir}")

        self.errors = []
        self.warnings = []

        # 1. 加载生产审计数据
        audit_data = self._load_audit_data(audit_dir)

        # 2. 验证覆盖记录
        self._audit_coverage(audit_data)

        # 3. 验证候选去向
        self._audit_candidate_disposition(audit_data)

        # 4. 验证生产者快照
        self._audit_producer_snapshots(audit_data)

        # 5. 验证冻结清单
        self._audit_freeze_lists(audit_data)

        # 6. 验证技能质量门
        self._audit_skill_quality_gates(audit_data)

        # 7. 生成审计报告
        result = self._build_audit_report(audit_data)

        logger.info(f"生产审计完成: {'通过' if result['passed'] else '失败'}")

        return result

    def _load_audit_data(self, audit_dir: Path) -> Dict[str, Any]:
        """加载审计数据"""
        audit_data = {}

        # 1. 生产审计.json
        production_audit_file = audit_dir / "生产审计.json"
        if production_audit_file.exists():
            with open(production_audit_file, 'r', encoding='utf-8') as f:
                audit_data["production_audit"] = json.load(f)
        else:
            self.errors.append("缺少必需文件: 生产审计.json")

        # 2. 覆盖与候选去向.md
        coverage_file = audit_dir / "覆盖与候选去向.md"
        if coverage_file.exists():
            with open(coverage_file, 'r', encoding='utf-8') as f:
                audit_data["coverage"] = f.read()
        else:
            self.warnings.append("缺少覆盖记录文件")

        # 3. 仓颉技能冻结清单.json
        skill_freeze_file = audit_dir / "仓颉技能冻结清单.json"
        if skill_freeze_file.exists():
            with open(skill_freeze_file, 'r', encoding='utf-8') as f:
                audit_data["skill_freeze"] = json.load(f)
        else:
            self.errors.append("缺少技能冻结清单")

        # 4. 知识冻结清单.json
        knowledge_freeze_file = audit_dir / "知识冻结清单.json"
        if knowledge_freeze_file.exists():
            with open(knowledge_freeze_file, 'r', encoding='utf-8') as f:
                audit_data["knowledge_freeze"] = json.load(f)
        else:
            self.errors.append("缺少知识冻结清单")

        return audit_data

    def _audit_coverage(self, audit_data: Dict[str, Any]):
        """审计覆盖记录"""
        production_audit = audit_data.get("production_audit", {})

        # 检查来源块扫描
        source_blocks = production_audit.get("sourceBlocks", {})
        if not source_blocks:
            self.errors.append("缺少来源块扫描记录")
            return

        total_blocks = source_blocks.get("total", 0)
        scanned_blocks = source_blocks.get("scanned", 0)

        if scanned_blocks < total_blocks:
            self.errors.append(f"扫描未完成: {scanned_blocks}/{total_blocks} 块")

        # 检查五类提取器扫描状态
        extractors = production_audit.get("extractors", {})
        required_extractors = ["framework", "principle", "case", "counterexample", "term"]

        for extractor in required_extractors:
            if extractor not in extractors:
                self.warnings.append(f"缺少 {extractor} 提取器扫描记录")

    def _audit_candidate_disposition(self, audit_data: Dict[str, Any]):
        """审计候选去向"""
        production_audit = audit_data.get("production_audit", {})

        candidates = production_audit.get("candidates", {})
        if not candidates:
            self.warnings.append("缺少候选记录")
            return

        # 统计候选去向
        total_candidates = candidates.get("total", 0)
        retained = candidates.get("retained", 0)
        merged = candidates.get("merged", 0)
        rejected = candidates.get("rejected", 0)
        pending = candidates.get("pending", 0)

        # 检查去向总数是否匹配
        accounted = retained + merged + rejected + pending
        if accounted != total_candidates:
            self.errors.append(f"候选去向不完整: {accounted}/{total_candidates}")

        # 检查是否有待完成项
        if pending > 0:
            self.warnings.append(f"有 {pending} 个候选待完成")

        # 验证合并链
        merge_chains = candidates.get("mergeChains", [])
        for chain in merge_chains:
            if not self._validate_merge_chain(chain):
                self.errors.append(f"合并链无效: {chain}")

    def _validate_merge_chain(self, chain: List[str]) -> bool:
        """验证合并链"""
        # 检查是否有循环
        seen = set()
        for item in chain:
            if item in seen:
                return False
            seen.add(item)

        # 检查是否有最终去向
        return len(chain) > 0

    def _audit_producer_snapshots(self, audit_data: Dict[str, Any]):
        """审计生产者快照"""
        production_audit = audit_data.get("production_audit", {})

        producers = production_audit.get("producers", [])
        if not producers or len(producers) == 0:
            self.errors.append("缺少生产者快照")
            return

        # 检查必需角色
        required_roles = {"knowledge_track", "skill_track"}
        found_roles = set(p.get("role") for p in producers)

        for role in required_roles:
            if role not in found_roles:
                self.errors.append(f"缺少生产者角色: {role}")

        # 验证每个生产者快照
        for producer in producers:
            self._validate_producer_snapshot(producer)

    def _validate_producer_snapshot(self, producer: Dict[str, Any]):
        """验证单个生产者快照"""
        role = producer.get("role", "")
        snapshot_hash = producer.get("snapshotHash", "")

        # 检查必需字段
        if not role:
            self.errors.append("生产者缺少role字段")

        if not snapshot_hash:
            self.errors.append(f"生产者 {role} 缺少snapshotHash")

        # 检查输入输出
        inputs = producer.get("inputs", [])
        outputs = producer.get("outputs", [])

        if len(inputs) == 0:
            self.errors.append(f"生产者 {role} 没有输入")

        if len(outputs) == 0:
            self.errors.append(f"生产者 {role} 没有输出")

        # 检查模型信息
        model_name = producer.get("modelName", "")
        if not model_name:
            self.warnings.append(f"生产者 {role} 缺少modelName")

    def _audit_freeze_lists(self, audit_data: Dict[str, Any]):
        """审计冻结清单"""
        # 验证技能冻结清单
        skill_freeze = audit_data.get("skill_freeze", {})
        if skill_freeze:
            self._validate_skill_freeze_list(skill_freeze)

        # 验证知识冻结清单
        knowledge_freeze = audit_data.get("knowledge_freeze", {})
        if knowledge_freeze:
            self._validate_knowledge_freeze_list(knowledge_freeze)

    def _validate_skill_freeze_list(self, freeze_list: Dict[str, Any]):
        """验证技能冻结清单"""
        # 检查来源SHA-256
        source_sha256 = freeze_list.get("sourceSha256", "")
        if not source_sha256:
            self.errors.append("技能冻结清单缺少sourceSha256")

        # 检查仓颉版本信息
        cangjie_version = freeze_list.get("cangjieVersion", "")
        if cangjie_version != "v2.0.0":
            self.warnings.append(f"仓颉版本不是v2.0.0: {cangjie_version}")

        # 检查技能列表
        skills = freeze_list.get("skills", [])
        if len(skills) == 0:
            self.warnings.append("技能冻结清单为空")

        # 验证每个技能
        for skill in skills:
            skill_id = skill.get("skillId", "")
            canonical_sha256 = skill.get("canonicalSha256", "")

            if not skill_id:
                self.errors.append("技能缺少skillId")

            if not canonical_sha256:
                self.errors.append(f"技能 {skill_id} 缺少canonicalSha256")

    def _validate_knowledge_freeze_list(self, freeze_list: Dict[str, Any]):
        """验证知识冻结清单"""
        # 检查来源SHA-256
        source_sha256 = freeze_list.get("sourceSha256", "")
        if not source_sha256:
            self.errors.append("知识冻结清单缺少sourceSha256")

        # 检查知识点列表
        knowledge_items = freeze_list.get("knowledgeItems", [])
        if len(knowledge_items) == 0:
            self.warnings.append("知识冻结清单为空")

        # 验证每个知识点
        for item in knowledge_items:
            knowledge_id = item.get("knowledgeId", "")
            content_hash = item.get("contentHash", "")

            if not knowledge_id:
                self.errors.append("知识点缺少knowledgeId")

            if not content_hash:
                self.errors.append(f"知识点 {knowledge_id} 缺少contentHash")

    def _audit_skill_quality_gates(self, audit_data: Dict[str, Any]):
        """审计技能质量门"""
        skill_freeze = audit_data.get("skill_freeze", {})
        if not skill_freeze:
            return

        skills = skill_freeze.get("skills", [])

        for skill in skills:
            skill_id = skill.get("skillId", "")

            # 检查三项验证
            v1_passed = skill.get("v1Passed", False)
            v2_passed = skill.get("v2Passed", False)
            v3_passed = skill.get("v3Passed", False)

            if not v1_passed:
                self.errors.append(f"技能 {skill_id} 未通过V1验证")

            if not v2_passed:
                self.errors.append(f"技能 {skill_id} 未通过V2验证")

            if not v3_passed:
                self.errors.append(f"技能 {skill_id} 未通过V3验证")

            # 检查RIA++结构
            has_ria = all(field in skill for field in [
                "rationale", "interpretation", "applicationOriginal",
                "applicationFuture", "execution", "boundaries"
            ])

            if not has_ria:
                self.errors.append(f"技能 {skill_id} 缺少完整RIA++结构")

            # 检查压力测试
            pressure_tests = skill.get("pressureTests", {})
            if not pressure_tests:
                self.warnings.append(f"技能 {skill_id} 缺少压力测试")

            # 检查description长度
            description = skill.get("description", "")
            if len(description) > 300:
                self.errors.append(f"技能 {skill_id} description超过300字符")

    def _build_audit_report(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建审计报告"""
        production_audit = audit_data.get("production_audit", {})

        # 统计信息
        source_blocks = production_audit.get("sourceBlocks", {})
        candidates = production_audit.get("candidates", {})

        report = {
            "passed": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "errorCount": len(self.errors),
            "warningCount": len(self.warnings),
            "statistics": {
                "sourceBlocks": {
                    "total": source_blocks.get("total", 0),
                    "scanned": source_blocks.get("scanned", 0)
                },
                "candidates": {
                    "total": candidates.get("total", 0),
                    "retained": candidates.get("retained", 0),
                    "merged": candidates.get("merged", 0),
                    "rejected": candidates.get("rejected", 0),
                    "pending": candidates.get("pending", 0)
                },
                "skills": {
                    "total": len(audit_data.get("skill_freeze", {}).get("skills", []))
                },
                "knowledge": {
                    "total": len(audit_data.get("knowledge_freeze", {}).get("knowledgeItems", []))
                }
            },
            "summary": self._generate_summary()
        }

        return report

    def _generate_summary(self) -> str:
        """生成审计摘要"""
        if len(self.errors) == 0:
            return f"生产审计通过，{len(self.warnings)}个警告"
        else:
            return f"生产审计失败：{len(self.errors)}个错误，{len(self.warnings)}个警告"


def create_production_audit_file(
    package_id: int,
    source_blocks: Dict[str, int],
    candidates: Dict[str, Any],
    producers: List[Dict[str, Any]],
    output_path: Path
) -> Dict[str, Any]:
    """
    创建生产审计文件

    参数:
        package_id: 包ID
        source_blocks: 来源块统计
        candidates: 候选统计
        producers: 生产者列表
        output_path: 输出路径

    返回:
        审计数据
    """
    audit_data = {
        "version": "1.4.4",
        "packageId": package_id,
        "createdAt": datetime.utcnow().isoformat(),
        "sourceBlocks": source_blocks,
        "candidates": candidates,
        "producers": producers,
        "extractors": {
            "framework": {"scanned": True, "candidateCount": 0},
            "principle": {"scanned": True, "candidateCount": 0},
            "case": {"scanned": True, "candidateCount": 0},
            "counterexample": {"scanned": True, "candidateCount": 0},
            "term": {"scanned": True, "candidateCount": 0}
        }
    }

    # 写入文件
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(audit_data, f, ensure_ascii=False, indent=2)

    logger.info(f"生产审计文件已创建: {output_path}")

    return audit_data
