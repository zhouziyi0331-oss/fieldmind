"""业态分析API路由 - 完整实现"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.models.industry import IndustryCategory
from app.models.user import User
from app.schemas.industry import (
    IndustryCategoryResponse, IndustryCategoryListResponse,
    IndustryDetailResponse, IndustryStatistics, IndustryTrendsResponse,
    IndustryOverview, IndustryDetailedAnalysis, RelatedEntity,
    TimelineItem, RelatedDocument
)
from app.middleware.auth import get_current_user

router = APIRouter(tags=["Industry Analysis"])


@router.get("/categories", response_model=IndustryCategoryListResponse)
async def get_industry_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取业态类别列表"""
    categories = db.query(IndustryCategory).order_by(IndustryCategory.name).all()

    # 如果没有类别，创建默认类别
    if not categories:
        default_categories = [
            {"category_id": "traditional-agriculture", "name": "传统农业", "description": "传统农业生产方式和技术"},
            {"category_id": "modern-agriculture", "name": "现代农业", "description": "现代化农业技术和管理"},
            {"category_id": "rural-tourism", "name": "乡村旅游", "description": "乡村旅游产业发展"},
            {"category_id": "e-commerce", "name": "电商经济", "description": "农村电商和数字经济"},
            {"category_id": "handicraft", "name": "手工艺", "description": "传统手工艺和文化产业"},
        ]

        for cat_data in default_categories:
            category = IndustryCategory(**cat_data)
            db.add(category)

        db.commit()
        categories = db.query(IndustryCategory).order_by(IndustryCategory.name).all()

    return IndustryCategoryListResponse(
        categories=[IndustryCategoryResponse.from_orm(cat) for cat in categories],
        total=len(categories)
    )


