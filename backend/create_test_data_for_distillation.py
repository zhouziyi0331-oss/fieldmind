"""
为蒸馏功能创建测试数据
"""
import sys
sys.path.insert(0, 'src')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import uuid

DATABASE_URL = "sqlite:///./fieldmind.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def create_test_data():
    """创建测试数据"""
    print("\n" + "="*60)
    print("📝 创建蒸馏功能测试数据")
    print("="*60 + "\n")

    db = SessionLocal()

    try:
        # 1. 确保有项目
        result = db.execute(text("SELECT id FROM projects LIMIT 1"))
        project = result.fetchone()

        if not project:
            print("❌ 数据库中没有项目，请先创建项目")
            return

        project_id = project[0]
        print(f"✅ 使用项目 ID: {project_id}\n")

        # 2. 检查并创建必要的表
        print("🔧 检查数据库表...")

        # 检查document_chunks表
        try:
            db.execute(text("SELECT 1 FROM document_chunks LIMIT 1"))
            print("  ✅ document_chunks 表存在")
        except:
            print("  ⚠️  document_chunks 表不存在，需要运行迁移")
            print("     提示: 请确保已经执行过数据库迁移")
            return

        # 检查entities表
        try:
            db.execute(text("SELECT 1 FROM entities LIMIT 1"))
            print("  ✅ entities 表存在")
        except:
            print("  ⚠️  entities 表不存在")
            return

        # 检查timeline_events表
        try:
            db.execute(text("SELECT 1 FROM timeline_events LIMIT 1"))
            print("  ✅ timeline_events 表存在")
        except:
            print("  ⚠️  timeline_events 表不存在")

        # 3. 创建测试文档
        print("\n📄 创建测试文档...")

        doc_id = 999
        db.execute(text("""
            INSERT OR IGNORE INTO project_documents (id, project_id, filename, file_type, file_size, status, created_at, updated_at)
            VALUES (:id, :pid, :filename, :ftype, :size, :status, :created, :updated)
        """), {
            "id": doc_id,
            "pid": project_id,
            "filename": "测试访谈记录.txt",
            "ftype": "text",
            "size": 5000,
            "status": "completed",
            "created": datetime.utcnow().isoformat(),
            "updated": datetime.utcnow().isoformat()
        })
        db.commit()
        print(f"  ✅ 创建文档 ID: {doc_id}")

        # 4. 创建测试chunks
        print("\n📦 创建测试chunks...")

        test_chunks = [
            {
                "text": "村支书李明表示，这次土地改革对村民生活影响很大。他说：'我们村的土地流转工作进展顺利，农民收入普遍提高了30%。'",
                "speaker": "李明",
                "entities": [{"name": "李明", "type": "PERSON"}, {"name": "土地改革", "type": "CONCEPT"}],
                "tags": ["土地改革", "农民收入", "政策实施"]
            },
            {
                "text": "王教授在调研中发现，贵州村寨的传统文化保护面临挑战。他特别指出：'非常紧急！必须立即采取措施保护这些濒危的传统技艺。'",
                "speaker": "王教授",
                "entities": [{"name": "王教授", "type": "PERSON"}, {"name": "贵州村寨", "type": "LOCATION"}],
                "tags": ["文化保护", "传统技艺", "紧急措施"]
            },
            {
                "text": "村民张华的成功案例值得推广：他通过创新的茶叶种植技术，实现了年收入翻倍，成为村里的致富带头人。",
                "speaker": None,
                "entities": [{"name": "张华", "type": "PERSON"}, {"name": "茶叶种植", "type": "CONCEPT"}],
                "tags": ["成功案例", "创新", "致富"]
            },
            {
                "text": "李明与村民代表反复讨论，最终形成了一套完整的村务管理方法论。这套方法包括民主决策、透明公开、定期反馈三个核心环节。",
                "speaker": None,
                "entities": [{"name": "李明", "type": "PERSON"}, {"name": "村务管理", "type": "CONCEPT"}],
                "tags": ["方法论", "民主决策", "管理创新"]
            },
            {
                "text": "调研发现，年轻人流失问题需要立即解决。建议建立返乡创业扶持政策，提供创业资金和技术培训支持。",
                "speaker": None,
                "entities": [{"name": "返乡创业", "type": "CONCEPT"}],
                "tags": ["问题分析", "政策建议", "人才流失"]
            },
            {
                "text": "李明和王教授合作推动了文化旅游项目，张华负责茶叶销售，三人形成了良好的协作网络。",
                "speaker": None,
                "entities": [{"name": "李明", "type": "PERSON"}, {"name": "王教授", "type": "PERSON"}, {"name": "张华", "type": "PERSON"}],
                "tags": ["合作", "文化旅游", "协同发展"]
            }
        ]

        chunk_ids = []
        for i, chunk_data in enumerate(test_chunks):
            chunk_id = f"test_chunk_{i+1}"

            db.execute(text("""
                INSERT OR IGNORE INTO document_chunks (
                    id, chunk_id, document_id, project_id, chunk_index,
                    text, legacy_chunk_text, text_length, legacy_chunk_size,
                    speaker, key_entities, domain_tags, created_at
                )
                VALUES (
                    :id, :chunk_id, :doc_id, :pid, :idx,
                    :text, :text, :length, :length,
                    :speaker, :entities, :tags, :created
                )
            """), {
                "id": 1000 + i,
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "pid": project_id,
                "idx": i,
                "text": chunk_data["text"],
                "length": len(chunk_data["text"]),
                "speaker": chunk_data["speaker"],
                "entities": json.dumps(chunk_data["entities"]),
                "tags": json.dumps(chunk_data["tags"]),
                "created": datetime.utcnow().isoformat()
            })
            chunk_ids.append(1000 + i)

        db.commit()
        print(f"  ✅ 创建了 {len(test_chunks)} 个chunks")

        # 5. 创建测试实体
        print("\n👤 创建测试实体...")

        test_entities = [
            {"text": "李明", "type": "PERSON"},
            {"text": "王教授", "type": "PERSON"},
            {"text": "张华", "type": "PERSON"},
            {"text": "土地改革", "type": "CONCEPT"},
            {"text": "贵州村寨", "type": "LOCATION"},
            {"text": "茶叶种植", "type": "CONCEPT"},
        ]

        entity_ids = []
        for entity_data in test_entities:
            entity_id = str(uuid.uuid4())

            try:
                db.execute(text("""
                    INSERT INTO entities (id, text, type, legacy_name, legacy_entity_type, created_at, updated_at)
                    VALUES (:id, :text, :type, :text, :type, :created, :updated)
                """), {
                    "id": entity_id,
                    "text": entity_data["text"],
                    "type": entity_data["type"],
                    "created": datetime.utcnow().isoformat(),
                    "updated": datetime.utcnow().isoformat()
                })
                entity_ids.append(entity_id)
            except:
                # 实体可能已存在
                result = db.execute(text("SELECT id FROM entities WHERE text = :text AND type = :type"), {
                    "text": entity_data["text"],
                    "type": entity_data["type"]
                })
                existing = result.fetchone()
                if existing:
                    entity_ids.append(existing[0])

        db.commit()
        print(f"  ✅ 创建了 {len(entity_ids)} 个实体")

        # 6. 创建实体关系
        print("\n🔗 创建实体关系...")

        if len(entity_ids) >= 3:
            relations = [
                {"source": entity_ids[0], "target": entity_ids[1], "type": "合作"},
                {"source": entity_ids[0], "target": entity_ids[2], "type": "领导"},
                {"source": entity_ids[1], "target": entity_ids[2], "type": "指导"},
            ]

            for rel in relations:
                try:
                    db.execute(text("""
                        INSERT INTO entity_relations (source_entity_id, target_entity_id, relation_type, created_at, updated_at)
                        VALUES (:source, :target, :type, :created, :updated)
                    """), {
                        "source": rel["source"],
                        "target": rel["target"],
                        "type": rel["type"],
                        "created": datetime.utcnow().isoformat(),
                        "updated": datetime.utcnow().isoformat()
                    })
                except:
                    pass  # 关系可能已存在

            db.commit()
            print(f"  ✅ 创建了 {len(relations)} 个关系")

        # 7. 创建时间线事件
        print("\n📅 创建时间线事件...")

        test_events = [
            {"title": "土地改革启动会议", "date": "2024-01-15", "category": "政策"},
            {"title": "村民代表大会", "date": "2024-03-20", "category": "会议"},
            {"title": "茶叶合作社成立", "date": "2024-06-10", "category": "经济"},
            {"title": "文化旅游项目启动", "date": "2024-09-05", "category": "文化"},
        ]

        for event_data in test_events:
            event_id = str(uuid.uuid4())

            try:
                db.execute(text("""
                    INSERT INTO timeline_events (id, project_id, title, date, category, created_at, updated_at)
                    VALUES (:id, :pid, :title, :date, :category, :created, :updated)
                """), {
                    "id": event_id,
                    "pid": project_id,
                    "title": event_data["title"],
                    "date": event_data["date"],
                    "category": event_data["category"],
                    "created": datetime.utcnow().isoformat(),
                    "updated": datetime.utcnow().isoformat()
                })
            except:
                pass

        db.commit()
        print(f"  ✅ 创建了 {len(test_events)} 个事件")

        # 8. 统计
        print("\n" + "="*60)
        print("✅ 测试数据创建完成!")
        print("="*60 + "\n")

        print("📊 数据统计:")
        print(f"  - 项目ID: {project_id}")
        print(f"  - 文档: 1 个")
        print(f"  - Chunks: {len(test_chunks)} 个")
        print(f"  - 实体: {len(entity_ids)} 个")
        print(f"  - 关系: 3 个")
        print(f"  - 事件: {len(test_events)} 个")

        print("\n💡 现在可以运行: python3 test_distillation_phase2.py")

    except Exception as e:
        print(f"\n❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()

    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()
