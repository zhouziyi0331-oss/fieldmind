"""
测试蒸馏功能 Phase 2 - 完整提取逻辑测试
"""
import sys
sys.path.insert(0, 'src')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.services.distillation_engine import DistillationEngine
from app.models.distillation import DistilledUnit

# 使用测试数据库
DATABASE_URL = "sqlite:///./fieldmind.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def test_distillation_engine():
    """测试蒸馏引擎"""
    print("\n" + "="*60)
    print("🧪 Phase 2 蒸馏引擎测试")
    print("="*60 + "\n")

    db = SessionLocal()

    try:
        # 1. 检查数据库中是否有项目
        result = db.execute(text("SELECT id, name FROM projects LIMIT 5"))
        projects = result.fetchall()

        if not projects:
            print("⚠️  数据库中没有项目数据")
            print("提示: 请先创建项目并上传文档")
            return

        print(f"📊 发现 {len(projects)} 个项目:\n")
        for project in projects:
            print(f"  - ID: {project[0]}, 名称: {project[1]}")

        # 2. 选择第一个项目进行蒸馏测试
        project_id = projects[0][0]
        project_name = projects[0][1]

        print(f"\n🎯 测试项目: {project_name} (ID: {project_id})\n")

        # 3. 检查项目的结构化数据
        print("📋 检查结构化数据:")

        # Chunks
        chunks_count = db.execute(
            text("SELECT COUNT(*) FROM document_chunks WHERE project_id = :pid"),
            {"pid": project_id}
        ).scalar()
        print(f"  - Chunks: {chunks_count} 个")

        # Entities (通过document_entities)
        entities_count = db.execute(text("""
            SELECT COUNT(DISTINCT de.entity_id)
            FROM document_entities de
            JOIN document_chunks dc ON CAST(de.document_id AS INTEGER) = dc.document_id
            WHERE dc.project_id = :pid
        """), {"pid": project_id}).scalar()
        print(f"  - Entities: {entities_count} 个")

        # Events
        events_count = db.execute(
            text("SELECT COUNT(*) FROM timeline_events WHERE project_id = :pid"),
            {"pid": project_id}
        ).scalar()
        print(f"  - Events: {events_count} 个")

        if chunks_count == 0:
            print("\n⚠️  项目没有chunks数据，无法进行蒸馏")
            print("提示: 请先上传文档并进行处理")
            return

        # 4. 执行蒸馏
        print(f"\n🔬 开始蒸馏...\n")

        engine = DistillationEngine(db)
        result = engine.distill_project(project_id)

        print("\n" + "="*60)
        print("✅ 蒸馏完成!")
        print("="*60 + "\n")

        # 5. 显示统计结果
        print("📊 蒸馏结果统计:\n")
        print(f"  总计: {result['total_units']} 个知识单元\n")

        breakdown = result['breakdown']
        unit_type_names = {
            'insights': '核心洞察',
            'quotes': '经典原话',
            'models': '思维模型',
            'cases': '案例应用',
            'actions': '行动建议',
            'methods': '方法论'
        }

        for key, count in breakdown.items():
            name = unit_type_names.get(key, key)
            icon = "🔍" if key == "insights" else \
                   "💬" if key == "quotes" else \
                   "🧠" if key == "models" else \
                   "📚" if key == "cases" else \
                   "⚡" if key == "actions" else "📖"
            print(f"  {icon} {name}: {count} 个")

        # 6. 展示每类产物的示例
        print("\n" + "="*60)
        print("🎯 知识单元示例")
        print("="*60 + "\n")

        for unit_type, type_name in unit_type_names.items():
            units = db.query(DistilledUnit).filter(
                DistilledUnit.project_id == project_id,
                DistilledUnit.unit_type == unit_type
            ).limit(2).all()

            if units:
                icon = "🔍" if unit_type == "insights" else \
                       "💬" if unit_type == "quotes" else \
                       "🧠" if unit_type == "models" else \
                       "📚" if unit_type == "cases" else \
                       "⚡" if unit_type == "actions" else "📖"

                print(f"{icon} {type_name}:")
                for i, unit in enumerate(units, 1):
                    print(f"\n  [{i}] {unit.title}")
                    print(f"      可信度: {unit.credibility:.2f} | 置信度: {unit.confidence:.2f}")
                    content_preview = unit.content[:100] + "..." if len(unit.content) > 100 else unit.content
                    print(f"      内容: {content_preview}")
                print()

        # 7. 测试溯源功能
        print("="*60)
        print("🔗 测试溯源功能")
        print("="*60 + "\n")

        # 找一个有来源的单元
        unit_with_sources = db.query(DistilledUnit).filter(
            DistilledUnit.project_id == project_id,
            DistilledUnit.source_chunks != '[]',
            DistilledUnit.source_chunks.isnot(None)
        ).first()

        if unit_with_sources:
            print(f"测试单元: {unit_with_sources.title}")
            sources = engine.get_unit_sources(unit_with_sources.id)
            print(f"找到 {len(sources)} 个来源chunk:\n")

            for i, source in enumerate(sources[:3], 1):
                print(f"  [{i}] Chunk {source['chunk_id']}")
                if source.get('document_name'):
                    print(f"      文档: {source['document_name']}")
                if source.get('page_number'):
                    print(f"      页码: {source['page_number']}")
                if source.get('speaker'):
                    print(f"      说话人: {source['speaker']}")
                content = source.get('content', '')[:80]
                print(f"      内容: {content}...")
                print()

        print("\n" + "="*60)
        print("✅ Phase 2 测试完成!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    test_distillation_engine()
