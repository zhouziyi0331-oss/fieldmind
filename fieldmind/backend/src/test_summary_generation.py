"""
测试文件缩影生成功能
Test File Summary Generation

功能：
1. 测试数据库表是否创建成功
2. 测试缩影生成服务
3. 测试 API 接口

运行方式：
    cd /Users/alwan/Downloads/FieldMind/fieldmind/backend/src
    python test_summary_generation.py
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import SessionLocal, init_db
from app.models.project import ProjectDocument, Project
from app.services.summary_generator import FileSummaryGenerator, save_summary
from sqlalchemy import text
import json

def test_database_tables():
    """测试数据库表是否创建成功"""
    print("\n" + "="*60)
    print("测试 1: 检查数据库表")
    print("="*60)

    db = SessionLocal()

    try:
        # 检查 file_summaries 表
        result = db.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='file_summaries'
        """)).fetchone()

        if result:
            print("✅ file_summaries 表存在")
        else:
            print("❌ file_summaries 表不存在")
            return False

        # 检查 FTS5 索引
        result = db.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='file_summaries_fts'
        """)).fetchone()

        if result:
            print("✅ file_summaries_fts FTS5 索引存在")
        else:
            print("❌ file_summaries_fts FTS5 索引不存在")
            return False

        # 检查触发器
        triggers = db.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='trigger' AND tbl_name='file_summaries'
        """)).fetchall()

        print(f"✅ 找到 {len(triggers)} 个触发器")
        for trigger in triggers:
            print(f"   - {trigger[0]}")

        # 查看表结构
        columns = db.execute(text("""
            PRAGMA table_info(file_summaries)
        """)).fetchall()

        print(f"\n✅ file_summaries 表结构（{len(columns)} 个字段）:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        db.close()


def test_summary_generation():
    """测试缩影生成服务"""
    print("\n" + "="*60)
    print("测试 2: 缩影生成服务")
    print("="*60)

    db = SessionLocal()

    try:
        # 查找一个已处理的文档
        doc = db.query(ProjectDocument).filter(
            ProjectDocument.status == 'completed'
        ).first()

        if not doc:
            print("⚠️  没有找到已处理的文档，跳过测试")
            return True

        print(f"📄 找到文档: {doc.original_filename} (ID: {doc.id})")
        print(f"   项目ID: {doc.project_id}")
        print(f"   文件类型: {doc.file_type}")
        print(f"   状态: {doc.status}")

        # 生成缩影
        print("\n🔄 开始生成缩影...")
        generator = FileSummaryGenerator(db)
        summary_data = generator.generate_summary(doc.id)

        print("\n✅ 缩影生成完成!")
        print(f"   一句话摘要: {summary_data['one_line_summary']}")
        print(f"   关键词数量: {len(json.loads(summary_data['top_keywords']))}")
        print(f"   实体数量: {len(json.loads(summary_data['top_entities']))}")
        print(f"   主题数量: {len(json.loads(summary_data['top_topics']))}")
        print(f"   字数: {summary_data['word_count']}")
        print(f"   分块数: {summary_data['chunk_count']}")
        print(f"   主要维度: {summary_data['primary_dimension']}")

        # 保存到数据库
        print("\n💾 保存到数据库...")
        save_summary(db, summary_data)
        print("✅ 保存成功!")

        # 验证保存结果
        print("\n🔍 验证保存结果...")
        result = db.execute(text("""
            SELECT id, document_id, one_line_summary, status
            FROM file_summaries
            WHERE document_id = :document_id
        """), {'document_id': doc.id}).fetchone()

        if result:
            print(f"✅ 缩影已保存到数据库")
            print(f"   缩影ID: {result[0]}")
            print(f"   文档ID: {result[1]}")
            print(f"   摘要: {result[2]}")
            print(f"   状态: {result[3]}")
        else:
            print("❌ 缩影未找到")
            return False

        # 测试 FTS5 搜索
        print("\n🔍 测试 FTS5 全文搜索...")
        keywords = json.loads(summary_data['top_keywords'])
        if keywords:
            test_keyword = keywords[0]['word']
            print(f"   搜索关键词: {test_keyword}")

            search_result = db.execute(text("""
                SELECT s.id, s.one_line_summary
                FROM file_summaries s
                JOIN file_summaries_fts f ON s.id = f.rowid
                WHERE f.file_summaries_fts MATCH :keyword
            """), {'keyword': test_keyword}).fetchall()

            print(f"✅ 找到 {len(search_result)} 条匹配结果")
            for row in search_result:
                print(f"   - 缩影ID {row[0]}: {row[1][:50]}...")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_api_queries():
    """测试常见查询场景"""
    print("\n" + "="*60)
    print("测试 3: 常见查询场景")
    print("="*60)

    db = SessionLocal()

    try:
        # 场景1: 获取项目的所有缩影
        print("\n📋 场景1: 获取项目的所有缩影")
        result = db.execute(text("""
            SELECT COUNT(*) FROM file_summaries WHERE project_id = 1
        """)).scalar()
        print(f"   项目1共有 {result} 条缩影")

        # 场景2: 按维度统计
        print("\n📊 场景2: 按维度统计")
        results = db.execute(text("""
            SELECT primary_dimension, COUNT(*) as count
            FROM file_summaries
            WHERE project_id = 1
            GROUP BY primary_dimension
            ORDER BY count DESC
        """)).fetchall()

        for row in results:
            print(f"   {row[0]}: {row[1]} 个文档")

        # 场景3: 获取最近生成的缩影
        print("\n🕐 场景3: 最近生成的缩影")
        results = db.execute(text("""
            SELECT document_id, one_line_summary, generated_at
            FROM file_summaries
            ORDER BY generated_at DESC
            LIMIT 5
        """)).fetchall()

        for row in results:
            print(f"   文档{row[0]}: {row[1][:50]}...")
            print(f"   生成时间: {row[2]}")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        db.close()


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("FieldMind 文件缩影系统测试")
    print("="*60)

    # 初始化数据库
    print("\n🔧 初始化数据库...")
    init_db()

    # 运行测试
    results = []

    results.append(("数据库表检查", test_database_tables()))
    results.append(("缩影生成服务", test_summary_generation()))
    results.append(("常见查询场景", test_api_queries()))

    # 输出测试结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n🎉 所有测试通过!")
    else:
        print("\n⚠️  部分测试失败，请检查上面的错误信息")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
