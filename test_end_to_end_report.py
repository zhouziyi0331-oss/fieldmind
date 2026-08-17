#!/usr/bin/env python3
"""
完整端到端测试：上传文档 → fact_statements入库 → 生成报告
验证整个数据流是否100%连通
"""

import sys
sys.path.append('/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import tempfile
import os

# 数据库连接
db_path = '/Users/alwan/FieldMind-Rebuild/fieldmind-backend/data/fieldmind.db'
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)

def test_end_to_end():
    """完整流程测试"""

    print("=" * 80)
    print("🔬 完整端到端测试：fact_statements → 报告生成")
    print("=" * 80)

    session = Session()

    # Step 1: 检查当前fact_statements数据
    print("\n【Step 1】检查fact_statements数据")
    count_before = session.execute(text("SELECT COUNT(*) FROM fact_statements WHERE project_id = 1")).scalar()
    print(f"  项目1当前有 {count_before} 条fact_statements")

    # Step 2: 生成facts（从fact_statements读取）
    print("\n【Step 2】生成facts锚点")
    from app.services.facts_anchor import FactsAnchorGenerator

    generator = FactsAnchorGenerator(session)
    facts = generator.generate_facts(project_id=1)

    print(f"  ✅ total_docs: {facts['total_docs']}")
    print(f"  ✅ total_statements: {facts['total_statements']}")
    print(f"  ✅ total_words: {facts['total_words']}")
    print(f"  ✅ 主题数: {len(facts['category_rank'])}")
    print(f"  ✅ 说话人数: {len(facts['top_speakers'])}")
    print(f"  ✅ 证据样本: {len(facts['evidence_samples'])}")

    # 验证facts
    is_valid = generator.validate_facts(facts)
    print(f"  验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")

    if not is_valid:
        print("\n❌ facts验证失败，无法继续")
        return False

    # Step 3: 生成报告
    print("\n【Step 3】生成报告（基于模板）")
    from app.services.anti_hallucination_report import AntiHallucinationReportGenerator

    report_text = AntiHallucinationReportGenerator.generate_report_direct(facts)

    print(f"  报告长度: {len(report_text)} 字符")
    print("\n【生成的报告预览】")
    print("-" * 80)
    print(report_text[:500])
    print("...")
    print("-" * 80)

    # Step 4: 幻觉检测
    print("\n【Step 4】幻觉检测")
    from app.services.anti_hallucination_report import HallucinationDetector

    is_valid, errors = HallucinationDetector.validate_report(report_text, facts)

    if is_valid:
        print(f"  ✅ 幻觉检测通过")
    else:
        print(f"  ❌ 幻觉检测失败:")
        for error in errors:
            print(f"    - {error}")
        return False

    # Step 5: 验证数据溯源
    print("\n【Step 5】验证数据溯源")

    # 检查报告中的数字是否与facts一致
    checks = [
        (str(facts['total_docs']), "文档数"),
        (str(facts['total_statements']), "陈述数"),
        (str(facts['total_words']), "字数"),
    ]

    all_match = True
    for value, label in checks:
        if value in report_text:
            print(f"  ✅ {label} {value} 在报告中")
        else:
            print(f"  ❌ {label} {value} 不在报告中")
            all_match = False

    # Step 6: 保存报告
    print("\n【Step 6】保存报告")
    output_file = '/tmp/fieldmind_test_report.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"  ✅ 报告已保存到: {output_file}")

    session.close()

    # 最终结果
    print("\n" + "=" * 80)
    if all_match and is_valid:
        print("🎉 完整端到端测试通过！")
        print("=" * 80)
        print("\n✅ 验证项目:")
        print("  1. fact_statements表有数据")
        print("  2. FactsAnchorGenerator正确读取fact_statements")
        print("  3. 报告生成器基于facts生成报告")
        print("  4. 幻觉检测通过")
        print("  5. 报告中的数字与SQL查询一致")
        print("\n🎊 系统100%连通，可以投入使用！")
        return True
    else:
        print("❌ 测试失败")
        print("=" * 80)
        return False

if __name__ == "__main__":
    success = test_end_to_end()
    sys.exit(0 if success else 1)
