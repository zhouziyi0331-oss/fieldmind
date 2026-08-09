"""
Tasks 模块 - Celery 任务定义
"""
# 暂时注释掉不存在的导入，避免启动错误
# 这些任务需要在相应的文件中实现

try:
    from .document_tasks import process_document
except ImportError:
    process_document = None

try:
    from .audio_tasks import process_audio_chain
except ImportError:
    process_audio_chain = None

try:
    from .crawler_tasks import intelligent_crawl
except ImportError:
    intelligent_crawl = None

try:
    from .rag_tasks import triple_retrieval_query
except ImportError:
    triple_retrieval_query = None

try:
    from .graph_tasks import build_knowledge_graph
except ImportError:
    build_knowledge_graph = None

try:
    from .report_tasks import generate_report
except ImportError:
    generate_report = None

__all__ = [
    "process_document",
    "process_audio_chain",
    "intelligent_crawl",
    "triple_retrieval_query",
    "build_knowledge_graph",
    "generate_report",
]
