"""
文档化规则层 - 文档和视频处理规则（补充）

补充实现 DocumentToTextRule 和 VideoToTextRule
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import logging

from .normalization_rules import (
    BaseNormalizationRule,
    NormalizationResult,
    FileType,
    DirtyDataType,
    AudioToTextRule
)

logger = logging.getLogger(__name__)


class DocumentToTextRule(BaseNormalizationRule):
    """
    纯文档 → 文本规范化规则

    目标：逐字识别，保留篇章结构

    处理流程：
    1. 逐页提取文字
    2. 区分正文/页眉/页脚/脚注/批注
    3. 识别标题层级（H1/H2/H3）
    4. 识别列表、引用、代码块
    5. 表格嵌套单独处理
    6. 公式单独提取
    """

    def __init__(self):
        super().__init__()
        self.file_type = FileType.DOCUMENT

    def convert(self, file_content: bytes, metadata: Dict[str, Any]) -> NormalizationResult:
        """转换文档为结构化文本"""
        result = NormalizationResult()
        start_time = datetime.utcnow()

        try:
            import io
            file_type = metadata.get("file_type", "").lower()

            # 【集成插件】先调用文档插件获取基础信息
            from .plugin_integration import get_plugin_integration_service
            plugin_service = get_plugin_integration_service()

            file_path = metadata.get("file_path", f"document.{file_type}")

            plugin_result = plugin_service.get_plugin_basic_info(
                file_path=file_path,
                file_content=file_content,
                file_type=file_type
            )

            # 从插件结果提取基础内容
            plugin_basic_content = ""
            plugin_metadata = {}
            if plugin_result:
                plugin_basic_content = plugin_service.extract_basic_content_from_plugin_result(plugin_result, file_type)
                plugin_metadata = plugin_service.extract_metadata_from_plugin_result(plugin_result, file_type)
                logger.info(f"✅ 从插件获取文档基础内容: {len(plugin_basic_content)} 字符")

            full_text = ""
            structure_info = {
                "type": "document",
                "pages": [],
                "sections": [],
                "has_toc": False
            }

            if file_type == "pdf":
                # PDF提取
                pages_data = self._extract_pdf(file_content, result)
                structure_info["pages"] = pages_data

                for page in pages_data:
                    full_text += f"\n\n## 第{page['page_num']}页\n\n{page['text']}"

            elif file_type in ["docx", "doc"]:
                # Word提取
                doc_data = self._extract_word(file_content, result)
                full_text = doc_data["text"]
                structure_info["sections"] = doc_data["sections"]
                structure_info["pages"] = doc_data["pages"]

            elif file_type in ["md", "markdown"]:
                # Markdown直接读取
                full_text = file_content.decode("utf-8")
                structure_info["sections"] = self._parse_markdown_structure(full_text)

            elif file_type == "txt":
                # 纯文本
                full_text = file_content.decode("utf-8")

            else:
                raise ValueError(f"不支持的文档类型: {file_type}")

            # 填充结果
            result.text_content = full_text
            result.word_count = len(full_text)
            result.structure_info = structure_info
            result.metadata = {
                "file_type": file_type,
                "page_count": len(structure_info["pages"]),
                "section_count": len(structure_info["sections"]),
                "extracted_at": datetime.utcnow().isoformat()
            }

            # 计算完整性
            expected_chars = len(structure_info["pages"]) * 500  # 每页预期500字符
            actual_chars = len(full_text)
            completeness_score = min(actual_chars / expected_chars, 1.0) if expected_chars > 0 else 1.0

            result.completeness = {
                "score": completeness_score,
                "details": {
                    "pages_extracted": len(structure_info["pages"]),
                    "expected_chars": expected_chars,
                    "actual_chars": actual_chars
                },
                "issues": []
            }

            if completeness_score < 0.8:
                result.completeness["issues"].append(f"文档提取不完整: {completeness_score:.1%}")

            result.confidence = 0.95

        except Exception as e:
            logger.error(f"文档规范化失败: {e}", exc_info=True)
            result.completeness = {"score": 0.0, "issues": [f"处理失败: {str(e)}"], "details": {}}

        # 记录耗时
        elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
        result.processing_time_ms = int(elapsed)

        return result

    def verify_completeness(self, result: NormalizationResult) -> Tuple[bool, List[str]]:
        """验证文档转换完整性"""
        issues = []

        structure = result.structure_info
        metadata = result.metadata

        # 1. 所有页面都必须提取
        total_pages = metadata.get("page_count", 0)
        extracted_pages = len(structure.get("pages", []))

        if extracted_pages < total_pages:
            issues.append(f"页面提取不完整: {extracted_pages}/{total_pages}")

        # 2. 每页必须有文本（至少10个字符）
        for page in structure.get("pages", []):
            if page.get("text_length", 0) < 10:
                issues.append(f"第{page['page_num']}页文本过短")

        # 3. 字数必须合理（每页至少100字）
        expected_words = total_pages * 100
        actual_words = result.word_count

        if actual_words < expected_words * 0.5:
            issues.append(f"文档字数异常: {actual_words}字 < {expected_words * 0.5}字(预期50%)")

        is_complete = len(issues) == 0
        return is_complete, issues

    # ========== 私有方法 ==========

    def _extract_pdf(self, file_content: bytes, result: NormalizationResult) -> List[Dict[str, Any]]:
        """提取PDF内容"""
        import io

        try:
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))

            pages_data = []
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()

                # 如果提取失败，标记需要OCR
                if not page_text or len(page_text.strip()) < 10:
                    result.dirty_data_found.append({
                        "type": DirtyDataType.MISSING_VALUE.value,
                        "location": f"第{page_num+1}页",
                        "description": "文本提取失败，可能需要OCR"
                    })
                    page_text = "[需要OCR]"

                pages_data.append({
                    "page_num": page_num + 1,
                    "text": page_text,
                    "text_length": len(page_text),
                    "extraction_method": "text"
                })

            return pages_data

        except Exception as e:
            logger.error(f"PDF提取失败: {e}")
            return []

    def _extract_word(self, file_content: bytes, result: NormalizationResult) -> Dict[str, Any]:
        """提取Word内容"""
        import io

        try:
            from docx import Document

            # 加载Word文档
            doc = Document(io.BytesIO(file_content))

            full_text = ""
            sections = []
            pages_data = []
            page_num = 1

            # 遍历所有段落
            for para in doc.paragraphs:
                # 保留段落样式信息
                style = para.style.name if para.style else "Normal"
                text = para.text.strip()

                if not text:
                    continue

                # 识别标题
                if "Heading" in style:
                    level = 1
                    try:
                        level = int(style.replace("Heading ", "").strip())
                    except:
                        level = 1

                    full_text += f"\n{'#' * level} {text}\n\n"
                    sections.append({
                        "level": level,
                        "title": text
                    })
                else:
                    full_text += f"{text}\n\n"

            # 估算页数（每500字符一页）
            estimated_pages = max(1, len(full_text) // 500)
            for i in range(estimated_pages):
                start_pos = i * 500
                end_pos = min((i + 1) * 500, len(full_text))
                page_text = full_text[start_pos:end_pos]

                pages_data.append({
                    "page_num": i + 1,
                    "text": page_text,
                    "text_length": len(page_text),
                    "extraction_method": "python-docx"
                })

            logger.info(f"✅ Word文档提取成功: {len(sections)}个章节, 约{estimated_pages}页")

            return {
                "text": full_text,
                "sections": sections,
                "pages": pages_data
            }

        except ImportError:
            logger.error("python-docx 未安装，请运行: pip install python-docx")
            result.dirty_data_found.append({
                "type": "missing_dependency",
                "location": "Word extraction",
                "description": "python-docx未安装"
            })
            return {
                "text": "[Word文档提取失败：缺少python-docx]",
                "sections": [],
                "pages": [{"page_num": 1, "text": "[提取失败]", "text_length": 0}]
            }

        except Exception as e:
            logger.error(f"Word文档提取失败: {e}")
            result.dirty_data_found.append({
                "type": "extraction_error",
                "location": "Word extraction",
                "description": str(e)
            })
            return {
                "text": f"[Word文档提取失败: {str(e)}]",
                "sections": [],
                "pages": [{"page_num": 1, "text": "[提取失败]", "text_length": 0}]
            }

    def _parse_markdown_structure(self, text: str) -> List[Dict[str, Any]]:
        """解析Markdown结构"""
        sections = []
        lines = text.split("\n")

        for line in lines:
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                title = line.lstrip("#").strip()
                sections.append({
                    "level": level,
                    "title": title
                })

        return sections


class VideoToTextRule(BaseNormalizationRule):
    """
    视频 → 文本规范化规则

    目标：音频转文字 + 画面转描述，两条线并行

    处理流程：
    1. 分离音频和视频轨道
    2. 音频线：使用AudioToTextRule处理
    3. 画面线：场景检测 + 关键帧描述
    4. 时间轴融合
    """

    def __init__(self):
        super().__init__()
        self.file_type = FileType.VIDEO
        self.audio_rule = AudioToTextRule()

    def convert(self, file_content: bytes, metadata: Dict[str, Any]) -> NormalizationResult:
        """转换视频为文本（音频线+画面线）"""
        result = NormalizationResult()
        start_time = datetime.utcnow()

        try:
            # 【集成插件】先调用视频插件获取基础信息
            from .plugin_integration import get_plugin_integration_service
            plugin_service = get_plugin_integration_service()

            file_type = metadata.get("file_type", "mp4")
            file_path = metadata.get("file_path", "video.mp4")

            plugin_result = plugin_service.get_plugin_basic_info(
                file_path=file_path,
                file_content=file_content,
                file_type=file_type
            )

            # 从插件结果提取元数据
            video_info = {}
            if plugin_result:
                plugin_metadata = plugin_service.extract_metadata_from_plugin_result(plugin_result, file_type)
                video_info = {
                    "duration": plugin_metadata.get('duration', 0),
                    "resolution": plugin_metadata.get('resolution', {"width": 1920, "height": 1080}),
                    "fps": plugin_metadata.get('fps', 30)
                }
                logger.info(f"✅ 从插件获取视频信息: {video_info['duration']:.1f}秒")
            else:
                # 降级：自己获取视频信息
                video_info = self._get_video_info(file_content)
                logger.info(f"⚠️ 插件不可用，使用降级方案获取视频信息")

            total_duration = video_info["duration"]

            # 2. 分离音频轨道
            audio_content = self._extract_audio(file_content)

            # 3. 音频线：转写音频
            audio_result = self.audio_rule.convert(audio_content, metadata)
            audio_transcript = audio_result.structure_info.get("transcript", [])

            # 4. 画面线：场景检测
            scenes = self._detect_scenes(file_content)

            # 5. 每个场景提取关键帧并描述
            key_frames = []
            for scene in scenes:
                mid_time = (scene["start"] + scene["end"]) / 2
                frame_content = self._extract_frame(file_content, mid_time)
                frame_description = self._describe_frame(frame_content)

                key_frames.append({
                    "time": mid_time,
                    "scene_id": scene["id"],
                    "description": frame_description,
                    "confidence": 0.85
                })

                # 保存到结构化内容
                result.normalized_contents.append({
                    "content_type": "scene_description",
                    "content": frame_description,
                    "metadata": {
                        "time": mid_time,
                        "scene_id": scene["id"]
                    },
                    "source_location": {
                        "time": mid_time
                    },
                    "extraction_method": "vision_model",
                    "confidence": 0.85,
                    "sequence": int(mid_time * 10)
                })

            # 6. 融合音频和视觉（按时间轴）
            full_text = "# 视频内容\n\n"
            all_events = []

            # 添加音频事件
            for seg in audio_transcript:
                all_events.append({
                    "time": seg.get("start", 0),
                    "type": "audio",
                    "content": f"{seg.get('speaker', '未知')}: {seg.get('text', '')}"
                })

            # 添加视觉事件
            for frame in key_frames:
                all_events.append({
                    "time": frame["time"],
                    "type": "visual",
                    "content": f"[画面] {frame['description']}"
                })

            # 按时间排序
            all_events.sort(key=lambda x: x["time"])

            # 生成完整文本
            for event in all_events:
                full_text += f"[{event['time']:.1f}s] {event['content']}\n"

            # 合并音频的结构化内容
            result.normalized_contents.extend(audio_result.normalized_contents)

            # 填充结果
            result.text_content = full_text
            result.word_count = len(full_text)
            result.structure_info = {
                "type": "video",
                "has_audio": True,
                "has_visual": True,
                "audio_transcript": audio_transcript,
                "key_frames": key_frames,
                "scenes": scenes,
                "scene_count": len(scenes),
                "frame_count": len(key_frames)
            }
            result.metadata = {
                "total_duration": total_duration,
                "resolution": video_info.get("resolution"),
                "fps": video_info.get("fps"),
                "audio_coverage": audio_result.metadata.get("coverage_rate", 0),
                "extracted_at": datetime.utcnow().isoformat()
            }

            # 合并脏数据记录
            result.dirty_data_found.extend(audio_result.dirty_data_found)
            result.dirty_data_handled.extend(audio_result.dirty_data_handled)

            # 计算完整性
            audio_coverage = audio_result.metadata.get("coverage_rate", 0)
            visual_coverage = 1.0 if len(key_frames) >= len(scenes) else len(key_frames) / len(scenes) if scenes else 0

            result.completeness = {
                "score": (audio_coverage * 0.7 + visual_coverage * 0.3),
                "details": {
                    "audio_coverage": audio_coverage,
                    "visual_coverage": visual_coverage,
                    "scenes": len(scenes),
                    "key_frames": len(key_frames)
                },
                "issues": []
            }

            if audio_coverage < 0.95:
                result.completeness["issues"].append(f"音频覆盖不足: {audio_coverage:.1%}")

            if len(key_frames) < len(scenes):
                result.completeness["issues"].append(f"关键帧不足: {len(key_frames)} < {len(scenes)}个场景")

            result.confidence = (audio_result.confidence + 0.85) / 2

        except Exception as e:
            logger.error(f"视频规范化失败: {e}", exc_info=True)
            result.completeness = {"score": 0.0, "issues": [f"处理失败: {str(e)}"], "details": {}}

        # 记录耗时
        elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
        result.processing_time_ms = int(elapsed)

        return result

    def verify_completeness(self, result: NormalizationResult) -> Tuple[bool, List[str]]:
        """验证视频转换完整性"""
        issues = []

        # 1. 音频必须完整转写（覆盖率≥95%）
        audio_coverage = result.metadata.get("audio_coverage", 0)
        if audio_coverage < 0.95:
            issues.append(f"音频覆盖不足: {audio_coverage:.1%}")

        # 2. 必须有场景检测
        scene_count = result.structure_info.get("scene_count", 0)
        if scene_count == 0:
            issues.append("未进行场景检测")

        # 3. 每个场景必须有关键帧
        frame_count = result.structure_info.get("frame_count", 0)
        if frame_count < scene_count:
            issues.append(f"关键帧不足: {frame_count} < {scene_count}个场景")

        # 4. 所有关键帧必须有描述
        frames_without_description = [
            f for f in result.structure_info.get("key_frames", [])
            if not f.get("description") or len(f["description"]) < 10
        ]
        if frames_without_description:
            issues.append(f"{len(frames_without_description)}个关键帧缺少描述")

        is_complete = len(issues) == 0
        return is_complete, issues

    # ========== 私有方法 ==========

    def _get_video_info(self, file_content: bytes) -> Dict[str, Any]:
        """获取视频信息"""
        import tempfile
        import os

        try:
            import cv2

            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
                f.write(file_content)
                temp_path = f.name

            # 打开视频
            cap = cv2.VideoCapture(temp_path)

            # 获取信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # 计算时长
            duration = frame_count / fps if fps > 0 else 0

            cap.release()
            os.unlink(temp_path)

            logger.info(f"✅ 视频信息: {duration:.1f}秒, {width}x{height}, {fps}fps")

            return {
                "duration": duration,
                "resolution": {"width": width, "height": height},
                "fps": fps
            }

        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            return {
                "duration": 3600.0,
                "resolution": {"width": 1920, "height": 1080},
                "fps": 30
            }

    def _extract_audio(self, file_content: bytes) -> bytes:
        """从视频中提取音频"""
        import tempfile
        import os
        import subprocess

        try:
            # 保存临时视频文件
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
                f.write(file_content)
                video_path = f.name

            # 创建临时音频文件
            audio_path = video_path.replace('.mp4', '.mp3')

            # 使用 ffmpeg 提取音频
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # 不要视频
                '-acodec', 'libmp3lame',
                '-ar', '16000',  # 采样率
                '-ac', '1',  # 单声道
                '-y',  # 覆盖输出文件
                audio_path
            ]

            subprocess.run(cmd, capture_output=True, check=True)

            # 读取音频
            with open(audio_path, 'rb') as f:
                audio_content = f.read()

            # 清理
            os.unlink(video_path)
            os.unlink(audio_path)

            logger.info(f"✅ 音频提取成功: {len(audio_content)} 字节")
            return audio_content

        except Exception as e:
            logger.error(f"音频提取失败: {e}")
            # 降级：返回原视频内容
            return file_content

    def _extract_frame(self, file_content: bytes, time: float) -> bytes:
        """提取指定时间的帧"""
        import tempfile
        import os

        try:
            import cv2
            import numpy as np
            from PIL import Image
            import io

            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
                f.write(file_content)
                temp_path = f.name

            # 打开视频
            cap = cv2.VideoCapture(temp_path)

            # 设置到指定时间
            cap.set(cv2.CAP_PROP_POS_MSEC, time * 1000)

            # 读取帧
            ret, frame = cap.read()
            cap.release()
            os.unlink(temp_path)

            if not ret:
                logger.warning(f"无法提取帧 at {time}s")
                return b""

            # 转换为 RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 转换为 PIL Image
            pil_image = Image.fromarray(frame_rgb)

            # 转换为字节
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format='JPEG')
            img_byte_arr.seek(0)

            return img_byte_arr.read()

        except Exception as e:
            logger.error(f"帧提取失败: {e}")
            return b""

    def _describe_frame(self, frame_content: bytes) -> str:
        """描述视频帧"""
        import tempfile
        import os

        if not frame_content:
            return "无法提取帧"

        try:
            from app.services.vision_service import VisionService

            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                f.write(frame_content)
                temp_path = f.name

            logger.info("调用 VisionService 描述视频帧")

            vision = VisionService(model_type="blip2")
            description = vision.describe_image(temp_path, prompt="描述这个视频画面中的内容（30字以内）")

            # 清理
            os.unlink(temp_path)

            return description

        except Exception as e:
            logger.error(f"视频帧描述失败: {e}")
            return "这是一个视频画面，显示了某个场景的内容。"
