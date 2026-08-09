"""技能相关的Pydantic schemas"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.skill import SkillStatus, SkillCategory


class SkillBase(BaseModel):
    """技能基础信息"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: SkillCategory = SkillCategory.OTHER
    author: Optional[str] = None


class SkillCreate(SkillBase):
    """创建技能"""
    version: str = "1.0.0"
    dependencies: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None


class SkillUpdate(BaseModel):
    """更新技能"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[SkillStatus] = None
    config: Optional[Dict[str, Any]] = None


class ValidationResult(BaseModel):
    """验证结果"""
    syntax_check: bool = False
    dependencies_ok: bool = False
    test_passed: bool = False
    can_activate: bool = False
    errors: List[str] = []
    warnings: List[str] = []
    test_output: Optional[str] = None
    execution_time: Optional[str] = None


class SkillResponse(SkillBase):
    """技能响应"""
    id: str
    version: str
    status: SkillStatus
    file_path: str
    file_size: Optional[str] = None
    can_be_applied: bool
    validation_result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    last_tested: Optional[datetime] = None

    class Config:
        from_attributes = True


class SkillListResponse(BaseModel):
    """技能列表响应"""
    skills: List[SkillResponse]
    total: int


class SkillTestRequest(BaseModel):
    """测试技能请求"""
    test_input: str
    test_params: Optional[Dict[str, Any]] = None


class SkillTestResponse(BaseModel):
    """测试技能响应"""
    success: bool
    output: Optional[str] = None
    execution_time: Optional[float] = None
    errors: List[str] = []
