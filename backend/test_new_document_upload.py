#!/usr/bin/env python3
"""
测试新文档上传 - 验证自动提取时间线事件和关键词
"""
import sys
import os
from pathlib import Path
import tempfile

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_new_document_upload():
    """测试上传新文档并验证自动提取"""

    # 创建测试文档
    test_content = """
2024年5月15日，中国人工智能产业发展迅速。

根据最新报告，2023年AI市场规模达到1000亿元，同比增长35%。
预计到2025年，市场规模将突破3000亿元。

2024年3月，OpenAI发布了GPT-5模型，性能提升显著。
同年6月，Anthropic推出Claude 3.5，在多项基准测试中表现优异。

人工智能技术在医疗、教育、金融等领域得到广泛应用。
特别是在医疗诊断方面，AI辅助诊断系统的准确率已超过90%。

关键技术包括：深度学习、自然语言处理、计算机视觉、强化学习。
主要应用场景：智能客服、自动驾驶、医疗影像分析、金融风控。

2024年10月，第二届AI峰会在北京举行，吸引了全球200多家企业参与。
会议讨论了AI伦理、数据安全、算法透明度等重要议题。
"""

    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_file_path = f.name

    logger.info("=" * 80)
    logger.info("🧪 测试新文档上传 - 自动提取验证")
    logger.info("=" * 80)
    logger.info(f"📄 临时测试文件: {temp_file_path}")
    logger.info(f"📝 内容长度: {len(test_content)} 字符")
    logger.info("")

    try:
        # 连接数据库
        db_path = Path(__file__).parent / 'src' / 'data' / 'fieldmind.db'
        engine = create_engine(f'sqlite:///{db_path}')
        Session = sessionmaker(bind=engine)
        db = Session()

        # 记录上传前的统计
        before_docs = db.execute(text("SELECT COUNT(*) FROM project_documents")).scalar()
        before_events = db.execute(text("SELECT COUNT(*) FROM timeline_events")).scalar()
        before_keywords = db.execute(text("SELECT COUNT(*) FROM document_keywords")).scalar()

        logger.info("📊 上传前统计:")
        logger.info(f"  文档数: {before_docs}")
        logger.info(f"  时间线事件数: {before_events}")
        logger.info(f"  关键词数: {before_keywords}")
        logger.info("")

        # 模拟文档上传 - 使用 DocumentProcessingPipeline
        logger.info("🚀 开始模拟文档上传...")

        from app.services.document_processing_pipeline_complete import DocumentProcessingPipeline

        # 创建处理流水线
        pipeline = DocumentProcessingPipeline(db)

        # 准备文档数据
        project_id = 1  # 使用项目1
        filename = "test_ai_report_2024.txt"

        # 执行完整的处理流水线
        result = pipeline.process_document(
            project_id=project_id,
            file_path=temp_file_path,
            filename=filename,
            file_type='text/plain'
        )

        document_id = result.get('document_id')
        logger.info(f"✅ 文档处理完成，ID: {document_id}")
        logger.info("")

        # 等待一下确保数据写入
        import time
        time.sleep(1)

        # 记录上传后的统计
        after_docs = db.execute(text("SELECT COUNT(*) FROM project_documents")).scalar()
        after_events = db.execute(text("SELECT COUNT(*) FROM timeline_events WHERE document_id = :doc_id"),
                                 {"doc_id": document_id}).scalar()
        after_keywords = db.execute(text("SELECT COUNT(*) FROM document_keywords WHERE document_id = :doc_id"),
                                   {"doc_id": document_id}).scalar()

        logger.info("📊 上传后统计:")
        logger.info(f"  文档数: {after_docs} (+{after_docs - before_docs})")
        logger.info(f"  该文档的时间线事件数: {after_events}")
        logger.info(f"  该文档的关键词数: {after_keywords}")
        logger.info("")

        # 显示提取的时间线事件
        if after_events > 0:
            events = db.execute(text("""
                SELECT date, title, event_type, confidence_score
                FROM timeline_events
                WHERE document_id = :doc_id
                ORDER BY date
                LIMIT 10
            """), {"doc_id": document_id}).fetchall()

            logger.info(f"⏰ 提取的时间线事件 (前10个):")
            for event in events:
                date_str = event[0][:10] if event[0] else '未知'
                logger.info(f"  • {date_str} - {event[1][:50]}... (类型: {event[2]}, 置信度: {event[3]}%)")

        logger.info("")

        # 显示提取的关键词
        if after_keywords > 0:
            keywords = db.execute(text("""
                SELECT dk.weight, dk.extraction_method
                FROM document_keywords dk
                WHERE dk.document_id = :doc_id
                ORDER BY dk.weight DESC
                LIMIT 15
            """), {"doc_id": document_id}).fetchall()

            logger.info(f"🔑 提取的关键词 (前15个，按权重排序):")
            for idx, kw in enumerate(keywords, 1):
                logger.info(f"  {idx}. 权重: {kw[0]:.3f}, 方法: {kw[1]}")

        logger.info("")

        # 验证结果
        logger.info("=" * 80)
        logger.info("✅ 自动提取验证结果")
        logger.info("=" * 80)

        success = True
        issues = []

        if after_docs <= before_docs:
            logger.error("❌ 文档未成功创建")
            success = False
            issues.append("文档创建失败")
        else:
            logger.info("✅ 文档创建成功")

        if after_events == 0:
            logger.warning("⚠️ 时间线事件未提取（可能文档中没有时间表达式）")
            issues.append("时间线事件为空")
        else:
            logger.info(f"✅ 时间线事件提取成功 ({after_events} 个)")

        if after_keywords == 0:
            logger.warning("⚠️ 关键词未提取")
            issues.append("关键词为空")
        else:
            logger.info(f"✅ 关键词提取成功 ({after_keywords} 个)")

        logger.info("")

        if success and not issues:
            logger.info("🎉 完美！编年史和关键词功能已完全集成，自动提取正常工作！")
        elif success:
            logger.info(f"⚠️ 文档上传成功，但存在问题: {', '.join(issues)}")
        else:
            logger.error("❌ 文档上传失败")

        db.close()

    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            logger.info(f"🗑️ 已清理临时文件: {temp_file_path}")


if __name__ == '__main__':
    test_new_document_upload()
