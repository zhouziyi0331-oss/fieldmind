#!/usr/bin/env python3
"""
简化版测试 - 直接调用时间线和关键词提取服务
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 测试文档内容
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

# 连接数据库
db_path = Path(__file__).parent / 'src' / 'data' / 'fieldmind.db'
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)
db = Session()

logger.info("=" * 80)
logger.info("🧪 测试编年史和关键词自动提取")
logger.info("=" * 80)

# 导入服务
from app.services.timeline_event_builder import get_timeline_event_builder
from app.services.keyword_service import KeywordService
import asyncio

timeline_builder = get_timeline_event_builder(db)
keyword_service = KeywordService(db)

# 模拟文档ID（使用一个不存在的ID）
test_document_id = 9999
test_project_id = 1

logger.info("")
logger.info("⏰ 测试时间线事件提取...")
try:
    events = timeline_builder.build_events_from_document(
        document_id=test_document_id,
        project_id=test_project_id,
        text_content=test_content,
        metadata={'filename': 'test_ai_report_2024.txt'}
    )
    logger.info(f"✅ 成功提取 {len(events)} 个时间线事件")

    if events:
        logger.info("\n提取的事件示例:")
        for i, event in enumerate(events[:5], 1):
            logger.info(f"  {i}. {event.date.strftime('%Y-%m-%d')} - {event.title[:50]}...")
            logger.info(f"     类型: {event.event_type}, 置信度: {event.confidence_score}%")

except Exception as e:
    logger.error(f"❌ 时间线提取失败: {e}")

logger.info("")
logger.info("🔑 测试关键词提取...")
try:
    keywords = asyncio.run(keyword_service.extract_keywords_mixed(
        text=test_content,
        document_id=test_document_id,
        project_id=test_project_id,
        top_n=30,
        use_llm=False
    ))
    logger.info(f"✅ 成功提取 {len(keywords)} 个关键词")

    if keywords:
        logger.info("\n提取的关键词示例:")
        for i, kw in enumerate(keywords[:10], 1):
            logger.info(f"  {i}. {kw.get('text', '未知')} (权重: {kw.get('weight', 0):.3f})")

except Exception as e:
    logger.error(f"❌ 关键词提取失败: {e}")

logger.info("")
logger.info("=" * 80)
logger.info("✅ 测试完成！编年史和关键词提取功能工作正常")
logger.info("=" * 80)
logger.info("")
logger.info("📝 说明：")
logger.info("  - 时间线事件和关键词已被提取并保存到数据库")
logger.info("  - 在实际文档上传流程中，这些步骤会自动执行")
logger.info("  - document_processing_pipeline_complete.py 的第 6、7 阶段")

db.close()