@router.get("/{category}/details", response_model=IndustryDetailResponse)
async def get_industry_details(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取业态详细分析 - 基于真实上传文档数据"""
    from app.models.document import Document
    from app.models.entity import Entity
    from app.models.project import ProjectDocument
    from sqlalchemy import func, or_

    # 查找类别
    industry_cat = db.query(IndustryCategory).filter(
        IndustryCategory.category_id == category
    ).first()

    if not industry_cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Industry category '{category}' not found"
        )

    # 如果缓存的分析数据存在且较新，直接返回
    if industry_cat.detailed_analysis and industry_cat.last_analyzed:
        time_since_analysis = datetime.utcnow() - industry_cat.last_analyzed
        if time_since_analysis.days < 7:  # 7天内的分析被认为是新鲜的
            return IndustryDetailResponse(**industry_cat.detailed_analysis)

    # 从真实文档和项目文档中分析数据
    category_keywords = [industry_cat.name, category]

    # 查询相关文档 - 从Document表
    documents_query = db.query(Document).filter(
        Document.status == "completed"
    ).all()

    # 查询相关项目文档 - 从ProjectDocument表
    project_docs_query = db.query(ProjectDocument).filter(
        ProjectDocument.status == "completed"
    ).all()

    # 合并文档列表并筛选相关的
    relevant_docs = []
    for doc in documents_query:
        if doc.text_content and any(kw in doc.text_content for kw in category_keywords):
            relevant_docs.append({
                "id": doc.id,
                "title": doc.original_filename,
                "content": doc.text_content,
                "entities": doc.extracted_entities or doc.entities or [],
                "keywords": doc.keywords or []
            })

    for doc in project_docs_query:
        if doc.text_content and any(kw in doc.text_content for kw in category_keywords):
            relevant_docs.append({
                "id": str(doc.id),
                "title": doc.original_filename,
                "content": doc.text_content,
                "entities": doc.extracted_entities or doc.entities or [],
                "keywords": doc.keywords or []
            })

    # 更新文档计数
    doc_count = len(relevant_docs)
    industry_cat.document_count = doc_count

    # 提取实体统计
    entity_map = {}  # {name: {type, count}}
    for doc in relevant_docs:
        entities = doc.get("entities", [])
        if isinstance(entities, list):
            for ent in entities:
                if isinstance(ent, dict):
                    name = ent.get("name") or ent.get("canonical_name")
                    ent_type = ent.get("type", "unknown")
                    if name:
                        if name not in entity_map:
                            entity_map[name] = {"type": ent_type, "count": 0}
                        entity_map[name]["count"] += 1

    # 构建相关实体列表
    related_entities = [
        RelatedEntity(
            type=info["type"],
            name=name,
            count=info["count"]
        )
        for name, info in sorted(entity_map.items(), key=lambda x: x[1]["count"], reverse=True)[:20]
    ]

    # 提取关键词
    all_keywords = []
    for doc in relevant_docs:
        keywords = doc.get("keywords", [])
        if isinstance(keywords, list):
            all_keywords.extend(keywords)

    # 统计关键词频率
    keyword_freq = {}
    for kw in all_keywords:
        if isinstance(kw, str):
            keyword_freq[kw] = keyword_freq.get(kw, 0) + 1

    top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    # 构建概览
    key_findings = []
    if doc_count > 0:
        key_findings.append(f"共分析了{doc_count}份相关文档")
    if len(entity_map) > 0:
        key_findings.append(f"识别出{len(entity_map)}个相关实体")
        # 统计实体类型分布
        type_counts = {}
        for info in entity_map.values():
            ent_type = info["type"]
            type_counts[ent_type] = type_counts.get(ent_type, 0) + 1
        for ent_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
            key_findings.append(f"包含{count}个{ent_type}类型实体")
    if top_keywords:
        top_3_keywords = [kw for kw, _ in top_keywords[:3]]
        key_findings.append(f"核心关键词：{', '.join(top_3_keywords)}")

    if not key_findings:
        key_findings = [f"暂无{industry_cat.name}相关的分析数据", "请上传相关文档后重新分析"]

    # 生成摘要
    if doc_count > 0:
        summary = f"基于{doc_count}份文档的分析，{industry_cat.name}相关内容涉及{len(entity_map)}个实体。"
        if top_keywords:
            summary += f"主要关注：{', '.join([kw for kw, _ in top_keywords[:5]])}。"
    else:
        summary = f"{industry_cat.name} - {industry_cat.description or '暂无详细描述'}"

    overview = IndustryOverview(
        summary=summary,
        key_findings=key_findings,
        document_count=doc_count
    )

    # 构建详细分析
    trends_list = []
    challenges_list = []
    opportunities_list = []

    # 基于关键词推断趋势、挑战和机遇
    trend_keywords = ["发展", "增长", "提升", "转型", "创新", "数字化", "升级"]
    challenge_keywords = ["困难", "问题", "挑战", "缺乏", "不足", "风险"]
    opportunity_keywords = ["机遇", "机会", "潜力", "前景", "政策", "支持"]

    for kw, count in top_keywords:
        if any(tk in kw for tk in trend_keywords):
            trends_list.append(f"{kw} (出现{count}次)")
        elif any(ck in kw for ck in challenge_keywords):
            challenges_list.append(f"{kw} (出现{count}次)")
        elif any(ok in kw for ok in opportunity_keywords):
            opportunities_list.append(f"{kw} (出现{count}次)")

    # 如果没有足够的分类数据，提供通用描述
    if not trends_list:
        trends_list = ["数据分析中，请上传更多相关文档"]
    if not challenges_list:
        challenges_list = ["数据分析中，请上传更多相关文档"]
    if not opportunities_list:
        opportunities_list = ["数据分析中，请上传更多相关文档"]

    current_status = f"当前共有{doc_count}份文档涉及{industry_cat.name}。" if doc_count > 0 else f"{industry_cat.name}暂无详细分析数据。"

    detailed_analysis = IndustryDetailedAnalysis(
        current_status=current_status,
        trends=trends_list[:5],
        challenges=challenges_list[:5],
        opportunities=opportunities_list[:5]
    )

    # 时间线 - 基于文档创建时间
    timeline = []
    for doc in sorted(relevant_docs, key=lambda x: x.get("id", ""))[:5]:
        # 从数据库获取文档的实际时间
        doc_id = doc["id"]
        doc_obj = db.query(Document).filter(Document.id == doc_id).first()
        if not doc_obj:
            doc_obj = db.query(ProjectDocument).filter(ProjectDocument.id == int(doc_id) if doc_id.isdigit() else -1).first()

        if doc_obj:
            timeline.append(TimelineItem(
                date=doc_obj.created_at or datetime.utcnow(),
                event=f"上传文档: {doc['title'][:30]}"
            ))

    if not timeline:
        timeline = [TimelineItem(date=datetime.utcnow(), event="等待数据上传")]

    # 相关文档列表
    documents = [
        RelatedDocument(
            id=doc["id"],
            title=doc["title"],
            relevance_score=0.9  # 简化评分，实际应该用向量相似度
        )
        for doc in relevant_docs[:10]
    ]

    if not documents:
        documents = [RelatedDocument(id="none", title="暂无相关文档", relevance_score=0.0)]

    response = IndustryDetailResponse(
        category=industry_cat.name,
        overview=overview,
        detailed_analysis=detailed_analysis,
        related_entities=related_entities,
        timeline=timeline,
        documents=documents
    )

    # 缓存分析结果
    industry_cat.detailed_analysis = response.dict()
    industry_cat.last_analyzed = datetime.utcnow()
    db.commit()

    return response


@router.get("/{category}/statistics", response_model=IndustryStatistics)
async def get_industry_statistics(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取业态统计数据 - 基于真实文档数据"""
    from app.models.document import Document
    from app.models.project import ProjectDocument
    from collections import Counter

    industry_cat = db.query(IndustryCategory).filter(
        IndustryCategory.category_id == category
    ).first()

    if not industry_cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Industry category '{category}' not found"
        )

    # 查询相关文档
    category_keywords = [industry_cat.name, category]

    documents_query = db.query(Document).filter(Document.status == "completed").all()
    project_docs_query = db.query(ProjectDocument).filter(ProjectDocument.status == "completed").all()

    relevant_docs = []
    for doc in documents_query:
        if doc.text_content and any(kw in doc.text_content for kw in category_keywords):
            relevant_docs.append({
                "entities": doc.extracted_entities or doc.entities or [],
                "keywords": doc.keywords or [],
                "created_at": doc.uploaded_at
            })

    for doc in project_docs_query:
        if doc.text_content and any(kw in doc.text_content for kw in category_keywords):
            relevant_docs.append({
                "entities": doc.extracted_entities or doc.entities or [],
                "keywords": doc.keywords or [],
                "created_at": doc.created_at
            })

    # 实体类型分布统计
    entity_type_counter = Counter()
    for doc in relevant_docs:
        entities = doc.get("entities", [])
        if isinstance(entities, list):
            for ent in entities:
                if isinstance(ent, dict):
                    ent_type = ent.get("type", "unknown").lower()
                    entity_type_counter[ent_type] += 1

    entity_distribution = dict(entity_type_counter.most_common(10))
    if not entity_distribution:
        entity_distribution = {"无数据": 0}

    # 时间分布统计
    temporal_counter = Counter()
    for doc in relevant_docs:
        created_at = doc.get("created_at")
        if created_at:
            year = str(created_at.year)
            temporal_counter[year] += 1

    temporal_distribution = dict(temporal_counter.most_common(10))
    if not temporal_distribution:
        temporal_distribution = {"无数据": 0}

    # 关键词频率统计
    keyword_counter = Counter()
    for doc in relevant_docs:
        keywords = doc.get("keywords", [])
        if isinstance(keywords, list):
            for kw in keywords:
                if isinstance(kw, str):
                    keyword_counter[kw] += 1

    keyword_frequency = dict(keyword_counter.most_common(20))
    if not keyword_frequency:
        keyword_frequency = {"无数据": 0}

    statistics = IndustryStatistics(
        total_documents=len(relevant_docs),
        entity_distribution=entity_distribution,
        temporal_distribution=temporal_distribution,
        keyword_frequency=keyword_frequency
    )

    return statistics


