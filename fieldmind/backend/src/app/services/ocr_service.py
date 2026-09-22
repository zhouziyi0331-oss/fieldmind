"""
OCR 服务 - 基于 PaddleOCR

核心功能：
1. 图片文字识别（支持中英文）
2. 扫描 PDF 文字提取
3. 表格图片识别
4. 版面分析

技术栈：
- PaddleOCR：百度开源 OCR 引擎
- 支持 80+ 语言
- CPU 可运行
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class OCRService:
    """OCR 服务 - PaddleOCR 实现"""

    def __init__(self):
        """初始化 OCR 引擎"""
        self.ocr = None
        self._init_ocr()

    def _init_ocr(self):
        """延迟初始化 PaddleOCR"""
        try:
            from paddleocr import PaddleOCR

            logger.info("🔧 初始化 PaddleOCR...")

            # 配置参数
            self.ocr = PaddleOCR(
                use_angle_cls=True,      # 启用方向分类器（处理旋转图片）
                lang='ch'                # 中文模型（同时支持英文）
            )

            logger.info("✅ PaddleOCR 初始化成功")

        except ImportError:
            logger.warning("⚠️ PaddleOCR 未安装，请运行: pip install paddleocr")
            self.ocr = None
        except Exception as e:
            logger.error(f"❌ PaddleOCR 初始化失败: {e}")
            self.ocr = None

    def _rapid_ocr(self):
        """RapidOCR 轻量兜底，不依赖 PaddleOCR/Tesseract。"""
        try:
            from rapidocr_onnxruntime import RapidOCR
            return RapidOCR()
        except Exception as e:
            logger.warning(f"RapidOCR 不可用: {e}")
            return None

    def extract_text_from_image(
        self,
        image_path: str,
        return_confidence: bool = True,
        return_boxes: bool = False
    ) -> Dict[str, Any]:
        """
        从图片中提取文字

        Args:
            image_path: 图片路径
            return_confidence: 是否返回置信度
            return_boxes: 是否返回文字位置框

        Returns:
            {
                "text": "完整文本",
                "lines": [
                    {"text": "第一行", "confidence": 0.98, "box": [[x1,y1], [x2,y2], ...]},
                    ...
                ],
                "method": "paddleocr",
                "language": "ch"
            }
        """
        if not self.ocr:
            rapid = self._rapid_ocr()
            if rapid is None:
                logger.warning("OCR 引擎未初始化")
                return {
                    "text": "",
                    "lines": [],
                    "method": "none",
                    "error": "OCR engine not initialized"
                }
            logger.info("📷 使用 RapidOCR 识别图片...")
            try:
                result, _ = rapid(image_path)
                lines = []
                texts = []
                for item in result or []:
                    try:
                        box, text, confidence = item
                        text = str(text).strip()
                        if not text:
                            continue
                        texts.append(text)
                        line_data = {"text": text, "confidence": round(float(confidence), 4)}
                        if return_boxes:
                            line_data["box"] = box
                        lines.append(line_data)
                    except Exception:
                        continue
                full_text = "\n".join(texts)
                avg_confidence = sum(l.get("confidence", 0) for l in lines) / len(lines) if lines else 0
                return {
                    "text": full_text,
                    "lines": lines,
                    "method": "rapidocr_onnxruntime",
                    "language": "ch",
                    "statistics": {
                        "line_count": len(lines),
                        "char_count": len(full_text),
                        "avg_confidence": round(avg_confidence, 4)
                    }
                }
            except Exception as e:
                logger.error(f"RapidOCR 识别失败: {e}")
                return {
                    "text": "",
                    "lines": [],
                    "method": "rapidocr_onnxruntime",
                    "error": str(e)
                }

        try:
            logger.info(f"📷 OCR 识别图片: {Path(image_path).name}")

            # 执行 OCR（不使用 cls 参数）
            result = self.ocr.ocr(image_path)

            if not result or len(result) == 0:
                logger.warning("OCR 未识别到文字")
                return {
                    "text": "",
                    "lines": [],
                    "method": "paddleocr"
                }

            # 解析结果（适配新版 PaddleOCR API）
            lines = []
            texts = []

            # 新版本返回 OCRResult 对象
            ocr_result = result[0]

            # 检查是否有 rec_texts 和 rec_scores
            if hasattr(ocr_result, 'get') and 'rec_texts' in ocr_result:
                rec_texts = ocr_result['rec_texts']
                rec_scores = ocr_result.get('rec_scores', [])

                for i, text in enumerate(rec_texts):
                    texts.append(text)

                    line_data = {"text": text}

                    if return_confidence and i < len(rec_scores):
                        line_data["confidence"] = round(float(rec_scores[i]), 4)

                    lines.append(line_data)

            # 兼容旧版本格式
            elif isinstance(ocr_result, list):
                for line in ocr_result:
                    try:
                        box = line[0]
                        text = line[1][0]
                        confidence = line[1][1]

                        texts.append(text)

                        line_data = {"text": text}

                        if return_confidence:
                            line_data["confidence"] = round(confidence, 4)

                        if return_boxes:
                            line_data["box"] = box

                        lines.append(line_data)
                    except (IndexError, TypeError) as e:
                        logger.warning(f"解析 OCR 结果失败: {e}")
                        continue

            full_text = "\n".join(texts)

            # 统计
            avg_confidence = sum(l.get("confidence", 0) for l in lines) / len(lines) if lines else 0

            logger.info(f"✅ OCR 完成: {len(lines)} 行, 平均置信度: {avg_confidence:.2f}")

            return {
                "text": full_text,
                "lines": lines,
                "method": "paddleocr",
                "language": "ch",
                "statistics": {
                    "line_count": len(lines),
                    "char_count": len(full_text),
                    "avg_confidence": round(avg_confidence, 4)
                }
            }

        except Exception as e:
            logger.error(f"❌ OCR 识别失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())

            return {
                "text": "",
                "lines": [],
                "method": "paddleocr",
                "error": str(e)
            }

    def extract_text_from_pdf(
        self,
        pdf_path: str,
        page_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        从扫描 PDF 中提取文字

        Args:
            pdf_path: PDF 路径
            page_range: 页码范围 (start, end)，None 表示全部页

        Returns:
            {
                "text": "完整文本",
                "pages": [
                    {"page": 1, "text": "...", "confidence": 0.95},
                    ...
                ],
                "method": "paddleocr_pdf"
            }
        """
        try:
            # 将 PDF 转换为图片
            from pdf2image import convert_from_path

            logger.info(f"📄 转换 PDF 为图片: {Path(pdf_path).name}")

            # 转换参数
            images = convert_from_path(
                pdf_path,
                dpi=200,  # 分辨率
                first_page=page_range[0] if page_range else None,
                last_page=page_range[1] if page_range else None
            )

            logger.info(f"✅ 转换完成: {len(images)} 页")

            # 逐页 OCR
            pages = []
            all_texts = []

            for i, image in enumerate(images):
                page_num = (page_range[0] if page_range else 1) + i

                logger.info(f"🔍 识别第 {page_num} 页...")

                # 保存为临时图片
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp_path = tmp.name
                    image.save(tmp_path, 'PNG')

                try:
                    # OCR 识别
                    ocr_result = self.extract_text_from_image(tmp_path, return_confidence=True)

                    page_text = ocr_result.get("text", "")
                    all_texts.append(page_text)

                    pages.append({
                        "page": page_num,
                        "text": page_text,
                        "line_count": len(ocr_result.get("lines", [])),
                        "confidence": ocr_result.get("statistics", {}).get("avg_confidence", 0)
                    })

                finally:
                    # 删除临时文件
                    import os
                    os.unlink(tmp_path)

            full_text = "\n\n".join(all_texts)

            logger.info(f"✅ PDF OCR 完成: {len(pages)} 页")

            return {
                "text": full_text,
                "pages": pages,
                "method": "pdf_ocr",
                "statistics": {
                    "page_count": len(pages),
                    "total_chars": len(full_text)
                }
            }

        except ImportError:
            logger.error("❌ pdf2image 未安装，请运行: pip install pdf2image")
            return {
                "text": "",
                "pages": [],
                "error": "pdf2image not installed"
            }
        except Exception as e:
            logger.error(f"❌ PDF OCR 失败: {e}")
            return {
                "text": "",
                "pages": [],
                "error": str(e)
            }

    def extract_table_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        从图片中提取表格（使用 PaddleOCR 的表格识别）

        Args:
            image_path: 图片路径

        Returns:
            {
                "text": "表格文本",
                "table_structure": {...},
                "method": "paddleocr_table"
            }
        """
        # 注：PaddleOCR 的表格识别需要额外的模型
        # 这里先用基础 OCR，未来可以升级
        logger.info("⚠️ 表格识别功能需要额外模型，当前使用基础 OCR")
        return self.extract_text_from_image(image_path)


# 全局单例
_ocr_service = None


def get_ocr_service() -> OCRService:
    """获取 OCR 服务单例"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service


if __name__ == "__main__":
    # 测试代码
    print("=" * 80)
    print("🧪 OCR 服务测试")
    print("=" * 80)

    service = get_ocr_service()

    if service.ocr:
        print("✅ OCR 引擎初始化成功")
        print("\n使用示例:")
        print("""
# 识别图片
result = ocr_service.extract_text_from_image("test.png")
print(result["text"])

# 识别扫描 PDF
result = ocr_service.extract_text_from_pdf("scan.pdf")
print(result["text"])
        """)
    else:
        print("❌ OCR 引擎未初始化")
        print("请安装: pip install paddleocr")
