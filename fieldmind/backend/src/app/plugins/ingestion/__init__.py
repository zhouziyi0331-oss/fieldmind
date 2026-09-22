"""
采集插件包
"""

from app.plugins.ingestion.pdf_plugin import PDFPlugin
from app.plugins.ingestion.docx_plugin import DOCXPlugin
from app.plugins.ingestion.text_plugin import TextPlugin, MarkdownPlugin
from app.plugins.ingestion.image_plugin import ImagePlugin
from app.plugins.ingestion.audio_plugin import AudioPlugin
from app.plugins.ingestion.video_plugin import VideoPlugin
from app.plugins.ingestion.excel_plugin import ExcelPlugin, CSVPlugin

__all__ = [
    'PDFPlugin',
    'DOCXPlugin',
    'TextPlugin',
    'MarkdownPlugin',
    'ImagePlugin',
    'AudioPlugin',
    'VideoPlugin',
    'ExcelPlugin',
    'CSVPlugin',
]
