"""
技能生成API端点

提供从模式生成技能、测试和部署接口
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.generated_skill import SkillGenerationStatus
from app.services.skill_generator import SkillGenerator


router = APIRouter()


# ==================== Pydantic 模型 ====================

class SkillGenerationRequest(BaseModel):
    """技能生成请求"""
    pattern_id: str = Field(..., description="模式ID")
    project_id: int = Field(..., description="项目ID")


class TestCaseInput(BaseModel):
    """测试用例"""
    name: str = Field(..., description="测试用例名称")
    input: Dict[str, Any] = Field(..., description="测试输入")
    expected_output: Optional[Dict[str, Any]] = Field(None, description="期望输出")


class SkillTestRequest(BaseModel):
    """技能测试请求"""
    test_cases: List[TestCaseInput] = Field(..., description="测试用例列表")


class ValidationFeedbackRequest(BaseModel):
    """验证反馈请求"""
    is_approved: bool = Field(..., description="是否批准")
    validation_rating: Optional[int] = Field(None, description="评分（1-5）", ge=1, le=5)
    feedback_text: Optional[str] = Field(None, description="反馈文本")
    improvement_suggestions: Optional[Dict[str, str]] = Field(None, description="改进建议")


class GeneratedSkillResponse(BaseModel):
    """生成技能响应"""
    id: str
    skill_name: str
    skill_description: str
    skill_category: Optional[str]
    project_id: int
    generation_method: str
    source_pattern_id: Optional[str]
    skill_code: str
    skill_parameters: Dict[str, Any]
    skill_dependencies: Optional[Dict[str, Any]]
    applicable_contexts: Dict[str, Any]
    quality_score: Optional[float]
    confidence_score: float
    test_cases_passed: int
    test_cases_total: int
    test_success_rate: Optional[float]
    usage_count: int
    success_count: int
    failure_count: int
    status: str
    is_active: bool
    generated_at: str
    tested_at: Optional[str]
    validated_at: Optional[str]
    deployed_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class SkillTestResultResponse(BaseModel):
    """测试结果响应"""
    id: str
    skill_id: str
    test_case_name: str
    test_input: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]]
    actual_output: Optional[Dict[str, Any]]
    test_passed: bool
    error_message: Optional[str]
    execution_time: Optional[float]
    tested_at: str

    class Config:
        from_attributes = True


class ValidationFeedbackResponse(BaseModel):
    """验证反馈响应"""
    id: str
    skill_id: str
    user_id: int
    is_approved: bool
    validation_rating: Optional[int]
    feedback_text: Optional[str]
    improvement_suggestions: Optional[Dict[str, str]]
    validated_at: str

    class Config:
        from_attributes = True


# ==================== 依赖项 ====================

def get_skill_generator(db: Session = Depends(get_db)) -> SkillGenerator:
    """获取技能生成服务"""
    return SkillGenerator(db)


# ==================== 技能生成 ====================

@router.post("/generate", response_model=GeneratedSkillResponse, summary="生成技能")
async def generate_skill(
    request: SkillGenerationRequest,
    current_user: User = Depends(get_current_user),
    generator: SkillGenerator = Depends(get_skill_generator)
):
    """
    从模式生成技能

    - **pattern_id**: 模式ID
    - **project_id**: 项目ID

    系统将根据模式类型自动生成对应的技能代码
    """
    skill = generator.generate_skill_from_pattern(
        pattern_id=request.pattern_id,
        project_id=request.project_id,
        user_id=current_user.id
    )

    return GeneratedSkillResponse(
        id=skill.id,
        skill_name=skill.skill_name,
        skill_description=skill.skill_description,
        skill_category=skill.skill_category,
        project_id=skill.project_id,
        generation_method=skill.generation_method.value,
        source_pattern_id=skill.source_pattern_id,
        skill_code=skill.skill_code,
        skill_parameters=skill.skill_parameters,
        skill_dependencies=skill.skill_dependencies,
        applicable_contexts=skill.applicable_contexts,
        quality_score=skill.quality_score,
        confidence_score=skill.confidence_score,
        test_cases_passed=skill.test_cases_passed,
        test_cases_total=skill.test_cases_total,
        test_success_rate=skill.test_success_rate,
        usage_count=skill.usage_count,
        success_count=skill.success_count,
        failure_count=skill.failure_count,
        status=skill.status.value,
        is_active=skill.is_active,
        generated_at=skill.generated_at.isoformat(),
        tested_at=skill.tested_at.isoformat() if skill.tested_at else None,
        validated_at=skill.validated_at.isoformat() if skill.validated_at else None,
        deployed_at=skill.deployed_at.isoformat() if skill.deployed_at else None,
        created_at=skill.created_at.isoformat()
    )


# ==================== 技能测试 ====================

@router.post("/skills/{skill_id}/test", response_model=List[SkillTestResultResponse], summary="测试技能")
async def test_skill(
    skill_id: str = Path(..., description="技能ID"),
    request: SkillTestRequest = ...,
    current_user: User = Depends(get_current_user),
    generator: SkillGenerator = Depends(get_skill_generator)
):
    """
    测试技能

    - **skill_id**: 技能ID
    - **test_cases**: 测试用例列表

    系统将在沙盒环境中执行测试用例
    """
    test_cases = [tc.dict() for tc in request.test_cases]

    results = generator.test_skill(
        skill_id=skill_id,
        test_cases=test_cases
    )

    return [
        SkillTestResultResponse(
            id=r.id,
            skill_id=r.skill_id,
            test_case_name=r.test_case_name,
            test_input=r.test_input,
            expected_output=r.expected_output,
            actual_output=r.actual_output,
            test_passed=r.test_passed,
            error_message=r.error_message,
            execution_time=r.execution_time,
            tested_at=r.tested_at.isoformat()
        )
        for r in results
    ]


# ==================== 技能验证 ====================

@router.post("/skills/{skill_id}/validate", response_model=ValidationFeedbackResponse, summary="验证技能")
async def validate_skill(
    skill_id: str = Path(..., description="技能ID"),
    feedback: ValidationFeedbackRequest = ...,
    current_user: User = Depends(get_current_user),
    generator: SkillGenerator = Depends(get_skill_generator)
):
    """
    提交技能验证反馈

    - **skill_id**: 技能ID
    - **is_approved**: 是否批准
    - **validation_rating**: 评分（1-5）
    - **feedback_text**: 反馈文本
    - **improvement_suggestions**: 改进建议
    """
    result = generator.submit_validation_feedback(
        skill_id=skill_id,
        user_id=current_user.id,
        is_approved=feedback.is_approved,
        rating=feedback.validation_rating,
        feedback_text=feedback.feedback_text,
        improvement_suggestions=feedback.improvement_suggestions
    )

    return ValidationFeedbackResponse(
        id=result.id,
        skill_id=result.skill_id,
        user_id=result.user_id,
        is_approved=result.is_approved,
        validation_rating=result.validation_rating,
        feedback_text=result.feedback_text,
        improvement_suggestions=result.improvement_suggestions,
        validated_at=result.validated_at.isoformat()
    )


# ==================== 技能部署 ====================

@router.post("/skills/{skill_id}/deploy", response_model=GeneratedSkillResponse, summary="部署技能")
async def deploy_skill(
    skill_id: str = Path(..., description="技能ID"),
    current_user: User = Depends(get_current_user),
    generator: SkillGenerator = Depends(get_skill_generator)
):
    """
    部署技能

    将验证通过的技能部署到生产环境
    """
    skill = generator.deploy_skill(skill_id=skill_id)

    return GeneratedSkillResponse(
        id=skill.id,
        skill_name=skill.skill_name,
        skill_description=skill.skill_description,
        skill_category=skill.skill_category,
        project_id=skill.project_id,
        generation_method=skill.generation_method.value,
        source_pattern_id=skill.source_pattern_id,
        skill_code=skill.skill_code,
        skill_parameters=skill.skill_parameters,
        skill_dependencies=skill.skill_dependencies,
        applicable_contexts=skill.applicable_contexts,
        quality_score=skill.quality_score,
        confidence_score=skill.confidence_score,
        test_cases_passed=skill.test_cases_passed,
        test_cases_total=skill.test_cases_total,
        test_success_rate=skill.test_success_rate,
        usage_count=skill.usage_count,
        success_count=skill.success_count,
        failure_count=skill.failure_count,
        status=skill.status.value,
        is_active=skill.is_active,
        generated_at=skill.generated_at.isoformat(),
        tested_at=skill.tested_at.isoformat() if skill.tested_at else None,
        validated_at=skill.validated_at.isoformat() if skill.validated_at else None,
        deployed_at=skill.deployed_at.isoformat() if skill.deployed_at else None,
        created_at=skill.created_at.isoformat()
    )


# ==================== 技能查询 ====================

@router.get("/skills", response_model=List[GeneratedSkillResponse], summary="获取生成的技能列表")
async def get_generated_skills(
    project_id: int = Query(..., description="项目ID"),
    status: Optional[SkillGenerationStatus] = Query(None, description="技能状态"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_user: User = Depends(get_current_user),
    generator: SkillGenerator = Depends(get_skill_generator)
):
    """
    获取生成的技能列表

    按创建时间倒序返回
    """
    skills = generator.get_generated_skills(
        project_id=project_id,
        status=status,
        is_active=is_active
    )

    return [
        GeneratedSkillResponse(
            id=skill.id,
            skill_name=skill.skill_name,
            skill_description=skill.skill_description,
            skill_category=skill.skill_category,
            project_id=skill.project_id,
            generation_method=skill.generation_method.value,
            source_pattern_id=skill.source_pattern_id,
            skill_code=skill.skill_code,
            skill_parameters=skill.skill_parameters,
            skill_dependencies=skill.skill_dependencies,
            applicable_contexts=skill.applicable_contexts,
            quality_score=skill.quality_score,
            confidence_score=skill.confidence_score,
            test_cases_passed=skill.test_cases_passed,
            test_cases_total=skill.test_cases_total,
            test_success_rate=skill.test_success_rate,
            usage_count=skill.usage_count,
            success_count=skill.success_count,
            failure_count=skill.failure_count,
            status=skill.status.value,
            is_active=skill.is_active,
            generated_at=skill.generated_at.isoformat(),
            tested_at=skill.tested_at.isoformat() if skill.tested_at else None,
            validated_at=skill.validated_at.isoformat() if skill.validated_at else None,
            deployed_at=skill.deployed_at.isoformat() if skill.deployed_at else None,
            created_at=skill.created_at.isoformat()
        )
        for skill in skills
    ]


@router.get("/skills/{skill_id}", response_model=GeneratedSkillResponse, summary="获取技能详情")
async def get_skill_detail(
    skill_id: str = Path(..., description="技能ID"),
    current_user: User = Depends(get_current_user),
    generator: SkillGenerator = Depends(get_skill_generator)
):
    """获取技能详细信息"""
    from app.models.generated_skill import GeneratedSkill

    skill = generator.db.query(GeneratedSkill).filter(
        GeneratedSkill.id == skill_id
    ).first()

    if not skill:
        raise HTTPException(status_code=404, detail="技能不存在")

    return GeneratedSkillResponse(
        id=skill.id,
        skill_name=skill.skill_name,
        skill_description=skill.skill_description,
        skill_category=skill.skill_category,
        project_id=skill.project_id,
        generation_method=skill.generation_method.value,
        source_pattern_id=skill.source_pattern_id,
        skill_code=skill.skill_code,
        skill_parameters=skill.skill_parameters,
        skill_dependencies=skill.skill_dependencies,
        applicable_contexts=skill.applicable_contexts,
        quality_score=skill.quality_score,
        confidence_score=skill.confidence_score,
        test_cases_passed=skill.test_cases_passed,
        test_cases_total=skill.test_cases_total,
        test_success_rate=skill.test_success_rate,
        usage_count=skill.usage_count,
        success_count=skill.success_count,
        failure_count=skill.failure_count,
        status=skill.status.value,
        is_active=skill.is_active,
        generated_at=skill.generated_at.isoformat(),
        tested_at=skill.tested_at.isoformat() if skill.tested_at else None,
        validated_at=skill.validated_at.isoformat() if skill.validated_at else None,
        deployed_at=skill.deployed_at.isoformat() if skill.deployed_at else None,
        created_at=skill.created_at.isoformat()
    )
