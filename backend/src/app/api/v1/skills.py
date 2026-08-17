"""技能管理API路由 - 完整实现"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import hashlib
import json
import ast
import subprocess
import time
from pathlib import Path

from app.core.database import get_db
from app.models.skill import Skill, SkillValidation, SkillStatus, SkillCategory
from app.models.user import User, UserRole
from app.schemas.skill import (
    SkillResponse, SkillListResponse, SkillTestRequest, SkillTestResponse,
    ValidationResult
)
from app.middleware.auth import get_current_user, require_role

router = APIRouter(tags=["Skills"])

# 技能存储目录 - 使用相对路径
SKILLS_DIR = Path(os.getenv("SKILLS_DIR", "./skills"))
SKILLS_DIR.mkdir(exist_ok=True)


def calculate_file_hash(file_path: str) -> str:
    """计算文件SHA256哈希"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def validate_skill_syntax(file_path: str) -> tuple[bool, List[str]]:
    """验证Python文件语法"""
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        return True, []
    except SyntaxError as e:
        errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        return False, errors
    except Exception as e:
        errors.append(f"Parse error: {str(e)}")
        return False, errors


def check_dependencies(dependencies: List[str]) -> tuple[bool, List[str], List[str]]:
    """检查依赖包是否可用"""
    errors = []
    warnings = []
    all_ok = True

    for dep in dependencies:
        try:
            # 尝试导入包
            result = subprocess.run(
                ["python3", "-c", f"import {dep.split('==')[0].split('>=')[0].split('<=')[0]}"],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                errors.append(f"Dependency '{dep}' not available")
                all_ok = False
        except subprocess.TimeoutExpired:
            warnings.append(f"Timeout checking dependency '{dep}'")
        except Exception as e:
            warnings.append(f"Could not check dependency '{dep}': {str(e)}")

    return all_ok, errors, warnings


def test_skill_execution(file_path: str, test_input: str = "test") -> tuple[bool, str, float, List[str]]:
    """测试技能基本执行"""
    errors = []
    try:
        start_time = time.time()

        # 简单的导入测试
        result = subprocess.run(
            ["python3", "-c", f"import sys; sys.path.insert(0, '{file_path.parent}'); import {file_path.stem}"],
            capture_output=True,
            timeout=10,
            text=True
        )

        execution_time = time.time() - start_time

        if result.returncode != 0:
            errors.append(f"Execution failed: {result.stderr}")
            return False, result.stderr, execution_time, errors

        return True, result.stdout, execution_time, []
    except subprocess.TimeoutExpired:
        errors.append("Execution timeout (>10s)")
        return False, "", 10.0, errors
    except Exception as e:
        errors.append(f"Execution error: {str(e)}")
        return False, "", 0.0, errors


@router.get("", response_model=SkillListResponse)
async def get_skills(
    status: Optional[SkillStatus] = None,
    category: Optional[SkillCategory] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有技能"""
    query = db.query(Skill)

    if status:
        query = query.filter(Skill.status == status)
    if category:
        query = query.filter(Skill.category == category)

    skills = query.order_by(Skill.created_at.desc()).all()

    # 如果没有技能，创建默认技能
    if not skills:
        default_skills = [
            {
                "name": "乡土中国",
                "description": "费孝通《乡土中国》理论框架分析",
                "category": SkillCategory.ACADEMIC,
                "status": SkillStatus.ACTIVE,
                "version": "1.0.0",
                "file_path": "builtin/xiangtu_china.py",
                "file_hash": "builtin",
                "file_size": 0,
                "author_id": current_user.id
            },
            {
                "name": "项链·消逝的满族",
                "description": "萨满教与满族文化研究框架",
                "category": SkillCategory.ACADEMIC,
                "status": SkillStatus.ACTIVE,
                "version": "1.0.0",
                "file_path": "builtin/manchu_culture.py",
                "file_hash": "builtin",
                "file_size": 0,
                "author_id": current_user.id
            },
            {
                "name": "景军·神圣记忆",
                "description": "景军教授记忆与身份认同研究框架",
                "category": SkillCategory.ACADEMIC,
                "status": SkillStatus.ACTIVE,
                "version": "1.0.0",
                "file_path": "builtin/sacred_memory.py",
                "file_hash": "builtin",
                "file_size": 0,
                "author_id": current_user.id
            },
            {
                "name": "多村落 SOP",
                "description": "跨村落田野调查标准操作流程",
                "category": SkillCategory.METHODOLOGY,
                "status": SkillStatus.ACTIVE,
                "version": "1.0.0",
                "file_path": "builtin/multi_village_sop.py",
                "file_hash": "builtin",
                "file_size": 0,
                "author_id": current_user.id
            },
            {
                "name": "商业可行性分析",
                "description": "乡村产业商业可行性评估框架",
                "category": SkillCategory.BUSINESS,
                "status": SkillStatus.ACTIVE,
                "version": "1.0.0",
                "file_path": "builtin/business_feasibility.py",
                "file_hash": "builtin",
                "file_size": 0,
                "author_id": current_user.id
            },
            {
                "name": "文献市场研究",
                "description": "基于文献的市场调研方法",
                "category": SkillCategory.RESEARCH,
                "status": SkillStatus.ACTIVE,
                "version": "1.0.0",
                "file_path": "builtin/literature_market_research.py",
                "file_hash": "builtin",
                "file_size": 0,
                "author_id": current_user.id
            }
        ]

        for skill_data in default_skills:
            skill = Skill(**skill_data)
            db.add(skill)

        db.commit()

        # 重新查询
        query = db.query(Skill)
        if status:
            query = query.filter(Skill.status == status)
        if category:
            query = query.filter(Skill.category == category)
        skills = query.order_by(Skill.created_at.desc()).all()

    return SkillListResponse(
        skills=[SkillResponse.from_orm(skill) for skill in skills],
        total=len(skills)
    )


@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_skill(
    file: UploadFile = File(...),
    metadata: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RESEARCHER))
):
    """上传新技能（带验证约束）"""
    # 解析元数据
    try:
        metadata_dict = json.loads(metadata)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid metadata JSON"
        )

    # 验证文件类型
    if not file.filename.endswith(('.py', '.zip')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .py and .zip files are allowed"
        )

    # 检查技能名称是否已存在
    skill_name = metadata_dict.get('name')
    if not skill_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill name is required in metadata"
        )

    existing_skill = db.query(Skill).filter(Skill.name == skill_name).first()
    if existing_skill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Skill '{skill_name}' already exists"
        )

    # 保存文件
    skill_file_path = SKILLS_DIR / file.filename
    with open(skill_file_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    # 计算文件哈希
    file_hash = calculate_file_hash(str(skill_file_path))
    file_size = os.path.getsize(skill_file_path)

    # 开始验证
    validation_errors = []
    validation_warnings = []

    # 1. 语法检查
    syntax_ok = False
    if file.filename.endswith('.py'):
        syntax_ok, syntax_errors = validate_skill_syntax(str(skill_file_path))
        validation_errors.extend(syntax_errors)
    else:
        syntax_ok = True  # .zip文件跳过语法检查

    # 2. 依赖检查
    dependencies = metadata_dict.get('dependencies', [])
    deps_ok, dep_errors, dep_warnings = check_dependencies(dependencies)
    validation_errors.extend(dep_errors)
    validation_warnings.extend(dep_warnings)

    # 3. 执行测试
    test_passed = False
    test_output = ""
    execution_time = 0.0
    if syntax_ok and file.filename.endswith('.py'):
        test_passed, test_output, execution_time, test_errors = test_skill_execution(
            skill_file_path
        )
        validation_errors.extend(test_errors)

    # 判断是否可以激活
    can_activate = syntax_ok and deps_ok and test_passed

    # 创建技能记录
    new_skill = Skill(
        name=skill_name,
        description=metadata_dict.get('description'),
        version=metadata_dict.get('version', '1.0.0'),
        category=SkillCategory(metadata_dict.get('category', 'other')),
        status=SkillStatus.ACTIVE if can_activate else SkillStatus.INACTIVE,
        file_path=str(skill_file_path),
        file_size=f"{file_size} bytes",
        file_hash=file_hash,
        can_be_applied=can_activate,
        validation_result={
            "valid": can_activate,
            "errors": validation_errors,
            "warnings": validation_warnings
        },
        author=metadata_dict.get('author', current_user.username),
        dependencies=dependencies,
        config=metadata_dict.get('config', {})
    )

    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)

    # 创建验证记录
    validation_record = SkillValidation(
        skill_id=new_skill.id,
        syntax_check=syntax_ok,
        dependencies_ok=deps_ok,
        test_passed=test_passed,
        can_activate=can_activate,
        errors=validation_errors,
        warnings=validation_warnings,
        test_output=test_output,
        execution_time=f"{execution_time:.2f}s"
    )

    db.add(validation_record)
    db.commit()

    return {
        "skill_id": new_skill.id,
        "validation": {
            "syntax_check": syntax_ok,
            "dependencies_ok": deps_ok,
            "test_passed": test_passed,
            "can_activate": can_activate,
            "errors": validation_errors,
            "warnings": validation_warnings
        }
    }


@router.put("/{skill_id}/activate", response_model=dict)
async def activate_skill(
    skill_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RESEARCHER))
):
    """激活技能"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )

    # 检查是否可以激活
    if not skill.can_be_applied:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill validation failed, cannot activate",
            headers={"X-Validation-Errors": json.dumps(skill.validation_result)}
        )

    skill.status = SkillStatus.ACTIVE
    db.commit()

    return {"status": "active", "message": "Skill activated successfully"}


@router.put("/{skill_id}/deactivate", response_model=dict)
async def deactivate_skill(
    skill_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RESEARCHER))
):
    """停用技能"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )

    skill.status = SkillStatus.INACTIVE
    db.commit()

    return {"status": "inactive", "message": "Skill deactivated successfully"}


@router.delete("/{skill_id}", response_model=dict)
async def delete_skill(
    skill_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RESEARCHER))
):
    """删除技能"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )

    # 删除文件
    try:
        if os.path.exists(skill.file_path):
            os.remove(skill.file_path)
    except Exception as e:
        # 记录错误但继续删除数据库记录
        print(f"Warning: Could not delete file {skill.file_path}: {e}")

    # 删除验证记录
    db.query(SkillValidation).filter(SkillValidation.skill_id == skill_id).delete()

    # 删除技能记录
    db.delete(skill)
    db.commit()

    return {"message": "Skill deleted successfully"}


