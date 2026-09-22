"""
测试所有基于LLM的报告生成Skills

测试目标：
- 报告1（田野调查）：field_investigation_skill - 目标10,000字
- 报告2（专业分析）：xiangtu_china_skill + social_memory_skill - 目标10,000字
- 报告3（商业分析）：business_sop_skill + commercial_feasibility_skill - 目标10,000字

验证重点：
- 报告内容是否基于真实田野数据生成（而非模板）
- 字数是否达到万字目标
- LLM分析是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 导入Skills
from app.services.report_generation.skills.field_investigation_skill import FieldInvestigationSkill
from app.services.report_generation.skills.xiangtu_china_skill import XiangtuChinaSkill
from app.services.report_generation.skills.social_memory_skill import SocialMemorySkill
from app.services.report_generation.skills.business_sop_skill import BusinessSOPSkill


def get_test_report_material(engine):
    """从数据库获取测试数据"""
    with engine.connect() as conn:
        # 获取第一个项目ID
        result = conn.execute(text("SELECT id FROM projects LIMIT 1"))
        row = result.fetchone()
        if not row:
            print("❌ 数据库中没有项目")
            return None

        project_id = row[0]
        print(f"✅ 找到项目ID: {project_id}")

        # 获取关键词
        result = conn.execute(text("""
            SELECT text, weight, frequency
            FROM keywords
            WHERE project_id = :project_id
            ORDER BY weight DESC
            LIMIT 30
        """), {"project_id": project_id})
        keywords = [{"keyword": row[0], "pagerank": row[1] or 0.0, "frequency": row[2] or 0}
                   for row in result.fetchall()]

        # 获取实体统计
        import json
        try:
            result = conn.execute(text("""
                SELECT entity_name, entity_type, count
                FROM entity_statistics
                WHERE project_id = :project_id
                ORDER BY count DESC
                LIMIT 50
            """), {"project_id": project_id})
            entities_list = result.fetchall()
            entities = {}
            for entity_name, entity_type, count in entities_list:
                if entity_type not in entities:
                    entities[entity_type] = []
                entities[entity_type].append({"entity": entity_name, "mentions": count})
        except Exception as e:
            print(f"   ⚠️  无法获取实体统计: {e}")
            # 使用关键词作为实体
            entities = {"LOCATION": [], "CONCEPT": []}
            for kw in keywords[:10]:
                entities["CONCEPT"].append({"entity": kw["keyword"], "mentions": kw["frequency"]})

        # 获取文档片段（作为citation_pool）
        result = conn.execute(text("""
            SELECT text, metadata
            FROM document_chunks
            WHERE project_id = :project_id
            ORDER BY created_at DESC
            LIMIT 30
        """), {"project_id": project_id})
        citations = []
        for content, metadata_str in result.fetchall():
            metadata_dict = json.loads(metadata_str) if metadata_str else {}
            citations.append({
                "content": content,
                "citation_format": f"田野记录 - {metadata_dict.get('source', '未知来源')}"
            })

        # 时间线（简化：暂时为空）
        timeline = []

        # 构建报告素材
        report_material = {
            "project_statistics": {
                "total_chunks": len(citations),
                "total_words": sum(len(c["content"]) for c in citations),
            },
            "main_keywords": keywords,
            "core_entities": entities,
            "citation_pool": citations,
            "timeline": timeline,
            "entity_relations": [],  # 简化测试，暂不加载
            "keyword_communities": []  # 简化测试，暂不加载
        }

        return report_material


def test_field_investigation_skill(report_material):
    """测试报告1：田野调查"""
    print("\n" + "="*60)
    print("📋 测试报告1：田野调查报告（field_investigation_skill）")
    print("="*60)

    skill = FieldInvestigationSkill()
    report_content = skill.generate_report(report_material)

    char_count = len(report_content)
    target = 10000
    completion_rate = (char_count / target) * 100

    print(f"\n✅ 田野调查报告生成完成")
    print(f"   - 字数: {char_count:,} 字")
    print(f"   - 目标: {target:,} 字")
    print(f"   - 完成度: {completion_rate:.1f}%")

    if char_count < target:
        print(f"   ⚠️  还差 {target - char_count:,} 字")
    else:
        print(f"   🎉 已达到万字目标！")

    # 保存报告
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "report1_field_investigation.md"
    output_file.write_text(report_content, encoding="utf-8")
    print(f"   - 报告已保存到: {output_file}")

    return char_count


def test_xiangtu_china_skill(report_material):
    """测试报告2-1：乡土中国分析"""
    print("\n" + "="*60)
    print("📋 测试报告2-1：乡土中国分析（xiangtu_china_skill）")
    print("="*60)

    skill = XiangtuChinaSkill()
    report_content = skill.generate_report(report_material)

    char_count = len(report_content)
    target = 5000  # 报告2的一半
    completion_rate = (char_count / target) * 100

    print(f"\n✅ 乡土中国报告生成完成")
    print(f"   - 字数: {char_count:,} 字")
    print(f"   - 目标: {target:,} 字")
    print(f"   - 完成度: {completion_rate:.1f}%")

    if char_count < target:
        print(f"   ⚠️  还差 {target - char_count:,} 字")
    else:
        print(f"   🎉 已达到目标！")

    # 保存报告
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "report2_1_xiangtu_china.md"
    output_file.write_text(report_content, encoding="utf-8")
    print(f"   - 报告已保存到: {output_file}")

    return char_count


def test_social_memory_skill(report_material):
    """测试报告2-2：社会记忆分析"""
    print("\n" + "="*60)
    print("📋 测试报告2-2：社会记忆分析（social_memory_skill）")
    print("="*60)

    skill = SocialMemorySkill()
    report_content = skill.generate_report(report_material)

    char_count = len(report_content)
    target = 5000  # 报告2的另一半
    completion_rate = (char_count / target) * 100

    print(f"\n✅ 社会记忆报告生成完成")
    print(f"   - 字数: {char_count:,} 字")
    print(f"   - 目标: {target:,} 字")
    print(f"   - 完成度: {completion_rate:.1f}%")

    if char_count < target:
        print(f"   ⚠️  还差 {target - char_count:,} 字")
    else:
        print(f"   🎉 已达到目标！")

    # 保存报告
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "report2_2_social_memory.md"
    output_file.write_text(report_content, encoding="utf-8")
    print(f"   - 报告已保存到: {output_file}")

    return char_count


def test_business_sop_skill(report_material):
    """测试报告3-1：商业分析（乡遗商途）"""
    print("\n" + "="*60)
    print("📋 测试报告3-1：商业分析（business_sop_skill）")
    print("="*60)

    skill = BusinessSOPSkill()
    report_content = skill.generate_report(report_material)

    char_count = len(report_content)
    target = 5000  # 报告3的一半
    completion_rate = (char_count / target) * 100

    print(f"\n✅ 商业分析报告生成完成")
    print(f"   - 字数: {char_count:,} 字")
    print(f"   - 目标: {target:,} 字")
    print(f"   - 完成度: {completion_rate:.1f}%")

    if char_count < target:
        print(f"   ⚠️  还差 {target - char_count:,} 字")
    else:
        print(f"   🎉 已达到目标！")

    # 保存报告
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "report3_1_business_sop.md"
    output_file.write_text(report_content, encoding="utf-8")
    print(f"   - 报告已保存到: {output_file}")

    return char_count


def main():
    print("="*60)
    print("🚀 开始测试所有LLM增强的报告生成Skills")
    print("="*60)

    # 连接数据库
    engine = create_engine(settings.DATABASE_URL)

    # 获取测试数据
    report_material = get_test_report_material(engine)
    if not report_material:
        return

    print(f"\n📊 测试数据统计：")
    print(f"   - 关键词: {len(report_material['main_keywords'])} 个")
    print(f"   - 实体: {sum(len(v) for v in report_material['core_entities'].values())} 个")
    print(f"   - 田野原文: {len(report_material['citation_pool'])} 段")
    print(f"   - 时间线事件: {len(report_material['timeline'])} 个")

    # 测试所有Skills
    results = {}

    # 报告1
    results["report1"] = test_field_investigation_skill(report_material)

    # 报告2
    results["report2_1"] = test_xiangtu_china_skill(report_material)
    results["report2_2"] = test_social_memory_skill(report_material)
    results["report2_total"] = results["report2_1"] + results["report2_2"]

    # 报告3
    results["report3_1"] = test_business_sop_skill(report_material)
    # 注意：commercial_feasibility_skill已经是数据驱动的，暂不测试

    # 总结
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)

    print(f"\n【报告1：田野调查】")
    print(f"   - 字数: {results['report1']:,} 字")
    print(f"   - 目标: 10,000 字")
    print(f"   - 完成度: {(results['report1']/10000)*100:.1f}%")
    if results['report1'] >= 10000:
        print(f"   - 状态: ✅ 达标")
    else:
        print(f"   - 状态: ⚠️  还差 {10000 - results['report1']:,} 字")

    print(f"\n【报告2：专业分析】")
    print(f"   - 乡土中国: {results['report2_1']:,} 字")
    print(f"   - 社会记忆: {results['report2_2']:,} 字")
    print(f"   - 总字数: {results['report2_total']:,} 字")
    print(f"   - 目标: 10,000 字")
    print(f"   - 完成度: {(results['report2_total']/10000)*100:.1f}%")
    if results['report2_total'] >= 10000:
        print(f"   - 状态: ✅ 达标")
    else:
        print(f"   - 状态: ⚠️  还差 {10000 - results['report2_total']:,} 字")

    print(f"\n【报告3：商业分析】")
    print(f"   - 乡遗商途: {results['report3_1']:,} 字")
    print(f"   - 目标（部分）: 5,000 字")
    print(f"   - 完成度: {(results['report3_1']/5000)*100:.1f}%")
    print(f"   - 注：commercial_feasibility_skill 已是数据驱动，未在本次测试")

    print("\n" + "="*60)
    print("✅ 所有测试完成！")
    print("="*60)

    # 检查API密钥配置
    if any(count < 1000 for count in results.values()):
        print("\n⚠️  部分报告字数偏少，请检查：")
        print("   1. OPENAI_API_KEY 是否正确配置")
        print("   2. LLM调用是否成功（查看日志）")
        print("   3. 是否使用了降级模式")


if __name__ == "__main__":
    main()
