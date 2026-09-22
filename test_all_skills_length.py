"""
测试所有 Skills 生成的报告字数
"""

import sys
sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.report_generation.data_driven_report_builder import DataDrivenReportBuilder
from app.services.report_generation.skills.field_investigation_skill import FieldInvestigationSkill
from app.services.report_generation.skills.xiangtu_china_skill import XiangtuChinaSkill
from app.services.report_generation.skills.social_memory_skill import SocialMemorySkill
from app.services.report_generation.skills.business_sop_skill import BusinessSOPSkill
from app.services.report_generation.skills.commercial_feasibility_skill import CommercialFeasibilitySkill

# 初始化数据库连接
DATABASE_URL = "sqlite:///backend/src/data/fieldmind.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# 初始化
builder = DataDrivenReportBuilder(db=session)

# 提取数据
project_id = 2
material_obj = builder.extract_report_material(project_id)
material = {
    'main_keywords': material_obj.main_keywords,
    'keyword_communities': material_obj.keyword_communities,
    'core_entities': material_obj.core_entities,
    'entity_relations': material_obj.entity_relations,
    'timeline': material_obj.timeline,
    'citation_pool': material_obj.citation_pool,
    'data_profile': material_obj.data_profile
}

print("=" * 80)
print(f"测试所有 Skills 生成的报告字数（项目ID: {project_id}）")
print("=" * 80)
print()

# 测试各个Skill
results = {}

# 1. 田野调查
try:
    field_skill = FieldInvestigationSkill()
    field_report = field_skill.generate_field_report_content(material, "田野调查综合分析")
    results['田野调查'] = len(field_report)
    print(f"✓ 田野调查: {len(field_report)} 字")
except Exception as e:
    print(f"✗ 田野调查: 失败 - {e}")
    results['田野调查'] = 0

# 2. 乡土中国
try:
    xiangtu_skill = XiangtuChinaSkill()
    xiangtu_report = xiangtu_skill.generate_report(material)
    results['乡土中国'] = len(xiangtu_report)
    print(f"✓ 乡土中国: {len(xiangtu_report)} 字")
except Exception as e:
    print(f"✗ 乡土中国: 失败 - {e}")
    results['乡土中国'] = 0

# 3. 社会记忆
try:
    memory_skill = SocialMemorySkill()
    memory_report = memory_skill.generate_report(material)
    results['社会记忆'] = len(memory_report)
    print(f"✓ 社会记忆: {len(memory_report)} 字")
except Exception as e:
    print(f"✗ 社会记忆: 失败 - {e}")
    results['社会记忆'] = 0

# 4. 商业SOP
try:
    business_sop_skill = BusinessSOPSkill()
    business_sop_report = business_sop_skill.generate_report(material)
    results['商业SOP'] = len(business_sop_report)
    print(f"✓ 商业SOP: {len(business_sop_report)} 字")
except Exception as e:
    print(f"✗ 商业SOP: 失败 - {e}")
    results['商业SOP'] = 0

# 5. 商业可行性验证
try:
    feasibility_skill = CommercialFeasibilitySkill()
    feasibility_report = feasibility_skill.generate_report(material)
    results['商业可行性验证'] = len(feasibility_report)
    print(f"✓ 商业可行性验证: {len(feasibility_report)} 字")
except Exception as e:
    print(f"✗ 商业可行性验证: 失败 - {e}")
    results['商业可行性验证'] = 0

print()
print("=" * 80)
print("三个万字报告的字数统计")
print("=" * 80)
print()

# 报告1：田野调查
report1_total = results.get('田野调查', 0)
print(f"【报告1：田野调查万字报告】")
print(f"  - 田野调查 Skill: {results.get('田野调查', 0)} 字")
print(f"  - 总计: {report1_total} 字")
print(f"  - 目标: 10,000 字")
print(f"  - 状态: {'✓ 已达标' if report1_total >= 10000 else f'✗ 还差 {10000 - report1_total} 字'}")
print()

# 报告2：专业分析
report2_total = results.get('乡土中国', 0) + results.get('社会记忆', 0)
print(f"【报告2：专业分析万字报告】")
print(f"  - 乡土中国 Skill: {results.get('乡土中国', 0)} 字")
print(f"  - 社会记忆 Skill: {results.get('社会记忆', 0)} 字")
print(f"  - 总计: {report2_total} 字")
print(f"  - 目标: 10,000 字")
print(f"  - 状态: {'✓ 已达标' if report2_total >= 10000 else f'✗ 还差 {10000 - report2_total} 字'}")
print()

# 报告3：商业分析
report3_total = results.get('商业SOP', 0) + results.get('商业可行性验证', 0)
print(f"【报告3：商业分析万字报告】")
print(f"  - 商业SOP Skill: {results.get('商业SOP', 0)} 字")
print(f"  - 商业可行性验证 Skill: {results.get('商业可行性验证', 0)} 字")
print(f"  - 总计: {report3_total} 字")
print(f"  - 目标: 10,000 字")
print(f"  - 状态: {'✓ 已达标' if report3_total >= 10000 else f'✗ 还差 {10000 - report3_total} 字'}")
print()

session.close()

print("=" * 80)
print("测试完成")
print("=" * 80)
