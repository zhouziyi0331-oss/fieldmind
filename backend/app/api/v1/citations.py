"""
引用溯源系统 API 端点

提供 HTTP API 接口访问引用追踪功能
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.rag.citation_integration import (
    RAGServiceWithCitations,
    create_rag_service_with_citations,
    CitationAnalyzer
)
from app.services.rag.citation_tracker import AnswerWithCitations, Citation, DocumentFragment

router = APIRouter(prefix="/api/v1/citations", tags=["citations"])

# 全局服务实例（实际应使用依赖注入）
_rag_service: Optional[RAGServiceWithCitations] = None


async def get_rag_service() -> RAGServiceWithCitations:
    """获取 RAG 服务实例（依赖注入）"""
    global _rag_service
    if _rag_service is None:
        _rag_service = await create_rag_service_with_citations()
    return _rag_service


# ============================================================================
# Request/Response Models
# ============================================================================

class DocumentIndexRequest(BaseModel):
    """文档索引请求"""
    doc_id: str = Field(..., description="文档ID")
    content: str = Field(..., description="文档内容")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")


class QueryRequest(BaseModel):
    """查询请求"""
    query: str = Field(..., description="用户问题", min_length=1, max_length=500)
    top_k: int = Field(default=5, description="检索文档数", ge=1, le=20)
    enable_citation_tracking: bool = Field(default=True, description="是否启用引用追踪")
    filter_metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据过滤")


class CitationResponse(BaseModel):
    """引用响应"""
    answer_sentence: str
    source_doc_id: str
    source_content: str
    start_char: int
    end_char: int
    confidence_score: float
    similarity_score: float
    match_type: str
    evidence_text: str


class QueryResponse(BaseModel):
    """查询响应"""
    query: str
    answer: str
    citations: List[CitationResponse]
    visualization: Dict[str, Any]
    metrics: Dict[str, Any]
    context_used: bool
    timestamp: datetime = Field(default_factory=datetime.now)


class ValidationRequest(BaseModel):
    """验证请求"""
    query: str
    answer: str
    citations: List[Dict[str, Any]]
    quality_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class ValidationResponse(BaseModel):
    """验证响应"""
    is_valid: bool
    quality_score: float
    overall_confidence: float
    coverage_ratio: float
    citation_breakdown: Dict[str, int]
    recommendation: str


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/index", summary="索引文档")
async def index_document(
    request: DocumentIndexRequest,
    service: RAGServiceWithCitations = Depends(get_rag_service)
):
    """
    索引单个文档到知识库

    **功能**:
    - 将文档内容向量化并存储
    - 支持元数据标记
    - 返回索引状态

    **示例**:
    ```json
    {
        "doc_id": "doc_001",
        "content": "FieldMind是一个智能知识管理系统...",
        "metadata": {"category": "intro", "version": "1.0"}
    }
    ```
    """
    try:
        document = await service.index_document(
            doc_id=request.doc_id,
            content=request.content,
            metadata=request.metadata
        )

        return {
            "success": True,
            "doc_id": document.doc_id,
            "indexed_at": document.created_at.isoformat(),
            "message": "文档索引成功"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"索引失败: {str(e)}")


@router.post("/index-batch", summary="批量索引文档")
async def index_documents_batch(
    documents: List[DocumentIndexRequest],
    service: RAGServiceWithCitations = Depends(get_rag_service)
):
    """
    批量索引多个文档

    **功能**:
    - 一次性索引多个文档
    - 提高索引效率
    - 返回成功和失败统计

    **限制**: 单次最多索引100个文档
    """
    if len(documents) > 100:
        raise HTTPException(status_code=400, detail="单次最多索引100个文档")

    success_count = 0
    failed_docs = []

    for doc_req in documents:
        try:
            await service.index_document(
                doc_id=doc_req.doc_id,
                content=doc_req.content,
                metadata=doc_req.metadata
            )
            success_count += 1
        except Exception as e:
            failed_docs.append({
                "doc_id": doc_req.doc_id,
                "error": str(e)
            })

    return {
        "success": True,
        "total": len(documents),
        "indexed": success_count,
        "failed": len(failed_docs),
        "failed_docs": failed_docs
    }


@router.post("/query", response_model=QueryResponse, summary="智能问答（带引用）")
async def query_with_citations(
    request: QueryRequest,
    service: RAGServiceWithCitations = Depends(get_rag_service)
):
    """
    执行智能问答并追踪引用来源

    **功能**:
    - 检索相关文档
    - 生成答案
    - 追踪每句话的引用来源
    - 提供置信度评分

    **返回**:
    - 答案文本
    - 详细引用列表
    - 可视化数据
    - 质量指标

    **示例**:
    ```json
    {
        "query": "FieldMind支持哪些文档格式？",
        "top_k": 5,
        "enable_citation_tracking": true
    }
    ```
    """
    try:
        result = await service.generate_with_citations(
            query=request.query,
            top_k=request.top_k,
            enable_citation_tracking=request.enable_citation_tracking
        )

        # 转换引用格式
        citations = []
        for c in result.get('citations', []):
            citations.append(CitationResponse(
                answer_sentence=c['answer_sentence'],
                source_doc_id=c['source_fragment']['doc_id'],
                source_content=c['source_fragment']['content'],
                start_char=c['source_fragment']['start_char'],
                end_char=c['source_fragment']['end_char'],
                confidence_score=c['confidence_score'],
                similarity_score=c['similarity_score'],
                match_type=c['match_type'],
                evidence_text=c['evidence_text']
            ))

        return QueryResponse(
            query=result['query'],
            answer=result['answer'],
            citations=citations,
            visualization=result.get('visualization', {}),
            metrics=result.get('metrics', {}),
            context_used=result.get('context_used', False)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/validate", response_model=ValidationResponse, summary="验证引用质量")
async def validate_citation_quality(
    request: ValidationRequest,
    service: RAGServiceWithCitations = Depends(get_rag_service)
):
    """
    验证答案的引用质量

    **功能**:
    - 评估引用置信度
    - 检查覆盖率
    - 识别问题引用
    - 提供改进建议

    **质量标准**:
    - 高质量: 质量分数 ≥ 0.8
    - 中等质量: 0.6 ≤ 质量分数 < 0.8
    - 低质量: 质量分数 < 0.6
    """
    try:
        # 重构为 AnswerWithCitations 对象
        citations_list = []
        for c_dict in request.citations:
            fragment = DocumentFragment(
                doc_id=c_dict['source_fragment']['doc_id'],
                content=c_dict['source_fragment']['content'],
                start_char=c_dict['source_fragment']['start_char'],
                end_char=c_dict['source_fragment']['end_char']
            )

            citation = Citation(
                answer_sentence=c_dict['answer_sentence'],
                source_fragment=fragment,
                confidence_score=c_dict['confidence_score'],
                similarity_score=c_dict['similarity_score'],
                match_type=c_dict['match_type'],
                evidence_text=c_dict['evidence_text']
            )
            citations_list.append(citation)

        # 计算整体置信度和覆盖率
        overall_confidence = sum(c.confidence_score for c in citations_list) / len(citations_list) if citations_list else 0
        covered_chars = sum(len(c.answer_sentence) for c in citations_list)
        coverage_ratio = min(1.0, covered_chars / len(request.answer)) if request.answer else 0

        answer_with_citations = AnswerWithCitations(
            query=request.query,
            answer=request.answer,
            citations=citations_list,
            overall_confidence=overall_confidence,
            coverage_ratio=coverage_ratio
        )

        validation = await service.validate_citation_quality(
            answer_with_citations,
            quality_threshold=request.quality_threshold
        )

        return ValidationResponse(**validation)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.get("/problematic", summary="识别问题引用")
async def identify_problematic_citations(
    query: str = Query(..., description="原始查询"),
    answer: str = Query(..., description="生成的答案"),
    confidence_threshold: float = Query(0.5, ge=0.0, le=1.0, description="置信度阈值"),
    service: RAGServiceWithCitations = Depends(get_rag_service)
):
    """
    识别答案中的问题引用

    **识别标准**:
    - 置信度低于阈值
    - 弱匹配类型
    - 相似度过低

    **返回**: 问题引用列表及改进建议
    """
    try:
        # 重新生成引用（实际应该从缓存或数据库获取）
        result = await service.generate_with_citations(
            query=query,
            enable_citation_tracking=True
        )

        # 构建 AnswerWithCitations
        citations_list = []
        for c_dict in result['citations']:
            fragment = DocumentFragment(
                doc_id=c_dict['source_fragment']['doc_id'],
                content=c_dict['source_fragment']['content'],
                start_char=c_dict['source_fragment']['start_char'],
                end_char=c_dict['source_fragment']['end_char']
            )

            citation = Citation(
                answer_sentence=c_dict['answer_sentence'],
                source_fragment=fragment,
                confidence_score=c_dict['confidence_score'],
                similarity_score=c_dict['similarity_score'],
                match_type=c_dict['match_type'],
                evidence_text=c_dict['evidence_text']
            )
            citations_list.append(citation)

        answer_with_citations = AnswerWithCitations(
            query=result['query'],
            answer=result['answer'],
            citations=citations_list,
            overall_confidence=result['metrics']['overall_confidence'],
            coverage_ratio=result['metrics']['coverage_ratio']
        )

        # 识别问题引用
        problematic = CitationAnalyzer.identify_problematic_citations(
            answer_with_citations,
            confidence_threshold=confidence_threshold
        )

        return {
            "total_citations": len(answer_with_citations.citations),
            "problematic_count": len(problematic),
            "problematic_citations": problematic
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")


@router.get("/statistics", summary="获取引用统计")
async def get_citation_statistics(
    service: RAGServiceWithCitations = Depends(get_rag_service)
):
    """
    获取系统的引用统计信息

    **统计内容**:
    - 总文档数
    - 总查询数
    - 平均引用数
    - 置信度分布

    **注意**: 实际生产环境应该从数据库读取历史数据
    """
    try:
        stats = service.get_statistics()

        return {
            "total_documents": stats.get("total_documents", 0),
            "embedding_dim": stats.get("embedding_dim", 768),
            "message": "统计信息（当前会话）"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.delete("/document/{doc_id}", summary="删除文档")
async def delete_document(
    doc_id: str,
    service: RAGServiceWithCitations = Depends(get_rag_service)
):
    """
    从知识库删除文档

    **功能**:
    - 删除文档及其向量
    - 清理相关索引

    **注意**: 删除后无法恢复
    """
    try:
        success = await service.delete_document(doc_id)

        if success:
            return {
                "success": True,
                "doc_id": doc_id,
                "message": "文档删除成功"
            }
        else:
            raise HTTPException(status_code=404, detail="文档不存在")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/health", summary="健康检查")
async def health_check(service: RAGServiceWithCitations = Depends(get_rag_service)):
    """
    引用溯源系统健康检查

    **检查项**:
    - 服务状态
    - 向量存储状态
    - 引用追踪器状态
    """
    try:
        stats = service.get_statistics()

        return {
            "status": "healthy",
            "service": "citation_tracker",
            "components": {
                "vector_store": "ok",
                "embedding_service": "ok",
                "citation_tracker": "ok"
            },
            "statistics": stats
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# ============================================================================
# 使用说明
# ============================================================================

"""
## API 使用流程

### 1. 索引文档
POST /api/v1/citations/index
{
    "doc_id": "doc_001",
    "content": "文档内容...",
    "metadata": {"category": "intro"}
}

### 2. 执行查询
POST /api/v1/citations/query
{
    "query": "FieldMind支持哪些功能？",
    "top_k": 5,
    "enable_citation_tracking": true
}

### 3. 验证引用质量
POST /api/v1/citations/validate
{
    "query": "原始问题",
    "answer": "生成的答案",
    "citations": [...],
    "quality_threshold": 0.7
}

### 4. 识别问题引用
GET /api/v1/citations/problematic?query=...&answer=...&confidence_threshold=0.5

### 5. 查看统计
GET /api/v1/citations/statistics

## 集成到主应用

在 main.py 中添加:
```python
from app.api.v1.citations import router as citations_router
app.include_router(citations_router)
```
"""
