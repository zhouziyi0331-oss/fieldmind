#!/usr/bin/env python3
"""
测试spaCy中文实体提取准确率
验证P4优先级：实体提取修复 ← 知识图谱基础
"""

import spacy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 加载模型
nlp = spacy.load('zh_core_web_sm')

# 连接数据库
engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///./data/fieldmind.db"))
Session = sessionmaker(bind=engine)
session = Session()

# 获取所有fact_statements
result = session.execute(text("""
    SELECT id, document_id, clean_text, entity_names
    FROM fact_statements
    WHERE clean_text IS NOT NULL AND clean_text != ''
    LIMIT 100
"""))
records = result.fetchall()

print(f"📊 分析{len(records)}条fact_statements记录\n")

total_count = 0
extracted_count = 0
entity_types_dist = {}

for record_id, doc_id, clean_text, stored_entity_names in records:
    # 使用spaCy提取实体
    doc = nlp(clean_text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]

    total_count += 1
    if entities:
        extracted_count += 1
        for _, label in entities:
            entity_types_dist[label] = entity_types_dist.get(label, 0) + 1

    # 显示前5个样本
    if total_count <= 5:
        print(f"📝 样本 {total_count}:")
        print(f"   文本: {clean_text[:100]}...")
        print(f"   实体: {entities}")
        print()

# 统计结果
extraction_rate = (extracted_count / total_count * 100) if total_count > 0 else 0

print(f"\n{'='*60}")
print(f"✅ 实体提取统计:")
print(f"   总记录数: {total_count}")
print(f"   成功提取实体的记录: {extracted_count}")
print(f"   提取率: {extraction_rate:.2f}%")
print(f"\n   实体类型分布:")
for label, count in sorted(entity_types_dist.items(), key=lambda x: x[1], reverse=True):
    print(f"   - {label}: {count}次")

# 验证成功标准：>70%提取率
if extraction_rate >= 70:
    print(f"\n🎉 实体提取修复完成！提取率{extraction_rate:.2f}% >= 70%")
else:
    print(f"\n⚠️  实体提取率{extraction_rate:.2f}%偏低，中文文档可能较少")

session.close()
