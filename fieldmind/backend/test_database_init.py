#!/usr/bin/env python3
"""
FieldMind 数据库初始化测试脚本
测试数据库连接、表创建、基础CRUD操作
"""
import sys
import os
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from datetime import datetime
from app.core.database import engine, SessionLocal, init_db, get_db_context
from app.models import (
    Document, DocumentType, DocumentStatus,
    DocumentMetadata,
    Entity, EntityType, DocumentEntity,
    Tag, DocumentTag,
    DocumentChunk,
)


def test_database_connection():
    """测试数据库连接"""
    print("\n" + "=" * 60)
    print("测试1: 数据库连接")
    print("=" * 60)

    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ 数据库连接成功")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def test_create_tables():
    """测试创建表"""
    print("\n" + "=" * 60)
    print("测试2: 创建数据库表")
    print("=" * 60)

    try:
        init_db()
        print("✅ 数据库表创建成功")
        return True
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False


def test_insert_document():
    """测试插入文档"""
    print("\n" + "=" * 60)
    print("测试3: 插入文档记录")
    print("=" * 60)

    try:
        with get_db_context() as db:
            # 创建测试文档
            document = Document(
                id="test_doc_001",
                project_id=1,
                name="测试文档.pdf",
                type=DocumentType.DOCUMENT,
                mime_type="application/pdf",
                file_size=1024000,
                file_path="/storage/test_doc_001.pdf",
                hash="abc123def456",
                status=DocumentStatus.UPLOADED
            )

            db.add(document)
            db.commit()

            print(f"✅ 文档插入成功: {document.id}")
            print(f"   名称: {document.name}")
            print(f"   类型: {document.type.value}")
            print(f"   状态: {document.status.value}")
            return True

    except Exception as e:
        print(f"❌ 插入文档失败: {e}")
        return False


def test_query_document():
    """测试查询文档"""
    print("\n" + "=" * 60)
    print("测试4: 查询文档记录")
    print("=" * 60)

    try:
        with get_db_context() as db:
            document = db.query(Document).filter_by(id="test_doc_001").first()

            if document:
                print(f"✅ 查询成功:")
                print(f"   ID: {document.id}")
                print(f"   名称: {document.name}")
                print(f"   类型: {document.type.value}")
                print(f"   大小: {document.file_size} bytes")
                print(f"   哈希: {document.hash}")
                return True
            else:
                print("❌ 未找到文档")
                return False

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return False


def test_insert_metadata():
    """测试插入元数据"""
    print("\n" + "=" * 60)
    print("测试5: 插入元数据")
    print("=" * 60)

    try:
        with get_db_context() as db:
            metadata = DocumentMetadata(
                document_id="test_doc_001",
                metadata_type="structure",
                metadata={
                    "page_count": 10,
                    "word_count": 5000,
                    "language": "zh"
                },
                confidence=0.95
            )

            db.add(metadata)
            db.commit()

            print(f"✅ 元数据插入成功")
            print(f"   文档ID: {metadata.document_id}")
            print(f"   类型: {metadata.metadata_type}")
            print(f"   内容: {metadata.metadata}")
            return True

    except Exception as e:
        print(f"❌ 插入元数据失败: {e}")
        return False


def test_insert_entity():
    """测试插入实体"""
    print("\n" + "=" * 60)
    print("测试6: 插入实体")
    print("=" * 60)

    try:
        with get_db_context() as db:
            # 创建实体
            entity = Entity(
                text="张三",
                type=EntityType.PERSON.value,
                canonical_form="张三"
            )
            db.add(entity)
            db.flush()  # 获取entity.id

            # 关联到文档
            doc_entity = DocumentEntity(
                document_id="test_doc_001",
                entity_id=entity.id,
                mentions=3,
                confidence=0.92,
                context="张三在文档中被提到了3次"
            )
            db.add(doc_entity)
            db.commit()

            print(f"✅ 实体插入成功")
            print(f"   实体ID: {entity.id}")
            print(f"   实体文本: {entity.text}")
            print(f"   实体类型: {entity.type}")
            print(f"   提及次数: {doc_entity.mentions}")
            return True

    except Exception as e:
        print(f"❌ 插入实体失败: {e}")
        return False


