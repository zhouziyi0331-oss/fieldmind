"""
在地业态分析API端点
基于真实材料的业态推演和可行性评估
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.document_chunk import DocumentChunk
from app.models.entity import Entity
from app.models.project import Project, ProjectDocument
from app.schemas.response import success_response
from collections import defaultdict
import json
import re

router = APIRouter()


# ==================== 业态数据库 ====================

# 导入业态数据库配置
from app.config.business_database import (
    EXISTING_BUSINESS_DATABASE as EXISTING_BUSINESS_KEYWORDS,
    POTENTIAL_BUSINESS_RULES,
    FEASIBILITY_WEIGHTS,
    SUSTAINABILITY_WEIGHTS
)


# ==================== 辅助函数 ====================

def calculate_keyword_frequency(chunks: List[DocumentChunk], keywords: List[str]) -> int:
    """计算关键词出现频次"""
    total_freq = 0
    for chunk in chunks:
        text = chunk.text.lower()
        for keyword in keywords:
            total_freq += text.count(keyword.lower())
    return total_freq


def calculate_emotion_score(chunks: List[DocumentChunk], keywords: List[str]) -> float:
    """
    计算情感得分（-1到1之间）
    这里简化处理，实际应该有情感分析模型
    """
    # 简化版：统计正面词和负面词
    positive_words = ["好", "发展", "增长", "改善", "提升", "成功", "繁荣", "兴旺"]
    negative_words = ["难", "问题", "困难", "减少", "衰退", "流失", "断层", "危机"]

    positive_count = 0
    negative_count = 0

    relevant_chunks = []
    for chunk in chunks:
        text = chunk.text.lower()
        if any(kw.lower() in text for kw in keywords):
            relevant_chunks.append(chunk)

    if not relevant_chunks:
        return 0.0

    for chunk in relevant_chunks:
        text = chunk.text
        for word in positive_words:
            positive_count += text.count(word)
        for word in negative_words:
            negative_count += text.count(word)

    total = positive_count + negative_count
    if total == 0:
        return 0.0

    # 归一化到 -1 到 1
    return (positive_count - negative_count) / total


def calculate_trend_score(chunks: List[DocumentChunk], keywords: List[str]) -> float:
    """
    计算趋势得分（-1到1之间）
    通过时间轴上的分布判断趋势
    """
    if not chunks:
        return 0.0

    # 按时间排序
    time_chunks = [(c.created_at, c) for c in chunks if c.created_at]
    if not time_chunks:
        return 0.0

    time_chunks.sort(key=lambda x: x[0])

    # 分成前半段和后半段
    mid_point = len(time_chunks) // 2
    first_half = time_chunks[:mid_point]
    second_half = time_chunks[mid_point:]

    # 计算每段的关键词频次
    first_freq = sum(
        1 for _, chunk in first_half
        if any(kw.lower() in chunk.text.lower() for kw in keywords)
    )
    second_freq = sum(
        1 for _, chunk in second_half
        if any(kw.lower() in chunk.text.lower() for kw in keywords)
    )

    total = first_freq + second_freq
    if total == 0:
        return 0.0

    # 归一化
    return (second_freq - first_freq) / total


def calculate_business_score(
    chunks: List[DocumentChunk],
    keywords: List[str]
) -> Dict[str, Any]:
    """
    计算业态综合得分

    得分 = 覆盖度(40%) + 情感值(30%) + 趋势(30%)
    """
    # 覆盖度：关键词出现频次
    frequency = calculate_keyword_frequency(chunks, keywords)
    total_chunks = len(chunks)
    coverage = min(frequency / max(total_chunks * 0.1, 1), 1.0) if total_chunks > 0 else 0.0

    # 情感值
    emotion = calculate_emotion_score(chunks, keywords)
    emotion_normalized = (emotion + 1) / 2  # 转换到 0-1

    # 趋势
    trend = calculate_trend_score(chunks, keywords)
    trend_normalized = (trend + 1) / 2  # 转换到 0-1

    # 综合得分
    final_score = (coverage * 0.4 + emotion_normalized * 0.3 + trend_normalized * 0.3) * 100

    return {
        "score": round(final_score, 1),
        "coverage": round(coverage * 100, 1),
        "emotion": round(emotion_normalized * 100, 1),
        "trend": round(trend_normalized * 100, 1),
        "frequency": frequency
    }


def calculate_feasibility_score(
    chunks: List[DocumentChunk],
    business_name: str,
    required_keywords: List[str],
    supporting_factors: List[str]
) -> Dict[str, Any]:
    """
    计算可行性评分

    可行性 = 关键词频次(30%) + 情感值(20%) + 政策匹配(20%) + 资源可用性(30%)
    """
    total_chunks = len(chunks)

    # 1. 关键词频次 (30%)
    keyword_freq = calculate_keyword_frequency(chunks, required_keywords)
    keyword_score = min(keyword_freq / max(total_chunks * 0.05, 1), 1.0) if total_chunks > 0 else 0.0

    # 2. 情感值 (20%)
    emotion = calculate_emotion_score(chunks, required_keywords)
    emotion_score = (emotion + 1) / 2

    # 3. 政策匹配度 (20%)
    policy_keywords = ["政策", "支持", "政府", "资金", "补贴", "项目"]
    policy_freq = calculate_keyword_frequency(chunks, policy_keywords)
    policy_score = min(policy_freq / max(total_chunks * 0.02, 1), 1.0) if total_chunks > 0 else 0.0

    # 4. 资源可用性 (30%)
    resource_freq = calculate_keyword_frequency(chunks, supporting_factors)
    resource_score = min(resource_freq / max(total_chunks * 0.03, 1), 1.0) if total_chunks > 0 else 0.0

    # 综合可行性分数
    feasibility = (
        keyword_score * 0.3 +
        emotion_score * 0.2 +
        policy_score * 0.2 +
        resource_score * 0.3
    ) * 100

    return {
        "feasibility_score": round(feasibility, 1),
        "keyword_frequency": keyword_freq,
        "emotion_score": round(emotion_score * 100, 1),
        "policy_support": round(policy_score * 100, 1),
        "resource_availability": round(resource_score * 100, 1)
    }


# ==================== API端点 ====================

@router.get("/projects/{project_id}/business-analysis/existing")
async def get_existing_businesses(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(get_db)
):
    """
    获取现有业态分析

    返回：
    - 业态列表（3-5个）
    - 每个业态的得分、描述、可持续性、支撑材料
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取所有chunks
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.project_id == project_id
    ).all()

    if not chunks:
        return success_response(data={"businesses": []})

    # 分析每个业态
    businesses = []

    for business_name, business_data in EXISTING_BUSINESS_KEYWORDS.items():
        keywords = business_data["keywords"]

        # 计算得分
        score_data = calculate_business_score(chunks, keywords)

        # 找到支撑材料
        supporting_chunks = [
            chunk for chunk in chunks
            if any(kw.lower() in chunk.text.lower() for kw in keywords)
        ]

        # 获取材料列表
        doc_ids = list(set(chunk.document_id for chunk in supporting_chunks[:10]))
        materials = db.query(ProjectDocument).filter(
            ProjectDocument.id.in_(doc_ids)
        ).limit(5).all()

        material_list = [
            {
                "id": doc.id,
                "title": doc.title or doc.filename,
                "filename": doc.filename
            }
            for doc in materials
        ]

        # 可持续性评估
        sustainability = score_data["score"]

        # 标签
        tags = []
        if score_data["score"] >= 70:
            tags.append("核心业态")
        if score_data["trend"] >= 60:
            tags.append("增长中")
        elif score_data["trend"] <= 40:
            tags.append("需关注")
        if score_data["emotion"] >= 60:
            tags.append("满意度高")

        businesses.append({
            "name": business_name,
            "description": business_data["description"],
            "score": score_data["score"],
            "sustainability": sustainability,
            "coverage": score_data["coverage"],
            "emotion": score_data["emotion"],
            "trend": score_data["trend"],
            "frequency": score_data["frequency"],
            "tags": tags,
            "supporting_materials": material_list,
            "material_count": len(supporting_chunks)
        })

    # 按得分排序
    businesses.sort(key=lambda x: x["score"], reverse=True)

    return success_response(data={"businesses": businesses})


