"""
Excel转换服务 - 表格内容提取 + 公式识别
支持.xlsx, .xls格式
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import openpyxl
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


class ExcelConverter:
    """Excel表格转换器 - 提取内容和公式"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.name = "ExcelConverter"

    def convert(self, file_path: str) -> Dict[str, Any]:
        """
        转换Excel文件为结构化数据

        Returns:
            {
                "text": "表格的文本表示（用于后续处理）",
                "sheets": {
                    "Sheet1": {
                        "rows": 100,
                        "cols": 10,
                        "data": [[...], [...]],
                        "formulas": {"C5": "=SUM(A1:A4)", ...},
                        "calculated_values": {"C5": 150, ...}
                    }
                },
                "metadata": {...}
            }
        """
        try:
            logger.info(f"📊 ExcelConverter: 开始转换 {file_path}")

            # 加载工作簿
            workbook = openpyxl.load_workbook(file_path, data_only=False)

            sheets_data = {}
            all_text_lines = []

            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                sheet_info = self._extract_sheet(sheet)
                sheets_data[sheet_name] = sheet_info

                # 构建文本表示
                all_text_lines.append(f"\n=== 表格: {sheet_name} ===\n")
                all_text_lines.append(self._sheet_to_text(sheet_info))

            # 生成文本表示（用于后续NLP处理）
            text = "\n".join(all_text_lines)

            metadata = {
                "sheet_count": len(workbook.sheetnames),
                "sheet_names": workbook.sheetnames,
                "has_formulas": any(
                    len(s.get("formulas", {})) > 0
                    for s in sheets_data.values()
                )
            }

            logger.info(f"✅ Excel转换完成: {len(workbook.sheetnames)}个表格")

            return {
                "text": text,
                "sheets": sheets_data,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"❌ Excel转换失败: {e}")
            raise

    def _extract_sheet(self, sheet) -> Dict[str, Any]:
        """提取单个工作表的数据"""
        max_row = sheet.max_row
        max_col = sheet.max_column

        # 提取数据
        data = []
        formulas = {}
        calculated_values = {}

        for row_idx in range(1, max_row + 1):
            row_data = []
            for col_idx in range(1, max_col + 1):
                cell = sheet.cell(row=row_idx, column=col_idx)
                cell_ref = f"{get_column_letter(col_idx)}{row_idx}"

                # 保存单元格值
                value = cell.value
                row_data.append(value)

                # 如果是公式，同时保存公式和计算结果
                if cell.data_type == 'f':  # formula
                    formulas[cell_ref] = f"={cell.value}"

                    # 尝试获取计算结果
                    # 需要重新加载工作簿（data_only=True）来获取计算值
                    calculated_values[cell_ref] = value

            data.append(row_data)

        return {
            "rows": max_row,
            "cols": max_col,
            "data": data,
            "formulas": formulas,
            "calculated_values": calculated_values
        }

    def _sheet_to_text(self, sheet_info: Dict[str, Any]) -> str:
        """将表格转换为文本表示"""
        lines = []

        data = sheet_info["data"]
        formulas = sheet_info.get("formulas", {})

        # 表头信息
        lines.append(f"行数: {sheet_info['rows']}, 列数: {sheet_info['cols']}")

        # 如果有公式，先列出
        if formulas:
            lines.append("\n公式:")
            for cell_ref, formula in formulas.items():
                calc_value = sheet_info["calculated_values"].get(cell_ref, "")
                lines.append(f"  {cell_ref}: {formula} = {calc_value}")

        # 表格内容（限制行数，避免过长）
        lines.append("\n表格内容:")
        max_preview_rows = min(20, len(data))

        for row_idx, row in enumerate(data[:max_preview_rows]):
            # 过滤空行
            if all(cell is None or cell == "" for cell in row):
                continue

            # 格式化行
            row_str = " | ".join(str(cell) if cell is not None else "" for cell in row)
            lines.append(f"  第{row_idx + 1}行: {row_str}")

        if len(data) > max_preview_rows:
            lines.append(f"  ... (省略 {len(data) - max_preview_rows} 行)")

        return "\n".join(lines)

    def get_calculated_values(self, file_path: str) -> Dict[str, Any]:
        """
        获取Excel中所有公式的计算结果
        需要用data_only=True模式重新加载
        """
        try:
            workbook = openpyxl.load_workbook(file_path, data_only=True)

            calculated = {}
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                sheet_calc = {}

                for row in sheet.iter_rows():
                    for cell in row:
                        if cell.value is not None:
                            cell_ref = f"{get_column_letter(cell.column)}{cell.row}"
                            sheet_calc[cell_ref] = cell.value

                calculated[sheet_name] = sheet_calc

            return calculated

        except Exception as e:
            logger.error(f"❌ 获取计算值失败: {e}")
            return {}


class CSVConverter:
    """CSV转换器"""

    def __init__(self):
        self.name = "CSVConverter"

    def convert(self, file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        转换CSV文件

        Returns:
            {
                "text": "CSV内容的文本表示",
                "data": [[...], [...]],
                "metadata": {...}
            }
        """
        import csv

        try:
            logger.info(f"📄 CSVConverter: 开始转换 {file_path}")

            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                reader = csv.reader(f)
                data = list(reader)

            # 生成文本表示
            text_lines = []
            text_lines.append(f"CSV文件包含 {len(data)} 行数据\n")

            # 预览前20行
            max_preview = min(20, len(data))
            for idx, row in enumerate(data[:max_preview]):
                row_str = " | ".join(row)
                text_lines.append(f"第{idx + 1}行: {row_str}")

            if len(data) > max_preview:
                text_lines.append(f"... (省略 {len(data) - max_preview} 行)")

            text = "\n".join(text_lines)

            metadata = {
                "rows": len(data),
                "cols": len(data[0]) if data else 0,
                "encoding": encoding
            }

            logger.info(f"✅ CSV转换完成: {len(data)}行")

            return {
                "text": text,
                "data": data,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"❌ CSV转换失败: {e}")
            raise
