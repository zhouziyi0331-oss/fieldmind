"""
表格处理器
表格数据解析和提取
"""

import os
from typing import Dict, Any, List
from pathlib import Path

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingException
from app.core.errors import ErrorCode


class TableProcessor:
    """表格处理器"""

    @staticmethod
    def process(file_path: str, mime_type: str) -> Dict[str, Any]:
        """
        处理表格文件

        Args:
            file_path: 表格文件路径
            mime_type: MIME类型

        Returns:
            Dict: 处理结果
                {
                    "text": str,              # 表格内容（文本格式）
                    "data": List[List],       # 表格数据（二维数组）
                    "rows": int,              # 行数
                    "columns": int,           # 列数
                    "metadata": dict,         # 元数据
                }
        """
        logger.info(f"处理表格: {file_path}")

        try:
            if mime_type == "text/csv":
                return CSVParser.parse(file_path)

            elif mime_type in [
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ]:
                return ExcelParser.parse(file_path)

            else:
                raise DocumentProcessingException(
                    error_code=ErrorCode.DOCUMENT_TYPE_UNSUPPORTED,
                    message=f"Unsupported table type: {mime_type}"
                )

        except Exception as e:
            logger.error(f"表格处理失败: {e}", file_path=file_path)
            raise DocumentProcessingException(
                error_code=ErrorCode.DOCUMENT_PROCESSING_FAILED,
                message=f"Failed to process table: {str(e)}"
            )


class CSVParser:
    """CSV 解析器"""

    @staticmethod
    def parse(file_path: str) -> Dict[str, Any]:
        """
        解析 CSV 文件

        Args:
            file_path: CSV 文件路径

        Returns:
            Dict: 解析结果
        """
        import csv

        data = []
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']

        # 尝试多种编码
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

        return {
            "text": text,
            "data": data,
            "rows": len(data),
            "columns": len(data[0]) if data else 0,
            "metadata": {
                "format": "csv",
                "has_header": True if data else False
            },
            "word_count": len(text.split()),
        }


class ExcelParser:
    """Excel 解析器"""

    @staticmethod
    def parse(file_path: str) -> Dict[str, Any]:
        """
        解析 Excel 文件

        Args:
            file_path: Excel 文件路径

        Returns:
            Dict: 解析结果
        """
        try:
            import pandas as pd

            # 读取所有工作表
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names

            all_data = []
            text_lines = []

            for sheet_name in sheet_names:
                # 读取工作表
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                # 添加工作表标题
                text_lines.append(f"\n=== {sheet_name} ===\n")

                # 转换为文本
                for _, row in df.iterrows():
                    row_text = " | ".join(str(cell) for cell in row)
                    text_lines.append(row_text)

                # 保存数据
                all_data.append({
                    "sheet": sheet_name,
                    "data": df.values.tolist(),
                    "columns": df.columns.tolist()
                })

            text = "\n".join(text_lines)

            # 计算总行列数
            total_rows = sum(len(sheet["data"]) for sheet in all_data)
            max_columns = max(
                (len(sheet["columns"]) for sheet in all_data),
                default=0
            )

            return {
                "text": text,
                "data": all_data,
                "rows": total_rows,
                "columns": max_columns,
                "metadata": {
                    "format": "excel",
                    "sheets": len(sheet_names),
                    "sheet_names": sheet_names
                },
                "word_count": len(text.split()),
            }

        except ImportError:
            logger.warning("pandas 未安装，使用基础解析器")
            return ExcelParser._parse_basic(file_path)

        except Exception as e:
            logger.error(f"Excel 解析失败: {e}")
            raise

    @staticmethod
    def _parse_basic(file_path: str) -> Dict[str, Any]:
        """
        基础 Excel 解析（不使用 pandas）

        Args:
            file_path: Excel 文件路径

        Returns:
            Dict: 解析结果
        """
        try:
            import openpyxl

            wb = openpyxl.load_workbook(file_path, read_only=True)
            sheet_names = wb.sheetnames

            all_data = []
            text_lines = []

            for sheet_name in sheet_names:
                sheet = wb[sheet_name]

                text_lines.append(f"\n=== {sheet_name} ===\n")

                sheet_data = []
                for row in sheet.iter_rows(values_only=True):
                    row_list = [str(cell) if cell is not None else "" for cell in row]
                    sheet_data.append(row_list)

                    row_text = " | ".join(row_list)
                    text_lines.append(row_text)

                all_data.append({
                    "sheet": sheet_name,
                    "data": sheet_data
                })

            text = "\n".join(text_lines)

            total_rows = sum(len(sheet["data"]) for sheet in all_data)
            max_columns = max(
                (len(row) for sheet in all_data for row in sheet["data"]),
                default=0
            )

            return {
                "text": text,
                "data": all_data,
                "rows": total_rows,
                "columns": max_columns,
                "metadata": {
                    "format": "excel",
                    "sheets": len(sheet_names),
                    "sheet_names": sheet_names
                },
                "word_count": len(text.split()),
            }

        except ImportError:
            logger.error("openpyxl 未安装，无法解析 Excel")
            raise

        except Exception as e:
            logger.error(f"Excel 基础解析失败: {e}")
            raise
