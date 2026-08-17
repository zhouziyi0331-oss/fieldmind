#!/usr/bin/env python3
"""
测试完整音频处理流程
包括：音频转录 -> 实体抽取 -> 知识图谱构建
"""
import sys
import os
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "backend" / "src"))

def test_audio_pipeline():
    """测试完整的音频处理流程"""

    print("=" * 60)
    print("音频处理流程测试")
    print("=" * 60)

    # 1. 检查文件
    audio_file = Path(__file__).parent / "backend" / "src" / "uploads" / "test_audio.wav"
    if not audio_file.exists():
        print(f"❌ 音频文件不存在: {audio_file}")
        return False

    print(f"\n✓ 音频文件: {audio_file}")
    print(f"  大小: {audio_file.stat().st_size / 1024 / 1024:.2f} MB")

    # 2. 检查配置
    print("\n" + "-" * 60)
    print("检查配置")
    print("-" * 60)

    try:
        from app.config import settings
        print(f"✓ 环境: {settings.ENVIRONMENT}")
        print(f"✓ 数据库: {settings.DATABASE_URL}")

        # 检查OpenAI API Key
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("sk-your"):
            print("⚠️  OPENAI_API_KEY 未配置或使用占位符")
            print("   需要真实的API key才能进行音频转录和实体抽取")
            return False
        else:
            print(f"✓ OPENAI_API_KEY: {'*' * 20}{settings.OPENAI_API_KEY[-4:]}")

    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

    # 3. 初始化服务
    print("\n" + "-" * 60)
    print("初始化服务")
    print("-" * 60)

    try:
        from app.database import SessionLocal
        from app.services.audio_processor import AudioProcessor
        from app.services.entity_extractor import EntityExtractor
        from app.services.knowledge_graph_builder import KnowledgeGraphBuilder

        db = SessionLocal()

        audio_processor = AudioProcessor()
        entity_extractor = EntityExtractor()
        kg_builder = KnowledgeGraphBuilder(db)

        print("✓ 数据库连接成功")
        print("✓ 音频处理器已初始化")
        print("✓ 实体抽取器已初始化")
        print("✓ 知识图谱构建器已初始化")

    except Exception as e:
        print(f"❌ 服务初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 4. 测试音频转录
    print("\n" + "-" * 60)
    print("步骤1: 音频转录")
    print("-" * 60)

    try:
        start_time = time.time()
        print(f"开始转录 {audio_file.name}...")

        transcript = audio_processor.transcribe(str(audio_file))

        elapsed = time.time() - start_time
        print(f"✓ 转录完成 (耗时: {elapsed:.2f}秒)")
        print(f"\n转录文本预览:")
        print("-" * 60)
        print(transcript[:500] + ("..." if len(transcript) > 500 else ""))
        print("-" * 60)
        print(f"总长度: {len(transcript)} 字符")

    except Exception as e:
        print(f"❌ 音频转录失败: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        return False

    # 5. 测试实体抽取
    print("\n" + "-" * 60)
    print("步骤2: 实体抽取")
    print("-" * 60)

    try:
        start_time = time.time()
        print("开始抽取实体...")

        entities = entity_extractor.extract_entities(transcript)

        elapsed = time.time() - start_time
        print(f"✓ 实体抽取完成 (耗时: {elapsed:.2f}秒)")
        print(f"  发现 {len(entities)} 个实体")

        # 显示实体统计
        entity_types = {}
        for entity in entities:
            entity_type = entity.get('type', 'unknown')
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

        print("\n实体类型分布:")
        for entity_type, count in sorted(entity_types.items(), key=lambda x: -x[1]):
            print(f"  - {entity_type}: {count}")

        print("\n前5个实体示例:")
        for i, entity in enumerate(entities[:5], 1):
            print(f"  {i}. {entity.get('name')} ({entity.get('type')})")

    except Exception as e:
        print(f"❌ 实体抽取失败: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        return False

    # 6. 测试知识图谱构建
    print("\n" + "-" * 60)
    print("步骤3: 知识图谱构建")
    print("-" * 60)

    try:
        start_time = time.time()
        print("开始构建知识图谱...")

        # 创建测试项目（如果不存在）
        from app.models.project import Project
        project = db.query(Project).filter(Project.id == 1).first()
        if not project:
            project = Project(name="测试项目", description="音频测试")
            db.add(project)
            db.commit()
            db.refresh(project)

        # 创建文档记录
        from app.models.document import Document
        doc = Document(
            filename="test_audio.wav",
            file_path=str(audio_file),
            file_type="audio/wav",
            file_size=audio_file.stat().st_size,
            project_id=project.id,
            content=transcript
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        print(f"✓ 文档记录已创建 (ID: {doc.id})")

        # 构建知识图谱
        result = kg_builder.build_from_documents([doc])

        elapsed = time.time() - start_time
        print(f"✓ 知识图谱构建完成 (耗时: {elapsed:.2f}秒)")
        print(f"\n构建结果:")
        print(f"  - 实体数: {result.get('entities_count', 0)}")
        print(f"  - 关系数: {result.get('relations_count', 0)}")
        print(f"  - 时间线事件: {result.get('timeline_events_count', 0)}")

    except Exception as e:
        print(f"❌ 知识图谱构建失败: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        return False

    # 7. 验证数据库
    print("\n" + "-" * 60)
    print("步骤4: 验证数据库")
    print("-" * 60)

    try:
        from app.models.entity import Entity
        from app.models.relation import Relation

        entity_count = db.query(Entity).filter(Entity.project_id == project.id).count()
        relation_count = db.query(Relation).filter(Relation.project_id == project.id).count()

        print(f"✓ 数据库验证通过")
        print(f"  - 实体总数: {entity_count}")
        print(f"  - 关系总数: {relation_count}")

        # 显示部分实体
        entities = db.query(Entity).filter(Entity.project_id == project.id).limit(5).all()
        print(f"\n前5个实体:")
        for i, entity in enumerate(entities, 1):
            print(f"  {i}. {entity.name} ({entity.entity_type})")

    except Exception as e:
        print(f"❌ 数据库验证失败: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        return False

    finally:
        db.close()

    # 总结
    print("\n" + "=" * 60)
    print("✅ 音频处理流程测试完成")
    print("=" * 60)
    print("\n完整流程:")
    print("  ✓ 音频文件加载")
    print("  ✓ 音频转录 (Whisper)")
    print("  ✓ 实体抽取 (OpenAI)")
    print("  ✓ 知识图谱构建")
    print("  ✓ 数据库存储")
    print("  ✓ 数据验证")

    return True


if __name__ == "__main__":
    success = test_audio_pipeline()
    sys.exit(0 if success else 1)
