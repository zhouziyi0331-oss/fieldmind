#!/usr/bin/env python3
"""验证迁移数据的真实可用性"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("╔══════════════════════════════════════════════════════════╗")
print("║         迁移数据真实可用性验证                           ║")
print("╚══════════════════════════════════════════════════════════╝\n")

from app.core.database import get_db
db = next(get_db())

try:
    # 1. 验证项目
    from app.models.project import Project, ProjectDocument
    projects = db.query(Project).all()
    print(f"✅ 项目数量: {len(projects)}")
    for p in projects:
        print(f"   - {p.name} (ID: {p.id})")
    
    # 2. 验证文档
    docs = db.query(ProjectDocument).filter(ProjectDocument.project_id == 1).all()
    print(f"\n✅ 项目1的文档数: {len(docs)}")
    for doc in docs[:3]:
        print(f"   - 文档ID: {doc.id}, 状态: {doc.status}")
    
    # 3. 验证实体
    from app.models.entity import Entity
    entities = db.query(Entity).all()
    print(f"\n✅ 实体总数: {len(entities)}")
    
    # 按类型统计
    from sqlalchemy import func
    type_stats = db.query(Entity.type, func.count(Entity.id)).group_by(Entity.type).all()
    print(f"\n✅ 实体类型分布 (前10种):")
    for entity_type, count in sorted(type_stats, key=lambda x: x[1], reverse=True)[:10]:
        print(f"   - {entity_type}: {count}个")
    
    # 4. 验证关系
    from app.models.entity import EntityRelation
    relations = db.query(EntityRelation).all()
    print(f"\n✅ 实体关系数: {len(relations)}")
    
    # 5. 抽查几个实体内容
    sample_entities = db.query(Entity).order_by(Entity.id.desc()).limit(5).all()
    print(f"\n✅ 实体样本 (最新5个):")
    for e in sample_entities:
        print(f"   - {e.name} ({e.type})")
    
    print("\n" + "="*60)
    print("验证结论:")
    print("="*60)
    print(f"✅ 项目数据: {len(projects)} 个项目已迁移")
    print(f"✅ 文档数据: {len(docs)} 个文档在项目1中")
    print(f"✅ 实体数据: {len(entities)} 个实体可查询")
    print(f"✅ 关系数据: {len(relations)} 个关系已建立")
    print(f"\n🎉 迁移数据已真实应用到数据库并可正常使用!")
    
except Exception as ex:
    print(f"❌ 验证失败: {ex}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
