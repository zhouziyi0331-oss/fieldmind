"""
RAG增强系统 API - 真实集成版

集成到FieldMind系统，连接项目、文档、数据库
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.models.project import Project, ProjectDocument
from app.core.logging_config import get_logger

# 导入RAG增强模块（生产版本）
from app.services.rag.production_agent import create_production_rag_agent, ProductionRAGAgent
from app.services.rag.evaluation import RAGEvaluator, TestDataset
from app.services.rag.citation_tracker import CitationTracker

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/rag-enhanced", tags=["RAG增强系统"])

# 全局Agent实例缓存（按项目ID）
_agent_cache: Dict[int, ProductionRAGAgent] = {}


# ============================================================================
# Request/Response Models
# ============================================================================

class IndexDocumentsRequest(BaseModel):
    """索引文档请求"""
    project_id: int = Field(..., description="项目ID")
    document_ids: Optional[List[int]] = Field(None, description="文档ID列表，为空则索引项目所有文档")
    force_rebuild: bool = Field(False, description="是否强制重建索引")


class QueryRequest(BaseModel):
    """智能查询请求"""
    project_id: int = Field(..., description="项目ID")
    query: str = Field(..., description="用户查询", min_length=1, max_length=500)
    top_k: int = Field(5, description="返回结果数", ge=1, le=20)
    enable_hybrid: bool = Field(True, description="启用混合检索")
    enable_diversity: bool = Field(True, description="启用多样性重排序")
    enable_citation: bool = Field(True, description="启用引用追踪")
    use_conversation_context: bool = Field(False, description="使用对话上下文")


class EvaluationRequest(BaseModel):
    """评测请求"""
    project_id: int = Field(..., description="项目ID")
    test_dataset_path: Optional[str] = Field(None, description="测试数据集路径")
    version: str = Field("v1.0", description="版本标识")


class QueryResponse(BaseModel):
    """查询响应"""
    query: str
    answer: str
    intent: Dict[str, Any]
    retrieval_results: List[Dict[str, Any]]
    retrieval_metrics: Dict[str, Any]
    citations: List[Dict[str, Any]]
    citation_metrics: Dict[str, Any]
    visualization: Dict[str, Any]
    strategy: str
    processing_time_ms: float
    project_id: int


# ============================================================================
# Helper Functions
# ============================================================================

async def get_or_create_agent(project_id: int, db: Session) -> ProductionRAGAgent:
    """获取或创建项目的Agent实例"""
    if project_id in _agent_cache:
        return _agent_cache[project_id]

    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

    # 创建新Agent（使用生产版本：真实嵌入+LLM）
    agent = await create_production_rag_agent(enable_all_features=True)
    _agent_cache[project_id] = agent

    logger.info(f"为项目 {project_id} 创建了生产级Agent实例")
    return agent


async def index_project_documents(
    project_id: int,
    document_ids: Optional[List[int]],
    db: Session,
    agent: ProductionRAGAgent
) -> Dict[str, Any]:
    """索引项目文档"""
    # 获取文档
    query = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id)

    if document_ids:
        query = query.filter(ProjectDocument.id.in_(document_ids))

    documents = query.all()

    if not documents:
        return {
            "indexed": 0,
            "failed": 0,
            "message": "没有找到要索引的文档"
        }

    indexed = 0
    failed = 0

    for doc in documents:
        try:
            # 获取文档内容
            content = doc.content or doc.extracted_text or ""

            if not content or len(content) < 10:
                logger.warning(f"文档 {doc.id} 内容为空或太短，跳过索引")
                failed += 1
                continue

            # 构建元数据
            metadata = {
                "project_id": project_id,
                "document_id": doc.id,
                "file_name": doc.file_name,
                "file_type": doc.file_type,
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            }

            # 索引到Agent
            await agent.index_document(
                doc_id=f"proj_{project_id}_doc_{doc.id}",
                content=content,
                metadata=metadata
            )

            indexed += 1
            logger.info(f"成功索引文档 {doc.id}: {doc.file_name}")

        except Exception as e:
            logger.error(f"索引文档 {doc.id} 失败: {str(e)}")
            failed += 1

    return {
        "indexed": indexed,
        "failed": failed,
        "total": len(documents),
        "message": f"成功索引 {indexed} 个文档，失败 {failed} 个"
    }


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/index", summary="索引项目文档到RAG系统")
async def index_documents(
    request: IndexDocumentsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    索引项目文档到RAG系统

    **功能**:
    - 将项目文档索引到增强型RAG Agent
    - 支持向量检索、关键词检索、BM25检索
    - 自动提取实体和关键词

    **使用场景**:
    - 项目创建后首次索引
    - 新增文档后增量索引
    - 更新文档后重新索引
    """
    try:
        # 获取Agent
        agent = await get_or_create_agent(request.project_id, db)

        # 如果强制重建，清空现有索引
        if request.force_rebuild:
            # 重新创建Agent实例
            agent = await create_enhanced_rag_agent(enable_all_features=True)
            _agent_cache[request.project_id] = agent
            logger.info(f"项目 {request.project_id} 强制重建索引")

        # 执行索引
        result = await index_project_documents(
            project_id=request.project_id,
            document_ids=request.document_ids,
            db=db,
            agent=agent
        )

        return {
            "success": True,
            "project_id": request.project_id,
            **result,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"索引文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"索引失败: {str(e)}")


@router.post("/query", response_model=QueryResponse, summary="智能查询（增强型RAG）")
async def query_with_rag(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    使用增强型RAG系统执行智能查询

    **功能**:
    - 意图识别（10种意图类型）
    - 多路召回（向量+关键词+BM25）
    - 多样性重排序
    - 引用溯源
    - 质量分析

    **返回**:
    - 生成的答案
    - 检索结果及质量指标
    - 引用来源及置信度
    - 可视化数据
    """
    try:
        # 获取Agent
        agent = await get_or_create_agent(request.project_id, db)

        # 检查是否已索引文档
        stats = agent.get_statistics()
        if stats.get("total_documents", 0) == 0:
            raise HTTPException(
                status_code=400,
                detail="项目尚未索引任何文档，请先调用 /index 接口"
            )

        # 执行查询
        result = await agent.process_query(
            query=request.query,
            top_k=request.top_k,
            use_conversation_context=request.use_conversation_context
        )

        # 添加项目ID
        result["project_id"] = request.project_id

        return QueryResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/conversation-history/{project_id}", summary="获取对话历史")
async def get_conversation_history(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目的对话历史

    **功能**:
    - 查看多轮对话记录
    - 分析对话上下文
    """
    try:
        agent = await get_or_create_agent(project_id, db)
        history = agent.get_conversation_history()

        return {
            "project_id": project_id,
            "conversation_count": len(history),
            "history": history
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话历史失败: {str(e)}")


@router.delete("/conversation/{project_id}", summary="清空对话历史")
async def clear_conversation(
    project_id: int,
    db: Session = Depends(get_db)
):
    """清空项目的对话历史"""
    try:
        agent = await get_or_create_agent(project_id, db)
        agent.clear_conversation()

        return {
            "success": True,
            "project_id": project_id,
            "message": "对话历史已清空"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空对话历史失败: {str(e)}")


@router.post("/evaluate", summary="评测RAG系统质量")
async def evaluate_rag(
    request: EvaluationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    评测RAG系统质量

    **评测指标**:
    - 准确率（答案与预期的相似度）
    - 召回率（检索到的相关文档比例）
    - 引用正确率（引用来源的准确性）
    - 回答完整度（覆盖了多少关键点）

    **使用场景**:
    - 系统上线前质量验证
    - 版本迭代效果对比
    - 持续质量监控
    """
    try:
        agent = await get_or_create_agent(request.project_id, db)

        # 加载测试数据集
        if request.test_dataset_path:
            import json
            with open(request.test_dataset_path, 'r', encoding='utf-8') as f:
                dataset_dict = json.load(f)
                test_dataset = TestDataset.from_dict(dataset_dict)
        else:
            # 使用默认测试集
            from app.services.rag.evaluation import generate_default_test_dataset
            test_dataset = generate_default_test_dataset()

        # 创建评测器
        evaluator = RAGEvaluator(
            test_dataset=test_dataset,
            results_dir=f"evaluation_results/project_{request.project_id}"
        )

        # 执行评测（后台任务）
        def run_evaluation():
            predictions = []
            for test_case in test_dataset.test_cases[:10]:  # 先评测10个样本
                try:
                    import asyncio
                    result = asyncio.run(agent.process_query(test_case.question, top_k=5))

                    predictions.append({
                        "test_case_id": test_case.id,
                        "predicted_answer": result["answer"],
                        "retrieved_doc_ids": [
                            r["doc_id"] for r in result.get("retrieval_results", [])
                        ],
                        "sources": result.get("citations", [])
                    })
                except Exception as e:
                    logger.error(f"评测测试用例 {test_case.id} 失败: {str(e)}")

            # 生成评测报告
            report = evaluator.evaluate_batch(predictions, request.version)
            logger.info(f"评测完成: {report.to_dict()}")

        background_tasks.add_task(run_evaluation)

        return {
            "success": True,
            "project_id": request.project_id,
            "version": request.version,
            "test_cases_count": len(test_dataset.test_cases),
            "message": "评测任务已启动，请稍后查看结果"
        }

    except Exception as e:
        logger.error(f"评测失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"评测失败: {str(e)}")


@router.get("/statistics/{project_id}", summary="获取系统统计")
async def get_statistics(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目RAG系统的统计信息

    **统计内容**:
    - 索引文档数
    - 对话轮次数
    - 可用工具数
    - 启用的功能
    """
    try:
        agent = await get_or_create_agent(project_id, db)
        stats = agent.get_statistics()

        return {
            "project_id": project_id,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/health", summary="健康检查")
async def health_check():
    """RAG增强系统健康检查"""
    return {
        "status": "healthy",
        "service": "rag_enhanced",
        "cached_agents": len(_agent_cache),
        "timestamp": datetime.now().isoformat()
    }


@router.delete("/cache/{project_id}", summary="清除项目Agent缓存")
async def clear_agent_cache(project_id: int):
    """清除项目的Agent缓存（释放内存）"""
    if project_id in _agent_cache:
        del _agent_cache[project_id]
        return {
            "success": True,
            "project_id": project_id,
            "message": "Agent缓存已清除"
        }
    else:
        return {
            "success": False,
            "project_id": project_id,
            "message": "该项目没有缓存的Agent"
        }
