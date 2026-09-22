"""
SBPACK验证器

验证蒸馏结果包的完整性和正确性
"""

from typing import Dict, Any, List, Optional, Tuple
import json
import hashlib


class SBPACKValidator:
    """
    SBPACK格式验证器

    验证蒸馏结果是否符合第二大脑标准格式
    """

    def __init__(self, strict_mode: bool = False):
        """
        初始化验证器

        Args:
            strict_mode: 是否启用严格模式
        """
        self.strict_mode = strict_mode
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, package: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        验证SBPACK包

        Args:
            package: 待验证的包数据

        Returns:
            (是否有效, 错误列表, 警告列表)
        """
        self.errors = []
        self.warnings = []

        # 1. 验证基础结构
        self._validate_structure(package)

        # 2. 验证版本
        self._validate_version(package)

        # 3. 验证内容完整性
        self._validate_content(package)

        # 4. 验证校验和
        self._validate_checksum(package)

        # 5. 验证关系完整性
        self._validate_relations(package)

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _validate_structure(self, package: Dict[str, Any]) -> None:
        """验证基础结构"""
        required_fields = ["version", "generation_id", "created_at", "source", "content"]

        for field in required_fields:
            if field not in package:
                self.errors.append(f"缺少必需字段: {field}")

        if "content" in package:
            content = package["content"]
            if not isinstance(content, dict):
                self.errors.append("content字段必须是字典类型")
            else:
                for key in ["knowledge", "methods", "relations"]:
                    if key not in content:
                        self.errors.append(f"content缺少必需字段: {key}")
                    elif not isinstance(content[key], list):
                        self.errors.append(f"content.{key}必须是列表类型")

    def _validate_version(self, package: Dict[str, Any]) -> None:
        """验证版本号"""
        if "version" not in package:
            return

        version = package["version"]
        if not isinstance(version, str):
            self.errors.append("version必须是字符串类型")
        elif not version.startswith("1."):
            self.warnings.append(f"未知的版本号: {version}")

    def _validate_content(self, package: Dict[str, Any]) -> None:
        """验证内容完整性"""
        if "content" not in package:
            return

        content = package["content"]

        # 验证知识项
        if "knowledge" in content:
            for idx, item in enumerate(content["knowledge"]):
                self._validate_knowledge_item(item, idx)

        # 验证方法项
        if "methods" in content:
            for idx, item in enumerate(content["methods"]):
                self._validate_method_item(item, idx)

    def _validate_knowledge_item(self, item: Dict[str, Any], index: int) -> None:
        """验证知识项"""
        required = ["id", "type", "content"]
        for field in required:
            if field not in item:
                self.errors.append(f"知识项[{index}]缺少字段: {field}")

        if "type" in item and item["type"] != "knowledge":
            self.warnings.append(f"知识项[{index}]类型不是'knowledge': {item['type']}")

    def _validate_method_item(self, item: Dict[str, Any], index: int) -> None:
        """验证方法项"""
        required = ["id", "type", "name"]
        for field in required:
            if field not in item:
                self.errors.append(f"方法项[{index}]缺少字段: {field}")

        if "type" in item and item["type"] != "method":
            self.warnings.append(f"方法项[{index}]类型不是'method': {item['type']}")

    def _validate_checksum(self, package: Dict[str, Any]) -> None:
        """验证校验和"""
        if "checksum" not in package:
            if self.strict_mode:
                self.errors.append("缺少checksum字段")
            else:
                self.warnings.append("缺少checksum字段")
            return

        if "content" not in package:
            return

        # 重新计算校验和
        content_str = json.dumps(package["content"], sort_keys=True, ensure_ascii=False)
        calculated = hashlib.sha256(content_str.encode()).hexdigest()

        if calculated != package["checksum"]:
            self.errors.append("校验和不匹配")

    def _validate_relations(self, package: Dict[str, Any]) -> None:
        """验证关系完整性"""
        if "content" not in package:
            return

        content = package["content"]
        if "relations" not in content:
            return

        # 收集所有有效ID
        valid_ids = set()
        if "knowledge" in content:
            valid_ids.update(item.get("id") for item in content["knowledge"] if "id" in item)
        if "methods" in content:
            valid_ids.update(item.get("id") for item in content["methods"] if "id" in item)

        # 验证关系引用
        for idx, relation in enumerate(content["relations"]):
            if "source_id" in relation and relation["source_id"] not in valid_ids:
                self.warnings.append(f"关系[{idx}]的source_id不存在: {relation['source_id']}")
            if "target_id" in relation and relation["target_id"] not in valid_ids:
                self.warnings.append(f"关系[{idx}]的target_id不存在: {relation['target_id']}")

    def get_validation_report(self) -> str:
        """
        获取验证报告

        Returns:
            格式化的验证报告
        """
        report = []

        if self.errors:
            report.append("❌ 错误:")
            for error in self.errors:
                report.append(f"  - {error}")

        if self.warnings:
            report.append("⚠️  警告:")
            for warning in self.warnings:
                report.append(f"  - {warning}")

        if not self.errors and not self.warnings:
            report.append("✅ 验证通过")

        return "\n".join(report)
