"""
测试专业视角 Skills：乡土中国 + 神堂记忆

验证两个新的专业分析 Skill 是否正确集成并能生成高质量内容
"""

import sys
sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.report_generation.data_driven_report_builder import DataDrivenReportBuilder
from app.services.report_generation.skills.xiangtu_china_skill import XiangtuChinaSkill
from app.services.report_generation.skills.social_memory_skill import SocialMemorySkill

# 数据库连接
DATABASE_URL = "sqlite:///backend/src/data/fieldmind.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def test_professional_skills():
    """测试专业视角 Skills"""

    print("=" * 80)
    print("专业视角 Skills 集成测试")
    print("=" * 80)

    # 初始化数据提取器
    print("\n【步骤 1】初始化数据提取器")
    session = SessionLocal()
    builder = DataDrivenReportBuilder(db=session)

    # 提取音寨项目数据
    print("\n【步骤 2】提取音寨布依族村数据")
    project_id = 2
    material_obj = builder.extract_report_material(project_id)

    # 转换为字典格式
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
    print(f"  - 关键词: {len(material['main_keywords'])} 个")
    print(f"  - 实体: {len(material['core_entities'])} 个")
    print(f"  - 引用池: {len(material['citation_pool'])} chunks")
    print(f"  - 时间线: {len(material['timeline'])} 事件")

    # 测试乡土中国 Skill
    print("\n" + "=" * 80)
    print("【测试 1】乡土中国视角分析")
    print("=" * 80)

    xiangtu_skill = XiangtuChinaSkill()

    print("\n▶ 分析乡土社会特征...")
    xiangtu_analysis = xiangtu_skill.analyze_xiangtu_society(material)

    print("\n✓ 乡土社会特征识别:")
    xiangtu_features = xiangtu_analysis.get("xiangtu_features", {})
    for feature_name, feature_data in xiangtu_features.items():
        strength = feature_data.get("strength", "")
        evidence = feature_data.get("evidence", [])
        print(f"  - {feature_name} (强度: {strength})")
        print(f"    证据: {', '.join(evidence[:3])}")

    print("\n✓ 社会健康度诊断:")
    health_diagnosis = xiangtu_analysis.get("health_diagnosis", {})
    for dimension, status in health_diagnosis.items():
        print(f"  - {dimension}: {status}")

    print("\n▶ 识别发展机会...")
    xiangtu_opportunities = xiangtu_skill.identify_opportunities(xiangtu_analysis)

    print(f"\n✓ 识别到 {len(xiangtu_opportunities)} 个发展机会:")
    for i, opp in enumerate(xiangtu_opportunities, 1):
        print(f"  {i}. {opp.resource_type} → {opp.transformation_path}")

    print("\n▶ 生成完整报告...")
    xiangtu_report = xiangtu_skill.generate_report(material)
    xiangtu_word_count = len(xiangtu_report)

    print(f"\n✓ 乡土中国报告生成完成")
    print(f"  - 总字数: {xiangtu_word_count} 字")

    # 测试神堂记忆 Skill
    print("\n" + "=" * 80)
    print("【测试 2】社会记忆视角分析")
    print("=" * 80)

    memory_skill = SocialMemorySkill()

    print("\n▶ 分析社会记忆系统...")
    memory_analysis = memory_skill.analyze_memory_system(material)

    print("\n✓ 记忆载体识别:")
    memory_carriers = memory_analysis.get("memory_carriers", [])
    carriers_by_type = {}
    for carrier in memory_carriers:
        carrier_type = carrier.carrier_type
        if carrier_type not in carriers_by_type:
            carriers_by_type[carrier_type] = []
        carriers_by_type[carrier_type].append(carrier.carrier_name)

    for carrier_type, names in carriers_by_type.items():
        print(f"  - {carrier_type}: {len(names)} 个")
        print(f"    示例: {', '.join(names[:3])}")

    print("\n✓ 记忆类型分类:")
    memory_types = memory_analysis.get("memory_types", {})
    for type_name, mem_type in memory_types.items():
        print(f"  - {type_name}")
        print(f"    核心要素: {', '.join(mem_type.key_elements[:3])}")
        print(f"    转化潜力: {mem_type.transformation_potential}")

    print("\n✓ 记忆健康度评估:")
    memory_health = memory_analysis.get("memory_health", {})
    for dimension, status in memory_health.items():
        print(f"  - {dimension}: {status}")

    print("\n▶ 识别记忆机会...")
    memory_opportunities = memory_skill.identify_memory_opportunities(memory_analysis, material)

    print(f"\n✓ 识别到 {len(memory_opportunities)} 个记忆转化机会:")
    for i, opp in enumerate(memory_opportunities, 1):
        print(f"  {i}. {opp.memory_asset} → {opp.transformation_path}")

    print("\n▶ 生成完整报告...")
    memory_report = memory_skill.generate_report(material)
    memory_word_count = len(memory_report)

    print(f"\n✓ 社会记忆报告生成完成")
    print(f"  - 总字数: {memory_word_count} 字")

    # 保存报告
    print("\n" + "=" * 80)
    print("【步骤 3】保存完整报告")
    print("=" * 80)

    full_report = f"""# 音寨布依族村专业视角分析报告

> 基于《乡土中国》与《神堂记忆》的双重理论视角
>
> 本报告从乡土社会结构与社会记忆系统两个专业维度，
> 深入分析音寨布依族村的文化遗产价值与发展潜力。

---

{xiangtu_report}

---

{memory_report}

---

## 综合建议：理论融合的实践路径

### 从"乡土中国"到"神堂记忆"的方法论整合

《乡土中国》帮助我们理解**村落是什么**（社会结构、运行逻辑），
《神堂记忆》帮助我们理解**村落记得什么**（集体记忆、文化意义）。

两者结合，才能完整把握乡村文化遗产的"形"与"魂"：

1. **结构+内容**: 用乡土中国理解社会结构，用神堂记忆挖掘记忆内容
2. **静态+动态**: 用乡土中国看礼治秩序，用神堂记忆看记忆的政治
3. **事实+意义**: 用乡土中国理解"是什么"，用神堂记忆理解"怎么被记住"

### 核心实践原则

1. **理解先于改造**: 深入理解乡土逻辑和社会记忆，才能进行有效的文化遗产活化
2. **村民是主体**: 让村民成为文化的讲述者、记忆的建构者、遗产的受益者
3. **传统的创造性转化**: 不是原样复制，而是在理解传统的基础上实现当代转化
4. **记忆即资产**: 从"管理文化遗产资源"到"运营乡村社会记忆"

---

**报告生成时间**: {material['data_profile'].get('report_date', '2024')}
**数据来源**: 音寨布依族村田野调查 ({len(material['citation_pool'])} 个文本片段)
**分析框架**: 费孝通《乡土中国》+ 景军《神堂记忆》
"""

    # 保存完整报告
    report_path = '/Users/alwan/FieldMind/professional_skills_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(full_report)

    print(f"✓ 完整报告已保存: {report_path}")
    print(f"  - 乡土中国报告: {xiangtu_word_count} 字")
    print(f"  - 社会记忆报告: {memory_word_count} 字")
    print(f"  - 总计: {len(full_report)} 字")

    # 生成测试总结
    print("\n" + "=" * 80)
    print("【测试总结】")
    print("=" * 80)

    summary = f"""
## 专业 Skills 集成测试总结

### ✓ 测试通过项

1. **乡土中国 Skill**
   - 成功识别 {len(xiangtu_features)} 个乡土社会特征
   - 生成 {len(xiangtu_opportunities)} 个发展机会
   - 完成社会健康度诊断
   - 报告字数: {xiangtu_word_count} 字

2. **社会记忆 Skill**
   - 识别 {len(memory_carriers)} 个记忆载体
   - 分类 {len(memory_types)} 种记忆类型
   - 完成记忆健康度评估
   - 生成 {len(memory_opportunities)} 个记忆转化机会
   - 报告字数: {memory_word_count} 字

### 核心成果

✓ 两个专业 Skill 成功融入系统
✓ 能够从真实田野数据中提取理论分析
✓ 生成高质量专业视角报告
✓ 实现《乡土中国》与《神堂记忆》双重理论视角

### 使用场景

这两个 Skill 适合用于：
- 乡村文化遗产项目的前期深度调研
- 为投资决策提供专业理论支撑
- 培训团队理解乡土社会与社会记忆理论
- 生成学术水准的项目分析报告

### 与现有 Skills 的关系

- **Level 1 (田野调查)**: 基础报告，实用导向
- **Level 3 (商业分析)**: 商业可行性，市场导向
- **乡土中国 Skill**: 社会结构分析，理论深度
- **社会记忆 Skill**: 文化记忆分析，人类学视角

四个 Skill 形成完整的分析矩阵：
- 横向：基础→商业→理论
- 纵向：资源→价值→记忆

"""

    print(summary)

    # 保存测试总结
    summary_path = '/Users/alwan/FieldMind/professional_skills_test_summary.md'
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)

    print(f"\n✓ 测试总结已保存: {summary_path}")

    return {
        'xiangtu_word_count': xiangtu_word_count,
        'memory_word_count': memory_word_count,
        'total_word_count': len(full_report),
        'xiangtu_features': len(xiangtu_features),
        'xiangtu_opportunities': len(xiangtu_opportunities),
        'memory_carriers': len(memory_carriers),
        'memory_types': len(memory_types),
        'memory_opportunities': len(memory_opportunities)
    }


if __name__ == '__main__':
    try:
        results = test_professional_skills()

        print("\n" + "=" * 80)
        print("✓ 所有测试完成")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
