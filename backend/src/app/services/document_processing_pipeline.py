"""
完整的文档处理流水线
清洗 → 切分 → 向量化 → 入库
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import re

from app.services.document_converter import DocumentConverter
from app.services.document_chunker import DocumentChunker
from app.services.vectorization_service_complete import VectorizationService, DocumentChunk
from app.services.knowledge_graph_service import get_knowledge_graph_service
from app.models.project import ProjectDocument

logger = logging.getLogger(__name__)

# 全局单例：确保整个应用只有一个VectorizationService实例
_global_vectorizer = None

def get_vectorization_service():
    """获取全局VectorizationService单例"""
    global _global_vectorizer
    if _global_vectorizer is None:
        _global_vectorizer = VectorizationService()
    return _global_vectorizer


class DocumentProcessingPipeline:
    """文档处理流水线 - 完整的6步处理（新增知识图谱构建）"""

    def __init__(self):
        self.converter = DocumentConverter()
        self.chunker = DocumentChunker(
            min_chunk_size=200,
            max_chunk_size=500,
            target_chunk_size=350
        )
        self.vectorizer = get_vectorization_service()  # 使用全局单例
        self.kg_service = get_knowledge_graph_service()  # 新增：知识图谱服务

    def process_document(
        self,
        document_id: int,
        file_path: str,
        project_id: int,
        db: Session,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        完整处理单个文档

        Args:
            document_id: 文档ID
            file_path: 文件路径
            project_id: 项目ID
            db: 数据库会话
            progress_callback: 进度回调函数 callback(stage, progress, message)

        Returns:
            处理结果统计
        """
        logger.info(f"开始处理文档 {document_id}: {file_path}")

        result = {
            "document_id": document_id,
            "stages": {},
            "success": False,
            "error": None
        }

        try:
            # 【阶段1】内容提取
            if progress_callback:
                progress_callback("extract", 0.1, "提取文档内容...")

            text_content, metadata = self._extract_content(file_path, document_id)
            result["stages"]["extract"] = {
                "success": True,
                "text_length": len(text_content),
                "metadata": metadata
            }

            if progress_callback:
                progress_callback("extract", 0.2, "内容提取完成")

            # 【阶段2】数据清洗
            if progress_callback:
                progress_callback("clean", 0.3, "清洗文本数据...")

            cleaned_text, clean_metadata = self._clean_text(text_content, metadata)
            result["stages"]["clean"] = {
                "success": True,
                "original_length": len(text_content),
                "cleaned_length": len(cleaned_text),
                "removed_chars": len(text_content) - len(cleaned_text)
            }

            if progress_callback:
                progress_callback("clean", 0.4, "数据清洗完成")

            # 【阶段2.5】插入fact_statements（新增）
            if progress_callback:
                progress_callback("fact_extraction", 0.45, "提取结构化事实...")

            fact_count = 0
            try:
                # 检查是否为音频/视频（有segments）
                if metadata.get('segments'):
                    fact_count = self._insert_fact_statements_from_segments(
                        metadata['segments'],
                        document_id,
                        project_id,
                        metadata.get('file_name', 'unknown'),
                        db
                    )
                else:
                    # 普通文本文档
                    fact_count = self._insert_fact_statements(
                        cleaned_text,
                        document_id,
                        project_id,
                        metadata.get('source_file', 'unknown'),
                        db
                    )
                logger.info(f"✅ 文档 {document_id} 插入了 {fact_count} 条fact_statements")

                if progress_callback:
                    progress_callback("fact_extraction", 0.5, f"提取了 {fact_count} 条事实")
            except Exception as e:
                logger.error(f"插入fact_statements失败: {e}")
                import traceback
                traceback.print_exc()
                # 不阻断流程，继续执行

            # 【阶段3】文档切分
            if progress_callback:
                progress_callback("chunk", 0.5, "切分文档...")

            chunks = self.chunker.chunk_document(cleaned_text, clean_metadata)
            result["stages"]["chunk"] = {
                "success": True,
                "total_chunks": len(chunks),
                "avg_chunk_size": sum(len(c["text"]) for c in chunks) // len(chunks) if chunks else 0
            }

            if progress_callback:
                progress_callback("chunk", 0.6, f"切分完成：{len(chunks)} 个chunks")

            # 【阶段4】向量化
            if progress_callback:
                progress_callback("vectorize", 0.7, "向量化文本...")

            vectorized_chunks = self.vectorizer.vectorize_chunks(chunks)
            result["stages"]["vectorize"] = {
                "success": True,
                "vectorized_chunks": len(vectorized_chunks),
                "embedding_model": self.vectorizer.model_name,
                "embedding_dim": self.vectorizer.embedding_dim
            }

            if progress_callback:
                progress_callback("vectorize", 0.8, "向量化完成")

            # 【阶段5】入库索引
            if progress_callback:
                progress_callback("index", 0.9, "存储到数据库...")

            saved_chunks = self.vectorizer.store_chunks(
                vectorized_chunks,
                document_id,
                project_id,
                db
            )

            result["stages"]["index"] = {
                "success": True,
                "stored_chunks": len(saved_chunks)
            }

            # 【阶段6】知识图谱构建（新增）
            if progress_callback:
                progress_callback("knowledge_graph", 0.92, "构建知识图谱...")

            try:
                entities, relations = self.kg_service.extract_entities_and_relations(
                    cleaned_text,
                    document_id=document_id,
                    use_llm=True  # 使用LLM增强
                )

                # 添加到图谱
                self.kg_service.add_entities_and_relations(entities, relations)

                result["stages"]["knowledge_graph"] = {
                    "success": True,
                    "entities_count": len(entities),
                    "relations_count": len(relations),
                    "entity_types": {},
                }

                # 统计实体类型
                entity_type_counts = {}
                for entity in entities:
                    entity_type_counts[entity.entity_type] = entity_type_counts.get(entity.entity_type, 0) + 1
                result["stages"]["knowledge_graph"]["entity_types"] = entity_type_counts

                logger.info(f"✅ 文档 {document_id} 知识图谱构建完成: {len(entities)}个实体, {len(relations)}个关系")

                if progress_callback:
                    progress_callback("knowledge_graph", 0.95, f"知识图谱构建完成: {len(entities)}个实体")

            except Exception as e:
                logger.warning(f"知识图谱构建失败（非致命）: {e}")
                result["stages"]["knowledge_graph"] = {
                    "success": False,
                    "error": str(e)
                }

            # 更新文档状态
            doc = db.query(ProjectDocument).filter(
                ProjectDocument.id == document_id
            ).first()

            if doc:
                doc.text_content = cleaned_text
                doc.chunk_count = len(chunks)
                doc.status = "completed"
                doc.processing_progress = 100
                doc.extra_data = doc.extra_data or {}
                doc.extra_data["processing_result"] = result["stages"]
                db.commit()

            if progress_callback:
                progress_callback("index", 1.0, "处理完成")

            result["success"] = True
            logger.info(f"文档 {document_id} 处理完成")

        except Exception as e:
            logger.error(f"文档 {document_id} 处理失败: {e}", exc_info=True)
            result["success"] = False
            result["error"] = str(e)

            # 更新文档为失败状态
            doc = db.query(ProjectDocument).filter(
                ProjectDocument.id == document_id
            ).first()
            if doc:
                doc.status = "failed"
                doc.error_message = str(e)
                db.commit()

        return result

    def _extract_content(
        self,
        file_path: str,
        document_id: int
    ) -> tuple[str, Dict[str, Any]]:
        """
        阶段1：内容提取
        支持文档和音频文件
        """
        from pathlib import Path

        file_extension = Path(file_path).suffix.lower()

        # 检查是否为音频文件
        if file_extension in ['.mp3', '.wav', '.m4a', '.flac', '.ogg']:
            logger.info(f"检测到音频文件: {file_path}")
            return self._extract_audio_content(file_path, document_id)

        # 检查是否为视频文件
        elif file_extension in ['.mp4', '.avi', '.mov', '.mkv']:
            logger.info(f"检测到视频文件: {file_path}")
            return self._extract_video_content(file_path, document_id)

        # 普通文档
        else:
            result = self.converter.convert_file(file_path)

            if not result:
                raise ValueError("内容提取失败")

            text = result.get("text_content", "")
            metadata = result.get("metadata", {})

            return text, metadata

    def _extract_audio_content(
        self,
        file_path: str,
        document_id: int
    ) -> tuple[str, Dict[str, Any]]:
        """
        提取音频内容 - 使用统一转录服务（Whisper或FunASR）
        返回完整文本 + segments元数据
        """
        from app.core.unified_transcription import transcription
        from pathlib import Path

        logger.info(f"🎤 开始音频转录: {file_path}")

        result = transcription.transcribe(file_path, language="zh")

        # 返回完整文本和segments
        text = result.get("text", "")
        metadata = {
            "file_name": Path(file_path).name,
            "file_extension": Path(file_path).suffix,
            "segments": result.get("segments", []),  # 保存segments用于后续处理
            "language": result.get("language", "zh"),
            "is_audio": True
        }

        logger.info(f"✅ 转录完成: {len(result.get('segments', []))} 个片段")

        return text, metadata

    def _extract_video_content(
        self,
        file_path: str,
        document_id: int
    ) -> tuple[str, Dict[str, Any]]:
        """
        提取视频内容 - 先提取音轨，再用Whisper转录
        """
        import subprocess
        import tempfile
        from pathlib import Path

        logger.info(f"提取视频音轨: {file_path}")

        # 创建临时音频文件
        temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_audio_path = temp_audio.name
        temp_audio.close()

        try:
            # 使用ffmpeg提取音轨
            cmd = [
                'ffmpeg', '-i', file_path,
                '-vn',  # 不处理视频
                '-acodec', 'pcm_s16le',  # 转为WAV格式
                '-ar', '16000',  # 采样率16kHz
                '-ac', '1',  # 单声道
                '-y',  # 覆盖输出文件
                temp_audio_path
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"音轨提取完成: {temp_audio_path}")

            # 调用音频处理
            text, metadata = self._extract_audio_content(temp_audio_path, document_id)

            # 更新metadata标记为视频
            metadata["original_file"] = Path(file_path).name
            metadata["is_video"] = True

            return text, metadata

        finally:
            # 清理临时文件
            import os
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)

    def _clean_text(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """
        阶段2：数据清洗

        清洗规则：
        1. 移除音频转写时间戳 [00:12:15.234]
        2. 合并连续换行符（>2个）
        3. 移除纯标点/数字/特殊字符行
        4. 提取说话人标注
        5. 替换OCR乱码
        6. 去除首尾空白
        """
        import re

        original_text = text

        # 规则1：移除音频转写时间戳
        # 匹配格式：[00:12:15] 或 [00:12:15.234]
        text = re.sub(r'\[\d{2}:\d{2}:\d{2}(?:\.\d{3})?\]', '', text)

        # 规则2：合并连续换行符（保留最多2个）
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 规则3：移除纯标点/数字/特殊字符行
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()
            # 如果是空行，保留
            if not stripped:
                cleaned_lines.append(line)
                continue

            # 如果整行都是标点、数字、空格、特殊字符，删除
            if re.match(r'^[\s\d\-_=\*#\.。，,！!？?；;：:]+$', stripped):
                continue

            cleaned_lines.append(line)

        text = '\n'.join(cleaned_lines)

        # 规则4：提取说话人标注
        # 匹配格式：Speaker1: 或 【张三】：
        speakers = []
        speaker_pattern = r'(?:Speaker\d+|【[^】]+】)[:：]\s*'

        for match in re.finditer(speaker_pattern, text):
            speaker = match.group().strip(':：').strip()
            if speaker not in speakers:
                speakers.append(speaker)

        # 移除说话人前缀（保留内容）
        text = re.sub(speaker_pattern, '', text)

        # 保存说话人信息到metadata
        if speakers:
            metadata["speakers"] = speakers

        # 规则5：替换常见OCR乱码
        replacements = {
            '〇': '零',
            '—': '--',
            '～': '~',
            '，，': '，',
            '。。': '。',
            '  ': ' '  # 多个空格替换为单个
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # 规则6：去除首尾空白和空段落
        text = text.strip()

        # 统计清洗效果
        metadata["cleaning_stats"] = {
            "original_length": len(original_text),
            "cleaned_length": len(text),
            "removed_characters": len(original_text) - len(text),
            "removed_percentage": round((len(original_text) - len(text)) / len(original_text) * 100, 2) if original_text else 0
        }

        return text, metadata

    def _insert_fact_statements(
        self,
        content: str,  # 改名避免与sqlalchemy.text冲突
        document_id: int,
        project_id: int,
        source_file: str,
        db: Session
    ) -> int:
        """
        将清洗后的文本按句子切分并插入fact_statements表
        支持解析文本中的时间戳格式 [HH:MM:SS.mmm]

        Returns:
            插入的条数
        """
        logger.info(f"开始插入fact_statements: text长度={len(content)}, document_id={document_id}")

        # 按句子切分（简单版本）
        sentences = re.split(r'[。！？\n]+', content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]

        logger.info(f"切分出 {len(sentences)} 个句子")

        inserted_count = 0

        for idx, sentence in enumerate(sentences):
            try:
                # 尝试提取时间戳 [HH:MM:SS] 或 [HH:MM:SS.mmm]
                timestamp_match = re.match(r'\[(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?\]\s*(.*)', sentence)

                if timestamp_match:
                    # 解析时间戳
                    hours, minutes, seconds, milliseconds, text_without_timestamp = timestamp_match.groups()
                    start_sec = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
                    if milliseconds:
                        start_sec += float(f"0.{milliseconds}")

                    sentence = text_without_timestamp  # 使用去除时间戳的文本
                    end_sec = start_sec + 5.0  # 假设持续5秒
                else:
                    start_sec = None
                    end_sec = None

                # 清洗：去除口语词
                clean_text = re.sub(r'(呃|啊|那个|就是说|然后呢|基本上)\s*', '', sentence)
                clean_text = clean_text.strip()

                if len(clean_text) < 5:
                    logger.debug(f"句子太短，跳过: {clean_text}")
                    continue

                # 提取关键词（简单版本：取2-4字的词）
                keywords = re.findall(r'[一-龥]{2,4}', clean_text)
                keywords = ','.join(list(set(keywords))[:10])  # 去重，最多10个

                # 提取实体名（简单规则：XXX说）
                entity_match = re.search(r'([^，。！？\s]{2,4})(说|讲|告诉|表示)', clean_text)
                entity_names = entity_match.group(1) if entity_match else ''

                # 判断句子类型
                if '？' in sentence or '吗' in sentence:
                    sentence_type = '疑问句'
                elif '！' in sentence:
                    sentence_type = '感叹句'
                else:
                    sentence_type = '陈述句'

                # 插入数据库（使用原生SQL）
                sql = text("""
                    INSERT INTO fact_statements
                    (source_file, document_id, project_id, speaker, start_sec, end_sec,
                     original_text, clean_text, topic_tag, entity_names, keywords,
                     sentence_type, chunk_index, word_count, created_at)
                    VALUES
                    (:source_file, :document_id, :project_id, :speaker, :start_sec, :end_sec,
                     :original_text, :clean_text, :topic_tag, :entity_names, :keywords,
                     :sentence_type, :chunk_index, :word_count, :created_at)
                """)

                db.execute(sql, {
                    'source_file': source_file,
                    'document_id': document_id,
                    'project_id': project_id,
                    'speaker': entity_names or None,
                    'start_sec': start_sec,
                    'end_sec': end_sec,
                    'original_text': sentence,
                    'clean_text': clean_text,
                    'topic_tag': '其他',
                    'entity_names': entity_names,
                    'keywords': keywords,
                    'sentence_type': sentence_type,
                    'chunk_index': idx,
                    'word_count': len(clean_text),
                    'created_at': datetime.now()
                })

                inserted_count += 1
                if start_sec is not None:
                    logger.debug(f"成功插入第{idx+1}条(带时间戳 {start_sec:.1f}s): {clean_text[:20]}...")
                else:
                    logger.debug(f"成功插入第{idx+1}条: {clean_text[:20]}...")

            except Exception as e:
                logger.error(f"插入fact_statement失败: {e}")
                import traceback
                traceback.print_exc()
                continue

        # 提交事务
        db.commit()

        logger.info(f"✅ 插入完成，共 {inserted_count} 条")

        return inserted_count

    def _insert_fact_statements_from_segments(
        self,
        segments: list,
        document_id: int,
        project_id: int,
        source_file: str,
        db: Session
    ) -> int:
        """
        从Whisper segments插入fact_statements
        每个segment对应一条fact_statement，带完整时间戳

        Args:
            segments: Whisper返回的segments列表
            [
                {"id": 0, "text": "王大爷说...", "start": 10.5, "end": 15.2},
                ...
            ]
        """
        logger.info(f"开始从segments插入fact_statements: {len(segments)}个片段")

        inserted_count = 0

        for idx, segment in enumerate(segments):
            try:
                sentence = segment.get('text', '').strip()
                start_sec = segment.get('start')
                end_sec = segment.get('end')

                if not sentence or len(sentence) < 5:
                    continue

                # 清洗：去除口语词
                clean_text = re.sub(r'(呃|啊|那个|就是说|然后呢|基本上)\s*', '', sentence)
                clean_text = clean_text.strip()

                if len(clean_text) < 5:
                    continue

                # 提取关键词
                keywords = re.findall(r'[一-龥]{2,4}', clean_text)
                keywords = ','.join(list(set(keywords))[:10])

                # 提取说话人（简单规则：XXX说）
                entity_match = re.search(r'([^，。！？\s]{2,4})(说|讲|告诉|表示)', clean_text)
                entity_names = entity_match.group(1) if entity_match else ''

                # 判断句子类型
                if '？' in sentence or '吗' in sentence:
                    sentence_type = '疑问句'
                elif '！' in sentence:
                    sentence_type = '感叹句'
                else:
                    sentence_type = '陈述句'

                # 插入数据库
                sql = text("""
                    INSERT INTO fact_statements
                    (source_file, document_id, project_id, speaker, start_sec, end_sec,
                     original_text, clean_text, topic_tag, entity_names, keywords,
                     sentence_type, chunk_index, word_count, created_at)
                    VALUES
                    (:source_file, :document_id, :project_id, :speaker, :start_sec, :end_sec,
                     :original_text, :clean_text, :topic_tag, :entity_names, :keywords,
                     :sentence_type, :chunk_index, :word_count, :created_at)
                """)

                db.execute(sql, {
                    'source_file': source_file,
                    'document_id': document_id,
                    'project_id': project_id,
                    'speaker': entity_names or None,
                    'start_sec': start_sec,  # 关键：保留时间戳
                    'end_sec': end_sec,      # 关键：保留时间戳
                    'original_text': sentence,
                    'clean_text': clean_text,
                    'topic_tag': '其他',
                    'entity_names': entity_names,
                    'keywords': keywords,
                    'sentence_type': sentence_type,
                    'chunk_index': idx,
                    'word_count': len(clean_text),
                    'created_at': datetime.now()
                })

                inserted_count += 1
                logger.debug(f"成功插入segment {idx+1}: {clean_text[:20]}... (时间戳: {start_sec:.1f}s-{end_sec:.1f}s)")

            except Exception as e:
                logger.error(f"插入segment失败: {e}")
                import traceback
                traceback.print_exc()
                continue

        # 提交事务
        db.commit()

        logger.info(f"✅ 从segments插入完成，共 {inserted_count} 条（带时间戳）")

        return inserted_count

    def get_processing_status(
        self,
        document_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        获取文档处理状态
        """
        doc = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not doc:
            return {"error": "文档不存在"}

        # 获取chunks统计
        chunks_count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).count()

        vectorized_count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id,
            DocumentChunk.embedding.isnot(None)
        ).count()

        return {
            "document_id": document_id,
            "status": doc.status,
            "progress": doc.processing_progress,
            "stages": {
                "extract": {"completed": doc.text_content is not None},
                "clean": {"completed": doc.text_content is not None},
                "chunk": {"completed": chunks_count > 0, "count": chunks_count},
                "vectorize": {"completed": vectorized_count > 0, "count": vectorized_count},
                "index": {"completed": chunks_count > 0 and chunks_count == vectorized_count}
            },
            "error": doc.error_message
        }

    def reprocess_document(
        self,
        document_id: int,
        project_id: int,
        db: Session,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        重新处理文档（清空旧chunks，重新走完整流程）
        """
        logger.info(f"重新处理文档 {document_id}")

        # 删除旧的chunks
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete()
        db.commit()

        # 获取文档
        doc = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not doc:
            raise ValueError(f"文档 {document_id} 不存在")

        # 重新处理
        return self.process_document(
            document_id,
            doc.file_path,
            project_id,
            db,
            progress_callback
        )
