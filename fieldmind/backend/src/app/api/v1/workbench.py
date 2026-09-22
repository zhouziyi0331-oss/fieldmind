"""
工作舱统一 API 接口

提供工作舱所有服务的统一 REST API 入口
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.workbench_services import get_workbench_services, WorkbenchServices
from app.core.deps import get_db, get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


# ==================== 请求/响应模型 ====================

class NLPRequest(BaseModel):
    """NLP 请求"""
    text: str
    language: str = "zh"


class KeywordExtractionRequest(BaseModel):
    """关键词提取请求"""
    text: str
    top_k: int = 10


class EntityExtractionRequest(BaseModel):
    """实体提取请求"""
    text: str


class RAGQueryRequest(BaseModel):
    """RAG 查询请求"""
    question: str
    project_id: int
    top_k: int = 5
    strategy: str = "auto"


class KGBuildRequest(BaseModel):
    """知识图谱构建请求"""
    document_ids: List[int]
    project_id: int


class KGQueryRequest(BaseModel):
    """知识图谱查询请求"""
    query: str
    project_id: int
    limit: int = 10


class DocumentProcessRequest(BaseModel):
    """文档处理请求"""
    project_id: int


class CrawlerRequest(BaseModel):
    """爬虫请求"""
    url: str
    max_depth: int = 2
    max_pages: int = 100


# ==================== 工作舱健康检查 ====================

@router.get("/health")
async def health_check(
    db: Session = Depends(get_db)
):
    """
    工作舱健康检查

    返回所有服务的状态
    """
    services = get_workbench_services(db)
    return services.health_check()


@router.get("/services")
async def list_services(
    db: Session = Depends(get_db)
):
    """
    列出所有服务

    返回每个服务的详细信息
    """
    services = get_workbench_services(db)
    all_services = services.get_all_services_status()

    return {
        "services": [
            {
                "name": info.name,
                "status": info.status.value,
                "version": info.version,
                "description": info.description,
                "capabilities": info.capabilities
            }
            for info in all_services.values()
        ]
    }


# ==================== NLP 服务 API ====================

@router.post("/nlp/tokenize")
async def tokenize(
    request: NLPRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    分词

    对输入文本进行分词
    """
    services = get_workbench_services(db)
    tokens = services.nlp.tokenize(request.text, request.language)

    return {
        "tokens": tokens,
        "count": len(tokens)
    }


