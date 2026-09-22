"""
表格采集插件
"""

from typing import Dict, Any
from app.agents.ingestion_agent import IngestionPlugin
from app.core.logging import logger


class ExcelPlugin(IngestionPlugin):
    """Excel 采集插件"""

    @property
    def plugin_name(self) -> str:
        return "ExcelPlugin"

    @property
    def supported_formats(self) -> list:
        return ["xlsx", "xls"]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        采集 Excel 文件

        ⭐⭐⭐ 关键修复：使用结构化解析器，而不是简单转文本
        """
        try:
            # ⭐⭐⭐ 使用结构化表格解析器
            from app.services.structured_table_parser import structured_table_parser

            logger.info(f"📊 使用结构化解析器处理 Excel: {file_path}")

            # 调用结构化解析
            structured_result = structured_table_parser.parse_excel_structured(file_path)

            # 提取文本表示（用于向量检索）
            text = structured_result['text_representation']

            # 构建 sources（类似音频的 segments）
            sources = []
            for sheet_name, sheet_data in structured_result['sheets'].items():
                # 遍历每一行数据
                for row_data in sheet_data['data']:
                    # 构建行的文本表示
                    row_text_parts = []
                    row_cells = []

                    for cell in row_data:
                        cell_value = cell.get('value')
                        if cell_value is not None and str(cell_value).strip():
                            row_text_parts.append(str(cell_value))

                        # 保存单元格结构化数据
                        row_cells.append({
                            "col": cell['col'],
                            "value": cell_value,
                            "type": cell['type'],
                            "formula": cell.get('formula')
                        })

                    # 构建 source 对象（传递给 ChunkingAgent）
                    if row_text_parts:
                        sources.append({
                            "sentence": " | ".join(row_text_parts),  # 文本表示
                            "source": {
                                "sheet": sheet_name,
                                "row": row_data[0]['row'] if row_data else 0,
                                "row_data": {  # ⭐⭐⭐ 完整的结构化行数据
                                    "row": row_data[0]['row'] if row_data else 0,
                                    "cells": row_cells
                                }
                            }
                        })

            # 构建元数据
            structured_metadata = {
                "format": "excel",
                "sheets": len(structured_result['sheets']),
                "sheet_names": list(structured_result['sheets'].keys()),
                "total_rows": sum(len(s['data']) for s in structured_result['sheets'].values()),
                "total_formulas": structured_result['metadata'].get('total_formulas', 0),
                "parsing_method": "structured",  # ⭐ 标记使用了结构化解析
                "language": self._detect_language(text),
                # ⭐⭐⭐ 保存完整的结构化数据
                "structured_data": structured_result['sheets']
            }

            return {
                "raw_text": text,
                "structured_metadata": structured_metadata,
                "content_type": "table",
                "extraction_method": "structured_table_parser",  # ⭐ 新方法
                "confidence": 0.95,
                # ⭐⭐⭐ 关键：传递 sources 给后续流程
                "sources": sources
            }

        except ImportError as e:
            logger.warning(f"⚠️ 结构化解析器不可用，使用降级方案: {e}")
            return self._ingest_fallback(file_path)
        except Exception as e:
            logger.error(f"❌ Excel 结构化解析失败，使用降级方案: {e}")
            return self._ingest_fallback(file_path)

    def _ingest_fallback(self, file_path: str) -> Dict[str, Any]:
        """降级方案：使用 pandas 简单解析"""
        try:
            import pandas as pd

            # 读取所有工作表
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names

            all_data = []
            text_lines = []

            for sheet_name in sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                text_lines.append(f"\n=== {sheet_name} ===\n")

                for _, row in df.iterrows():
                    row_text = " | ".join(str(cell) for cell in row)
                    text_lines.append(row_text)

                all_data.append({
                    "sheet": sheet_name,
                    "rows": len(df),
                    "columns": len(df.columns)
                })

            text = "\n".join(text_lines)

            structured_metadata = {
                "format": "excel",
                "sheets": len(sheet_names),
                "sheet_names": sheet_names,
                "total_rows": sum(s["rows"] for s in all_data),
                "total_words": len(text.replace(" ", "")),
                "language": self._detect_language(text),
                "parsing_method": "fallback"
            }

            return {
                "raw_text": text,
                "structured_metadata": structured_metadata,
                "content_type": "table",
                "extraction_method": "pandas",
                "confidence": 0.75
            }

        except Exception as e:
            logger.error(f"Excel 采集失败: {e}")
            raise

    def _detect_language(self, text: str) -> str:
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        total_chars = len(text)
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return "zh"
        return "en"


class CSVPlugin(IngestionPlugin):
    """CSV 采集插件"""

    @property
    def plugin_name(self) -> str:
        return "CSVPlugin"

    @property
    def supported_formats(self) -> list:
        return ["csv"]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """采集 CSV 文件"""
        try:
            import csv

            data = []
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        reader = csv.reader(f)
                        data = [row for row in reader]
                    break
                except UnicodeDecodeError:
                    continue

            if not data:
                raise ValueError("无法识别 CSV 文件编码")

            # 转换为文本
            text_lines = []
            for row in data:
                text_lines.append(" | ".join(str(cell) for cell in row))

            text = "\n".join(text_lines)

            structured_metadata = {
                "format": "csv",
                "rows": len(data),
                "columns": len(data[0]) if data else 0,
                "has_header": True if data else False,
                "total_words": len(text.replace(" ", "")),
                "language": self._detect_language(text)
            }

            return {
                "raw_text": text,
                "structured_metadata": structured_metadata,
                "content_type": "table",
                "extraction_method": "csv_reader",
                "confidence": 1.0
            }

        except Exception as e:
            logger.error(f"CSV 采集失败: {e}")
            raise

    def _detect_language(self, text: str) -> str:
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        total_chars = len(text)
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return "zh"
        return "en"
