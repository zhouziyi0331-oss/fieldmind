import sys
sys.path.append('/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

from app.database import SessionLocal
from app.models import Project, ProjectDocument
from app.services.knowledge_graph_v2 import knowledge_graph_service_v2

db = SessionLocal()

# 获取项目2的文档
project_id = 2
documents = db.query(ProjectDocument).filter(
    ProjectDocument.project_id == project_id,
    ProjectDocument.status == "completed"
).all()

print(f"找到 {len(documents)} 个文档")

# 转换为字典列表
doc_dicts = []
for doc in documents:
    doc_dict = {
        'id': doc.id,
        'text_content': doc.text_content,
        'converted_content': doc.converted_content if hasattr(doc, 'converted_content') else None,
        'content': doc.text_content or (doc.converted_content if hasattr(doc, 'converted_content') else '') or ''
    }
    doc_dicts.append(doc_dict)
    print(f"文档 {doc.id}: text_content={len(doc.text_content or '')} chars")

# 测试提取关键词
try:
    keywords = knowledge_graph_service_v2.extract_keywords(doc_dicts, 10)
    print(f"\n✅ 成功提取 {len(keywords)} 个关键词:")
    for kw in keywords[:5]:
        print(f"  - {kw}")
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()

db.close()
