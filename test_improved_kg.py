#!/usr/bin/env python3
"""
测试改进的知识图谱服务
对比旧版（正则）vs 新版（jieba）的效果
"""
import sys
sys.path.insert(0, '/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

from app.services.knowledge_graph import KnowledgeGraphService
from app.services.knowledge_graph_improved import ImprovedKnowledgeGraphService

# 测试文本
test_text = """
田野调查笔记

调查地点：某村落，位于山区，人口约500人。

主要发现：
1. 当地保留了传统的节日庆祝方式
2. 年轻人大多外出务工，留守老人和儿童居多
3. 村里有一座历史悠久的祠堂

访谈对象：
- 张三（65岁，退休教师）
- 李四（42岁，村委会主任）
- 王五（38岁，村民）

调查时间：2023年6月15日至2023年6月30日
"""

print("=" * 60)
print("知识图谱服务对比测试")
print("=" * 60)

# 旧版服务（正则）
print("\n【旧版 - 正则表达式】")
print("-" * 60)
old_service = KnowledgeGraphService()
old_entities = old_service.extract_entities(test_text)

for entity_type, entities in old_entities.items():
    print(f"\n{entity_type.upper()} ({len(entities)}个):")
    for e in entities[:10]:  # 只显示前10个
        print(f"  • {e['name']}")

print(f"\n统计：")
for entity_type, entities in old_entities.items():
    print(f"  {entity_type}: {len(entities)}个")

# 新版服务（jieba）
print("\n\n【新版 - jieba分词】")
print("-" * 60)
new_service = ImprovedKnowledgeGraphService()
new_entities = new_service.extract_entities(test_text)

for entity_type, entities in new_entities.items():
    print(f"\n{entity_type.upper()} ({len(entities)}个):")
    for e in entities[:10]:
        print(f"  • {e['name']}")

print(f"\n统计：")
for entity_type, entities in new_entities.items():
    print(f"  {entity_type}: {len(entities)}个")

# 对比分析
print("\n\n【对比分析】")
print("=" * 60)

old_person_names = {e['name'] for e in old_entities.get('person', [])}
new_person_names = {e['name'] for e in new_entities.get('person', [])}

print(f"\n人名识别对比：")
print(f"  旧版识别出：{old_person_names}")
print(f"  新版识别出：{new_person_names}")

print(f"\n质量评估：")
print(f"  ❌ 旧版误识别：{'田野调查' in old_person_names or '笔记' in old_person_names or '调查地点' in old_person_names}")
print(f"  ✅ 新版准确性：{'张三' in new_person_names and '田野调查' not in new_person_names}")

print("\n" + "=" * 60)
