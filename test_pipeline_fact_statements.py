#!/usr/bin/env python3
"""
验证Pipeline是否真的插入fact_statements
"""

import sys
sys.path.append('/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.document_processing_pipeline import DocumentProcessingPipeline
import os

# 创建数据库连接
db_path = '/Users/alwan/FieldMind-Rebuild/fieldmind-backend/data/fieldmind.db'
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)

def test_pipeline():
    """测试Pipeline是否插入fact_statements"""

    print("=" * 60)
    print("🧪 验证Pipeline插入fact_statements")
    print("=" * 60)

    # 1. 检查插入前的数据量
    session = Session()
    before_count = session.execute(text("SELECT COUNT(*) FROM fact_statements")).scalar()
    print(f"\n【插入前】fact_statements表有 {before_count} 条数据")

    # 2. 创建测试文本文件
    test_file = '/tmp/test_document.txt'
    test_content = """
王大爷说，我们村有三百多年历史。
李婶告诉我，年轻人都去城里打工了。
村里的祠堂是明代建筑，保存得很好。
传统节日活动越来越少了。
你觉得这种变化好吗？
太可惜了！
    """.strip()

    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)

    print(f"\n【创建测试文件】{test_file}")
    print(f"内容预览：\n{test_content[:100]}...")

    # 3. 运行Pipeline
    print("\n【开始处理】调用DocumentProcessingPipeline...")

    try:
        pipeline = DocumentProcessingPipeline()

        result = pipeline.process_document(
            document_id=999,
            file_path=test_file,
            project_id=1,
            db=session,
            progress_callback=lambda stage, progress, msg: print(f"  [{stage}] {progress*100:.0f}% - {msg}")
        )

        print(f"\n【处理结果】")
        print(f"  成功: {result.get('success')}")
        print(f"  阶段: {list(result.get('stages', {}).keys())}")

    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()

    # 4. 检查插入后的数据量
    session = Session()
    after_count = session.execute(text("SELECT COUNT(*) FROM fact_statements")).scalar()
    print(f"\n【插入后】fact_statements表有 {after_count} 条数据")

    inserted = after_count - before_count

    if inserted > 0:
        print(f"\n✅ 成功插入了 {inserted} 条fact_statements")

        # 查看最新插入的数据
        print("\n【最新数据】")
        rows = session.execute(text("""
            SELECT id, speaker, clean_text, keywords, sentence_type
            FROM fact_statements
            WHERE document_id = 999
            LIMIT 5
        """)).fetchall()

        for row in rows:
            print(f"  ID={row[0]} | {row[1] or '无说话人'} | {row[2][:30]}... | 关键词:{row[3][:20]}... | {row[4]}")

    else:
        print(f"\n❌ 没有插入任何数据！Pipeline有问题")

    session.close()

    print("\n" + "=" * 60)
    print("🏁 验证完成")
    print("=" * 60)

if __name__ == "__main__":
    test_pipeline()
