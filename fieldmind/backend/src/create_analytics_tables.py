"""
数据库迁移脚本 - 创建结构化分析表

运行方式:
    python create_analytics_tables.py
"""

import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.core.database import engine, Base
from app.models.structured_insight import StructuredInsight, TopicStatistics, EntityStatistics

print("=" * 70)
print("🗄️  创建数据分析表")
print("=" * 70)

try:
    # 创建表
    print("\n📝 正在创建以下表:")
    print("   1. structured_insights - 结构化洞察表（主表）")
    print("   2. topic_statistics - 主题统计表")
    print("   3. entity_statistics - 实体统计表")

    Base.metadata.create_all(bind=engine, tables=[
        StructuredInsight.__table__,
        TopicStatistics.__table__,
        EntityStatistics.__table__
    ])

    print("\n✅ 表创建成功！")

    # 验证表是否存在
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("\n📋 当前数据库表列表:")
    for table in sorted(tables):
        print(f"   - {table}")

    # 检查新表
    required_tables = ['structured_insights', 'topic_statistics', 'entity_statistics']
    missing_tables = [t for t in required_tables if t not in tables]

    if missing_tables:
        print(f"\n⚠️ 警告: 以下表未创建成功: {missing_tables}")
    else:
        print(f"\n✅ 所有必需表已创建")

except Exception as e:
    print(f"\n❌ 创建表失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ 数据库迁移完成")
print("=" * 70)

api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
print(f"""
📝 后续步骤:
1. 重新处理现有文档，填充结构化数据:
   python /tmp/batch_reprocess_36_42.py

2. 测试数据分析API:
   curl {api_url}/api/analytics/projects/1/topic-distribution

3. 查看统计数据:
   sqlite3 data/fieldmind.db "SELECT * FROM topic_statistics LIMIT 10;"
""")
