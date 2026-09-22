"""
PDF 增强服务
基于 pdfcn 的核心功能
支持 PDF 预览、注释、标记
🔥 WorkflowEngine集成 - 阶段1
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from app.services.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)


class PDFEnhancedService:
    """
    PDF 增强服务
    🔥 支持WorkflowEngine DAG执行

    功能：
    1. PDF 文本提取
    2. PDF 元数据提取
    3. PDF 注释支持
    4. PDF 预览生成
    """

    def __init__(self, use_workflow_engine: bool = True):
        self._init_pdf_library()
        self.use_workflow_engine = use_workflow_engine  # 🔥 新增

        # 🔥 初始化WorkflowEngine
        if use_workflow_engine:
            self.workflow_engine = WorkflowEngine(max_workers=4)

    def _init_pdf_library(self):
        """初始化 PDF 库"""
        try:
            import PyPDF2
            self.pdf_lib = PyPDF2
            self.has_pypdf = True
        except ImportError:
            logger.warning("PyPDF2 未安装")
            self.has_pypdf = False

    def extract_text(self, pdf_path: str) -> str:
        """提取 PDF 文本"""
        if not self.has_pypdf:
            return self._fallback_extract(pdf_path)

        try:
            with open(pdf_path, 'rb') as f:
                reader = self.pdf_lib.PdfReader(f)
                text_parts = []

                for page in reader.pages:
                    text_parts.append(page.extract_text())

                return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"PDF 提取失败: {e}")
            return ""

    def process_pdf(
        self,
        pdf_path: str,
        extract_text: bool = True,
        extract_metadata: bool = True,
        extract_images: bool = False,
        use_workflow_engine: bool = None
    ) -> Dict[str, Any]:
        """
        🔥 完整处理PDF文件

        Args:
            pdf_path: PDF文件路径
            extract_text: 是否提取文本
            extract_metadata: 是否提取元数据
            extract_images: 是否提取图片
            use_workflow_engine: 是否使用WorkflowEngine（默认使用初始化配置）

        Returns:
            处理结果字典
        """
        if use_workflow_engine is None:
            use_workflow_engine = self.use_workflow_engine

        if use_workflow_engine:
            return self._process_with_workflow_engine(
                pdf_path=pdf_path,
                extract_text=extract_text,
                extract_metadata=extract_metadata,
                extract_images=extract_images
            )
        else:
            return self._process_traditional(
                pdf_path=pdf_path,
                extract_text=extract_text,
                extract_metadata=extract_metadata,
                extract_images=extract_images
            )

    def _process_with_workflow_engine(
        self,
        pdf_path: str,
        extract_text: bool,
        extract_metadata: bool,
        extract_images: bool
    ) -> Dict[str, Any]:
        """
        🔥 使用WorkflowEngine处理PDF（DAG模式）
        """
        logger.info(f"🔥 [WorkflowEngine] 开始处理PDF: {pdf_path}")

        # 创建工作流
        workflow = self.workflow_engine.create_workflow(
            name=f"pdf_processing_{Path(pdf_path).stem}",
            description=f"PDF处理流水线 - {pdf_path}"
        )

        # 🔥 Task 1: 验证PDF文件
        self.workflow_engine.add_task(
            workflow,
            name="validate",
            func=self._task_validate_pdf,
            kwargs={'pdf_path': pdf_path},
            dependencies=[]
        )

        # 🔥 Task 2: 提取元数据（可与文本提取并行）
        if extract_metadata:
            self.workflow_engine.add_task(
                workflow,
                name="metadata",
                func=self._task_extract_metadata,
                kwargs={'pdf_path': pdf_path},
                dependencies=["validate"]
            )

        # 🔥 Task 3: 提取文本（可与元数据提取并行）
        if extract_text:
            self.workflow_engine.add_task(
                workflow,
                name="text",
                func=self._task_extract_text,
                kwargs={'pdf_path': pdf_path},
                dependencies=["validate"]
            )

        # 🔥 Task 4: 提取图片（依赖验证）
        if extract_images:
            self.workflow_engine.add_task(
                workflow,
                name="images",
                func=self._task_extract_images,
                kwargs={'pdf_path': pdf_path},
                dependencies=["validate"]
            )

        # 🔥 Task 5: 汇总结果
        self.workflow_engine.add_task(
            workflow,
            name="finalize",
            func=self._task_finalize_results,
            kwargs={
                'pdf_path': pdf_path,
                'metadata': '$metadata' if extract_metadata else None,
                'text': '$text.text' if extract_text else None,
                'images': '$images.images' if extract_images else None
            },
            dependencies=[
                dep for dep in ["validate", "metadata", "text", "images"]
                if (dep == "validate" or
                    (dep == "metadata" and extract_metadata) or
                    (dep == "text" and extract_text) or
                    (dep == "images" and extract_images))
            ]
        )

        # 执行工作流
        results = self.workflow_engine.execute(workflow)

        logger.info(f"✅ [WorkflowEngine] PDF处理完成: {pdf_path}")
        return results['finalize']

    def _process_traditional(
        self,
        pdf_path: str,
        extract_text: bool,
        extract_metadata: bool,
        extract_images: bool
    ) -> Dict[str, Any]:
        """
        传统顺序处理模式（向后兼容）
        """
        logger.info(f"📝 [传统模式] 开始处理PDF: {pdf_path}")

        result = {
            'pdf_path': pdf_path,
            'success': True
        }

        try:
            # 验证文件
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

            # 提取元数据
            if extract_metadata:
                result['metadata'] = self.extract_metadata(pdf_path)

            # 提取文本
            if extract_text:
                result['text'] = self.extract_text(pdf_path)

            # 提取图片
            if extract_images:
                result['images'] = self._extract_images(pdf_path)

            logger.info(f"✅ [传统模式] PDF处理完成: {pdf_path}")
            return result

        except Exception as e:
            logger.error(f"❌ PDF处理失败: {e}")
            result['success'] = False
            result['error'] = str(e)
            return result

    # ========================================
    # 🔥 WorkflowEngine Task Functions
    # ========================================

    def _task_validate_pdf(self, pdf_path: str, _context: dict) -> dict:
        """
        🔥 Task 1: 验证PDF文件
        """
        logger.info(f"  [Task] validate: {pdf_path}")

        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        if not path.suffix.lower() == '.pdf':
            raise ValueError(f"不是PDF文件: {pdf_path}")

        file_size = path.stat().st_size

        logger.info(f"  ✅ validate: PDF文件有效，大小 {file_size} 字节")
        return {
            'valid': True,
            'file_size': file_size,
            'file_name': path.name
        }

    def _task_extract_metadata(self, pdf_path: str, _context: dict) -> dict:
        """
        🔥 Task 2: 提取PDF元数据
        """
        logger.info(f"  [Task] metadata: 提取元数据")

        metadata = self.extract_metadata(pdf_path)

        logger.info(f"  ✅ metadata: 提取完成，共 {metadata.get('num_pages', 0)} 页")
        return metadata

    def _task_extract_text(self, pdf_path: str, _context: dict) -> dict:
        """
        🔥 Task 3: 提取PDF文本
        """
        logger.info(f"  [Task] text: 提取文本")

        text = self.extract_text(pdf_path)
        text_length = len(text)

        logger.info(f"  ✅ text: 提取完成，共 {text_length} 字符")
        return {
            'text': text,
            'length': text_length
        }

    def _task_extract_images(self, pdf_path: str, _context: dict) -> dict:
        """
        🔥 Task 4: 提取PDF图片
        """
        logger.info(f"  [Task] images: 提取图片")

        images = self._extract_images(pdf_path)

        logger.info(f"  ✅ images: 提取完成，共 {len(images)} 张图片")
        return {
            'images': images,
            'count': len(images)
        }

    def _task_finalize_results(self, pdf_path: str, metadata, text, images, _context: dict) -> dict:
        """
        🔥 Task 5: 汇总结果
        """
        logger.info(f"  [Task] finalize: 汇总结果")

        result = {
            'pdf_path': pdf_path,
            'success': True
        }

        if metadata is not None:
            result['metadata'] = metadata

        if text is not None:
            result['text'] = text

        if images is not None:
            result['images'] = images

        logger.info(f"  ✅ finalize: 结果汇总完成")
        return result

    def _extract_images(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        提取PDF中的图片（占位实现）
        """
        # TODO: 实现图片提取逻辑
        logger.info(f"图片提取功能尚未实现: {pdf_path}")
        return []

    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """提取 PDF 元数据"""
        if not self.has_pypdf:
            return {}

        try:
            with open(pdf_path, 'rb') as f:
                reader = self.pdf_lib.PdfReader(f)

                metadata = {
                    "num_pages": len(reader.pages),
                    "title": reader.metadata.title if reader.metadata else None,
                    "author": reader.metadata.author if reader.metadata else None,
                    "subject": reader.metadata.subject if reader.metadata else None,
                    "creator": reader.metadata.creator if reader.metadata else None,
                }

                return metadata

        except Exception as e:
            logger.error(f"元数据提取失败: {e}")
            return {}

    def _fallback_extract(self, pdf_path: str) -> str:
        """备用提取方法"""
        from app.services.markitdown_converter import enhanced_converter
        return enhanced_converter.convert(pdf_path) or ""

    def get_page_count(self, pdf_path: str) -> int:
        """获取页数"""
        metadata = self.extract_metadata(pdf_path)
        return metadata.get("num_pages", 0)


# 全局实例
pdf_service = PDFEnhancedService()
