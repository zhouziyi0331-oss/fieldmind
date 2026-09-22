"""
数据库迁移脚本 - 关键词系统表
"""

# 运行方式：
# cd /Users/alwan/FieldMind/backend/src
# python -c "from app.models.keyword import *; from app.core.database import engine, Base; Base.metadata.create_all(bind=engine)"

import sys
sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')

from app.core.database import engine, Base
from app.models.keyword import Keyword, DocumentKeyword, KeywordRelation, KeywordExtractionTask

print("=" * 60)
print("创建关键词系统数据库表")
print("=" * 60)

# 创建表
Base.metadata.create_all(bind=engine)

print("\n✅ 数据库表创建成功！")
print("\n已创建的表：")
print("  - keywords              关键词表")
print("  - document_keywords     文档-关键词关联表")
print("  - keyword_relations     关键词关系表")
print("  - keyword_extraction_tasks  批量提取任务表")
print("\n" + "=" * 60)
