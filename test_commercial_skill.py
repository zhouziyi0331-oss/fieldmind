"""
商业可行性验证 Skill 测试脚本

测试 CommercialFeasibilitySkill 与 DataDrivenReportBuilder 的集成
"""

import sys
sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.report_generation.data_driven_report_builder import DataDrivenReportBuilder
from app.services.report_generation.skills.commercial_feasibility_skill import CommercialFeasibilitySkill


def test_commercial_skill():
    """测试商业可行性验证 Skill"""

    print("=" * 80)
    print("商业可行性验证 Skill 测试")
    print("=" * 80)
    print()

    # 1. 初始化数据库连接
    DATABASE_URL = "sqlite:///backend/src/data/fieldmind.db"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # 2. 初始化 ReportBuilder 和 Skill
    builder = DataDrivenReportBuilder(db=session)
    skill = CommercialFeasibilitySkill()

    # 3. 使用音寨村数据（project_id=2）
    project_id = 2
    print(f"📊 正在提取项目数据 (project_id={project_id})...")

    try:
        material_obj = builder.extract_report_material(project_id)

        # 转换为字典
        material = {
            'main_keywords': material_obj.main_keywords,
            'keyword_communities': material_obj.keyword_communities,
            'core_entities': material_obj.core_entities,
            'entity_relations': material_obj.entity_relations,
            'timeline': material_obj.timeline,
            'citation_pool': material_obj.citation_pool,
            'data_profile': material_obj.data_profile
        }

        print(f"✓ 数据提取完成")
        print(f"  - 主关键词: {len(material['main_keywords'])} 个")
        print(f"  - 核心实体: {len(material['core_entities'])} 个")
        print(f"  - 引用池: {len(material['citation_pool'])} 条")
        print()

        # 4. 生成商业可行性报告
        print("🎯 正在生成商业可行性验证报告...")
        print()

        report = skill.generate_report(material)

        print("✓ 报告生成完成")
        print()

        # 5. 分析报告统计
        report_lines = report.split('\n')
        char_count = len(report)

        # 统计各部分
        a_grade_count = report.count('A级方案')
        b_grade_count = report.count('B级方案')
        c_grade_count = report.count('C级方案')
        veto_count = report.count('一票否决方案')
        opportunity_count = report.count('### ') - (a_grade_count + b_grade_count + c_grade_count + veto_count)

        print("=" * 80)
        print("报告统计")
        print("=" * 80)
        print(f"总字数: {char_count} 字")
        print(f"总行数: {len(report_lines)} 行")
        print()
        print(f"识别商业机会: {opportunity_count} 个")
        print(f"A级方案: {a_grade_count} 个")
        print(f"B级方案: {b_grade_count} 个")
        print(f"C级方案: {c_grade_count} 个")
        print(f"否决方案: {veto_count} 个")
        print()

        # 6. 保存报告
        output_file = '/Users/alwan/FieldMind/commercial_feasibility_report.md'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✓ 报告已保存: {output_file}")
        print()

        # 7. 显示报告预览
        print("=" * 80)
        print("报告预览（前50行）")
        print("=" * 80)
        print()
        print('\n'.join(report_lines[:50]))
        print()
        print(f"... (共 {len(report_lines)} 行，完整报告见 {output_file})")
        print()

        session.close()

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        session.close()
        return False


if __name__ == "__main__":
    success = test_commercial_skill()

    if success:
        print("=" * 80)
        print("✅ 所有测试完成")
        print("=" * 80)
    else:
        print("=" * 80)
        print("❌ 测试失败")
        print("=" * 80)
        sys.exit(1)
