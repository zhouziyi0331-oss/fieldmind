#!/usr/bin/env python3
"""
测试 Skills 集成效果

测试项目：
1. 田野调查 Skill (Level 1)
2. 商业分析 Skill (Level 3)
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.report_generation.data_driven_report_builder import DataDrivenReportBuilder
from app.services.report_generation.report_content_engine import ReportContentEngine

# 数据库连接
DATABASE_URL = "sqlite:///backend/src/data/fieldmind.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def test_field_investigation_skill():
    """测试田野调查 Skill (Level 1)"""
    print("\n" + "="*80)
    print("🧪 测试 1: 田野调查 Skill (Level 1)")
    print("="*80)

    db = SessionLocal()
    try:
        # 1. 提取报告素材
        print("\n📊 步骤 1: 提取报告素材...")
        builder = DataDrivenReportBuilder(db)
        material = builder.extract_report_material(project_id=1)

        print(f"✅ 素材提取完成")
        print(f"   - 文档块数: {material.total_chunks}")
        print(f"   - 总字数: {material.total_words:,}")
        print(f"   - 关键词数: {len(material.main_keywords)}")
        print(f"   - 关键词社区数: {len(material.keyword_communities)}")

        # 2. 生成 Level 1 大纲
        print("\n📋 步骤 2: 生成 Level 1 大纲...")
        outline = builder.generate_dynamic_outline(material, report_level=1)

        print(f"✅ 大纲生成完成")
        print(f"   - 章节数: {len(outline)}")

        # 计算预计字数
        estimated_words = sum(section.get('estimated_words', 0) for section in outline)
        print(f"   - 预计字数: {estimated_words:,}")

        # 3. 使用 ReportContentEngine 填充章节
        print("\n✍️  步骤 3: 使用田野调查 Skill 填充章节...")
        engine = ReportContentEngine()

        # 选择一个关键词社区章节进行测试
        test_section = None
        for section in outline:
            content_sources = section.get('content_sources', {})
            if content_sources.get('type') == 'keyword_community':
                test_section = section
                break

        if test_section:
            print(f"\n🎯 测试章节: {test_section['chapter']}")
            print(f"   - 内容类型: {test_section['content_sources']['type']}")

            result = engine.fill_section(
                section_outline=test_section,
                material=material,
                report_level=1
            )

            print(f"\n✅ 章节填充完成")
            print(f"   - 字数: {result['word_count']}")
            print(f"   - 引用数: {len(result['citations'])}")
            print(f"   - 引用验证: {result['citation_validation']}")

            print(f"\n📄 生成内容预览（前500字）:")
            print("-" * 80)
            print(result['content'][:500])
            print("...")
            print("-" * 80)

            return True
        else:
            print("❌ 未找到关键词社区章节")
            return False

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_business_sop_skill():
    """测试商业分析 Skill (Level 3)"""
    print("\n" + "="*80)
    print("🧪 测试 2: 商业分析 Skill (Level 3)")
    print("="*80)

    db = SessionLocal()
    try:
        # 1. 提取报告素材
        print("\n📊 步骤 1: 提取报告素材...")
        builder = DataDrivenReportBuilder(db)
        material = builder.extract_report_material(project_id=1)

        print(f"✅ 素材提取完成")

        # 2. 生成 Level 3 大纲
        print("\n📋 步骤 2: 生成 Level 3 大纲...")
        outline = builder.generate_dynamic_outline(material, report_level=3)

        print(f"✅ 大纲生成完成")
        print(f"   - 章节数: {len(outline)}")

        # 计算预计字数
        estimated_words = sum(section.get('estimated_words', 0) for section in outline)
        print(f"   - 预计字数: {estimated_words:,}")

        # 3. 使用 ReportContentEngine 填充章节
        print("\n✍️  步骤 3: 使用商业分析 Skill 填充章节...")
        engine = ReportContentEngine()

        # 测试第一个章节（通常是田野扫描或资源盘点）
        test_section = outline[1] if len(outline) > 1 else outline[0]

        print(f"\n🎯 测试章节: {test_section['chapter']}")

        result = engine.fill_section(
            section_outline=test_section,
            material=material,
            report_level=3
        )

        print(f"\n✅ 章节填充完成")
        print(f"   - 字数: {result['word_count']}")
        print(f"   - 引用数: {len(result['citations'])}")

        print(f"\n📄 生成内容预览（前800字）:")
        print("-" * 80)
        print(result['content'][:800])
        print("...")
        print("-" * 80)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_skill_quality():
    """测试 Skill 内容质量"""
    print("\n" + "="*80)
    print("🧪 测试 3: Skill 内容质量评估")
    print("="*80)

    db = SessionLocal()
    try:
        builder = DataDrivenReportBuilder(db)
        material = builder.extract_report_material(project_id=1)
        engine = ReportContentEngine()

        results = {
            'level1': {'sections': 0, 'total_words': 0, 'avg_words': 0},
            'level3': {'sections': 0, 'total_words': 0, 'avg_words': 0}
        }

        # 测试 Level 1 所有章节
        print("\n📊 Level 1 (田野调查报告) 章节质量:")
        outline_l1 = builder.generate_dynamic_outline(material, report_level=1)

        for section in outline_l1[:3]:  # 测试前3个章节
            try:
                result = engine.fill_section(section, material, report_level=1)
                results['level1']['sections'] += 1
                results['level1']['total_words'] += result['word_count']
                print(f"   ✅ {section['chapter']}: {result['word_count']}字")
            except Exception as e:
                print(f"   ❌ {section['chapter']}: 失败 - {e}")

        if results['level1']['sections'] > 0:
            results['level1']['avg_words'] = results['level1']['total_words'] // results['level1']['sections']

        # 测试 Level 3 所有章节
        print("\n📊 Level 3 (商业分析报告) 章节质量:")
        outline_l3 = builder.generate_dynamic_outline(material, report_level=3)

        for section in outline_l3[:3]:  # 测试前3个章节
            try:
                result = engine.fill_section(section, material, report_level=3)
                results['level3']['sections'] += 1
                results['level3']['total_words'] += result['word_count']
                print(f"   ✅ {section['chapter']}: {result['word_count']}字")
            except Exception as e:
                print(f"   ❌ {section['chapter']}: 失败 - {e}")

        if results['level3']['sections'] > 0:
            results['level3']['avg_words'] = results['level3']['total_words'] // results['level3']['sections']

        # 输出质量报告
        print("\n" + "="*80)
        print("📈 质量评估结果")
        print("="*80)
        print(f"\nLevel 1 (田野调查报告):")
        print(f"   - 成功生成章节: {results['level1']['sections']}")
        print(f"   - 总字数: {results['level1']['total_words']:,}")
        print(f"   - 平均字数/章: {results['level1']['avg_words']:,}")

        print(f"\nLevel 3 (商业分析报告):")
        print(f"   - 成功生成章节: {results['level3']['sections']}")
        print(f"   - 总字数: {results['level3']['total_words']:,}")
        print(f"   - 平均字数/章: {results['level3']['avg_words']:,}")

        # 判断是否达标
        print("\n" + "="*80)
        success = (
            results['level1']['sections'] >= 2 and
            results['level3']['sections'] >= 2 and
            results['level1']['avg_words'] >= 500 and
            results['level3']['avg_words'] >= 500
        )

        if success:
            print("✅ 质量测试通过")
        else:
            print("⚠️  质量测试未完全通过，但基础功能正常")

        return success

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("🚀 Skills 集成测试")
    print("="*80)
    print("\n测试目标:")
    print("1. 验证田野调查 Skill 正确集成到 Level 1 报告生成")
    print("2. 验证商业分析 Skill 正确集成到 Level 3 报告生成")
    print("3. 评估生成内容的质量和字数")

    results = []

    # 运行测试
    results.append(("田野调查 Skill", test_field_investigation_skill()))
    results.append(("商业分析 Skill", test_business_sop_skill()))
    results.append(("内容质量评估", test_skill_quality()))

    # 总结
    print("\n" + "="*80)
    print("📊 测试结果总结")
    print("="*80)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {name}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 所有测试通过！Skills 集成成功。")
    else:
        print("\n⚠️  部分测试失败，请检查错误日志。")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
