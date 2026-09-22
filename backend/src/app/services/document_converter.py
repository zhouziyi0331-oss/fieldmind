"""
Document conversion service using MarkItDown
Converts various document formats to Markdown for processing
"""
from typing import Optional, Dict, Any
from pathlib import Path
import logging

try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False
    logging.warning("MarkItDown not installed. Document conversion will be limited.")

logger = logging.getLogger(__name__)


class DocumentConverter:
    """Convert documents to Markdown using MarkItDown"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        if MARKITDOWN_AVAILABLE:
            self.converter = MarkItDown()
        else:
            self.converter = None

    def is_available(self) -> bool:
        """Check if MarkItDown is available"""
        return MARKITDOWN_AVAILABLE and self.converter is not None

    def convert_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Convert a document file to Markdown

        Args:
            file_path: Path to the document file

        Returns:
            Dictionary with:
                - text_content: Converted markdown text
                - title: Document title (if available)
                - metadata: Additional metadata
        """
        if not self.is_available():
            logger.error("MarkItDown is not available")
            return None

        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.error(f"File not found: {file_path}")
                return None

            # Convert the document
            result = self.converter.convert(str(file_path))

            return {
                "text_content": result.text_content,
                "title": result.title if hasattr(result, 'title') else file_path_obj.stem,
                "metadata": {
                    "file_name": file_path_obj.name,
                    "file_extension": file_path_obj.suffix,
                    "file_size": file_path_obj.stat().st_size,
                }
            }

        except Exception as e:
            logger.error(f"Error converting document {file_path}: {str(e)}")
            return None

    def supported_formats(self) -> list:
        """Return list of supported document formats"""
        return [
            ".pdf", ".docx", ".doc", ".pptx", ".ppt",
            ".xlsx", ".xls", ".html", ".htm",
            ".txt", ".md", ".csv", ".json", ".xml"
        ]

    def is_supported(self, file_path: str) -> bool:
        """Check if a file format is supported"""
        extension = Path(file_path).suffix.lower()
        return extension in self.supported_formats()


# Global instance
document_converter = DocumentConverter()
