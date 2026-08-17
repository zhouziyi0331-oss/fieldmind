#!/usr/bin/env python3
"""测试知识图谱前端集成"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from app.core.database import SessionLocal
from app.models.entity import Entity
from app.models.relation import Relation
from app.models.knowledge_graph import KnowledgeGraph
import json
from datetime import datetime

def create_test_knowledge_graph():
    """创建测试知识图谱数据"""
    db = SessionLocal()

    try:
        # 获取第一个项目
        from app.models.project import Project
        project = db.query(Project).first()

        if not project:
            print("❌ 没有找到项目")
            return

        print(f"✓ 使用项目: {project.name} (ID: {project.id})")

        # 检查是否已有实体
        entities = db.query(Entity).filter(Entity.project_id == project.id).all()

        if not entities or len(entities) < 3:
            print("创建测试实体...")
            # 创建一些测试实体
            test_entities = [
                Entity(
                    entity_id=f"entity_{i}",
                    name=name,
                    entity_type=etype,
                    project_id=project.id,
                    mentions=mentions,
                    context=f"这是{name}的上下文信息",
                    confidence=0.9
                )
                for i, (name, etype, mentions) in enumerate([
                    ("张三", "人物", 5),
                    ("北京大学", "机构", 3),
                    ("人工智能", "文化概念", 8),
                    ("李四", "人物", 4),
                    ("上海", "地名", 6),
                    ("深度学习", "文化概念", 7),
                ])
            ]

            db.add_all(test_entities)
            db.commit()
            entities = test_entities
            print(f"✓ 创建了 {len(test_entities)} 个实体")
        else:
            print(f"✓ 找到 {len(entities)} 个现有实体")

        # 创建关系
        print("创建测试关系...")
        relations = []

        # 确保至少有3个实体
        if len(entities) >= 3:
            relation_data = [
                (entities[0].entity_id, "工作于", entities[1].entity_id, "张三在北京大学工作"),
                (entities[0].entity_id, "研究", entities[2].entity_id, "张三研究人工智能"),
                (entities[3].entity_id, "位于", entities[4].entity_id, "李四位于上海"),
                (entities[3].entity_id, "研究", entities[5].entity_id, "李四研究深度学习"),
                (entities[2].entity_id, "包含", entities[5].entity_id, "人工智能包含深度学习"),
            ]

            for idx, (subj, rel_type, obj, context) in enumerate(relation_data):
                if idx >= len(entities):
                    break

                relation = Relation(
                    relation_id=f"rel_{idx}",
                    subject_entity_id=subj,
                    relation_type=rel_type,
                    object_entity_id=obj,
                    context=context,
                    confidence=0.85
                )
                relations.append(relation)

            db.add_all(relations)
            db.commit()
            print(f"✓ 创建了 {len(relations)} 个关系")

        # 创建知识图谱记录
        print("创建知识图谱记录...")

        # 构建图数据结构
        graph_data = {
            "nodes": [
                {
                    "id": e.entity_id,
                    "name": e.name,
                    "type": e.entity_type,
                    "mentions": e.mentions
                }
                for e in entities[:6]  # 只取前6个
            ],
            "edges": [
                {
                    "id": r.relation_id,
                    "source": r.subject_entity_id,
                    "target": r.object_entity_id,
                    "type": r.relation_type,
                    "confidence": r.confidence
                }
                for r in relations
            ]
        }

        kg = KnowledgeGraph(
            project_id=project.id,
            graph_data=json.dumps(graph_data, ensure_ascii=False),
            entity_count=len(entities[:6]),
            relation_count=len(relations),
            created_at=datetime.now()
        )

        db.add(kg)
        db.commit()

        print(f"\n✅ 知识图谱创建成功！")
        print(f"   - 项目ID: {project.id}")
        print(f"   - 实体数: {len(entities[:6])}")
        print(f"   - 关系数: {len(relations)}")
        print(f"\n🌐 在浏览器中访问:")
        print(f"   http://localhost:3003/projects/{project.id}/knowledge-graph")

        return project.id

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_knowledge_graph()
