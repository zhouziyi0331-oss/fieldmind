#!/usr/bin/env python3
"""
向量化链路完整诊断脚本
检查：文档上传 → 切分 → 向量化 → 数据库存储 → 检索的完整链路
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_database_schema(db_path: str):
    """检查数据库表结构"""
    print("\n" + "="*80)
    print("第1步：检查数据库表结构")
    print("="*80)

    engine = create_engine(f"sqlite:///{db_path}")

    with engine.connect() as conn:
        # 检查核心表是否存在
        tables_to_check = [
            'project_documents',
            'document_chunks',
            'embeddings',
            'processing_tasks'
        ]

        for table in tables_to_check:
            result = conn.execute(text(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
            ))
            exists = result.fetchone()

            if exists:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"✅ {table:30s} | 记录数: {count}")
            else:
                print(f"❌ {table:30s} | 表不存在")

    return engine


def check_document_chunks_structure(engine):
    """检查document_chunks表的详细结构"""
    print("\n" + "="*80)
    print("第2步：检查document_chunks表结构")
    print("="*80)

    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='document_chunks'"
        ))
        schema = result.fetchone()

        if schema:
            print("表结构：")
            print(schema[0])

            # 检查关键字段
            key_fields = [
                'chunk_id', 'document_id', 'project_id', 'text',
                'embedding', 'chunk_index', 'text_length'
            ]

            schema_sql = schema[0].lower()
            print("\n关键字段检查：")
            for field in key_fields:
                if field.lower() in schema_sql:
                    print(f"  ✅ {field}")
                else:
                    print(f"  ❌ {field} (缺失)")
        else:
            print("❌ document_chunks表不存在")


def check_sample_documents(engine):
    """检查示例文档"""
    print("\n" + "="*80)
    print("第3步：检查已上传文档")
    print("="*80)

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                id,
                filename,
                file_type,
                status,
                chunk_count,
                word_count,
                created_at
            FROM project_documents
            ORDER BY created_at DESC
            LIMIT 10
        """))

        docs = result.fetchall()

        if docs:
            print(f"找到 {len(docs)} 个文档：\n")
            for doc in docs:
                doc_id, filename, file_type, status, chunk_count, word_count, created_at = doc
                print(f"文档ID: {doc_id}")
                print(f"  文件名: {filename}")
                print(f"  类型: {file_type}")
                print(f"  状态: {status}")
                print(f"  chunk数: {chunk_count}")
                print(f"  词数: {word_count}")
                print(f"  创建时间: {created_at}")
                print()
        else:
            print("❌ 没有找到任何文档")
            print("   原因可能是：")
            print("   1. 从未上传过文档")
            print("   2. 文档上传API未被调用")
            print("   3. 数据库路径配置错误")


def check_chunks_for_document(engine, document_id: int = None):
    """检查特定文档的chunks"""
    print("\n" + "="*80)
    print("第4步：检查文档切分结果")
    print("="*80)

    with engine.connect() as conn:
        if document_id:
            query = text("""
                SELECT
                    chunk_id,
                    chunk_index,
                    text_length,
                    embedding IS NOT NULL as has_embedding,
                    SUBSTR(text, 1, 100) as text_preview
                FROM document_chunks
                WHERE document_id = :doc_id
                ORDER BY chunk_index
                LIMIT 5
            """)
            result = conn.execute(query, {"doc_id": document_id})
        else:
            # 获取任意文档的chunks
            query = text("""
                SELECT
                    chunk_id,
                    document_id,
                    chunk_index,
                    text_length,
                    embedding IS NOT NULL as has_embedding,
                    SUBSTR(text, 1, 100) as text_preview
                FROM document_chunks
                ORDER BY document_id, chunk_index
                LIMIT 10
            """)
            result = conn.execute(query)

        chunks = result.fetchall()

        if chunks:
            print(f"找到 {len(chunks)} 个chunks：\n")
            for chunk in chunks:
                if document_id:
                    chunk_id, chunk_idx, text_len, has_emb, preview = chunk
                    print(f"Chunk {chunk_idx}:")
                else:
                    chunk_id, doc_id, chunk_idx, text_len, has_emb, preview = chunk
                    print(f"文档{doc_id} - Chunk {chunk_idx}:")

                print(f"  ID: {chunk_id}")
                print(f"  文本长度: {text_len}")
                print(f"  有向量: {'✅' if has_emb else '❌'}")
                print(f"  预览: {preview}...")
                print()
        else:
            print("❌ 没有找到任何chunks")
            print("   这说明文档处理管道没有执行到切分阶段")


def check_processing_pipeline_config():
    """检查处理管道配置"""
    print("\n" + "="*80)
    print("第5步：检查处理管道配置")
    print("="*80)

    try:
        from app.config import settings

        print(f"数据库URL: {settings.DATABASE_URL}")
        print(f"上传目录: {settings.UPLOAD_DIR}")
        print(f"向量化模型: {getattr(settings, 'VECTORIZATION_MODEL_PATH', '未配置')}")
        print(f"ChromaDB启用: {getattr(settings, 'ENABLE_CHROMA_INDEXING', False)}")
        print(f"动态发现启用: {getattr(settings, 'ENABLE_DYNAMIC_DISCOVERY', False)}")
        print(f"工作流串联启用: {getattr(settings, 'ENABLE_WORKFLOW_CHAINING', False)}")

    except Exception as e:
        print(f"❌ 无法加载配置: {e}")