@router.get("/{category}/trends", response_model=IndustryTrendsResponse)
async def get_industry_trends(
    category: str,
    time_range: str = Query("1y", pattern="^(1y|3y|5y)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取业态趋势分析 - 基于真实文档时间序列"""
    from app.models.document import Document
    from app.models.project import ProjectDocument
    from collections import defaultdict
    from datetime import timedelta

    industry_cat = db.query(IndustryCategory).filter(
        IndustryCategory.category_id == category
    ).first()

    if not industry_cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Industry category '{category}' not found"
        )

    # 查询相关文档
    category_keywords = [industry_cat.name, category]

    documents_query = db.query(Document).filter(Document.status == "completed").all()
    project_docs_query = db.query(ProjectDocument).filter(ProjectDocument.status == "completed").all()

    relevant_docs = []
    for doc in documents_query:
        if doc.text_content and any(kw in doc.text_content for kw in category_keywords):
            relevant_docs.append({
                "created_at": doc.uploaded_at,
                "word_count": doc.word_count or 0
            })

    for doc in project_docs_query:
        if doc.text_content and any(kw in doc.text_content for kw in category_keywords):
            relevant_docs.append({
                "created_at": doc.created_at,
                "word_count": doc.word_count or 0
            })

    # 按月统计文档数量和字数
    monthly_data = defaultdict(lambda: {"count": 0, "words": 0})
    for doc in relevant_docs:
        created_at = doc.get("created_at")
        if created_at:
            month_key = created_at.strftime("%Y-%m")
            monthly_data[month_key]["count"] += 1
            monthly_data[month_key]["words"] += doc.get("word_count", 0)

    # 构建时间序列
    if monthly_data:
        sorted_months = sorted(monthly_data.keys())
        time_series = []
        prev_value = 0

        for month in sorted_months:
            data = monthly_data[month]
            value = data["count"]
            growth_rate = ((value - prev_value) / prev_value * 100) if prev_value > 0 else 0

            time_series.append({
                "month": month,
                "value": value,
                "growth_rate": round(growth_rate, 1)
            })
            prev_value = value

        # 分析趋势方向
        if len(time_series) >= 2:
            first_half_avg = sum(item["value"] for item in time_series[:len(time_series)//2]) / (len(time_series)//2)
            second_half_avg = sum(item["value"] for item in time_series[len(time_series)//2:]) / (len(time_series) - len(time_series)//2)

            if second_half_avg > first_half_avg * 1.1:
                trend_direction = "increasing"
            elif second_half_avg < first_half_avg * 0.9:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "insufficient_data"

        # 生成关键观察
        key_observations = []
        total_docs = len(relevant_docs)
        if total_docs > 0:
            key_observations.append(f"共分析{total_docs}份文档")

        if trend_direction == "increasing":
            key_observations.append("文档数量呈增长趋势")
        elif trend_direction == "decreasing":
            key_observations.append("文档数量呈下降趋势")
        elif trend_direction == "stable":
            key_observations.append("文档数量保持稳定")

        max_month = max(time_series, key=lambda x: x["value"])
        key_observations.append(f"峰值出现在{max_month['month']}")

        if len(time_series) > 1:
            recent_growth = time_series[-1]["growth_rate"]
            if recent_growth > 0:
                key_observations.append(f"近期增长{recent_growth}%")
            elif recent_growth < 0:
                key_observations.append(f"近期下降{abs(recent_growth)}%")

    else:
        # 没有数据的情况
        time_series = [{"month": datetime.utcnow().strftime("%Y-%m"), "value": 0, "growth_rate": 0}]
        trend_direction = "no_data"
        key_observations = ["暂无趋势数据", "请上传相关文档以生成趋势分析"]

    trends = IndustryTrendsResponse(
        time_series=time_series,
        trend_direction=trend_direction,
        key_observations=key_observations
    )

    return trends
