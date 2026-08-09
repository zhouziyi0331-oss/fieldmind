"""
后台任务处理器（不使用 Celery）
使用 Python 线程池实现异步处理
"""

from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session
import os
import json
from pathlib import Path
import logging
import asyncio
from datetime import datetime

from app.core.database import SessionLocal
from app.models.project import ProjectDocument, Project
from app.services.document_converter import DocumentConverter
from app.services.video_processor import VideoProcessor
from app.core.transcription import transcription_service
from app.config import settings

logger = logging.getLogger(__name__)

# 创建线程池
executor = ThreadPoolExecutor(max_workers=2)

# 服务实例
document_converter = DocumentConverter()
video_processor = VideoProcessor()


# ===== 链路追踪工具 =====
import time

def trace_step(step_name: str, document_id: int, details: str = ""):
    """
    链路追踪日志 - 用于精确定位处理流程
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"🔍 [TRACE][Doc {document_id}] {step_name}"
    if details:
        log_msg += f" | {details}"
    log_msg += f" | {timestamp}"

    print(log_msg)  # 打印到控制台
    logger.info(log_msg)  # 记录到日志文件
# ===== 结束 =====


def process_document_async(document_id: int):
    """
    在后台线程中处理文档

    这个函数会在独立线程中运行，不会阻塞主线程
    """
    db = SessionLocal()

    try:
        trace_step("0. 任务启动", document_id, "后台线程开始执行")
        logger.info(f"开始处理文档 {document_id}")

        # 获取文档
        doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
        if not doc:
            logger.error(f"文档 {document_id} 不存在")
            return

        trace_step("1. 入站登记", document_id, f"文件类型={doc.file_type}, 大小={doc.file_size}字节")

        # 更新状态为处理中
        doc.status = "processing"
        db.commit()

        # 🔴 实时推送：开始处理
        notify_frontend(doc.project_id, document_id, "processing", {
            "step": "started",
            "message": "开始处理文档"
        })

        file_path = doc.file_path
        file_type = doc.file_type

        content = None
        transcript = None

        # 根据文件类型处理
        if file_type in ['video/mp4', 'video/mov', 'video/avi', 'video']:
            trace_step("2. 内容萃取 - 视频", document_id, "开始提取音频并转录")
            logger.info(f"处理视频文件: {file_path}")
            content, transcript = process_video(file_path)
            trace_step("2. 内容萃取 - 视频", document_id, f"转录完成，文本长度={len(content) if content else 0}")

        elif file_type in ['audio/mp3', 'audio/wav', 'audio/m4a', 'audio', 'mp3', 'wav', 'm4a', 'ogg', 'flac', 'aac']:
            trace_step("2. 内容萃取 - 音频", document_id, "开始Whisper转录")
            logger.info(f"处理音频文件: {file_path}")
            start_time = time.time()
            content, transcript = process_audio(file_path)
            elapsed = time.time() - start_time
            trace_step("2. 内容萃取 - 音频", document_id, f"Whisper转录完成，耗时={elapsed:.2f}秒，文本长度={len(content) if content else 0}")

        elif file_type in ['pdf', 'docx', 'doc', 'txt', 'md', 'document']:
            trace_step("2. 内容萃取 - 文档", document_id, "开始提取文本")
            logger.info(f"处理文档文件: {file_path}")
            content = process_document_file(file_path)
            trace_step("2. 内容萃取 - 文档", document_id, f"提取完成，文本长度={len(content) if content else 0}")

        elif file_type in ['image/png', 'image/jpg', 'image/jpeg', 'image']:
            trace_step("2. 内容萃取 - 图片", document_id, "开始OCR识别")
            logger.info(f"处理图片文件: {file_path}")
            content = process_image(file_path)
            trace_step("2. 内容萃取 - 图片", document_id, f"OCR完成，文本长度={len(content) if content else 0}")

        else:
            logger.warning(f"未知文件类型: {file_type}")

        # 保存处理结果
        if content:
            doc.text_content = content
            doc.word_count = len(content.split())
            logger.info(f"文档 {document_id} 提取了 {doc.word_count} 个词")
            db.commit()

            # 🔴 实时推送：内容提取完成
            notify_frontend(doc.project_id, document_id, "processing", {
                "step": "content_extracted",
                "message": f"提取了{len(content)}字符",
                "word_count": doc.word_count,
                "char_count": len(content)
            })

        if transcript:
            # 保存转写文本（带时间戳）
            save_transcript(document_id, transcript)
            doc.extra_data = doc.extra_data or {}
            doc.extra_data['has_transcript'] = True
            doc.extra_data['transcript'] = transcript  # ✅ 传递完整transcript到pipeline
            logger.info(f"文档 {document_id} 保存了转写文本，segments={len(transcript)}")

        # 提取关键词
        if content:
            trace_step("3. 关键词提取", document_id, "开始jieba分词")
            keywords = extract_keywords(content)
            doc.extra_data = doc.extra_data or {}
            doc.extra_data['keywords'] = keywords[:50]
            logger.info(f"文档 {document_id} 提取了 {len(keywords)} 个关键词")
            trace_step("3. 关键词提取", document_id, f"提取{len(keywords)}个关键词")
            db.commit()

            # 🔴 实时推送：关键词提取完成
            notify_frontend(doc.project_id, document_id, "processing", {
                "step": "keywords_extracted",
                "message": f"提取了{len(keywords)}个关键词",
                "keyword_count": len(keywords)
            })

        # ===== 新增：调用完整处理pipeline =====
        if content:
            trace_step("4. 向量化Pipeline启动", document_id, "开始文档切分和向量化")
            logger.info(f"🚀 开始完整处理pipeline: 向量化 + 语义分析")
            try:
                from app.services.document_processing_pipeline_complete import DocumentProcessingPipeline

                pipeline = DocumentProcessingPipeline(db)
                start_time = time.time()
                result = pipeline.process_document(
                    document_id=document_id,
                    project_id=doc.project_id,
                    text_content=content,
                    metadata=doc.extra_data or {}
                )
                elapsed = time.time() - start_time

                # 确保extra_data不为None
                if doc.extra_data is None:
                    doc.extra_data = {}

                if result.get('success'):
                    chunks_count = result.get('chunks_count')
                    trace_step("4. 向量化Pipeline完成", document_id, f"成功向量化{chunks_count}个chunks，耗时={elapsed:.2f}秒")
                    logger.info(f"✅ Pipeline处理成功: {chunks_count}个块已向量化")
                    doc.extra_data['pipeline_completed'] = True
                    doc.extra_data['chunks_count'] = chunks_count
                    db.commit()

                    # 🔴 实时推送：向量化完成
                    notify_frontend(doc.project_id, document_id, "processing", {
                        "step": "vectorized",
                        "message": f"向量化完成：{chunks_count}个块",
                        "chunks_count": chunks_count
                    })
                else:
                    trace_step("4. 向量化Pipeline失败", document_id, f"错误={result.get('error')}")
                    logger.error(f"❌ Pipeline处理失败: {result.get('error')}")
                    doc.extra_data['pipeline_error'] = result.get('error')

            except Exception as e:
                trace_step("4. 向量化Pipeline异常", document_id, f"异常={str(e)[:100]}")
                logger.error(f"❌ Pipeline执行异常: {e}", exc_info=True)
                if doc.extra_data is None:
                    doc.extra_data = {}
                doc.extra_data['pipeline_error'] = str(e)
        # ===== 结束 =====

        # ===== 🔪 破茧三刀：动态发现引擎（替代所有硬编码） =====
        if content and doc.extra_data.get('pipeline_completed'):
            trace_step("5. 动态发现引擎启动", document_id, "无预设词表、无固定分类、无模板框架")
            logger.info(f"🔪 破茧三刀启动...")
            try:
                from app.services.dynamic_discovery import DynamicDiscoveryEngine

                # 初始化引擎（禁用HanLP避免下载468MB模型）
                engine = DynamicDiscoveryEngine(enable_ner=False)

                # 切分文本为段落（用于聚类分析）
                paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 20]
                if not paragraphs:
                    paragraphs = [content]  # 整篇作为一个段落

                logger.info(f"📄 切分为 {len(paragraphs)} 个段落进行分析")

                # 第一刀：无监督主题发现
                topics_result = engine.discover_topics(paragraphs, min_topic_size=2)
                discovered_topics = topics_result.get('topics', [])

                # 第二刀：通用实体识别+指称消歧
                merged_entities = engine.extract_and_merge_entities(paragraphs, merge_threshold=0.85)

                # 第三刀：数据画像生成
                data_profile = engine.generate_data_profile(
                    paragraphs,
                    discovered_topics,
                    merged_entities
                )

                # 保存到Document新字段
                doc.extracted_entities = merged_entities[:50]  # Top 50实体
                doc.auto_clusters = discovered_topics
                doc.data_profile = data_profile

                # 同时保存到extra_data用于兼容旧代码
                doc.extra_data['dynamic_discovery'] = {
                    'topics': discovered_topics,
                    'entities': merged_entities[:50],
                    'profile': data_profile
                }
                doc.extra_data['discovery_completed'] = True
                db.commit()

                # 🔴 实时推送：实体提取完成
                notify_frontend(doc.project_id, document_id, "processing", {
                    "step": "entities_extracted",
                    "message": f"提取了{len(merged_entities)}个实体，发现{len(discovered_topics)}个主题",
                    "entity_count": len(merged_entities),
                    "topic_count": len(discovered_topics)
                })

                trace_step("5. 动态发现完成", document_id,
                          f"主题={len(discovered_topics)}, "
                          f"实体={len(merged_entities)}, "
                          f"维度={len(data_profile.get('discovered_dimensions', []))}")

                logger.info(f"✅ 破茧三刀完成: "
                           f"{len(discovered_topics)}个主题, "
                           f"{len(merged_entities)}个实体（已消歧）, "
                           f"{len(data_profile.get('discovered_dimensions', []))}个维度")

            except Exception as e:
                trace_step("5. 动态发现异常", document_id, f"错误={str(e)[:100]}")
                logger.error(f"❌ 动态发现异常: {e}", exc_info=True)
                doc.extra_data = doc.extra_data or {}
                doc.extra_data['discovery_error'] = str(e)
        # ===== 结束 =====

        # ===== 新增：数据质量检查 =====
        trace_step("6. 数据质量检查", document_id, "运行4重验证...")
        logger.info(f"🔍 开始数据质量检查...")

        try:
            from app.services.data_quality_checker import data_quality_checker

            quality_result = data_quality_checker.check_document(doc, db)

            # 确保extra_data不为None
            if doc.extra_data is None:
                doc.extra_data = {}

            # 保存质量检查结果
            doc.extra_data['quality_check'] = {
                "score": quality_result['score'],
                "passed": quality_result['passed'],
                "issues": quality_result['issues'],
                "checked_at": datetime.now().isoformat()
            }

            if quality_result['passed']:
                doc.status = "completed"
                doc.extra_data['quality_level'] = "approved"
                trace_step("6. 数据质量检查", document_id, f"✅ 通过 (得分={quality_result['score']:.1f})")
                logger.info(f"✅ 数据质量检查通过: 得分={quality_result['score']:.1f}")
            else:
                doc.status = "review_needed"
                doc.extra_data['quality_level'] = "pending_review"
                trace_step("6. 数据质量检查", document_id, f"⚠️ 未通过，需要审核 (得分={quality_result['score']:.1f})")
                logger.warning(f"⚠️ 数据质量检查未通过: 得分={quality_result['score']:.1f}, 问题={quality_result['issues']}")

            db.commit()

            # 🔴 实时推送：质量检查完成
            notify_frontend(doc.project_id, document_id, doc.status, {
                "step": "quality_checked",
                "quality_score": quality_result['score'],
                "quality_level": doc.extra_data['quality_level'],
                "passed": quality_result['passed'],
                "issues": quality_result['issues'],
                "message": "质量检查完成" if quality_result['passed'] else "质量检查未通过，需要审核"
            })

        except Exception as e:
            logger.error(f"数据质量检查失败: {e}", exc_info=True)
            # 如果检查失败，默认标记为completed（向下兼容）
            doc.status = "completed"
            if doc.extra_data is None:
                doc.extra_data = {}
            doc.extra_data['quality_check_error'] = str(e)

        db.commit()
        # ===== 结束 =====

        trace_step("7. 处理完成", document_id, f"状态={doc.status}, 总耗时={time.time() - start_time if 'start_time' in locals() else 0:.2f}秒")

        # ===== 新增：自动触发工作流串联 =====
        # 只有质量检查通过的文档才触发后续工作流
        if doc.status == "completed" and doc.extra_data.get('quality_level') == "approved":
            trace_step("8. 工作流串联", document_id, "触发后续工作流...")
            logger.info(f"🔗 开始工作流串联...")

            # 🔴 实时推送：开始工作流串联
            notify_frontend(doc.project_id, document_id, "completed", {
                "step": "workflow_chaining",
                "message": "开始工作流串联..."
            })

            try:
                from app.services.workflow_chain import workflow_chain

                workflow_chain.trigger_next_workflows(doc, db)

                trace_step("8. 工作流串联", document_id, "✅ 完成")
                logger.info(f"✅ 工作流串联完成")

                # 🔴 实时推送：工作流串联完成，刷新项目统计
                from app.core.websocket import manager
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # 获取最新的项目统计
                project_stats = _get_project_stats(doc.project_id, db)
                loop.run_until_complete(
                    manager.notify_project_stats(doc.project_id, project_stats)
                )
                loop.close()

            except Exception as e:
                trace_step("8. 工作流串联", document_id, f"⚠️ 部分失败: {str(e)[:50]}")
                logger.error(f"⚠️ 工作流串联部分失败（不影响文档处理）: {e}", exc_info=True)
        else:
            logger.info(f"⏭️ 跳过工作流串联（文档状态={doc.status}，质量={doc.extra_data.get('quality_level') if doc.extra_data else 'unknown'}）")
        # ===== 结束 =====

        # 更新项目统计（可能失败，不影响主流程）
        # 注意：这个函数已经被workflow_chain.trigger_next_workflows调用，这里保留作为fallback
        try:
            update_project_stats(doc.project_id, db)
        except Exception as e:
            logger.warning(f"⚠️ 更新项目统计失败（不影响主流程）: {e}")

        # 通知前端（WebSocket）- 暂时跳过
        try:
            notify_frontend(doc.project_id, document_id, "completed", {
                "word_count": doc.word_count,
                "has_transcript": bool(transcript)
            })
        except Exception as e:
            logger.warning(f"⚠️ 通知前端失败: {e}")

        logger.info(f"✅ 文档 {document_id} 处理完成")

    except Exception as e:
        logger.error(f"❌ 处理文档 {document_id} 失败: {e}", exc_info=True)

        if doc:
            doc.status = "failed"

            # 生成用户友好的错误信息
            error_msg = str(e)

            # 根据异常类型提供更具体的错误信息
            if "PDF" in error_msg and "encrypted" in error_msg.lower():
                error_msg = "PDF文件已加密，无法解析。请提供未加密的PDF文件。"
            elif "Whisper" in error_msg or "audio" in error_msg.lower():
                error_msg = f"音频转写失败：{error_msg}。请检查音频文件格式是否支持。"
            elif "ChromaDB" in error_msg or "vector" in error_msg.lower():
                error_msg = f"向量化存储失败：{error_msg}。请检查ChromaDB服务状态。"
            elif "permission" in error_msg.lower() or "denied" in error_msg.lower():
                error_msg = f"文件访问权限不足：{error_msg}"
            elif len(error_msg) > 200:
                # 如果错误信息太长，截取关键部分
                error_msg = error_msg[:200] + "..."

            # 同时写入error_message字段和extra_data
            doc.error_message = error_msg
            doc.extra_data = doc.extra_data or {}
            doc.extra_data['error'] = str(e)
            doc.extra_data['error_timestamp'] = datetime.now().isoformat()

            db.commit()

    finally:
        db.close()


def submit_task(document_id: int):
    """
    提交文档处理任务到线程池

    Returns:
        Future 对象
    """
    future = executor.submit(process_document_async, document_id)
    logger.info(f"已提交文档 {document_id} 到后台处理队列")
    return future


def process_video(file_path: str):
    """处理视频：提取音频 → Whisper 转写"""
    try:
        # 1. 提取音频
        audio_path = video_processor.extract_audio(file_path)

        # 2. Whisper 转写
        result = transcription_service.transcribe(audio_path)

        # 3. 提取结果
        transcript = result.get('segments', [])
        text = result.get('text', '')

        # 4. 清理临时文件
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return text, transcript

    except Exception as e:
        logger.error(f"视频处理失败: {e}")
        return None, None


def process_audio(file_path: str):
    """处理音频：Whisper 转写"""
    try:
        result = transcription_service.transcribe(file_path)
        transcript = result.get('segments', [])
        text = result.get('text', '')
        return text, transcript
    except Exception as e:
        logger.error(f"音频处理失败: {e}")
        return None, None


def process_document_file(file_path: str):
    """处理文档：转换为文本（使用Unstructured增强解析）"""
    try:
        # 优先使用Unstructured（支持表格、复杂PDF）
        from app.services.document_converter_v2 import UnstructuredConverter

        logger.info(f"使用Unstructured解析文档: {file_path}")
        text = UnstructuredConverter.convert_to_text(file_path)

        if text:
            logger.info(f"✅ Unstructured解析成功，提取{len(text)}字符")
            return text
        else:
            logger.warning(f"⚠️ Unstructured未提取到内容，尝试fallback")

    except Exception as e:
        logger.warning(f"⚠️ Unstructured解析失败: {e}，使用fallback")

    # Fallback: 使用原有DocumentConverter
    try:
        result = document_converter.convert_file(file_path)
        if result:
            return result.get('text_content', '')
    except Exception as e:
        logger.error(f"❌ Fallback文档处理也失败: {e}")

    return None


def process_image(file_path: str):
    """处理图片：OCR 提取文字"""
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        result = ocr.ocr(file_path)

        text_lines = []
        for line in result:
            for word_info in line:
                text_lines.append(word_info[1][0])

        return '\n'.join(text_lines)
    except Exception as e:
        logger.error(f"图片OCR失败: {e}")
        return None


def save_transcript(document_id: int, transcript: list):
    """保存转写文本到文件"""
    try:
        transcript_dir = Path(settings.UPLOAD_DIR) / "transcripts"
        transcript_dir.mkdir(parents=True, exist_ok=True)

        transcript_file = transcript_dir / f"doc_{document_id}.json"
        with open(transcript_file, 'w', encoding='utf-8') as f:
            json.dump(transcript, f, ensure_ascii=False, indent=2)

        logger.info(f"转写文本已保存: {transcript_file}")
    except Exception as e:
        logger.error(f"保存转写文本失败: {e}")


def extract_keywords(text: str, top_n: int = 50):
    """从文本提取关键词"""
    try:
        import jieba.analyse
        keywords = jieba.analyse.extract_tags(text, topK=top_n, withWeight=True)
        return [{"word": word, "weight": float(weight)} for word, weight in keywords]
    except Exception as e:
        logger.error(f"提取关键词失败: {e}")
        return []


def update_project_stats(project_id: int, db: Session):
    """更新项目统计信息"""
    try:
        from sqlalchemy import func

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return

        # 统计文档数量
        doc_count = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).count()

        # 统计总字数
        total_words = db.query(func.sum(ProjectDocument.word_count)).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.word_count.isnot(None)
        ).scalar() or 0

        # 更新
        project.document_count = doc_count
        project.total_words = int(total_words)
        db.commit()

        logger.info(f"项目 {project_id} 统计已更新: {doc_count} 个文档, {total_words} 个词")
    except Exception as e:
        logger.error(f"更新项目统计失败: {e}")


def notify_frontend(project_id: int, document_id: int, status: str, details: dict = None):
    """
    通知前端更新
    使用 asyncio 在新的事件循环中运行
    """
    try:
        from app.core.websocket import manager

        # 创建新的事件循环（因为在线程中）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # 通知文档状态
        loop.run_until_complete(
            manager.notify_document_status(project_id, document_id, status, details)
        )

        loop.close()
        logger.info(f"✅ 已通知前端: project={project_id}, doc={document_id}, status={status}")

    except Exception as e:
        logger.error(f"通知前端失败: {e}")


def _get_project_stats(project_id: int, db: Session) -> dict:
    """获取项目统计数据"""
    from sqlalchemy import func
    from app.models.project import ProjectDocument
    from app.models.entity import Entity

    try:
        # 文档统计
        total_docs = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id
        ).scalar() or 0

        completed_docs = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "completed"
        ).scalar() or 0

        processing_docs = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "processing"
        ).scalar() or 0

        # 实体统计
        entity_count = db.query(func.count(Entity.id)).filter(
            Entity.project_id == project_id
        ).scalar() or 0

        return {
            "total_documents": total_docs,
            "completed_documents": completed_docs,
            "processing_documents": processing_docs,
            "total_entities": entity_count
        }
    except Exception as e:
        logger.error(f"获取项目统计失败: {e}")
        return {}



def execute_skill_analysis(skill_name: str, document_id: int, content: str, project_id: int, db: Session) -> dict:
    """
    执行skill分析（支持动态加载）

    Args:
        skill_name: skill名称
        document_id: 文档ID
        content: 文档内容
        project_id: 项目ID
        db: 数据库会话

    Returns:
        分析结果字典
    """
    try:
        # 尝试从skills目录动态加载
        try:
            import importlib
            skill_module = importlib.import_module(f'app.services.skills.{skill_name}')
            if hasattr(skill_module, 'analyze'):
                logger.info(f"  使用动态加载的Skill模块: {skill_name}")
                return skill_module.analyze(content, {"document_id": document_id, "project_id": project_id})
        except ImportError:
            logger.debug(f"Skill模块 {skill_name} 不存在，使用内置实现")
        except AttributeError:
            logger.warning(f"Skill模块 {skill_name} 缺少analyze方法")

        # 回退到硬编码的Skill
        if skill_name == 'rural_sop':
            return analyze_rural_sop(content, document_id, project_id, db)
        elif skill_name == 'fei_xiaotong':
            return analyze_fei_xiaotong(content, document_id, project_id, db)
        else:
            logger.warning(f"未知的skill: {skill_name}")
            return None

    except Exception as e:
        logger.error(f"Skill {skill_name} 分析失败: {e}", exc_info=True)
        return None


def analyze_rural_sop(content: str, document_id: int, project_id: int, db: Session) -> dict:
    """
    乡村运营 SOP 分析

    分析维度：
    - 社区基础调研：人口结构、经济来源、土地权属
    - 文化资产盘点：非遗、传统技艺、节庆
    - 利益相关方分析：村委、村民、外来资本
    - 业态可行性评估：资源匹配度、市场需求
    - 风险识别：政策风险、社区矛盾
    - 行动路径规划：短期切入点、中期目标
    """
    logger.info(f"  分析维度：乡村运营SOP框架")

    result = {
        "skill_name": "乡村运营 SOP",
        "analysis_time": datetime.now().isoformat(),
        "dimensions": {}
    }

    # 使用简单的关键词匹配和统计
    dimensions = {
        "community_research": {
            "keywords": ["人口", "年龄", "务工", "收入", "土地", "户籍", "劳动力"],
            "findings": []
        },
        "cultural_assets": {
            "keywords": ["非遗", "传统", "技艺", "节庆", "民俗", "文化", "手工艺"],
            "findings": []
        },
        "stakeholders": {
            "keywords": ["村委", "村民", "政府", "企业", "资本", "投资", "合作"],
            "findings": []
        },
        "business_feasibility": {
            "keywords": ["旅游", "产业", "市场", "需求", "资源", "可行性", "业态"],
            "findings": []
        },
        "risks": {
            "keywords": ["风险", "矛盾", "冲突", "问题", "困难", "障碍"],
            "findings": []
        },
        "action_plan": {
            "keywords": ["规划", "计划", "路径", "目标", "愿景", "措施"],
            "findings": []
        }
    }

    # 简单的关键词提取和上下文
    import jieba
    words = list(jieba.cut(content))

    for dim_name, dim_config in dimensions.items():
        matched_contexts = []

        # 查找包含关键词的句子
        sentences = content.split('。')
        for sentence in sentences[:100]:  # 限制前100句
            for keyword in dim_config['keywords']:
                if keyword in sentence:
                    matched_contexts.append(sentence.strip()[:200])  # 限制长度
                    break

        result["dimensions"][dim_name] = {
            "matched_count": len(matched_contexts),
            "contexts": matched_contexts[:5]  # 最多5条
        }

    logger.info(f"  ✅ 乡村运营SOP分析完成: {len([d for d in result['dimensions'].values() if d['matched_count'] > 0])} 个维度有发现")

    return result


def analyze_fei_xiaotong(content: str, document_id: int, project_id: int, db: Session) -> dict:
    """
    费孝通·乡土中国分析

    分析维度：
    - 差序格局：血缘、地缘关系网络
    - 礼治秩序：传统规范、社会控制
    - 熟人社会：信任机制、社会资本
    - 变迁分析：现代化冲击、结构变化
    """
    logger.info(f"  分析维度：费孝通差序格局框架")

    result = {
        "skill_name": "费孝通·乡土中国",
        "analysis_time": datetime.now().isoformat(),
        "dimensions": {}
    }

    dimensions = {
        "differential_mode": {
            "keywords": ["亲戚", "家族", "血缘", "宗族", "亲属", "关系", "人情"],
            "findings": []
        },
        "ritual_order": {
            "keywords": ["规矩", "习俗", "传统", "礼节", "仪式", "规范", "约定"],
            "findings": []
        },
        "acquaintance_society": {
            "keywords": ["熟人", "信任", "口碑", "面子", "名声", "邻里"],
            "findings": []
        },
        "modernization": {
            "keywords": ["外出", "打工", "城市", "流动", "变化", "冲击", "现代"],
            "findings": []
        }
    }

    # 简单的关键词提取和上下文
    sentences = content.split('。')

    for dim_name, dim_config in dimensions.items():
        matched_contexts = []

        for sentence in sentences[:100]:
            for keyword in dim_config['keywords']:
                if keyword in sentence:
                    matched_contexts.append(sentence.strip()[:200])
                    break

        result["dimensions"][dim_name] = {
            "matched_count": len(matched_contexts),
            "contexts": matched_contexts[:5]
        }

    logger.info(f"  ✅ 费孝通框架分析完成: {len([d for d in result['dimensions'].values() if d['matched_count'] > 0])} 个维度有发现")

    return result

