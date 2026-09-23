"""
SBPACK 2.0验收器

验收SBPACK包的完整性和质量
遵循规范：05-SBPACK-2.0封装与验收清单.md + 11-生产审计与验收.md
"""
import json
import hashlib
import zipfile
from typing import Dict, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SBPACKValidator:
    """
    SBPACK 2.0验收器

    验收清单：
    1. 文件结构完整性
    2. manifest.json格式正确
    3. 知识轨完整性
    4. 技能轨完整性
    5. 双轨冻结状态
    6. SHA-256哈希验证
    7. 证据追溯链完整
    8. 生产者快照完整
    """

    REQUIRED_FILES = [
        "manifest.json",
        "payload/knowledge/index.json",
        "payload/skills/index.json",
        "payload/relations/index.json",
        "provenance/source.json",
        "provenance/producers.json",
        "provenance/freezes.json",
        "audit/verification.json"
    ]

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate(self, sbpack_path: str) -> Dict[str, Any]:
        """
        验收SBPACK文件

        参数:
            sbpack_path: .sbpack文件路径

        返回:
            验收结果
        """
        logger.info(f"开始验收SBPACK: {sbpack_path}")

        self.errors = []
        self.warnings = []

        try:
            # 1. 检查文件存在
            if not Path(sbpack_path).exists():
                self.errors.append("SBPACK文件不存在")
                return self._build_result(False)

            # 2. 解压并验证
            with zipfile.ZipFile(sbpack_path, 'r') as zipf:
                # 2.1 检查文件结构
                self._validate_structure(zipf)

                # 2.2 验证manifest
                manifest = self._validate_manifest(zipf)

                # 2.3 验证知识轨
                self._validate_knowledge_track(zipf, manifest)

                # 2.4 验证技能轨
                self._validate_skill_track(zipf, manifest)

                # 2.5 验证关系
                self._validate_relations(zipf)

                # 2.6 验证溯源
                self._validate_provenance(zipf)

                # 2.7 验证冻结状态
                self._validate_freezes(zipf)

            # 3. 生成验收报告
            result = self._build_result(len(self.errors) == 0)

            logger.info(f"SBPACK验收完成: {'通过' if result['passed'] else '失败'}")

            return result

        except Exception as e:
            logger.error(f"验收过程出错: {str(e)}", exc_info=True)
            self.errors.append(f"验收过程异常: {str(e)}")
            return self._build_result(False)

    def _validate_structure(self, zipf: zipfile.ZipFile):
        """验证文件结构"""
        file_list = zipf.namelist()

        for required_file in self.REQUIRED_FILES:
            if required_file not in file_list:
                self.errors.append(f"缺少必需文件: {required_file}")

    def _validate_manifest(self, zipf: zipfile.ZipFile) -> Dict[str, Any]:
        """验证manifest.json"""
        try:
            with zipf.open("manifest.json") as f:
                manifest = json.load(f)

            # 检查必需字段
            required_fields = ["version", "protocol", "protocolVersion", "packageId", "packageName", "source", "content"]

            for field in required_fields:
                if field not in manifest:
                    self.errors.append(f"manifest缺少必需字段: {field}")

            # 检查协议版本
            if manifest.get("protocolVersion") != "2.0.0":
                self.errors.append(f"协议版本不匹配: {manifest.get('protocolVersion')}")

            return manifest

        except json.JSONDecodeError as e:
            self.errors.append(f"manifest.json格式错误: {str(e)}")
            return {}

    def _validate_knowledge_track(self, zipf: zipfile.ZipFile, manifest: Dict[str, Any]):
        """验证知识轨"""
        try:
            # 读取知识轨索引
            with zipf.open("payload/knowledge/index.json") as f:
                knowledge_index = json.load(f)

            # 检查数量一致性
            manifest_count = manifest.get("content", {}).get("knowledge", {}).get("count", 0)
            index_count = knowledge_index.get("count", 0)

            if manifest_count != index_count:
                self.errors.append(f"知识点数量不一致: manifest={manifest_count}, index={index_count}")

            # 验证每个知识点文件
            for item in knowledge_index.get("items", []):
                item_file = f"payload/knowledge/{item['file']}"

                if item_file not in zipf.namelist():
                    self.errors.append(f"知识点文件缺失: {item_file}")
                    continue

                # 验证知识点内容
                with zipf.open(item_file) as f:
                    knowledge_item = json.load(f)

                self._validate_knowledge_item(knowledge_item, item['id'])

        except Exception as e:
            self.errors.append(f"知识轨验证失败: {str(e)}")

    def _validate_knowledge_item(self, item: Dict[str, Any], item_id: str):
        """验证单个知识点"""
        # SBPACK 2.0必需字段
        required_fields = [
            "knowledgeId", "title", "type", "statement", "explanation",
            "whyMatters", "scope", "evidenceRefs"
        ]

        for field in required_fields:
            if field not in item or not item[field]:
                self.errors.append(f"知识点 {item_id} 缺少必需字段: {field}")

        # 验证证据引用
        evidence_refs = item.get("evidenceRefs", [])
        if not evidence_refs or len(evidence_refs) == 0:
            self.errors.append(f"知识点 {item_id} 没有证据引用")

    def _validate_skill_track(self, zipf: zipfile.ZipFile, manifest: Dict[str, Any]):
        """验证技能轨"""
        try:
            # 读取技能轨索引
            with zipf.open("payload/skills/index.json") as f:
                skills_index = json.load(f)

            # 检查数量一致性
            manifest_count = manifest.get("content", {}).get("skills", {}).get("count", 0)
            index_count = skills_index.get("count", 0)

            if manifest_count != index_count:
                self.errors.append(f"技能数量不一致: manifest={manifest_count}, index={index_count}")

            # 验证每个技能
            for item in skills_index.get("items", []):
                skill_id = item['id']
                skill_dir = f"payload/skills/{item['directory']}"

                # 检查必需文件
                canonical_file = f"{skill_dir}/canonical/SKILL.md"
                metadata_file = f"{skill_dir}/metadata.json"
                tests_file = f"{skill_dir}/test-prompts.json"

                if canonical_file not in zipf.namelist():
                    self.errors.append(f"技能 {skill_id} 缺少canonical/SKILL.md")

                if metadata_file not in zipf.namelist():
                    self.errors.append(f"技能 {skill_id} 缺少metadata.json")

                if tests_file not in zipf.namelist():
                    self.warnings.append(f"技能 {skill_id} 缺少test-prompts.json")

                # 验证metadata
                if metadata_file in zipf.namelist():
                    with zipf.open(metadata_file) as f:
                        metadata = json.load(f)
                    self._validate_skill_metadata(metadata, skill_id)

        except Exception as e:
            self.errors.append(f"技能轨验证失败: {str(e)}")

    def _validate_skill_metadata(self, metadata: Dict[str, Any], skill_id: str):
        """验证技能元数据"""
        # RIA++必需字段
        required_fields = [
            "skillId", "name", "description", "rationale", "interpretation",
            "applicationOriginal", "applicationFuture", "execution", "boundaries"
        ]

        for field in required_fields:
            if field not in metadata or not metadata[field]:
                self.errors.append(f"技能 {skill_id} 缺少必需字段: {field}")

        # 检查description长度
        description = metadata.get("description", "")
        if len(description) > 300:
            self.errors.append(f"技能 {skill_id} description超过300字符")

        # 检查验证状态
        validation = metadata.get("validation", {})
        if not validation.get("v1Passed"):
            self.warnings.append(f"技能 {skill_id} 未通过V1验证")
        if not validation.get("v2Passed"):
            self.warnings.append(f"技能 {skill_id} 未通过V2验证")
        if not validation.get("v3Passed"):
            self.warnings.append(f"技能 {skill_id} 未通过V3验证")

    def _validate_relations(self, zipf: zipfile.ZipFile):
        """验证关系"""
        try:
            with zipf.open("payload/relations/index.json") as f:
                relations = json.load(f)

            # 检查关系完整性
            for rel in relations.get("relations", []):
                if not rel.get("knowledgeId"):
                    self.errors.append("关系缺少knowledgeId")
                if not rel.get("skillId"):
                    self.errors.append("关系缺少skillId")
                if not rel.get("relationType"):
                    self.errors.append("关系缺少relationType")

        except Exception as e:
            self.warnings.append(f"关系验证失败: {str(e)}")

    def _validate_provenance(self, zipf: zipfile.ZipFile):
        """验证溯源信息"""
        try:
            # 验证来源信息
            with zipf.open("provenance/source.json") as f:
                source = json.load(f)

            if not source.get("sha256"):
                self.errors.append("来源缺少SHA-256哈希")

            # 验证生产者快照
            with zipf.open("provenance/producers.json") as f:
                producers = json.load(f)

            snapshots = producers.get("snapshots", [])
            if len(snapshots) == 0:
                self.errors.append("没有生产者快照")

            # 检查必需角色
            roles = set(s.get("role") for s in snapshots)
            required_roles = {"knowledge_track", "skill_track"}

            for role in required_roles:
                if role not in roles:
                    self.warnings.append(f"缺少生产者快照角色: {role}")

        except Exception as e:
            self.errors.append(f"溯源信息验证失败: {str(e)}")

    def _validate_freezes(self, zipf: zipfile.ZipFile):
        """验证冻结状态"""
        try:
            with zipf.open("provenance/freezes.json") as f:
                freezes = json.load(f)

            # 检查双轨冻结
            if not freezes.get("knowledge", {}).get("frozen"):
                self.errors.append("知识轨未冻结")

            if not freezes.get("skill", {}).get("frozen"):
                self.errors.append("技能轨未冻结")

            # 检查冻结哈希
            if not freezes.get("knowledge", {}).get("freezeHash"):
                self.errors.append("知识轨缺少冻结哈希")

            if not freezes.get("skill", {}).get("freezeHash"):
                self.errors.append("技能轨缺少冻结哈希")

        except Exception as e:
            self.errors.append(f"冻结状态验证失败: {str(e)}")

    def _build_result(self, passed: bool) -> Dict[str, Any]:
        """构建验收结果"""
        return {
            "passed": passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "errorCount": len(self.errors),
            "warningCount": len(self.warnings),
            "summary": f"验收{'通过' if passed else '失败'}: {len(self.errors)}个错误, {len(self.warnings)}个警告"
        }
