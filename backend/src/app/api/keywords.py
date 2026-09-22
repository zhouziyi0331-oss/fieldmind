"""
关键词统一 API
整合分散的关键词功能，提供清晰的接口
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
import uuid

from app.core.database import get_db
from app.services.keyword_service import KeywordService
from app.models.keyword import Keyword, KeywordExtractionTask
from app.config.keyword_categories import get_all_categories, KeywordCategory
from app.schemas.response import success_response, error_response

router = APIRouter(prefix="/keywords", tags=["关键词管理"])
logger = logging.getLogger(__name__)


# ==================== Schemas ====================

class KeywordExtractRequest(BaseModel):
    """关键词提取请求"""
    text: Optional[str] = Field(None, description="直接提取的文本（与document_id二选一）")
    document_id: Optional[int] = Field(None, description="文档ID（与text二选一）")
    project_id: int = Field(..., description="项目ID")
    method: str = Field("mixed", description="提取方法: mixed | llm | tfidf")
    top_n: int = Field(30, ge=5, le=100, description="提取数量")
    use_llm: bool = Field(True, description="是否使用LLM精炼")


class KeywordSearchRequest(BaseModel):
    """关键词搜索请求"""
    keywords: List[str] = Field(..., min_items=1, description="关键词列表")
    project_id: int = Field(..., description="项目ID")
    scope: Dict[str, bool] = Field(
        default={"documents": True, "videos": False, "audios": False},
        description="搜索范围"
    )
    match_mode: str = Field("all", description="匹配模式: all | any")


class BatchExtractRequest(BaseModel):
    """批量提取请求"""
    document_ids: List[int] = Field(..., min_items=1, description="文档ID列表")
    project_id: int = Field(..., description="项目ID")
    method: str = Field("mixed", description="提取方法")


class KeywordResponse(BaseModel):
    """关键词响应"""
    id: int
    text: str
    category: Optional[str]
    frequency: int
    weight: float
    importance: float
    first_seen: Optional[str]
    last_seen: Optional[str]


# ==================== 端点 ====================

@router.post("/extract")
async def extract_keywords(
    request: KeywordExtractRequest,
    db: Session = Depends(get_db)
):
    """
    提取关键词（混合方法）

    方法说明：
    - mixed: TF-IDF + LLM（推荐，准确且快速）
    - llm: 仅使用LLM（最准确，但较慢）
    - tfidf: 仅使用TF-IDF（最快，但可能不够准确）
    """
    try:
        # 验证输入
        if not request.text and not request.document_id:
            raise HTTPException(status_code=400, detail="必须提供 text 或 document_id")

        # 获取文本内容
        text_content = None
        if request.text:
            text_content = request.text
        else:
            from app.models.document import ProjectDocument
            document = db.query(ProjectDocument).filter(
                ProjectDocument.id == request.document_id
            ).first()

            if not document:
                raise HTTPException(status_code=404, detail="文档不存在")

            if not document.text_content:
                raise HTTPException(status_code=400, detail="文档内容为空")

            text_content = document.text_content

        # 创建服务
        keyword_service = KeywordService(db)

        # 提取关键词
        keywords = await keyword_service.extract_keywords_mixed(
            text=text_content,
            document_id=request.document_id,
            project_id=request.project_id,
            top_n=request.top_n,
            use_llm=request.use_llm
        )

        return success_response(
            data={
                "document_id": request.document_id,
                "method": request.method,
                "keywords": keywords,
                "total": len(keywords)
            },
            message=f"成功提取 {len(keywords)} 个关键词"
        )

    except Exception as e:
        logger.error(f"关键词提取失败: {e}")
        return error_response(code="KEYWORD_EXTRACT_ERROR", message=f"提取失败: {str(e)}")


@router.get("/projects/{project_id}")
async def get_project_keywords(
    project_id: int,
    category: Optional[str] = None,
    top_n: int = 50,
    sort_by: str = "frequency",
    db: Session = Depends(get_db)
):
    """
    获取项目关键词

    参数：
    - category: 按类别筛选（可选）
    - top_n: 返回数量
    - sort_by: 排序方式（frequency | importance | recent）
    """
    try:
        keyword_service = KeywordService(db)
        keywords = keyword_service.get_project_keywords(
            project_id=project_id,
            category=category,
            top_n=top_n,
            sort_by=sort_by
        )

        return success_response(
            data={
                "project_id": project_id,
                "category": category,
                "keywords": keywords,
                "total": len(keywords)
            }
        )

    except Exception as e:
        logger.error(f"获取项目关键词失败: {e}")
        return error_response(message=str(e))


@router.get("/documents/{document_id}")
async def get_document_keywords(
    document_id: int,
    include_positions: bool = False,
    db: Session = Depends(get_db)
):
    """获取文档关键词"""
    try:
        from app.models.keyword import DocumentKeyword

        doc_keywords = db.query(DocumentKeyword).filter(
            DocumentKeyword.document_id == document_id
        ).all()

        results = []
        for dk in doc_keywords:
            keyword = db.query(Keyword).filter(Keyword.id == dk.keyword_id).first()
            if keyword:
                kw_data = {
                    "id": keyword.id,
                    "text": keyword.text,
                    "category": keyword.category,
                    "frequency": dk.frequency,
                    "weight": dk.weight
                }

                if include_positions:
                    kw_data["positions"] = dk.positions
                    kw_data["contexts"] = dk.contexts

                results.append(kw_data)

        return success_response(
            data={
                "document_id": document_id,
                "keywords": results,
                "total": len(results)
            }
        )

    except Exception as e:
        logger.error(f"获取文档关键词失败: {e}")
        return error_response(message=str(e))


@router.post("/search")
async def search_keywords(
    request: KeywordSearchRequest,
    db: Session = Depends(get_db)
):
    """
    关键词搜索
    在文档/视频/音频中搜索关键词
    """
    try:
        from app.models.keyword import DocumentKeyword

        results = {
            "documents": [],
            "videos": [],
            "audios": []
        }

        # 搜索文档
        if request.scope.get("documents", True):
            # 查找包含关键词的文档
            keyword_ids = db.query(Keyword.id).filter(
                Keyword.text.in_(request.keywords),
                Keyword.project_id == request.project_id
            ).all()
            keyword_ids = [k[0] for k in keyword_ids]

            doc_keywords = db.query(DocumentKeyword).filter(
                DocumentKeyword.keyword_id.in_(keyword_ids)
            ).all()

            # 按文档分组
            doc_map = {}
            for dk in doc_keywords:
                if dk.document_id not in doc_map:
                    doc_map[dk.document_id] = []
                doc_map[dk.document_id].append(dk)

            # 过滤匹配模式
            for doc_id, dks in doc_map.items():
                matched_keywords = set([dk.keyword_id for dk in dks])

                if request.match_mode == "all":
                    if len(matched_keywords) < len(request.keywords):
                        continue

                results["documents"].append({
                    "id": doc_id,
                    "matched_keywords": len(matched_keywords),
                    "total_keywords": len(request.keywords)
                })

        return success_response(data=results)

    except Exception as e:
        logger.error(f"关键词搜索失败: {e}")
        return error_response(message=str(e))


@router.get("/trending")
async def get_trending_keywords(
    time_range: str = "7d",
    category: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取热门关键词

    参数：
    - time_range: 时间范围（7d | 30d | 90d）
    - category: 类别筛选
    - limit: 返回数量
    """
    try:
        from datetime import datetime, timedelta

        # 计算时间范围
        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(time_range, 7)
        start_date = datetime.utcnow() - timedelta(days=days)

        query = db.query(Keyword).filter(
            Keyword.last_seen_at >= start_date
        )

        if category:
            query = query.filter(Keyword.category == category)

        keywords = query.order_by(Keyword.frequency.desc()).limit(limit).all()

        results = []
        for kw in keywords:
            results.append({
                "text": kw.text,
                "category": kw.category,
                "frequency": kw.frequency,
                "weight": kw.weight
            })

        return success_response(
            data={
                "time_range": time_range,
                "trending": results
            }
        )

    except Exception as e:
        logger.error(f"获取热门关键词失败: {e}")
        return error_response(message=str(e))


