"""
蒸馏封装器

负责将蒸馏结果打包成标准SBPACK格式
"""

import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


class DistillationPackager:
    """
    蒸馏结果封装器

    将蒸馏系统的输出封装成SBPACK（Second Brain Package）格式
    """

    def __init__(self, version: str = "1.4.4"):
        """
        初始化封装器

        Args:
            version: SBPACK格式版本
        """
        self.version = version

    def package(
        self,
        generation_id: str,
        knowledge_items: List[Dict[str, Any]],
        method_items: List[Dict[str, Any]],
        relations: List[Dict[str, Any]],
        source_metadata: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        打包蒸馏结果

        Args:
            generation_id: 生成ID
            knowledge_items: 知识项列表
            method_items: 方法项列表
            relations: 关系列表
            source_metadata: 源文档元信息
            output_path: 输出路径（可选）

        Returns:
            封装后的SBPACK数据
        """
        package = {
            "version": self.version,
            "generation_id": generation_id,
            "created_at": datetime.utcnow().isoformat(),
            "source": source_metadata,
            "content": {
                "knowledge": knowledge_items,
                "methods": method_items,
                "relations": relations
            },
            "statistics": {
                "total_knowledge": len(knowledge_items),
                "total_methods": len(method_items),
                "total_relations": len(relations)
            },
            "checksum": self._calculate_checksum({
                "knowledge": knowledge_items,
                "methods": method_items,
                "relations": relations
            })
        }

        if output_path:
            self._save_package(package, output_path)

        return package

    def _calculate_checksum(self, content: Dict[str, Any]) -> str:
        """
        计算内容校验和

        Args:
            content: 内容字典

        Returns:
            SHA256校验和
        """
        content_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _save_package(self, package: Dict[str, Any], output_path: str) -> None:
        """
        保存封装包到文件

        Args:
            package: 封装包数据
            output_path: 输出路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(package, f, ensure_ascii=False, indent=2)

    def validate_package(self, package: Dict[str, Any]) -> bool:
        """
        验证封装包完整性

        Args:
            package: 封装包数据

        Returns:
            是否有效
        """
        try:
            # 检查必需字段
            required_fields = ["version", "generation_id", "created_at", "source", "content"]
            if not all(field in package for field in required_fields):
                return False

            # 验证校验和
            if "checksum" in package:
                calculated = self._calculate_checksum(package["content"])
                if calculated != package["checksum"]:
                    return False

            return True
        except Exception:
            return False
