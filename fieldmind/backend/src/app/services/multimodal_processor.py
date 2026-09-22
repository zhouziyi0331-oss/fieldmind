"""
多模态处理器 - 统一处理音频/视频/文档/表格/图片
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class UnifiedContent:
    """统一的内容表示"""

    def __init__(self):
        self.text: str = ""  # 主文本内容
        self.tables: List[Dict] = []  # 表格数据
        self.formulas: List[Dict] = []  # 公式列表
        self.images: List[Dict] = []  # 图片描述
        self.audio_segments: List[Dict] = []  # 音频片段（带时间戳）
        self.video_info: Optional[Dict] = None  # 视频元信息
        self.metadata: Dict = {}  # 元数据
        self.source_type: str = ""  # 来源类型

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'text': self.text,
            'tables': self.tables,
            'formulas': self.formulas,
            'images': self.images,
            'audio_segments': self.audio_segments,
            'video_info': self.video_info,
            'metadata': self.metadata,
            'source_type': self.source_type,
            'word_count': len(self.text.split()) if self.text else 0,
            'table_count': len(self.tables),
            'formula_count': len(self.formulas),
            'has_audio': len(self.audio_segments) > 0,
            'has_video': self.video_info is not None
        }

    def get_full_text(self) -> str:
        """获取完整文本（包含表格和公式的文本化）"""
        parts = [self.text]

        # 添加表格摘要
        for table in self.tables:
            parts.append(f"\n[表格: {table.get('summary', '未命名表格')}]")

        # 添加公式
        for formula in self.formulas:
            parts.append(f"\n[公式: {formula.get('raw', '')}]")

        return "\n".join(parts)


class MultiModalProcessor:
    """多模态统一处理器"""

    def __init__(self):
        # 导入各个专用处理器
        from app.services.document_converter import DocumentConverter
        from app.services.video_processor import VideoProcessor
        from app.services.table_processor import table_processor
        from app.core.transcription import transcription_service

        self.doc_converter = DocumentConverter()
        self.video_processor = VideoProcessor()
        self.table_processor = table_processor
        self.transcription_service = transcription_service

        logger.info("✅ 多模态处理器初始化完成")

    def process_any_format(self, file_path: str, file_type: str) -> UnifiedContent:
        """
        统一处理入口 - 支持所有格式

        Args:
            file_path: 文件路径
            file_type: MIME类型

        Returns:
            UnifiedContent对象
        """
        content = UnifiedContent()
        content.source_type = file_type

        try:
            # 根据类型分发
            if file_type.startswith('video/'):
                content = self._process_video(file_path, content)

            elif file_type.startswith('audio/') or Path(file_path).suffix.lower() in ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac']:
                content = self._process_audio(file_path, content)

            elif file_type in ['application/pdf', 'pdf']:
                content = self._process_pdf(file_path, content)

            elif Path(file_path).suffix.lower() in ['.xlsx', '.xls', '.csv']:
                content = self._process_spreadsheet(file_path, content)

            elif file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                              'application/msword', 'docx', 'doc']:
                content = self._process_word(file_path, content)

            elif file_type.startswith('image/'):
                content = self._process_image(file_path, content)

            else:
                # 尝试作为文本处理
                content = self._process_text(file_path, content)

            logger.info(f"✅ 多模态处理完成: {file_type}")
            return content

        except Exception as e:
            logger.error(f"❌ 多模态处理失败: {e}", exc_info=True)
            return content

    def _process_video(self, file_path: str, content: UnifiedContent) -> UnifiedContent:
        """处理视频文件"""
        try:
            result = self.video_processor.process_video(file_path)

            content.text = result.get('text', '')
            content.audio_segments = result.get('segments', [])
            content.video_info = result.get('video_info', {})
            content.metadata = {
                'duration': result.get('video_info', {}).get('duration', 0),
                'language': result.get('language', 'zh'),
                'has_audio': True
            }

            logger.info(f"✅ 视频处理完成: {len(content.text)}字符")

        except Exception as e:
            logger.error(f"❌ 视频处理失败: {e}")

        return content

    def _process_audio(self, file_path: str, content: UnifiedContent) -> UnifiedContent:
        """处理音频文件"""
        try:
            result = self.transcription_service.transcribe(file_path)

            content.text = result.get('text', '')
            content.audio_segments = result.get('segments', [])
            content.metadata = {
                'duration': result.get('duration', 0),
                'language': result.get('language', 'zh')
            }

            logger.info(f"✅ 音频处理完成: {len(content.text)}字符")

        except Exception as e:
            logger.error(f"❌ 音频处理失败: {e}")

        return content

    def _process_pdf(self, file_path: str, content: UnifiedContent) -> UnifiedContent:
        """处理PDF文件"""
        try:
            # 提取文本
            text = self.doc_converter.convert_pdf(file_path)
            content.text = text

            # 提取表格
            table_result = self.table_processor.extract_tables_from_pdf(file_path)
            content.tables = table_result

            # 提取公式
            content.formulas = self.table_processor.extract_formulas(text)

            logger.info(f"✅ PDF处理完成: {len(text)}字符, {len(content.tables)}个表格")

        except Exception as e:
            logger.error(f"❌ PDF处理失败: {e}")

        return content

    def _process_spreadsheet(self, file_path: str, content: UnifiedContent) -> UnifiedContent:
        """处理表格文件"""
        try:
            result = self.table_processor.process_file(file_path)

            content.tables = result.get('tables', [])

            # 将表格转换为文本描述
            text_parts = []
            for table in content.tables:
                text_parts.append(f"【{table['sheet_name']}】")
                text_parts.append(table['summary'])

                # 添加前几行数据作为示例
                if 'data_json' in table and table['data_json']:
                    text_parts.append("数据示例：")
                    for row in table['data_json'][:3]:
                        text_parts.append(str(row))

            content.text = "\n".join(text_parts)

            logger.info(f"✅ 表格处理完成: {len(content.tables)}个表格")

        except Exception as e:
            logger.error(f"❌ 表格处理失败: {e}")

        return content

    def _process_word(self, file_path: str, content: UnifiedContent) -> UnifiedContent:
        """处理Word文档"""
        try:
            text = self.doc_converter.convert_docx(file_path)
            content.text = text

            # 提取公式
            content.formulas = self.table_processor.extract_formulas(text)

            logger.info(f"✅ Word处理完成: {len(text)}字符")

        except Exception as e:
            logger.error(f"❌ Word处理失败: {e}")

        return content

    def _process_image(self, file_path: str, content: UnifiedContent) -> UnifiedContent:
        """处理图片文件（OCR）"""
        try:
            # TODO: 集成OCR服务
            # 可以使用 pytesseract 或者调用云端OCR API
            content.images.append({
                'path': file_path,
                'description': '图片文件（OCR功能待实现）'
            })
            content.text = "[图片内容]"

            logger.info(f"✅ 图片处理完成")

        except Exception as e:
            logger.error(f"❌ 图片处理失败: {e}")

        return content

    def _process_text(self, file_path: str, content: UnifiedContent) -> UnifiedContent:
        """处理纯文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content.text = f.read()

            logger.info(f"✅ 文本处理完成: {len(content.text)}字符")

        except Exception as e:
            logger.error(f"❌ 文本处理失败: {e}")

        return content


# 全局实例
multimodal_processor = MultiModalProcessor()
