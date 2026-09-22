"""
重新处理历史文档 - 修复向量化失败的问题

此脚本用于：
1. 找出所有已完成但没有向量的文档
2. 重新运行向量化pipeline
3. 将向量存入ChromaDB
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.project import ProjectDocument
from app.tools.document import UnifiedDocumentPipeline
from sqlalchemy import text
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def reprocess_all_documents():
    """重新处理所有已完成的文档"""
    db = SessionLocal()

    try:
        # 查询所有completed状态的文档
        docs = db.query(ProjectDocument).filter(
            ProjectDocument.status == 'completed'
        ).order_by(ProjectDocument.id).all()

        logger.info(f"📊 找到 {len(docs)} 个已完成的文档需要重新处理")

        if len(docs) == 0:
            logger.info("✅ 没有需要重新处理的文档")
            return

        # 初始化pipeline
        pipeline = UnifiedDocumentPipeline(db)

        success_count = 0
        failed_count = 0

        for i, doc in enumerate(docs, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"📄 [{i}/{len(docs)}] 重新处理文档: {doc.id} - {doc.filename}")
            logger.info(f"   文件类型: {doc.file_type}")
            logger.info(f"   原始chunk数: {doc.chunk_count}")

            try:
                # 检查是否有text_content
                if not doc.text_content or len(doc.text_content.strip()) == 0:
                    logger.warning(f"⚠️ 文档 {doc.id} 没有text_content，跳过")
                    failed_count += 1
                    continue

                # 准备metadata
                metadata = doc.extra_data or {}

                # 如果是音频文档，尝试加载transcript
                if doc.file_type in ['audio', 'audio/mp3', 'audio/wav']:
                    transcript_path = Path(f"uploads/transcripts/doc_{doc.id}.json")
                    if transcript_path.exists():
                        import json
                        with open(transcript_path, 'r', encoding='utf-8') as f:
                            transcript = json.load(f)
                            metadata['transcript'] = transcript
                            metadata['has_transcript'] = True
                            logger.info(f"   ✅ 加载了transcript ({len(transcript)} segments)")

                # 重新处理
                logger.info(f"   🔄 开始重新处理...")
                result = pipeline.process_document(
                    document_id=doc.id,
                    project_id=doc.project_id,
                    text_content=doc.text_content,
                    metadata=metadata
                )

                if result.get('success'):
                    success_count += 1
                    chunks_count = result.get('chunks_count', 0)
                    processing_time = result.get('processing_time', 0)
                    logger.info(f"   ✅ 成功: {chunks_count} chunks, 耗时 {processing_time:.2f}s")
                else:
                    failed_count += 1
                    error = result.get('error', 'Unknown error')
                    logger.error(f"   ❌ 失败: {error}")

            except Exception as e:
                failed_count += 1
                logger.error(f"   ❌ 处理异常: {e}", exc_info=True)

        logger.info(f"\n{'='*60}")
        logger.info(f"📊 重新处理完成:")
        logger.info(f"   总计: {len(docs)} 个文档")
        logger.info(f"   成功: {success_count} 个")
        logger.info(f"   失败: {failed_count} 个")
        logger.info(f"   成功率: {success_count/len(docs)*100:.1f}%")

    except Exception as e:
        logger.error(f"❌ 脚本执行失败: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == '__main__':
    logger.info("🚀 开始重新处理历史文档...")
    reprocess_all_documents()
    logger.info("✅ 脚本执行完成")