@router.post("/nlp/keywords")
async def extract_keywords(
    request: KeywordExtractionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    关键词提取

    从文本中提取关键词
    """
    services = get_workbench_services(db)
    keywords = services.nlp.extract_keywords(request.text, request.top_k)

    return {
        "keywords": keywords
    }


@router.post("/nlp/entities")
async def extract_entities(
    request: EntityExtractionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    命名实体识别

    识别文本中的实体
    """
    services = get_workbench_services(db)
    entities = services.nlp.extract_entities(request.text)

    return {
        "entities": entities
    }


@router.post("/nlp/summarize")
async def summarize(
    request: NLPRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    文本摘要

    生成文本摘要
    """
    services = get_workbench_services(db)
    summary = services.nlp.summarize(request.text)

    return {
        "summary": summary
    }


@router.post("/nlp/sentiment")
async def sentiment_analysis(
    request: NLPRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    情感分析

    分析文本情感
    """
    services = get_workbench_services(db)
    result = services.nlp.sentiment_analysis(request.text)

    return result


# ==================== RAG 服务 API ====================

@router.post("/rag/query")
async def rag_query(
    request: RAGQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    RAG 问答

    基于知识库的智能问答
    """
    services = get_workbench_services(db)
    result = services.rag.query(
        question=request.question,
        project_id=request.project_id,
        top_k=request.top_k,
        strategy=request.strategy
    )

    return result


@router.post("/rag/index")
async def index_documents(
    request: KGBuildRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    索引文档

    将文档加入 RAG 索引
    """
    services = get_workbench_services(db)
    result = services.rag.index_documents(
        document_ids=request.document_ids,
        project_id=request.project_id
    )

    return result


# ==================== 知识图谱服务 API ====================

@router.post("/kg/build")
async def build_knowledge_graph(
    request: KGBuildRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    构建知识图谱

    从文档自动构建知识图谱
    """
    services = get_workbench_services(db)
    result = services.knowledge_graph.build_graph_from_documents(
        document_ids=request.document_ids,
        project_id=request.project_id
    )

    return result


@router.post("/kg/query")
async def query_knowledge_graph(
    request: KGQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询知识图谱

    查询知识图谱中的实体和关系
    """
    services = get_workbench_services(db)
    results = services.knowledge_graph.query_graph(
        query=request.query,
        project_id=request.project_id,
        limit=request.limit
    )

    return {
        "results": results
    }


@router.get("/kg/entity/{entity_id}/neighbors")
async def get_entity_neighbors(
    entity_id: int,
    project_id: int,
    depth: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取实体邻居

    获取指定实体的邻居节点
    """
    services = get_workbench_services(db)
    result = services.knowledge_graph.get_entity_neighbors(
        entity_id=entity_id,
        project_id=project_id,
        depth=depth
    )

    return result


# ==================== 文档处理服务 API ====================

@router.post("/document/process")
async def process_document(
    file: UploadFile = File(...),
    project_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    处理文档

    上传并处理文档
    """
    if not project_id:
        raise HTTPException(status_code=400, detail="缺少 project_id")

    # 保存上传的文件
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        services = get_workbench_services(db)
        result = services.document.process_file(
            file_path=tmp_path,
            project_id=project_id,
            user_id=current_user.id
        )

        return result

    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/document/formats")
async def get_supported_formats(
    db: Session = Depends(get_db)
):
    """
    获取支持的文件格式

    返回所有支持的文件格式列表
    """
    services = get_workbench_services(db)
    formats = services.document.get_supported_formats()

    return {
        "formats": formats,
        "count": len(formats)
    }


# ==================== 爬虫服务 API ====================

@router.post("/crawler/crawl")
async def crawl_website(
    request: CrawlerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    爬取网站

    爬取指定网站的内容

    注意：此功能需要整合爬虫系统后才能使用
    """
    services = get_workbench_services(db)

    try:
        result = services.crawler.crawl_website(
            url=request.url,
            max_depth=request.max_depth,
            max_pages=request.max_pages
        )
        return result

    except NotImplementedError as e:
        raise HTTPException(
            status_code=501,
            detail="爬虫服务尚未实现，需要整合 firecrawl"
        )


# ==================== 记忆服务 API ====================

@router.post("/memory/store")
async def store_memory(
    content: str,
    context: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    存储记忆

    存储用户的记忆内容

    注意：此功能需要整合 mem0 后才能使用
    """
    services = get_workbench_services(db)

    try:
        memory_id = services.memory.store_memory(
            user_id=current_user.id,
            content=content,
            context=context or {}
        )

        return {
            "memory_id": memory_id,
            "status": "stored"
        }

    except NotImplementedError as e:
        raise HTTPException(
            status_code=501,
            detail="记忆服务尚未实现，需要整合 mem0"
        )


@router.get("/memory/search")
async def search_memory(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    搜索记忆

    搜索用户的历史记忆

    注意：此功能需要整合 mem0 后才能使用
    """
    raise HTTPException(
        status_code=501,
        detail="记忆搜索功能尚未实现，需要整合 mem0"
    )


# ==================== 可视化服务 API ====================

@router.post("/visualization/mindmap")
async def generate_mind_map(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成思维导图

    根据数据生成思维导图

    注意：此功能需要整合思维导图工具后才能使用
    """
    services = get_workbench_services(db)

    try:
        result = services.visualization.generate_mind_map(data)
        return result

    except NotImplementedError as e:
        raise HTTPException(
            status_code=501,
            detail="可视化服务尚未实现，需要整合 mind-map"
        )


# ==================== 工作舱概览 API ====================

@router.get("/overview")
async def workbench_overview(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    工作舱概览

    获取工作舱的整体状态和统计信息
    """
    services = get_workbench_services(db)

    # 健康检查
    health = services.health_check()

    # TODO: 添加更多统计信息
    # - 文档数量
    # - 知识图谱节点/边数量
    # - RAG 索引大小
    # - 最近活动

    return {
        "health": health,
        "user": {
            "id": current_user.id,
            "email": current_user.email
        },
        "statistics": {
            "documents": 0,  # TODO
            "kg_nodes": 0,  # TODO
            "kg_edges": 0,  # TODO
            "indexed_chunks": 0  # TODO
        }
    }
