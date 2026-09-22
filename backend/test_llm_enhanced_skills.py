"""
测试LLM增强后的Skills

测试xiangtu_china_skill和social_memory_skill是否能正常生成报告
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.services.report_generation.data_driven_report_builder import DataDrivenReportBuilder
from app.services.report_generation.skills.xiangtu_china_skill import XiangtuChinaSkill
from app.services.report_generation.skills.social_memory_skill import SocialMemorySkill

def test_skills():
    """测试两个LLM增强的Skill"""

    # 初始化数据库
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # 项目ID
    project_id = 2  # 音寨布依族村

    print(f"\n{'='*60}")
    print(f"测试项目：project_id={project_id}")
    print(f"{'='*60}\n")

    try:
        # 提取报告素材
        print("📊 提取报告素材...")
        builder = DataDrivenReportBuilder(db)
        report_material = builder.extract_report_material(project_id)

        material_dict = {
            'main_keywords': report_material.main_keywords,
            'core_entities': report_material.core_entities,
            'citation_pool': report_material.citation_pool,
            'timeline': report_material.timeline,
            'total_chunks': report_material.total_chunks,
            'total_words': report_material.total_words,
            'total_documents': report_material.total_documents
        }

        print(f"✅ 素材提取完成")
        print(f"   - 关键词: {len(report_material.main_keywords)}个")
        print(f"   - 实体: {sum(len(v) for v in report_material.core_entities.values())}个")
        print(f"   - 引文: {len(report_material.citation_pool)}条")
        print(f"   - 时间线: {len(report_material.timeline)}个事件\n")

        # 测试1: 乡土中国Skill
        print(f"\n{'='*60}")
        print("测试1: 乡土中国Skill (费孝通理论)")
        print(f"{'='*60}\n")

        xiangtu_skill = XiangtuChinaSkill()
        xiangtu_report = xiangtu_skill.generate_report(material_dict)

        print(f"✅ 乡土中国报告生成完成")
        print(f"   - 字数: {len(xiangtu_report)} 字")
        print(f"   - 目标: 10,000 字")
        print(f"   - 完成度: {len(xiangtu_report)/10000*100:.1f}%")

        # 测试2: 社会记忆Skill
        print(f"\n{'='*60}")
        print("测试2: 社会记忆Skill (景军理论)")
        print(f"{'='*60}\n")

        memory_skill = SocialMemorySkill()
        memory_report = memory_skill.generate_report(material_dict)

        print(f"✅ 社会记忆报告生成完成")
        print(f"   - 字数: {len(memory_report)} 字")
        print(f"   - 目标: 10,000 字")
        print(f"   - 完成度: {len(memory_report)/10000*100:.1f}%")

        # 测试3: 报告2组合（乡土中国 + 社会记忆）
        print(f"\n{'='*60}")
        print("测试3: 报告2组合 (专业分析万字报告)")
        print(f"{'='*60}\n")

        combined_length = len(xiangtu_report) + len(memory_report)
        print(f"✅ 报告2总字数: {combined_length} 字")
        print(f"   - 目标: 10,000 字")
        print(f"   - 完成度: {combined_length/10000*100:.1f}%")

        if combined_length >= 10000:
            print(f"   ✅ 已达到万字目标！")
        else:
            gap = 10000 - combined_length
            print(f"   ⚠️  还差 {gap} 字")

        # 保存报告到文件（可选）
        output_dir = "test_output"
        os.makedirs(output_dir, exist_ok=True)

        with open(f"{output_dir}/xiangtu_report.md", "w", encoding="utf-8") as f:
            f.write(xiangtu_report)
        print(f"\n📄 乡土中国报告已保存: {output_dir}/xiangtu_report.md")

        with open(f"{output_dir}/memory_report.md", "w", encoding="utf-8") as f:
            f.write(memory_report)
        print(f"📄 社会记忆报告已保存: {output_dir}/memory_report.md")

        with open(f"{output_dir}/combined_report2.md", "w", encoding="utf-8") as f:
            f.write("# 报告2：专业分析万字报告\n\n")
            f.write(xiangtu_report)
            f.write("\n\n---\n\n")
            f.write(memory_report)
        print(f"📄 组合报告2已保存: {output_dir}/combined_report2.md")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_skills()
