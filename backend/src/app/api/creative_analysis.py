"""
在地文创分析引擎 API
核心：避免刻板建议，真正结合在地特色的创意思考
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.creative_analysis_service import CreativeAnalysisService
from app.core.exceptions import AIServiceException


router = APIRouter(tags=["文创分析"])


class CreativeAnalysisRequest(BaseModel):
    keywords: List[str]
    mode: str = "creative"  # creative / business / academic


class CulturalElement(BaseModel):
    element: str
    uniqueness: str
    cultural_meaning: str


class CreativePossibility(BaseModel):
    idea: str
    description: str
    innovation_point: str
    feasibility_score: int
    required_resources: List[str]
    target_audience: str
    market_potential: str
    unique_value: str
    risks: List[str]
    implementation_difficulty: str


class CreativeAnalysisResponse(BaseModel):
    keywords: List[str]
    cultural_elements: List[CulturalElement]
    creative_possibilities: List[CreativePossibility]
    anti_patterns: List[str]


@router.post("/projects/{project_id}/analyze", response_model=CreativeAnalysisResponse)
async def analyze_creative_possibilities(
    project_id: int,
    request: CreativeAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    在地文创分析引擎

    **核心目标**：提供真正有创意、接地气的文创建议

    **示例**：

    输入：关键词 = ["布依族", "山歌"]

    ❌ **刻板建议（避免）**：
    - 制作山歌CD/音像制品
    - 举办山歌广场表演
    - 开发山歌文创周边

    ✅ **深度创意（目标）**：
    - 山歌对唱互动体验：游客学习对歌，与当地人现场对唱，AI 实时翻译
    - 山歌剧本杀：将山歌融入剧本杀游戏，通过对歌推进剧情
    - 山歌疗愈空间：结合心理疗愈，山歌冥想、情绪释放工作坊
    - 山歌 × 电音：与当代音乐结合，制作融合专辑
    - 山歌 AR 体验：AR 技术重现山歌场景

    **分析方法**：
    1. 深度理解在地特色的独特性
    2. 寻找与当代生活/新技术的结合点
    3. 创造新的体验方式
    4. 确保真实可行且尊重当地文化
    """
    try:
        service = CreativeAnalysisService(db)
        results = await service.analyze_creative_possibilities(
            project_id=project_id,
            keywords=request.keywords,
            mode=request.mode
        )
        return results
    except Exception as e:
        raise AIServiceException(
            message="文创分析失败",
            service="creative_analysis",
            details={"error": str(e)}
        )


@router.get("/projects/{project_id}/cultural-elements")
async def get_cultural_elements(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    提取项目中的文化元素
    """
    service = CreativeAnalysisService(db)
    elements = await service.extract_cultural_elements(project_id)
    return {"project_id": project_id, "cultural_elements": elements}
