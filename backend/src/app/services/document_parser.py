"""文档解析服务 - 支持多种文档格式，集成MinerU高级解析"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# 尝试导入MinerU客户端
MINERU_AVAILABLE = False
try:
    mineru_path = Path(__file__).parent.parent.parent.parent / "mineru-service"
    sys.path.insert(0, str(mineru_path))
    from mineru_client import MinerUClient, MinerUParser
    MINERU_AVAILABLE = True
    logger.info("✅ MinerU客户端加载成功")
except ImportError as e:
    logger.warning(f"⚠️ MinerU客户端未找到: {e}")


class DocumentParser:
    """文档解析服务 - 支持基础解析和MinerU高级解析"""

    def __init__(self, use_mineru: bool = True, mineru_url: str = "http://localhost:8765"):
        """
        Args:
            use_mineru: 是否优先使用MinerU解析（自动降级）
            mineru_url: MinerU服务地址
        """
        self.supported_formats = {
            'pdf': self.parse_pdf,
            'docx': self.parse_docx,
            'doc': self.parse_doc,
            'pptx': self.parse_pptx,
            'xlsx': self.parse_xlsx,
            'xls': self.parse_xls,
            'txt': self.parse_txt,
            'md': self.parse_markdown,
        }

        # MinerU客户端初始化
        self.mineru_enabled = False
        self.mineru_client = None
        self.mineru_parser = None

        if use_mineru and MINERU_AVAILABLE:
            try:
                self.mineru_client = MinerUClient(mineru_url)
                if self.mineru_client.health_check():
                    self.mineru_parser = MinerUParser(self.mineru_client)
                    self.mineru_enabled = True
                    logger.info("✅ MinerU解析器已启用")
                else:
                    logger.warning("⚠️ MinerU服务不可用，使用基础解析")
            except Exception as e:
                logger.warning(f"⚠️ MinerU初始化失败: {e}，使用基础解析")

    def parse(self, file_path: str, use_advanced: bool = True) -> Dict[str, Any]:
        """
        解析文档

        Args:
            file_path: 文件路径
            use_advanced: 是否使用高级解析（MinerU）

        Returns:
            解析结果
        """
        file_ext = Path(file_path).suffix.lower().lstrip('.')

        if file_ext not in self.supported_formats:
            raise ValueError(f"不支持的文件格式: {file_ext}")

        # 尝试MinerU高级解析（仅对PDF、图片、Office文档）
        advanced_formats = ['pdf', 'docx', 'pptx', 'xlsx', 'png', 'jpg', 'jpeg']
        if use_advanced and self.mineru_enabled and file_ext in advanced_formats:
            try:
                result = self._parse_with_mineru(file_path)
                result['parser'] = 'mineru'
                logger.info(f"✅ MinerU解析成功: {file_path}")
                return result
            except Exception as e:
                logger.warning(f"⚠️ MinerU解析失败，降级到基础解析: {e}")

        # 基础解析
        parser_func = self.supported_formats[file_ext]
        result = parser_func(file_path)
        result['parser'] = 'basic'
        return result

    def _parse_with_mineru(self, file_path: str) -> Dict[str, Any]:
        """使用MinerU解析文档（高级解析）"""
        if not self.mineru_client:
            raise RuntimeError("MinerU客户端未初始化")

        # 调用MinerU API
        mineru_result = self.mineru_client.parse_document(
            file_path=file_path,
            output_format="markdown",
            extract_images=True,
            extract_tables=True
        )

        # 转换为统一格式
        content = mineru_result.get('markdown', '')

        # 提取段落（MinerU通常提供段落信息）
        paragraphs = []
        if 'paragraphs' in mineru_result:
            paragraphs = [p.get('text', '') for p in mineru_result['paragraphs']]
        else:
            # 简单分段
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        return {
            'text': content,
            'paragraphs': paragraphs,
            'page_count': mineru_result.get('pages', 0),
            'images': mineru_result.get('images', []),
            'tables': mineru_result.get('tables', []),
            'metadata': {
                'language': mineru_result.get('language', 'unknown'),
                'parser_version': mineru_result.get('version', 'unknown'),
                'has_ocr': mineru_result.get('has_ocr', False)
            },
            'format': Path(file_path).suffix.lower().lstrip('.')
        }

    def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """解析PDF文件"""
        try:
            import pdfplumber

            text_content = []
            metadata = {}
            page_count = 0

            with pdfplumber.open(file_path) as pdf:
                metadata = pdf.metadata or {}
                page_count = len(pdf.pages)

                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)

            return {
                'text': '\n\n'.join(text_content),
                'page_count': page_count,
                'metadata': metadata,
                'format': 'pdf'
            }

        except Exception as e:
            logger.error(f"PDF解析失败: {str(e)}")
            # 备用方案：使用PyPDF2
            try:
                import PyPDF2

                text_content = []
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    page_count = len(reader.pages)

                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)

                return {
                    'text': '\n\n'.join(text_content),
                    'page_count': page_count,
                    'metadata': reader.metadata or {},
                    'format': 'pdf'
                }
            except Exception as e2:
                logger.error(f"PDF备用解析也失败: {str(e2)}")
                raise Exception(f"PDF解析失败: {str(e2)}")

    def parse_docx(self, file_path: str) -> Dict[str, Any]:
        """解析DOCX文件"""
        try:
            from docx import Document

            doc = Document(file_path)

            # 提取文本
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            text = '\n\n'.join(paragraphs)

            # 提取表格
            tables_text = []
            for table in doc.tables:
                for row in table.rows:
                    row_text = ' | '.join(cell.text.strip() for cell in row.cells)
                    if row_text:
                        tables_text.append(row_text)

            if tables_text:
                text += '\n\n表格内容:\n' + '\n'.join(tables_text)

            # 元数据
            core_props = doc.core_properties
            metadata = {
                'author': core_props.author or '',
                'title': core_props.title or '',
                'subject': core_props.subject or '',
                'created': str(core_props.created) if core_props.created else '',
                'modified': str(core_props.modified) if core_props.modified else '',
            }

            return {
                'text': text,
                'paragraph_count': len(paragraphs),
                'table_count': len(doc.tables),
                'metadata': metadata,
                'format': 'docx'
            }

        except Exception as e:
            logger.error(f"DOCX解析失败: {str(e)}")
            raise Exception(f"DOCX解析失败: {str(e)}")

    def parse_doc(self, file_path: str) -> Dict[str, Any]:
        """解析DOC文件（需要转换）"""
        # DOC格式较老，建议用户转换为DOCX
        # 这里提供简单的文本提取
        try:
            import textract
            text = textract.process(file_path).decode('utf-8')

            return {
                'text': text,
                'metadata': {},
                'format': 'doc',
                'note': '建议转换为DOCX格式以获得更好的解析效果'
            }
        except ImportError:
            raise Exception("DOC解析需要安装textract: pip install textract")
        except Exception as e:
            logger.error(f"DOC解析失败: {str(e)}")
            raise Exception(f"DOC解析失败: {str(e)}")

    def parse_pptx(self, file_path: str) -> Dict[str, Any]:
        """解析PPTX文件"""
        try:
            from pptx import Presentation

            prs = Presentation(file_path)

            slides_text = []
            for i, slide in enumerate(prs.slides):
                slide_text = [f"--- 幻灯片 {i+1} ---"]

                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_text.append(shape.text)

                slides_text.append('\n'.join(slide_text))

            text = '\n\n'.join(slides_text)

            return {
                'text': text,
                'slide_count': len(prs.slides),
                'metadata': {},
                'format': 'pptx'
            }

        except Exception as e:
            logger.error(f"PPTX解析失败: {str(e)}")
            raise Exception(f"PPTX解析失败: {str(e)}")

    def parse_xlsx(self, file_path: str) -> Dict[str, Any]:
        """解析XLSX文件"""
        try:
            import openpyxl

            wb = openpyxl.load_workbook(file_path, data_only=True)

            sheets_text = []
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                sheet_text = [f"--- 工作表: {sheet_name} ---"]

                for row in sheet.iter_rows(values_only=True):
                    row_text = ' | '.join(str(cell) if cell is not None else '' for cell in row)
                    if row_text.strip(' |'):
                        sheet_text.append(row_text)

                sheets_text.append('\n'.join(sheet_text))

            text = '\n\n'.join(sheets_text)

            return {
                'text': text,
                'sheet_count': len(wb.sheetnames),
                'metadata': {},
                'format': 'xlsx'
            }

        except Exception as e:
            logger.error(f"XLSX解析失败: {str(e)}")
            raise Exception(f"XLSX解析失败: {str(e)}")

    def parse_xls(self, file_path: str) -> Dict[str, Any]:
        """解析XLS文件"""
        try:
            import xlrd

            wb = xlrd.open_workbook(file_path)

            sheets_text = []
            for sheet in wb.sheets():
                sheet_text = [f"--- 工作表: {sheet.name} ---"]

                for row_idx in range(sheet.nrows):
                    row = sheet.row_values(row_idx)
                    row_text = ' | '.join(str(cell) for cell in row)
                    if row_text.strip(' |'):
                        sheet_text.append(row_text)

                sheets_text.append('\n'.join(sheet_text))

            text = '\n\n'.join(sheets_text)

            return {
                'text': text,
                'sheet_count': wb.nsheets,
                'metadata': {},
                'format': 'xls'
            }

        except Exception as e:
            logger.error(f"XLS解析失败: {str(e)}")
            raise Exception(f"XLS解析失败: {str(e)}")

    def parse_txt(self, file_path: str) -> Dict[str, Any]:
        """解析TXT文件"""
        try:
            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        text = f.read()

                    return {
                        'text': text,
                        'metadata': {'encoding': encoding},
                        'format': 'txt'
                    }
                except UnicodeDecodeError:
                    continue

            raise Exception("无法识别文件编码")

        except Exception as e:
            logger.error(f"TXT解析失败: {str(e)}")
            raise Exception(f"TXT解析失败: {str(e)}")

    def parse_markdown(self, file_path: str) -> Dict[str, Any]:
        """解析Markdown文件"""
        return self.parse_txt(file_path)  # Markdown本质是纯文本


# 全局实例
document_parser = DocumentParser(use_mineru=True)


def get_parser(use_mineru: bool = True, mineru_url: str = "http://localhost:8765") -> DocumentParser:
    """获取文档解析器（可配置）"""
    return DocumentParser(use_mineru=use_mineru, mineru_url=mineru_url)