def test_insert_tag():
    """测试插入标签"""
    print("\n" + "=" * 60)
    print("测试7: 插入标签")
    print("=" * 60)

    try:
        with get_db_context() as db:
            # 创建标签
            tag = Tag(
                name="测试标签",
                category="manual",
                color="#EF4444"
            )
            db.add(tag)
            db.flush()

            # 关联到文档
            doc_tag = DocumentTag(
                document_id="test_doc_001",
                tag_id=tag.id,
                created_by="system"
            )
            db.add(doc_tag)
            db.commit()

            print(f"✅ 标签插入成功")
            print(f"   标签ID: {tag.id}")
            print(f"   标签名称: {tag.name}")
            print(f"   标签颜色: {tag.color}")
            return True

    except Exception as e:
        print(f"❌ 插入标签失败: {e}")
        return False


def test_insert_chunk():
    """测试插入文本分块"""
    print("\n" + "=" * 60)
    print("测试8: 插入文本分块")
    print("=" * 60)

    try:
        with get_db_context() as db:
            chunk = DocumentChunk(
                id="chunk_001",
                document_id="test_doc_001",
                chunk_index=0,
                text="这是第一个文本分块，用于测试RAG功能。",
                token_count=20,
                start_pos=0,
                end_pos=50
            )

            db.add(chunk)
            db.commit()

            print(f"✅ 文本分块插入成功")
            print(f"   分块ID: {chunk.id}")
            print(f"   索引: {chunk.chunk_index}")
            print(f"   Token数: {chunk.token_count}")
            print(f"   文本: {chunk.text}")
            return True

    except Exception as e:
        print(f"❌ 插入分块失败: {e}")
        return False


def test_relationships():
    """测试关系查询"""
    print("\n" + "=" * 60)
    print("测试9: 测试关系查询")
    print("=" * 60)

    try:
        with get_db_context() as db:
            document = db.query(Document).filter_by(id="test_doc_001").first()

            if document:
                # 查询元数据
                metadata_count = document.metadata_entries.count()
                print(f"✅ 文档元数据数量: {metadata_count}")

                # 查询实体
                entities_count = document.entities.count()
                print(f"✅ 文档实体数量: {entities_count}")

                # 查询标签
                tags_count = document.tags.count()
                print(f"✅ 文档标签数量: {tags_count}")

                # 查询分块
                chunks_count = document.chunks.count()
                print(f"✅ 文档分块数量: {chunks_count}")

                return True
            else:
                print("❌ 未找到文档")
                return False

    except Exception as e:
        print(f"❌ 关系查询失败: {e}")
        return False


def test_cleanup():
    """测试清理数据"""
    print("\n" + "=" * 60)
    print("测试10: 清理测试数据")
    print("=" * 60)

    try:
        with get_db_context() as db:
            # 删除测试文档（级联删除相关数据）
            document = db.query(Document).filter_by(id="test_doc_001").first()
            if document:
                db.delete(document)
                db.commit()
                print("✅ 测试数据清理成功")
                return True
            else:
                print("⚠️  未找到测试数据")
                return True

    except Exception as e:
        print(f"❌ 清理失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n")
    print("*" * 60)
    print(" " * 15 + "FieldMind 数据库初始化测试")
    print("*" * 60)

    tests = [
        ("数据库连接", test_database_connection),
        ("创建表", test_create_tables),
        ("插入文档", test_insert_document),
        ("查询文档", test_query_document),
        ("插入元数据", test_insert_metadata),
        ("插入实体", test_insert_entity),
        ("插入标签", test_insert_tag),
        ("插入分块", test_insert_chunk),
        ("关系查询", test_relationships),
        ("清理数据", test_cleanup),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            failed += 1

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"✅ 通过: {passed}/{len(tests)}")
    print(f"❌ 失败: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 所有测试通过！数据库初始化成功！")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查配置和日志")
        return 1


if __name__ == "__main__":
    sys.exit(main())