def check_vectorization_service():
    """检查向量化服务"""
    print("\n" + "="*80)
    print("第6步：检查向量化服务")
    print("="*80)

    try:
        from app.services.semantic_embedding import get_embedding_model

        print("正在加载向量化模型...")
        model = get_embedding_model()

        if model:
            print("✅ 向量化模型加载成功")

            # 测试向量化
            test_text = "这是一个测试文本"
            try:
                if hasattr(model, 'encode'):
                    vector = model.encode(test_text)
                    print(f"✅ 向量化测试成功，维度: {len(vector)}")
                else:
                    print("⚠️ 模型没有encode方法")
            except Exception as e:
                print(f"❌ 向量化测试失败: {e}")
        else:
            print("❌ 向量化模型加载失败")
            print("   将使用TF-IDF降级方案")

    except Exception as e:
        print(f"❌ 向量化服务检查失败: {e}")


def check_background_tasks():
    """检查后台任务状态"""
    print("\n" + "="*80)
    print("第7步：检查后台任务执行状态")
    print("="*80)

    try:
        from app.services.background_tasks import _active_tasks

        if _active_tasks:
            print(f"活跃任务数: {len(_active_tasks)}")
            for doc_id, future in _active_tasks.items():
                status = "运行中" if not future.done() else "已完成"
                print(f"  文档 {doc_id}: {status}")
        else:
            print("当前没有活跃的后台任务")

    except Exception as e:
        print(f"⚠️ 无法检查后台任务: {e}")


def test_document_upload_and_processing():
    """测试完整的文档上传和处理流程"""
    print("\n" + "="*80)
    print("第8步：测试文档上传和处理流程")
    print("="*80)

    try:
        # 创建测试文本文件
        test_file = Path("/tmp/test_document.txt")
        test_content = """
这是一个测试文档。

第一段：这个文档用于测试FieldMind的文档处理能力。
我们希望验证文档能够被正确切分、向量化并存储到数据库中。

第二段：向量化是知识管理系统的核心能力。
只有正确的向量化，才能实现语义搜索和智能检索。

第三段：如果这个测试成功，我们就能确认整个处理链路是完整的。
从文档上传到最终可检索，每一步都需要正常工作。
        """.strip()

        test_file.write_text(test_content, encoding='utf-8')
        print(f"✅ 创建测试文件: {test_file}")
        print(f"   内容长度: {len(test_content)} 字符")

        print("\n建议手动测试步骤：")
        print("1. 启动后端服务: cd src && uvicorn app.main:app --reload")
        print("2. 创建测试项目（如果没有）")
        print("3. 上传测试文件:")
        print(f"   curl -X POST http://localhost:8000/api/v1/documents/upload \\")
        print(f"        -F 'project_id=1' \\")
        print(f"        -F 'file=@{test_file}' \\")
        print(f"        -F 'auto_process=true'")
        print("4. 查看处理结果:")
        print("   SELECT * FROM document_chunks WHERE document_id = (上传返回的ID);")

    except Exception as e:
        print(f"❌ 测试准备失败: {e}")


def main():
    """主诊断流程"""
    print("\n" + "="*80)
    print("FieldMind 向量化链路完整诊断")
    print("="*80)

    # 数据库路径
    db_path = "/Users/alwan/FieldMind/backend/src/data/fieldmind.db"

    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return

    print(f"✅ 数据库文件存在: {db_path}")
    print(f"   文件大小: {os.path.getsize(db_path) / 1024:.2f} KB")

    # 执行诊断步骤
    engine = check_database_schema(db_path)
    check_document_chunks_structure(engine)
    check_sample_documents(engine)
    check_chunks_for_document(engine)
    check_processing_pipeline_config()
    check_vectorization_service()
    check_background_tasks()
    test_document_upload_and_processing()

    # 总结
    print("\n" + "="*80)
    print("诊断总结")
    print("="*80)
    print("""
根据以上诊断结果，问题可能出在：

1. ❌ 数据库表为空
   - project_documents = 0 条记录
   - document_chunks = 0 条记录
   - embeddings = 0 条记录

2. 可能的原因：
   ✓ 从未成功上传过文档
   ✓ 文档上传API未被调用
   ✓ 后台处理任务执行失败
   ✓ 数据库事务未提交
   ✓ 向量化服务未正常工作

3. 解决方案：
   步骤1: 上传一个测试文档（使用上面的curl命令）
   步骤2: 检查后台日志，查看处理过程
   步骤3: 确认document_chunks表有数据写入
   步骤4: 如果仍然失败，检查代码中的commit()调用
""")


if __name__ == "__main__":
    main()
