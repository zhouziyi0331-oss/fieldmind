#!/usr/bin/env python3
"""
处理音寨布依族村文档 - 使用完整的文档处理管道
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.document_processing_pipeline_complete import DocumentProcessingPipeline
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库连接
DATABASE_URL = "sqlite:///backend/src/data/fieldmind.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def main():
    session = SessionLocal()

    try:
        # 1. 查找音寨项目和文档
        logger.info("📂 查找音寨项目...")
        project_result = session.execute(text("""
            SELECT id, name FROM projects WHERE name = '音寨布依族村'
        """)).fetchone()

        if not project_result:
            logger.error("❌ 未找到音寨项目")
            return

        project_id = project_result[0]
        logger.info(f"✅ 找到项目: {project_result[1]} (ID: {project_id})")

        # 2. 查找文档
        doc_result = session.execute(text(f"""
            SELECT id, name, storage_path FROM documents
            WHERE project_id = {project_id} AND name LIKE '%音寨%'
        """)).fetchone()

        if not doc_result:
            logger.error("❌ 未找到音寨文档")
            return

        document_id = doc_result[0]
        doc_name = doc_result[1]
        storage_path = doc_result[2]

        logger.info(f"✅ 找到文档: {doc_name} (ID: {document_id})")
        logger.info(f"   文件路径: {storage_path}")

        # 3. 读取文档内容
        logger.info("📖 读取文档内容...")
        with open(storage_path, 'r', encoding='utf-8') as f:
            text_content = f.read()

        logger.info(f"✅ 已读取文档，字数: {len(text_content)}")

        # 4. 初始化处理管道
        logger.info("🔧 初始化文档处理管道...")
        pipeline = DocumentProcessingPipeline(
            db_connection=session,
            max_retries=3,
            retry_delay=1.0,
            enable_checkpoints=True
        )

        # 5. 处理文档
        logger.info("🚀 开始处理文档...")
        logger.info("=" * 80)

        result = pipeline.process_document(
            document_id=document_id,
            project_id=project_id,
            text_content=text_content,
            metadata={
                "filename": doc_name,
                "source": "yinzhai_field_investigation",
                "document_type": "field_report",
                "language": "zh"
            }
        )

        logger.info("=" * 80)

        # 6. 输出结果
        if result["success"]:
            logger.info(f"""
✅ 文档处理完成！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 处理统计:
   - 文档ID: {result['document_id']}
   - 生成块数: {result['chunks_count']}
   - 处理耗时: {result['processing_time']:.2f}秒
   - 完成阶段: {', '.join(result['stages_completed'])}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """)

            # 7. 验证数据提取结果
            logger.info("🔍 验证数据提取结果...")

            # 检查chunks
            chunk_count = session.execute(text(f"""
                SELECT COUNT(*) FROM document_chunks WHERE document_id = {document_id}
            """)).scalar()
            logger.info(f"   - Chunks: {chunk_count}")

            # 检查keywords
            keyword_count = session.execute(text(f"""
                SELECT COUNT(*) FROM keywords WHERE document_id = {document_id}
            """)).scalar()
            logger.info(f"   - Keywords: {keyword_count}")

            # 检查entities
            entity_count = session.execute(text(f"""
                SELECT COUNT(*) FROM entities WHERE document_id = {document_id}
            """)).scalar()
            logger.info(f"   - Entities: {entity_count}")

            # 检查timeline events
            timeline_count = session.execute(text(f"""
                SELECT COUNT(*) FROM timeline_events WHERE document_id = {document_id}
            """)).scalar()
            logger.info(f"   - Timeline Events: {timeline_count}")

            # 检查fact statements
            fact_count = session.execute(text(f"""
                SELECT COUNT(*) FROM fact_statements WHERE document_id = {document_id}
            """)).scalar()
            logger.info(f"   - Fact Statements: {fact_count}")

            logger.info("\n✅ 处理完成！数据已写入数据库，可以重新测试 Skills 了。")

        else:
            logger.error(f"""
❌ 文档处理失败
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
错误信息: {result.get('error')}
错误类型: {result.get('error_type')}
处理耗时: {result.get('processing_time', 0):.2f}秒
Checkpoint可用: {result.get('checkpoint_available', False)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """)

    except Exception as e:
        logger.error(f"❌ 处理过程出错: {e}", exc_info=True)

    finally:
        session.close()

if __name__ == "__main__":
    main()