@router.get("/projects/{project_id}/business-analysis/potential")
async def get_potential_businesses(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(get_db)
):
    """
    获取可能业态推演

    返回：
    - 推演业态列表（3-5个）
    - 每个业态的可行性评分、推演逻辑、依据材料
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取所有chunks
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.project_id == project_id
    ).all()

    if not chunks:
        return success_response(data={"potential_businesses": []})

    # 识别高频关键词
    all_text = " ".join(chunk.text for chunk in chunks)

    potential_businesses = []

    # 遍历推演规则
    for keyword, rules in POTENTIAL_BUSINESS_RULES.items():
        # 检查关键词是否在材料中高频出现
        keyword_freq = all_text.lower().count(keyword.lower())

        if keyword_freq < 5:  # 至少出现5次
            continue

        # 分析每个可能业态
        for business in rules["potential_businesses"]:
            # 计算可行性
            feasibility_data = calculate_feasibility_score(
                chunks,
                business["name"],
                business["required_keywords"],
                business["supporting_factors"]
            )

            # 推演逻辑
            reasoning = f"关键词「{keyword}」在材料中出现 {keyword_freq} 次，"
            reasoning += f"结合 {', '.join(business['supporting_factors'][:3])} 等要素，"
            reasoning += f"具备发展「{business['name']}」的基础条件。"

            # 找到依据材料
            relevant_chunks = [
                chunk for chunk in chunks
                if any(kw.lower() in chunk.text.lower() for kw in business["required_keywords"])
            ]

            doc_ids = list(set(chunk.document_id for chunk in relevant_chunks[:10]))
            materials = db.query(ProjectDocument).filter(
                ProjectDocument.id.in_(doc_ids)
            ).limit(5).all()

            material_list = [
                {
                    "id": doc.id,
                    "title": doc.title or doc.filename,
                    "excerpt": relevant_chunks[0].text[:100] + "..." if relevant_chunks else ""
                }
                for doc in materials
            ]

            potential_businesses.append({
                "name": business["name"],
                "description": business["description"],
                "feasibility_score": feasibility_data["feasibility_score"],
                "keyword_frequency": feasibility_data["keyword_frequency"],
                "emotion_score": feasibility_data["emotion_score"],
                "policy_support": feasibility_data["policy_support"],
                "resource_availability": feasibility_data["resource_availability"],
                "reasoning": reasoning,
                "supporting_materials": material_list,
                "base_keyword": keyword,
                "material_count": len(relevant_chunks)
            })

    # 按可行性排序
    potential_businesses.sort(key=lambda x: x["feasibility_score"], reverse=True)

    # 只返回前5个
    return success_response(data={"potential_businesses": potential_businesses[:5]})


class AIEvaluationRequest(BaseModel):
    """AI评估请求"""
    business_type: str = Field(..., description="业态类型（existing/potential）")
    business_name: str = Field(..., description="业态名称")


@router.post("/projects/{project_id}/business-analysis/ai-evaluation")
async def get_ai_evaluation(
    project_id: int = Path(..., description="项目ID"),
    request: AIEvaluationRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    获取AI综合评估

    基于业态数据生成综合评估文本、建议和风险提示
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取业态数据
    if request.business_type == "existing":
        existing_response = await get_existing_businesses(project_id, db)
        businesses = existing_response["data"]["businesses"]
        target_business = next((b for b in businesses if b["name"] == request.business_name), None)
    else:
        potential_response = await get_potential_businesses(project_id, db)
        businesses = potential_response["data"]["potential_businesses"]
        target_business = next((b for b in businesses if b["name"] == request.business_name), None)

    if not target_business:
        raise HTTPException(status_code=404, detail="业态不存在")

    # 构造评估文本（简化版，实际应该调用LLM）
    score_key = "score" if request.business_type == "existing" else "feasibility_score"
    score = target_business[score_key]

    # 评估文本
    if score >= 80:
        evaluation = f"「{request.business_name}」具备较强的发展潜力。"
    elif score >= 60:
        evaluation = f"「{request.business_name}」具备一定的发展基础，但需要注意风险。"
    else:
        evaluation = f"「{request.business_name}」当前条件尚不成熟，建议谨慎推进。"

    evaluation += f"\n\n基于 {target_business['material_count']} 份材料的交叉分析，"

    if request.business_type == "existing":
        evaluation += f"该业态的覆盖度为 {target_business['coverage']}%，"
        evaluation += f"情感倾向为 {target_business['emotion']}%，"
        evaluation += f"趋势得分为 {target_business['trend']}%。"
    else:
        evaluation += f"关键词出现频次为 {target_business['keyword_frequency']} 次，"
        evaluation += f"政策支持度为 {target_business['policy_support']}%，"
        evaluation += f"资源可用性为 {target_business['resource_availability']}%。"

    # 建议
    suggestions = []
    if score >= 70:
        suggestions.append(f"建议优先发展「{request.business_name}」，作为核心业态培育。")
    else:
        suggestions.append(f"建议先进行小规模试点，验证市场反馈后再扩大规模。")

    if request.business_type == "potential" and target_business.get("policy_support", 0) >= 60:
        suggestions.append("可申请相关政策支持和资金补贴。")

    # 风险提示
    risks = []
    if request.business_type == "existing" and target_business.get("trend", 0) <= 40:
        risks.append("⚠️ 该业态呈现下降趋势，需关注市场变化。")

    if target_business.get("material_count", 0) < 5:
        risks.append("⚠️ 支撑材料较少，建议补充更多调研数据。")

    # 数据依据
    data_evidence = {
        "material_count": target_business["material_count"],
        "score": score,
        "supporting_materials": target_business.get("supporting_materials", [])
    }

    return success_response(data={
        "evaluation": evaluation,
        "suggestions": suggestions,
        "risks": risks,
        "data_evidence": data_evidence
    })
