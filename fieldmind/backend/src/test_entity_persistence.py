#!/usr/bin/env python3
"""
测试实体持久化到SQLite
验证P4修复：实体提取 + 数据库持久化
"""

import sys
import os

# 使用环境变量或相对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.tools.knowledge.graph import UnifiedKnowledgeGraphEngine
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 测试文本
test_text = """
王大爷说，我们村有三百多年历史了。李婶告诉我，村里的祠堂是明代建筑。
张师傅在北京工作了二十年，现在回村里开农家乐。
十八洞村位于湖南省湘西土家族苗族自治州，是著名的扶贫示范村。
"""

print("📊 测试实体提取与持久化\n")

# 1. 提取实体
kg_service = UnifiedKnowledgeGraphEngine()
entities, relations = kg_service.extract_entities_and_relations(
    test_text,
    document_id=999,
    use_llm=False  # 仅使用spaCy+规则，避免LLM调用
)

print(f"✅ 提取结果:")
print(f"   实体数: {len(entities)}")
print(f"   关系数: {len(relations)}")

print(f"\n📝 实体详情:")
for i, entity in enumerate(entities[:10], 1):
    print(f"   {i}. {entity.name} ({entity.entity_type}) - source: {entity.properties.get('source')}")

# 2. 持久化到图谱
kg_service.add_entities_and_relations(entities, relations)

# 3. 验证SQLite持久化 - 使用环境变量
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'data', 'fieldmind.db')}")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

result = session.execute(text("""
    SELECT COUNT(*) as total,
           COUNT(DISTINCT name) as unique_names,
           entity_type,
           COUNT(*) as type_count
    FROM entities
    GROUP BY entity_type
    ORDER BY type_count DESC
"""))

print(f"\n{'='*60}")
print(f"✅ SQLite entities表统计:")
records = result.fetchall()
for total, unique_names, entity_type, type_count in records:
    print(f"   {entity_type}: {type_count}条记录")

# 查询最近添加的实体
result = session.execute(text("""
    SELECT name, entity_type, mention_count, created_at
    FROM entities
    ORDER BY created_at DESC
    LIMIT 10
"""))

print(f"\n📋 最近添加的实体:")
for name, entity_type, mention_count, created_at in result.fetchall():
    print(f"   - {name} ({entity_type}) - 提及{mention_count}次 - {created_at}")

session.close()

print(f"\n🎉 实体持久化测试完成！")
