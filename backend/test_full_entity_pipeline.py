#!/usr/bin/env python3
"""
重新处理历史文档，验证完整的实体提取+持久化流程
"""

import sys
sys.path.insert(0, '/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.document_processing_pipeline import DocumentProcessingPipeline
from app.models.document import Document

# 连接数据库
engine = create_engine('sqlite:////Users/alwan/FieldMind-Rebuild/fieldmind-backend/data/fieldmind.db')
Session = sessionmaker(bind=engine)
db = Session()

# 查找一个已完成的文档（有文本内容）
doc = db.query(Document).filter(
    Document.status == 'completed',
    Document.text_content.isnot(None)
).first()

if not doc:
    print("❌ 没有找到可处理的文档")
    exit(1)

print(f"📄 选择文档: ID={doc.id}, 文件名={doc.file_name}")
print(f"   文本长度: {len(doc.text_content or '')} 字符")

# 统计处理前的实体数
before_count = db.execute(text("SELECT COUNT(*) FROM entities")).scalar()
print(f"\n📊 处理前实体总数: {before_count}")

# 初始化pipeline
pipeline = DocumentProcessingPipeline()

# 仅执行知识图谱构建阶段
try:
    from app.services.knowledge_graph_service import get_knowledge_graph_service

    kg_service = get_knowledge_graph_service()

    print(f"\n🔄 开始提取实体...")
    entities, relations = kg_service.extract_entities_and_relations(
        doc.text_content,
        document_id=doc.id,
        use_llm=False  # 仅用spaCy+规则，避免LLM开销
    )

    print(f"✅ 提取结果: {len(entities)}个实体, {len(relations)}个关系")

    # 显示实体样本
    print(f"\n📝 实体样本（前10个）:")
    for i, entity in enumerate(entities[:10], 1):
        print(f"   {i}. {entity.name} ({entity.entity_type})")

    # 添加到图谱（会触发持久化）
    kg_service.add_entities_and_relations(entities, relations)

    # 统计处理后的实体数
    after_count = db.execute(text("SELECT COUNT(*) FROM entities")).scalar()
    new_entities = after_count - before_count

    print(f"\n{'='*60}")
    print(f"✅ 处理完成！")
    print(f"   处理前实体数: {before_count}")
    print(f"   处理后实体数: {after_count}")
    print(f"   新增实体数: {new_entities}")

    # 按类型统计
    result = db.execute(text("""
        SELECT entity_type, COUNT(*) as count
        FROM entities
        GROUP BY entity_type
        ORDER BY count DESC
    """))

    print(f"\n📊 实体类型分布:")
    for entity_type, count in result.fetchall():
        print(f"   {entity_type}: {count}")

except Exception as e:
    print(f"❌ 处理失败: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