@router.post("/{skill_id}/test", response_model=SkillTestResponse)
async def test_skill(
    skill_id: str,
    test_data: SkillTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试技能"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )

    # 执行测试
    test_passed, test_output, execution_time, test_errors = test_skill_execution(
        Path(skill.file_path),
        test_data.test_input
    )

    # 更新最后测试时间
    from datetime import datetime
    skill.last_tested = datetime.utcnow()
    db.commit()

    return SkillTestResponse(
        success=test_passed,
        output=test_output if test_passed else None,
        execution_time=execution_time,
        errors=test_errors
    )


@router.get("/available-for-task", response_model=SkillListResponse)
async def get_available_skills_for_task(
    task_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取可用于特定任务的技能"""
    # 映射任务类型到技能类别
    task_category_map = {
        "crawler": SkillCategory.CRAWLER,
        "nlp": SkillCategory.NLP,
        "analysis": SkillCategory.ANALYSIS,
        "visualization": SkillCategory.VISUALIZATION
    }

    category = task_category_map.get(task_type.lower())
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown task type: {task_type}"
        )

    # 查询激活的、可用的技能
    skills = db.query(Skill).filter(
        Skill.category == category,
        Skill.status == SkillStatus.ACTIVE,
        Skill.can_be_applied == True
    ).all()

    return SkillListResponse(
        skills=[SkillResponse.from_orm(skill) for skill in skills],
        total=len(skills)
    )
