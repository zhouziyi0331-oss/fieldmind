"""
测试田野调查 Skill 的报告字数
"""

import sys
sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.report_generation.data_driven_report_builder import DataDrivenReportBuilder
from app.services.report_generation.skills.field_investigation_skill import FieldInvestigationSkill

# 初始化数据库连接
DATABASE_URL = "sqlite:///backend/src/data/fieldmind.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# 初始化
builder = DataDrivenReportBuilder(db=session)
skill = FieldInvestigationSkill()

# 提取数据
material_obj = builder.extract_report_material(2)
material = {
    'main_keywords': material_obj.main_keywords,
    'keyword_communities': material_obj.keyword_communities,
    'core_entities': material_obj.core_entities,
    'entity_relations': material_obj.entity_relations,
    'timeline': material_obj.timeline,
    'citation_pool': material_obj.citation_pool,
    'data_profile': material_obj.data_profile
}

# 生成报告
report = skill.generate_report(material)

print(f"田野调查报告字数: {len(report)} 字")
print(f"报告行数: {len(report.split(chr(10)))} 行")
print(f"是否达到万字: {'✓ 是' if len(report) >= 10000 else '✗ 否，还差 ' + str(10000 - len(report)) + ' 字'}")

session.close()
