"""
结构化表格解析器 - Structured Table Parser

将 Excel/CSV 表格解析为完全结构化的 JSON 数据，而不是简单的文本
保留：单元格坐标、数据类型、公式、表头信息、列语义

核心理念：
- "表格化"（旧）：转成 "值1 | 值2 | 值3" 文本 ❌
- "结构化"（新）：保留完整的单元格元数据 ✅
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class CellData:
    """单元格数据结构"""

    def __init__(
        self,
        row: int,
        col: int,
        value: Any,
        data_type: str,
        format_string: Optional[str] = None,
        formula: Optional[str] = None,
        is_merged: bool = False,
        merge_range: Optional[Tuple[int, int, int, int]] = None
    ):
        self.row = row
        self.col = col
        self.value = value
        self.data_type = data_type  # string, number, date, boolean, formula, empty
        self.format_string = format_string
        self.formula = formula
        self.is_merged = is_merged
        self.merge_range = merge_range  # (start_row, start_col, end_row, end_col)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "row": self.row,
            "col": self.col,
            "value": self.value,
            "type": self.data_type
        }

        if self.format_string:
            result["format"] = self.format_string

        if self.formula:
            result["formula"] = self.formula

        if self.is_merged:
            result["is_merged"] = True
            result["merge_range"] = self.merge_range

        return result


class SheetStructure:
    """工作表结构"""
    def __init__(self, sheet_name: str, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.sheet_name = sheet_name
        self.dimensions = {"rows": 0, "cols": 0}
        self.headers = []  # 表头行
        self.data = []  # 数据行（每行是 CellData 列表）
        self.formulas = {}  # 公式字典 {cell_ref: {formula, result}}
        self.merged_cells = []  # 合并单元格范围
        self.column_types = {}  # 列数据类型推断
        self.column_semantics = {}  # 列语义（如"姓名列"、"金额列"）
        self.metadata = {}

    def infer_column_semantics(self):
        """推断列的语义"""
        if not self.headers:
            return

        # 根据表头推断列语义
        for col_idx, header_cell in enumerate(self.headers):
            header_text = str(header_cell.value).lower() if header_cell.value else ""

            # 人名列
            if any(keyword in header_text for keyword in ["姓名", "名字", "人名", "name", "person"]):
                self.column_semantics[col_idx] = {"type": "person_name", "description": "人名"}

            # 地名列
            elif any(keyword in header_text for keyword in ["地点", "地名", "位置", "location", "place"]):
                self.column_semantics[col_idx] = {"type": "location", "description": "地点"}

            # 时间列
            elif any(keyword in header_text for keyword in ["时间", "日期", "年月", "date", "time"]):
                self.column_semantics[col_idx] = {"type": "temporal", "description": "时间"}

            # 金额列
            elif any(keyword in header_text for keyword in ["金额", "价格", "费用", "amount", "price", "cost"]):
                self.column_semantics[col_idx] = {"type": "monetary", "description": "金额"}

            # 数量列
            elif any(keyword in header_text for keyword in ["数量", "个数", "count", "quantity"]):
                self.column_semantics[col_idx] = {"type": "quantity", "description": "数量"}

            # 百分比列
            elif any(keyword in header_text for keyword in ["比例", "占比", "百分", "percent", "ratio"]):
                self.column_semantics[col_idx] = {"type": "percentage", "description": "百分比"}

            # 描述列
            elif any(keyword in header_text for keyword in ["描述", "说明", "备注", "description", "note", "remark"]):
                self.column_semantics[col_idx] = {"type": "description", "description": "描述文本"}

            else:
                self.column_semantics[col_idx] = {"type": "general", "description": header_text}

    def infer_column_types(self):
        """推断每列的数据类型"""
        if not self.data:
            return

        for col_idx in range(self.dimensions["cols"]):
            types_count = {}

            for row in self.data:
                if col_idx < len(row):
                    cell = row[col_idx]
                    cell_type = cell.data_type
                    types_count[cell_type] = types_count.get(cell_type, 0) + 1

            # 选择出现最多的类型
            if types_count:
                dominant_type = max(types_count.items(), key=lambda x: x[1])[0]
                self.column_types[col_idx] = dominant_type

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "sheet_name": self.sheet_name,
            "dimensions": self.dimensions,
            "headers": [cell.to_dict() for cell in self.headers] if self.headers else [],
            "data": [
                [cell.to_dict() for cell in row]
                for row in self.data
            ],
            "formulas": self.formulas,
            "merged_cells": self.merged_cells,
            "column_types": self.column_types,
            "column_semantics": self.column_semantics,
            "metadata": self.metadata
        }


class StructuredTableParser:
    """
    结构化表格解析器

    核心功能：
    1. 解析 Excel (.xlsx, .xls) 为完全结构化的 JSON
    2. 解析 CSV 为结构化数据
    3. 保留单元格坐标、数据类型、公式
    4. 推断列语义（人名、地名、金额等）
    5. 同时生成文本表示（用于全文搜索）
    """

    def __init__(self):
        self.supported_formats = [".xlsx", ".xls", ".csv"]
        logger.info("✅ 结构化表格解析器初始化完成")

    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        统一解析入口

        Args:
            file_path: 文件路径

        Returns:
            {
                "sheets": {sheet_name: SheetStructure.to_dict()},
                "text_representation": str,  # 用于全文搜索
                "summary": str,
                "metadata": {...}
            }
        """
        file_path_obj = Path(file_path)
        extension = file_path_obj.suffix.lower()

        if extension not in self.supported_formats:
            raise ValueError(f"不支持的文件格式: {extension}")

        logger.info(f"📊 开始结构化解析: {file_path}")

        if extension in [".xlsx", ".xls"]:
            return self.parse_excel_structured(file_path)
        elif extension == ".csv":
            return self.parse_csv_structured(file_path)

    def parse_excel_structured(self, file_path: str) -> Dict[str, Any]:
        """
        解析 Excel 文件为完全结构化的数据

        Returns:
            完整的结构化表格数据
        """
        try:
            import openpyxl
            from openpyxl.utils import get_column_letter

            logger.info(f"📖 读取 Excel 文件: {file_path}")

            # 加载工作簿（保留公式）
            workbook = openpyxl.load_workbook(file_path, data_only=False)

            # 同时加载计算值版本
            workbook_values = openpyxl.load_workbook(file_path, data_only=True)

            sheets_data = {}
            text_lines = []
            total_rows = 0
            total_formulas = 0

            for sheet_name in workbook.sheetnames:
                logger.info(f"   解析工作表: {sheet_name}")

                sheet = workbook[sheet_name]
                sheet_values = workbook_values[sheet_name]

                # 创建 SheetStructure
                sheet_structure = SheetStructure(sheet_name)

                # 获取维度
                max_row = sheet.max_row
                max_col = sheet.max_column
                sheet_structure.dimensions = {"rows": max_row, "cols": max_col}

                # 检测表头（假设第一行是表头）
                if max_row > 0:
                    header_row = []
                    for col_idx in range(1, max_col + 1):
                        cell = sheet.cell(row=1, column=col_idx)
                        cell_data = self._parse_cell(
                            cell=cell,
                            value_cell=sheet_values.cell(row=1, column=col_idx),
                            row=0,  # 0-indexed
                            col=col_idx - 1
                        )
                        header_row.append(cell_data)

                    sheet_structure.headers = header_row

                # 解析数据行（从第二行开始）
                for row_idx in range(2, max_row + 1):
                    data_row = []

                    for col_idx in range(1, max_col + 1):
                        cell = sheet.cell(row=row_idx, column=col_idx)
                        value_cell = sheet_values.cell(row=row_idx, column=col_idx)

                        cell_data = self._parse_cell(
                            cell=cell,
                            value_cell=value_cell,
                            row=row_idx - 1,  # 0-indexed
                            col=col_idx - 1
                        )

                        data_row.append(cell_data)

                        # 记录公式
                        if cell_data.formula:
                            cell_ref = f"{get_column_letter(col_idx)}{row_idx}"
                            sheet_structure.formulas[cell_ref] = {
                                "formula": cell_data.formula,
                                "result": cell_data.value
                            }
                            total_formulas += 1

                    sheet_structure.data.append(data_row)

                # 检测合并单元格
                if hasattr(sheet, 'merged_cells'):
                    for merged_range in sheet.merged_cells.ranges:
                        sheet_structure.merged_cells.append({
                            "start_row": merged_range.min_row - 1,
                            "start_col": merged_range.min_col - 1,
                            "end_row": merged_range.max_row - 1,
                            "end_col": merged_range.max_col - 1,
                            "range": str(merged_range)
                        })

                # 推断列类型和语义
                sheet_structure.infer_column_types()
                sheet_structure.infer_column_semantics()

                # 元数据
                sheet_structure.metadata = {
                    "has_formulas": len(sheet_structure.formulas) > 0,
                    "has_merged_cells": len(sheet_structure.merged_cells) > 0,
                    "data_rows": len(sheet_structure.data)
                }

                sheets_data[sheet_name] = sheet_structure.to_dict()

                # 生成文本表示
                text_lines.append(self._generate_text_representation(sheet_structure))
                total_rows += len(sheet_structure.data)

            # 生成整体文本表示
            text_representation = "\n\n".join(text_lines)

            # 生成摘要
            summary = (
                f"{len(sheets_data)} 个工作表, "
                f"共 {total_rows} 行数据"
            )
            if total_formulas > 0:
                summary += f", {total_formulas} 个公式"

            metadata = {
                "file_type": "excel",
                "sheet_count": len(sheets_data),
                "total_rows": total_rows,
                "total_formulas": total_formulas,
                "parsed_at": datetime.utcnow().isoformat()
            }

            logger.info(f"✅ Excel 解析完成: {summary}")

            return {
                "sheets": sheets_data,
                "text_representation": text_representation,
                "summary": summary,
                "metadata": metadata
            }

        except ImportError:
            logger.error("❌ openpyxl 未安装，请运行: pip install openpyxl")
            raise
        except Exception as e:
            logger.error(f"❌ Excel 解析失败: {e}", exc_info=True)
            raise

    def _parse_cell(
        self,
        cell,
        value_cell,
        row: int,
        col: int
    ) -> CellData:
        """解析单个单元格"""
        # 获取值
        value = value_cell.value if value_cell else None

        # 判断数据类型
        data_type = "empty"
        formula = None

        if cell.data_type == 'f':  # formula
            data_type = "formula"
            formula = f"={cell.value}" if cell.value else None
        elif value is None or value == "":
            data_type = "empty"
        elif isinstance(value, bool):
            data_type = "boolean"
        elif isinstance(value, (int, float)):
            data_type = "number"
        elif isinstance(value, datetime):
            data_type = "date"
            value = value.isoformat()
        else:
            data_type = "string"
            value = str(value)

        # 获取格式
        format_string = cell.number_format if hasattr(cell, 'number_format') else None

        # 检查是否在合并单元格中
        is_merged = False
        merge_range = None

        return CellData(
            row=row,
            col=col,
            value=value,
            data_type=data_type,
            format_string=format_string,
            formula=formula,
            is_merged=is_merged,
            merge_range=merge_range
        )

    def parse_csv_structured(self, file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        解析 CSV 文件为结构化数据

        Args:
            file_path: CSV 文件路径
            encoding: 编码格式

        Returns:
            结构化表格数据
        """
        import csv

        try:
            logger.info(f"📖 读取 CSV 文件: {file_path}")

            # 尝试多种编码
            encodings = [encoding, 'utf-8', 'gbk', 'gb2312', 'latin1']
            content = None
            used_encoding = None

            for enc in encodings:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        reader = csv.reader(f)
                        content = list(reader)
                    used_encoding = enc
                    break
                except (UnicodeDecodeError, Exception):
                    continue

            if content is None:
                raise Exception("无法以任何编码读取 CSV")

            # 创建 SheetStructure
            sheet_structure = SheetStructure("CSV")

            if not content:
                return self._empty_result()

            # 维度
            max_row = len(content)
            max_col = max(len(row) for row in content) if content else 0
            sheet_structure.dimensions = {"rows": max_row, "cols": max_col}

            # 表头（第一行）
            if max_row > 0:
                header_row = []
                for col_idx, cell_value in enumerate(content[0]):
                    cell_data = CellData(
                        row=0,
                        col=col_idx,
                        value=cell_value,
                        data_type="string"
                    )
                    header_row.append(cell_data)
                sheet_structure.headers = header_row

            # 数据行
            for row_idx in range(1, max_row):
                data_row = []
                row_content = content[row_idx]

                for col_idx in range(max_col):
                    cell_value = row_content[col_idx] if col_idx < len(row_content) else ""

                    # 推断数据类型
                    data_type = self._infer_cell_type(cell_value)

                    # 转换值
                    parsed_value = self._parse_cell_value(cell_value, data_type)

                    cell_data = CellData(
                        row=row_idx,
                        col=col_idx,
                        value=parsed_value,
                        data_type=data_type
                    )
                    data_row.append(cell_data)

                sheet_structure.data.append(data_row)

            # 推断列类型和语义
            sheet_structure.infer_column_types()
            sheet_structure.infer_column_semantics()

            # 元数据
            sheet_structure.metadata = {
                "encoding": used_encoding,
                "data_rows": len(sheet_structure.data)
            }

            # 生成文本表示
            text_representation = self._generate_text_representation(sheet_structure)

            summary = f"1 个 CSV 表格, {len(sheet_structure.data)} 行数据"

            metadata = {
                "file_type": "csv",
                "encoding": used_encoding,
                "total_rows": len(sheet_structure.data),
                "parsed_at": datetime.utcnow().isoformat()
            }

            logger.info(f"✅ CSV 解析完成: {summary}")

            return {
                "sheets": {"CSV": sheet_structure.to_dict()},
                "text_representation": text_representation,
                "summary": summary,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"❌ CSV 解析失败: {e}", exc_info=True)
            raise

    def _infer_cell_type(self, value: str) -> str:
        """推断单元格数据类型"""
        if not value or value.strip() == "":
            return "empty"

        value = value.strip()

        # 布尔值
        if value.lower() in ["true", "false", "是", "否", "yes", "no"]:
            return "boolean"

        # 数字
        try:
            float(value.replace(",", ""))  # 移除千位分隔符
            return "number"
        except ValueError:
            pass

        # 日期（简单判断）
        if any(sep in value for sep in ["-", "/", "年", "月", "日"]):
            # 可以进一步用 dateutil.parser 解析
            return "date"

        return "string"

    def _parse_cell_value(self, value: str, data_type: str) -> Any:
        """根据类型解析单元格值"""
        if data_type == "empty":
            return None

        if data_type == "boolean":
            return value.lower() in ["true", "是", "yes"]

        if data_type == "number":
            try:
                # 移除千位分隔符
                clean_value = value.replace(",", "")
                if "." in clean_value:
                    return float(clean_value)
                else:
                    return int(clean_value)
            except ValueError:
                return value

        return value

    def _generate_text_representation(self, sheet_structure: SheetStructure) -> str:
        """生成表格的文本表示（用于全文搜索）"""
        lines = []

        # 表格标题
        lines.append(f"=== 表格: {sheet_structure.sheet_name} ===\n")

        # 维度信息
        lines.append(
            f"维度: {sheet_structure.dimensions['rows']} 行 × "
            f"{sheet_structure.dimensions['cols']} 列\n"
        )

        # 列语义
        if sheet_structure.column_semantics:
            lines.append("列信息:")
            for col_idx, semantic in sheet_structure.column_semantics.items():
                if col_idx < len(sheet_structure.headers):
                    header = sheet_structure.headers[col_idx]
                    lines.append(
                        f"  列 {col_idx + 1} ({header.value}): "
                        f"{semantic.get('description', '未知')} "
                        f"[{semantic.get('type', 'general')}]"
                    )
            lines.append("")

        # 公式
        if sheet_structure.formulas:
            lines.append(f"公式 ({len(sheet_structure.formulas)} 个):")
            for cell_ref, formula_info in list(sheet_structure.formulas.items())[:5]:
                lines.append(
                    f"  {cell_ref}: {formula_info['formula']} = {formula_info['result']}"
                )
            if len(sheet_structure.formulas) > 5:
                lines.append(f"  ... (还有 {len(sheet_structure.formulas) - 5} 个公式)")
            lines.append("")

        # 数据预览（前20行）
        lines.append("数据预览:")

        # 表头
        if sheet_structure.headers:
            header_texts = [str(cell.value) for cell in sheet_structure.headers]
            lines.append("  " + " | ".join(header_texts))
            lines.append("  " + "-" * (len(" | ".join(header_texts))))

        # 数据行
        preview_rows = min(20, len(sheet_structure.data))
        for row_idx in range(preview_rows):
            row = sheet_structure.data[row_idx]
            row_texts = [str(cell.value) if cell.value is not None else "" for cell in row]
            lines.append("  " + " | ".join(row_texts))

        if len(sheet_structure.data) > preview_rows:
            lines.append(f"  ... (还有 {len(sheet_structure.data) - preview_rows} 行)")

        return "\n".join(lines)

    def _empty_result(self) -> Dict[str, Any]:
        """返回空结果"""
        return {
            "sheets": {},
            "text_representation": "",
            "summary": "空表格",
            "metadata": {
                "file_type": "unknown",
                "parsed_at": datetime.utcnow().isoformat()
            }
        }


# 全局实例
structured_table_parser = StructuredTableParser()


def parse_structured_table(file_path: str) -> Dict[str, Any]:
    """便捷函数：解析结构化表格"""
    return structured_table_parser.parse(file_path)


if __name__ == "__main__":
    # 测试代码
    print("=" * 80)
    print("🧪 结构化表格解析器测试")
    print("=" * 80)

    # 这里可以添加测试代码
    print("\n✅ 结构化表格解析器模块加载完成")
    print("=" * 80)
