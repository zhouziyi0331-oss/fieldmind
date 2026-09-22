"""
表格处理服务 - 从PDF/Excel/图片中提取表格和公式
"""
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from pathlib import Path
import re
import json

logger = logging.getLogger(__name__)


class TableProcessor:
    """表格和公式处理器"""

    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls', '.csv', '.pdf']
        logger.info("✅ 表格处理器初始化完成")

    def extract_tables_from_excel(self, file_path: str) -> List[Dict[str, Any]]:
        """
        从Excel文件提取所有表格

        Returns:
            List of {
                'sheet_name': str,
                'data': DataFrame,
                'summary': str,
                'row_count': int,
                'col_count': int
            }
        """
        try:
            excel_file = pd.ExcelFile(file_path)
            tables = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                # 基本统计
                row_count, col_count = df.shape

                # 生成摘要
                summary = self._generate_table_summary(df, sheet_name)

                tables.append({
                    'sheet_name': sheet_name,
                    'data': df,
                    'data_json': df.to_dict('records'),
                    'columns': df.columns.tolist(),
                    'summary': summary,
                    'row_count': row_count,
                    'col_count': col_count
                })

            logger.info(f"✅ 从Excel提取了{len(tables)}个表格")
            return tables

        except Exception as e:
            logger.error(f"❌ Excel表格提取失败: {e}")
            return []

    def extract_tables_from_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """从CSV文件提取表格"""
        try:
            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except (UnicodeDecodeError, pd.errors.ParserError) as e:
                    logger.debug(f"编码 {encoding} 读取失败: {e}")
                    continue

            if df is None:
                raise Exception("无法以任何编码读取CSV")

            row_count, col_count = df.shape
            summary = self._generate_table_summary(df, "CSV数据")

            return [{
                'sheet_name': 'CSV',
                'data': df,
                'data_json': df.to_dict('records'),
                'columns': df.columns.tolist(),
                'summary': summary,
                'row_count': row_count,
                'col_count': col_count
            }]

        except Exception as e:
            logger.error(f"❌ CSV表格提取失败: {e}")
            return []

    def extract_tables_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        从PDF中提取表格（使用pdfplumber）
        """
        try:
            import pdfplumber

            tables = []
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()

                    for table_idx, table_data in enumerate(page_tables):
                        if not table_data or len(table_data) < 2:
                            continue

                        # 转换为DataFrame
                        df = pd.DataFrame(table_data[1:], columns=table_data[0])

                        row_count, col_count = df.shape
                        summary = self._generate_table_summary(df, f"第{page_num}页表格{table_idx+1}")

                        tables.append({
                            'sheet_name': f'Page{page_num}_Table{table_idx+1}',
                            'page': page_num,
                            'data': df,
                            'data_json': df.to_dict('records'),
                            'columns': df.columns.tolist(),
                            'summary': summary,
                            'row_count': row_count,
                            'col_count': col_count
                        })

            logger.info(f"✅ 从PDF提取了{len(tables)}个表格")
            return tables

        except ImportError:
            logger.warning("⚠️ pdfplumber未安装，无法提取PDF表格")
            return []
        except Exception as e:
            logger.error(f"❌ PDF表格提取失败: {e}")
            return []

    def extract_formulas(self, text: str) -> List[Dict[str, Any]]:
        """
        提取文本中的公式（数学表达式）
        """
        formulas = []

        # 正则匹配常见公式模式
        patterns = [
            # LaTeX公式: $...$, $$...$$
            (r'\$\$(.+?)\$\$', 'latex_display'),
            (r'\$(.+?)\$', 'latex_inline'),
            # 简单数学表达式: a = b + c
            (r'([a-zA-Z_]\w*)\s*=\s*(.+)', 'equation'),
            # 百分比: 增长率=20%
            (r'([一-龥]+)\s*[=＝]\s*(\d+\.?\d*%)', 'percentage'),
            # 比率: A:B = 3:2
            (r'(.+?)\s*[:：]\s*(.+?)\s*=\s*(\d+)\s*[:：]\s*(\d+)', 'ratio')
        ]

        for pattern, formula_type in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                formulas.append({
                    'type': formula_type,
                    'raw': match.group(0),
                    'content': match.group(1) if match.lastindex >= 1 else match.group(0),
                    'position': match.start()
                })

        logger.info(f"✅ 提取了{len(formulas)}个公式")
        return formulas

    def _generate_table_summary(self, df: pd.DataFrame, table_name: str) -> str:
        """生成表格摘要"""
        try:
            row_count, col_count = df.shape

            # 列名
            columns = ", ".join(df.columns.tolist()[:5])
            if col_count > 5:
                columns += f"等{col_count}列"

            # 数值列统计
            numeric_cols = df.select_dtypes(include=['number']).columns
            stats = []

            for col in numeric_cols[:3]:  # 只统计前3个数值列
                try:
                    mean_val = df[col].mean()
                    stats.append(f"{col}平均值={mean_val:.2f}")
                except (ValueError, TypeError) as e:
                    logger.debug(f"列 {col} 统计计算失败: {e}")
                    pass

            summary = f"{table_name}: {row_count}行×{col_count}列，包含列[{columns}]"
            if stats:
                summary += f"，{'; '.join(stats)}"

            return summary

        except Exception as e:
            return f"{table_name}: {df.shape[0]}行×{df.shape[1]}列"

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        统一处理入口 - 根据文件类型自动选择处理方法

        Returns:
            {
                'tables': List[Dict],
                'formulas': List[Dict],
                'summary': str
            }
        """
        file_path_obj = Path(file_path)
        extension = file_path_obj.suffix.lower()

        result = {
            'tables': [],
            'formulas': [],
            'summary': ''
        }

        try:
            # 提取表格
            if extension in ['.xlsx', '.xls']:
                result['tables'] = self.extract_tables_from_excel(file_path)
            elif extension == '.csv':
                result['tables'] = self.extract_tables_from_csv(file_path)
            elif extension == '.pdf':
                result['tables'] = self.extract_tables_from_pdf(file_path)

            # 生成整体摘要
            if result['tables']:
                table_count = len(result['tables'])
                total_rows = sum(t['row_count'] for t in result['tables'])
                result['summary'] = f"提取了{table_count}个表格，共{total_rows}行数据"

            return result

        except Exception as e:
            logger.error(f"❌ 文件处理失败: {e}")
            return result


# 全局实例
table_processor = TableProcessor()