@router.get("/stats")
async def get_keyword_stats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取关键词统计"""
    try:
        from sqlalchemy import func

        # 总数
        total = db.query(func.count(Keyword.id)).filter(
            Keyword.project_id == project_id
        ).scalar()

        # 按类别统计
        by_category = db.query(
            Keyword.category,
            func.count(Keyword.id)
        ).filter(
            Keyword.project_id == project_id
        ).group_by(Keyword.category).all()

        category_stats = {cat: count for cat, count in by_category}

        # 最高频关键词
        top_keyword = db.query(Keyword).filter(
            Keyword.project_id == project_id
        ).order_by(Keyword.frequency.desc()).first()

        return success_response(
            data={
                "total_keywords": total,
                "by_category": category_stats,
                "most_frequent": top_keyword.text if top_keyword else None
            }
        )

    except Exception as e:
        logger.error(f"获取统计失败: {e}")
        return error_response(message=str(e))


@router.get("/{keyword_id}/relations")
async def get_keyword_relations(
    keyword_id: int,
    project_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取关键词关系（用于知识脉络）"""
    try:
        from app.models.keyword import KeywordRelation

        # 查找相关的关键词
        relations = db.query(KeywordRelation).filter(
            KeywordRelation.project_id == project_id
        ).filter(
            (KeywordRelation.keyword1_id == keyword_id) |
            (KeywordRelation.keyword2_id == keyword_id)
        ).order_by(KeywordRelation.strength.desc()).limit(limit).all()

        results = []
        for rel in relations:
            # 确定相关的另一个关键词
            related_id = rel.keyword2_id if rel.keyword1_id == keyword_id else rel.keyword1_id
            related_keyword = db.query(Keyword).filter(Keyword.id == related_id).first()

            if related_keyword:
                results.append({
                    "text": related_keyword.text,
                    "category": related_keyword.category,
                    "co_occurrence": rel.co_occurrence,
                    "strength": rel.strength,
                    "relation_type": rel.relation_type
                })

        return success_response(
            data={
                "keyword_id": keyword_id,
                "related": results
            }
        )

    except Exception as e:
        logger.error(f"获取关键词关系失败: {e}")
        return error_response(message=str(e))


