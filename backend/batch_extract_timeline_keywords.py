#!/usr/bin/env python3
"""
批量为已有文档补充提取时间线事件和关键词
"""
import sys
import os
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import asyncio
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def batch_extract(limit: int = None, skip_existing: bool = True):
    """批量提取时间线事件和关键词

    Args:
        limit: 最多处理的文档数量，None 表示全部
        skip_existing: 是否跳过已有提取结果的文档
    """

    # 连接数据库
    db_path = Path(__file__).parent / 'src' / 'data' / 'fieldmind.db'
    if not db_path.exists():
        logger.error(f"数据库不存在: {db_path}")
        return

    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    db = Session()

    logger.info("=" * 80)
    logger.info("🚀 开始批量提取时间线事件和关键词")
    logger.info("=" * 80)

    try:
        # 导入服务
        from app.services.timeline_event_builder import get_timeline_event_builder
        from app.services.keyword_service import KeywordService

        timeline_builder = get_timeline_event_builder(db)
        keyword_service = KeywordService(db)

        # 获取需要处理的文档
        if skip_existing:
            # 只处理没有时间线事件或关键词的文档
            query = text("""
                SELECT DISTINCT pd.id, pd.filename, pd.project_id, pd.text_content
                FROM project_documents pd
                LEFT JOIN timeline_events te ON pd.id = te.document_id
                LEFT JOIN document_keywords dk ON pd.id = dk.document_id
                WHERE (te.id IS NULL OR dk.id IS NULL)
                  AND pd.text_content IS NOT NULL
                  AND LENGTH(pd.text_content) > 0
                ORDER BY pd.id
            """)
        else:
            # 处理所有文档
            query = text("""
                SELECT id, filename, project_id, text_content
                FROM project_documents
                WHERE text_content IS NOT NULL
                  AND LENGTH(text_content) > 0
                ORDER BY id
            """)

        if limit:
            query = text(str(query) + f" LIMIT {limit}")

        documents = db.execute(query).fetchall()

        total = len(documents)
        logger.info(f"📄 找到 {total} 个需要处理的文档")

        if total == 0:
            logger.info("✅ 没有需要处理的文档")
            return

        # 统计
        success_count = 0
        timeline_total = 0
        keyword_total = 0
        failed_docs = []

        # 逐个处理文档
        for idx, doc in enumerate(documents, 1):
            doc_id = doc[0]
            filename = doc[1]
            project_id = doc[2]
            text_content = doc[3]

            logger.info(f"\n{'='*80}")
            logger.info(f"📄 [{idx}/{total}] 处理文档 ID {doc_id}: {filename[:50]}")
            logger.info(f"{'='*80}")

            # 提取时间线事件
            events_extracted = 0
            try:
                logger.info("⏰ 提取时间线事件...")

                # 检查是否已有事件
                existing_events = db.execute(text(
                    "SELECT COUNT(*) FROM timeline_events WHERE document_id = :doc_id"
                ), {"doc_id": doc_id}).scalar()

                if existing_events > 0 and skip_existing:
                    logger.info(f"  ⏭️  已有 {existing_events} 个事件，跳过")
                else:
                    # 提取事件
                    events = timeline_builder.build_events_from_document(
                        document_id=doc_id,
                        project_id=project_id,
                        text_content=text_content,
                        metadata={}
                    )
                    events_extracted = len(events)
                    timeline_total += events_extracted
                    logger.info(f"  ✅ 提取了 {events_extracted} 个时间线事件")

            except Exception as e:
                logger.warning(f"  ⚠️ 时间线事件提取失败: {e}", exc_info=False)

            # 提取关键词
            keywords_extracted = 0
            try:
                logger.info("🔑 提取关键词...")

                # 检查是否已有关键词
                existing_keywords = db.execute(text(
                    "SELECT COUNT(*) FROM document_keywords WHERE document_id = :doc_id"
                ), {"doc_id": doc_id}).scalar()

                if existing_keywords > 0 and skip_existing:
                    logger.info(f"  ⏭️  已有 {existing_keywords} 个关键词，跳过")
                else:
                    # 提取关键词（不使用LLM以节省成本）
                    keywords = asyncio.run(keyword_service.extract_keywords_mixed(
                        text=text_content,
                        document_id=doc_id,
                        project_id=project_id,
                        top_n=30,
                        use_llm=False
                    ))
                    keywords_extracted = len(keywords)
                    keyword_total += keywords_extracted
                    logger.info(f"  ✅ 提取了 {keywords_extracted} 个关键词")

            except Exception as e:
                logger.warning(f"  ⚠️ 关键词提取失败: {e}", exc_info=False)

            # 记录结果
            if events_extracted > 0 or keywords_extracted > 0:
                success_count += 1
                logger.info(f"✅ 文档 {doc_id} 处理成功")
            else:
                failed_docs.append((doc_id, filename))
                logger.warning(f"⚠️ 文档 {doc_id} 未提取到任何内容")

        # 最终统计
        logger.info("\n" + "=" * 80)
        logger.info("📊 批量提取完成统计")
        logger.info("=" * 80)
        logger.info(f"✅ 成功处理: {success_count}/{total} 个文档")
        logger.info(f"⏰ 总时间线事件: {timeline_total} 个")
        logger.info(f"🔑 总关键词: {keyword_total} 个")

        if failed_docs:
            logger.info(f"\n⚠️ 未提取到内容的文档 ({len(failed_docs)}个):")
            for doc_id, filename in failed_docs[:10]:  # 只显示前10个
                logger.info(f"  • ID {doc_id}: {filename[:50]}")
            if len(failed_docs) > 10:
                logger.info(f"  ... 还有 {len(failed_docs) - 10} 个")

        logger.info("\n🎉 批量提取完成！")

    except Exception as e:
        logger.error(f"❌ 批量提取失败: {e}", exc_info=True)

    finally:
        db.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='批量提取时间线事件和关键词')
    parser.add_argument('--limit', type=int, default=None,
                       help='最多处理的文档数量（默认全部）')
    parser.add_argument('--no-skip', action='store_true',
                       help='不跳过已有提取结果的文档（重新提取）')
    parser.add_argument('--test', action='store_true',
                       help='测试模式：只处理前5个文档')

    args = parser.parse_args()

    limit = args.limit
    if args.test:
        limit = 5
        logger.info("🧪 测试模式：只处理前5个文档")

    batch_extract(
        limit=limit,
        skip_existing=not args.no_skip
    )
