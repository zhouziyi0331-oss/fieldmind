"""
检查 ReportMaterial 数据结构
"""

import sys
sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.report_generation.data_driven_report_builder import DataDrivenReportBuilder


# 初始化数据库连接
DATABASE_URL = "sqlite:///backend/src/data/fieldmind.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# 初始化 ReportBuilder
builder = DataDrivenReportBuilder(db=session)

# 提取数据
material_obj = builder.extract_report_material(2)

print("main_keywords type:", type(material_obj.main_keywords))
print("main_keywords sample:", material_obj.main_keywords[:3] if material_obj.main_keywords else [])
print()

print("core_entities type:", type(material_obj.core_entities))
print("core_entities sample:", material_obj.core_entities if isinstance(material_obj.core_entities, dict) else material_obj.core_entities[:3])
print()

print("citation_pool type:", type(material_obj.citation_pool))
print("citation_pool sample:", material_obj.citation_pool[:2] if material_obj.citation_pool else [])
print()

session.close()