@router.post("/batch-extract")
async def batch_extract_keywords(
    request: BatchExtractRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """批量提取关键词（异步任务）"""
    try:
        # 创建任务
        task_id = f"task_{uuid.uuid4().hex[:12]}"

        task = KeywordExtractionTask(
            task_id=task_id,
            project_id=request.project_id,
            document_ids=request.document_ids,
            method=request.method,
            status="pending",
            total_documents=len(request.document_ids)
        )
        db.add(task)
        db.commit()

        # 添加后台任务
        background_tasks.add_task(
            _process_batch_extraction,
            task_id=task_id,
            document_ids=request.document_ids,
            project_id=request.project_id,
            method=request.method
        )

        return success_response(
            data={
                "task_id": task_id,
                "status": "processing",
                "progress_url": f"/api/keywords/tasks/{task_id}"
            },
            message="批量提取任务已启动"
        )

    except Exception as e:
        logger.error(f"批量提取失败: {e}")
        return error_response(message=str(e))


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """获取批量任务状态"""
    try:
        task = db.query(KeywordExtractionTask).filter(
            KeywordExtractionTask.task_id == task_id
        ).first()

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        progress = 0
        if task.total_documents > 0:
            progress = (task.processed_documents / task.total_documents) * 100

        return success_response(
            data={
                "task_id": task.task_id,
                "status": task.status,
                "progress": round(progress, 2),
                "processed": task.processed_documents,
                "total": task.total_documents,
                "extracted_keywords": task.extracted_keywords,
                "error": task.error_message
            }
        )

    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        return error_response(message=str(e))


@router.get("/categories")
async def get_categories():
    """获取所有关键词分类"""
    from app.config.keyword_categories import CATEGORY_INFO

    categories = []
    for category, info in CATEGORY_INFO.items():
        categories.append({
            "value": category.value,
            "description": info["description"],
            "examples": info["examples"]
        })

    return success_response(data={"categories": categories})


@router.post("/analyze-relations/{project_id}")
async def analyze_relations(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """分析关键词关系（用于知识脉络生成）"""
    try:
        keyword_service = KeywordService(db)

        # 添加后台任务
        background_tasks.add_task(
            keyword_service.analyze_keyword_relations,
            project_id=project_id
        )

        return success_response(
            message="关键词关系分析已启动，结果将用于知识脉络生成"
        )

    except Exception as e:
        logger.error(f"分析关键词关系失败: {e}")
        return error_response(message=str(e))


# ==================== 后台任务 ====================

async def _process_batch_extraction(
    task_id: str,
    document_ids: List[int],
    project_id: int,
    method: str
):
    """处理批量提取任务"""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        task = db.query(KeywordExtractionTask).filter(
            KeywordExtractionTask.task_id == task_id
        ).first()

        if not task:
            return

        task.status = "processing"
        task.started_at = datetime.utcnow()
        db.commit()

        keyword_service = KeywordService(db)
        total_extracted = 0

        for doc_id in document_ids:
            try:
                # 获取文档
                from app.models.document import ProjectDocument
                document = db.query(ProjectDocument).filter(
                    ProjectDocument.id == doc_id
                ).first()

                if document and document.text_content:
                    # 提取关键词
                    keywords = await keyword_service.extract_keywords_mixed(
                        text=document.text_content,
                        document_id=doc_id,
                        project_id=project_id,
                        top_n=30,
                        use_llm=(method in ["mixed", "llm"])
                    )
                    total_extracted += len(keywords)

                # 更新进度
                task.processed_documents += 1
                task.extracted_keywords = total_extracted
                db.commit()

            except Exception as e:
                logger.error(f"处理文档 {doc_id} 失败: {e}")

        task.status = "completed"
        task.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.error(f"批量提取任务失败: {e}")
        if task:
            task.status = "failed"
            task.error_message = str(e)
            db.commit()
    finally:
        db.close()


from datetime import datetime
