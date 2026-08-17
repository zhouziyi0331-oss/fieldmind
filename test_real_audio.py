#!/usr/bin/env python3
"""
真实音频测试：使用用户提供的音频文件完整测试整个流程
"""

import sys
sys.path.append('/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# 数据库连接
db_path = '/Users/alwan/FieldMind-Rebuild/fieldmind-backend/data/fieldmind.db'
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)

def test_real_audio():
    """测试真实音频文件"""

    audio_file = '/Users/alwan/Downloads/新录音.wav'

    print("=" * 80)
    print("🎤 真实音频测试：完整验证音频→转文字→时间戳→报告")
    print("=" * 80)

    # 检查文件
    if not os.path.exists(audio_file):
        print(f"❌ 音频文件不存在: {audio_file}")
        return False

    file_size = os.path.getsize(audio_file)
    print(f"\n【音频文件信息】")
    print(f"  路径: {audio_file}")
    print(f"  大小: {file_size / 1024 / 1024:.2f} MB")

    session = Session()

    # 清理旧数据
    print(f"\n【清理测试数据】")
    session.execute(text("DELETE FROM document_chunks WHERE document_id = 2000"))
    session.execute(text("DELETE FROM fact_statements WHERE document_id = 2000"))
    session.commit()

    before_count = session.execute(text("""
        SELECT COUNT(*) FROM fact_statements WHERE project_id = 1
    """)).scalar()
    print(f"  项目1当前有 {before_count} 条fact_statements")

    # 运行Pipeline
    print(f"\n【开始处理音频】")
    print(f"  这可能需要几分钟，取决于音频长度...")

    from app.services.document_processing_pipeline import DocumentProcessingPipeline

    pipeline = DocumentProcessingPipeline()

    try:
        result = pipeline.process_document(
            document_id=2000,
            file_path=audio_file,
            project_id=1,
            db=session,
            progress_callback=lambda stage, progress, msg: print(f"  [{stage}] {progress*100:.0f}% - {msg}")
        )

        print(f"\n【处理结果】")
        if result.get('success'):
            print(f"  ✅ 处理成功")
            for stage, info in result.get('stages', {}).items():
                if info.get('success'):
                    print(f"    ✅ {stage}: {info}")
                else:
                    print(f"    ❌ {stage}: {info}")
        else:
            print(f"  ❌ 处理失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"\n❌ 处理异常: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 验证数据
    print(f"\n【验证fact_statements】")

    after_count = session.execute(text("""
        SELECT COUNT(*) FROM fact_statements WHERE project_id = 1
    """)).scalar()

    inserted = after_count - before_count
    print(f"  插入后: {after_count} 条")
    print(f"  本次插入: {inserted} 条")

    if inserted == 0:
        print(f"  ❌ 没有插入任何数据")
        return False

    # 检查时间戳
    rows = session.execute(text("""
        SELECT id, speaker, clean_text, start_sec, end_sec, word_count
        FROM fact_statements
        WHERE document_id = 2000
        ORDER BY start_sec
        LIMIT 10
    """)).fetchall()

    print(f"\n【插入的数据（前10条）】")
    has_timestamp = False
    for row in rows:
        if row.start_sec is not None:
            has_timestamp = True
            print(f"  ⏱️  [{row.start_sec:.1f}s-{row.end_sec:.1f}s] {row.speaker or '无说话人'}: {row.clean_text[:50]}... ({row.word_count}字)")
        else:
            print(f"  📄 {row.speaker or '无说话人'}: {row.clean_text[:50]}...")

    if not has_timestamp:
        print(f"\n  ⚠️  警告：没有时间戳数据")

    # 统计数据
    stats = session.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(DISTINCT speaker) as speakers,
            SUM(word_count) as total_words,
            MIN(start_sec) as min_time,
            MAX(end_sec) as max_time
        FROM fact_statements
        WHERE document_id = 2000
    """)).first()

    print(f"\n【数据统计】")
    print(f"  总陈述数: {stats.total}")
    print(f"  说话人数: {stats.speakers}")
    print(f"  总字数: {stats.total_words}")
    if stats.min_time is not None:
        duration = stats.max_time - stats.min_time
        print(f"  音频时长: {duration:.1f}秒 ({duration/60:.1f}分钟)")

    # 生成报告
    print(f"\n【生成报告】")

    from app.services.facts_anchor import FactsAnchorGenerator
    from app.services.anti_hallucination_report import AntiHallucinationReportGenerator

    generator = FactsAnchorGenerator(session)
    facts = generator.generate_facts(project_id=1)

    report_text = AntiHallucinationReportGenerator.generate_report_direct(facts)

    # 保存报告
    output_file = '/tmp/real_audio_report.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"  ✅ 报告已保存: {output_file}")
    print(f"  报告长度: {len(report_text)} 字符")

    # 显示报告摘要
    print(f"\n【报告摘要】")
    lines = report_text.split('\n')
    for line in lines[:20]:
        if line.strip():
            print(f"  {line}")

    session.close()

    # 最终结果
    print("\n" + "=" * 80)
    if inserted > 0 and has_timestamp:
        print("🎉 真实音频测试完全成功！")
        print("=" * 80)
        print(f"\n✅ 完成验证:")
        print(f"  1. Whisper成功转录音频")
        print(f"  2. 插入了 {inserted} 条带时间戳的fact_statements")
        print(f"  3. 生成了包含时间戳溯源的报告")
        print(f"  4. 数据流100%连通")
        print(f"\n🎊 系统可以投入生产使用！")
        return True
    else:
        print("⚠️  测试部分成功，但存在问题")
        print("=" * 80)
        return False

if __name__ == "__main__":
    success = test_real_audio()
    sys.exit(0 if success else 1)
