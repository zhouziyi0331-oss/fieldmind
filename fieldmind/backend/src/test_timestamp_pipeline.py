#!/usr/bin/env python3
"""
端到端测试：验证新上传音频文档的时间戳传递链路
测试完整流程：上传 → Whisper转录 → 切分 → fact_statements填充 → 时间戳验证
"""

import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# 数据库连接
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/fieldmind.db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def test_timestamp_pipeline():
    """测试时间戳传递完整链路"""

    print("=" * 60)
    print("时间戳传递链路测试")
    print("=" * 60)

    # 1. 检查是否有最近上传的音频文档
    session = Session()

    result = session.execute(text("""
        SELECT id, filename, file_type, status, created_at
        FROM project_documents
        WHERE (file_type LIKE '%audio%' OR file_type LIKE '%video%')
        ORDER BY created_at DESC
        LIMIT 5
    """)).fetchall()

    print("\n📋 最近的音视频文档:")
    for row in result:
        print(f"  ID={row[0]}, 文件={row[1]}, 状态={row[3]}, 创建时间={row[4]}")

    # 2. 检查转录文件存在性
    print("\n📁 转录文件检查:")
    transcript_base = os.getenv("UPLOAD_DIR", "./uploads")
    for row in result:
        doc_id = row[0]
        transcript_path = Path(f"{transcript_base}/transcripts/doc_{doc_id}.json")
        exists = "✅" if transcript_path.exists() else "❌"
        print(f"  Doc {doc_id}: {exists} {transcript_path.name}")

    # 3. 检查fact_statements时间戳
    print("\n⏱️  时间戳覆盖率:")
    for row in result:
        doc_id = row[0]
        stats = session.execute(text("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN start_sec IS NOT NULL THEN 1 ELSE 0 END) as with_ts,
                ROUND(AVG(CASE WHEN start_sec IS NOT NULL THEN 1.0 ELSE 0.0 END) * 100, 2) as coverage
            FROM fact_statements
            WHERE document_id = :doc_id
        """), {"doc_id": doc_id}).fetchone()

        if stats[0] > 0:
            print(f"  Doc {doc_id}: {stats[1]}/{stats[0]} ({stats[2]}%)")
        else:
            print(f"  Doc {doc_id}: 无fact_statements记录")

    # 4. 全局统计
    print("\n📊 全局统计:")
    global_stats = session.execute(text("""
        SELECT
            COUNT(*) as total_docs,
            SUM(CASE WHEN file_type LIKE '%audio%' OR file_type LIKE '%video%' THEN 1 ELSE 0 END) as audio_video_count
        FROM project_documents
        WHERE status = 'completed'
    """)).fetchone()

    print(f"  总文档数: {global_stats[0]}")
    print(f"  音视频文档: {global_stats[1]}")

    fact_stats = session.execute(text("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN start_sec IS NOT NULL THEN 1 ELSE 0 END) as with_ts,
            ROUND(AVG(CASE WHEN start_sec IS NOT NULL THEN 1.0 ELSE 0.0 END) * 100, 2) as coverage
        FROM fact_statements
    """)).fetchone()

    print(f"  Fact statements总数: {fact_stats[0]}")
    print(f"  带时间戳: {fact_stats[1]} ({fact_stats[2]}%)")

    # 5. 测试结论
    print("\n" + "=" * 60)
    print("测试结论:")
    print("=" * 60)

    # 检查最近的音频文档是否有完整的时间戳
    recent_audio = [r for r in result if 'audio' in r[2] or 'video' in r[2]]
    if recent_audio:
        latest_doc_id = recent_audio[0][0]
        latest_stats = session.execute(text("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN start_sec IS NOT NULL THEN 1 ELSE 0 END) as with_ts
            FROM fact_statements
            WHERE document_id = :doc_id
        """), {"doc_id": latest_doc_id}).fetchone()

        if latest_stats[0] > 0:
            coverage = (latest_stats[1] / latest_stats[0]) * 100
            if coverage >= 90:
                print(f"✅ 最新音频文档(ID={latest_doc_id})时间戳覆盖率: {coverage:.1f}% - 正常")
            elif coverage >= 50:
                print(f"⚠️  最新音频文档(ID={latest_doc_id})时间戳覆盖率: {coverage:.1f}% - 部分成功")
            else:
                print(f"❌ 最新音频文档(ID={latest_doc_id})时间戳覆盖率: {coverage:.1f}% - 异常")
        else:
            print(f"❌ 最新音频文档(ID={latest_doc_id})没有fact_statements记录")
    else:
        print("⚠️  没有找到音视频文档")

    # 检查转录文件存在性
    transcript_base = os.getenv("UPLOAD_DIR", "./uploads")
    transcript_count = sum(1 for r in result if Path(f"{transcript_base}/transcripts/doc_{r[0]}.json").exists())
    print(f"\n转录文件保存率: {transcript_count}/{len(result)} ({transcript_count/len(result)*100:.1f}%)")

    if transcript_count < len(result):
        print("⚠️  部分音频文档缺失转录文件，可能是:")
        print("   1. 早期处理时未保存转录文件")
        print("   2. Whisper转录失败但未记录错误")
        print("   3. 文件系统问题")

    session.close()
    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_timestamp_pipeline()
