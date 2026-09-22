"""
JSON/XML 数据采集插件
"""

from typing import Dict, Any
from app.agents.ingestion_agent import IngestionPlugin
from app.core.logging import logger


class JSONPlugin(IngestionPlugin):
    """JSON 数据采集插件"""

    @property
    def plugin_name(self) -> str:
        return "JSONPlugin"

    @property
    def supported_formats(self) -> list:
        return ["json"]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """采集 JSON 文件"""
        try:
            import json

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 转换为文本
            text_lines = self._flatten_json(data)
            full_text = "\n".join(text_lines)

            # 统计
            structured_metadata = {
                "format": "json",
                "keys": len(data) if isinstance(data, dict) else 0,
                "items": len(data) if isinstance(data, list) else 0,
                "total_words": len(full_text.replace(" ", "")),
                "language": self._detect_language(full_text)
            }

            return {
                "raw_text": full_text,
                "structured_metadata": structured_metadata,
                "content_type": "data",
                "extraction_method": "json_parse",
                "confidence": 1.0
            }

        except Exception as e:
            logger.error(f"JSON 采集失败: {e}")
            raise

    def _flatten_json(self, data, prefix="") -> list:
        """扁平化 JSON 为文本列表"""
        lines = []

        if isinstance(data, dict):
            for key, value in data.items():
                new_prefix = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    lines.extend(self._flatten_json(value, new_prefix))
                else:
                    lines.append(f"{new_prefix}: {value}")

        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_prefix = f"{prefix}[{i}]"
                if isinstance(item, (dict, list)):
                    lines.extend(self._flatten_json(item, new_prefix))
                else:
                    lines.append(f"{new_prefix}: {item}")

        else:
            lines.append(f"{prefix}: {data}")

        return lines

    def _detect_language(self, text: str) -> str:
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        total_chars = len(text)
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return "zh"
        return "en"


class XMLPlugin(IngestionPlugin):
    """XML 数据采集插件"""

    @property
    def plugin_name(self) -> str:
        return "XMLPlugin"

    @property
    def supported_formats(self) -> list:
        return ["xml"]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """采集 XML 文件"""
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(file_path)
            root = tree.getroot()

            # 提取文本
            text_lines = self._extract_xml_text(root)
            full_text = "\n".join(text_lines)

            # 统计
            structured_metadata = {
                "format": "xml",
                "root_tag": root.tag,
                "total_elements": len(list(root.iter())),
                "total_words": len(full_text.replace(" ", "")),
                "language": self._detect_language(full_text)
            }

            return {
                "raw_text": full_text,
                "structured_metadata": structured_metadata,
                "content_type": "data",
                "extraction_method": "xml_parse",
                "confidence": 1.0
            }

        except Exception as e:
            logger.error(f"XML 采集失败: {e}")
            raise

    def _extract_xml_text(self, element, prefix="") -> list:
        """递归提取 XML 文本"""
        lines = []

        # 元素标签
        tag = element.tag
        if '}' in tag:
            tag = tag.split('}', 1)[1]

        current_prefix = f"{prefix}/{tag}" if prefix else tag

        # 元素文本
        if element.text and element.text.strip():
            lines.append(f"{current_prefix}: {element.text.strip()}")

        # 属性
        for key, value in element.attrib.items():
            lines.append(f"{current_prefix}@{key}: {value}")

        # 子元素
        for child in element:
            lines.extend(self._extract_xml_text(child, current_prefix))

        return lines

    def _detect_language(self, text: str) -> str:
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        total_chars = len(text)
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return "zh"
        return "en"
