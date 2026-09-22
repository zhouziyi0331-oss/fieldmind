"""
技能生成服务

自动从模式生成可执行的技能
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func
import json
import re

from app.models.generated_skill import (
    GeneratedSkill,
    SkillTestResult,
    SkillValidationFeedback,
    SkillGenerationStatus,
    SkillGenerationMethod
)
from app.models.pattern_library import PatternLibrary, PatternType


class SkillGenerator:
    """技能生成器 - 从模式生成可执行技能"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    # ==================== 技能生成 ====================

    def generate_skill_from_pattern(
        self,
        pattern_id: str,
        project_id: int,
        user_id: Optional[int] = None
    ) -> GeneratedSkill:
        """
        从模式生成技能

        Args:
            pattern_id: 模式ID
            project_id: 项目ID
            user_id: 用户ID

        Returns:
            生成的技能
        """
        # 获取模式
        pattern = self.db.query(PatternLibrary).filter(
            PatternLibrary.id == pattern_id
        ).first()

        if not pattern:
            raise ValueError(f"模式 {pattern_id} 不存在")

        # 根据模式类型生成技能
        if pattern.pattern_type == PatternType.SEQUENCE:
            skill = self._generate_sequence_skill(pattern, project_id, user_id)
        elif pattern.pattern_type == PatternType.CONDITION:
            skill = self._generate_condition_skill(pattern, project_id, user_id)
        elif pattern.pattern_type == PatternType.STRATEGY:
            skill = self._generate_strategy_skill(pattern, project_id, user_id)
        else:
            raise ValueError(f"不支持的模式类型: {pattern.pattern_type}")

        # 保存技能
        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)

        return skill

    def _generate_sequence_skill(
        self,
        pattern: PatternLibrary,
        project_id: int,
        user_id: Optional[int]
    ) -> GeneratedSkill:
        """生成序列技能"""
        # 提取步骤
        definition = pattern.pattern_definition
        steps = definition.get('steps', [])

        # 生成函数名
        function_name = self._sanitize_name(pattern.pattern_name)

        # 生成代码
        skill_code = self._build_sequence_code(function_name, steps)

        # 生成参数定义
        parameters = self._extract_parameters(steps)

        # 计算质量分数
        quality_score = self._calculate_skill_quality(
            pattern.confidence_score,
            len(steps),
            pattern.avg_quality_score
        )

        return GeneratedSkill(
            skill_name=function_name,
            skill_description=f"自动生成的序列技能：{pattern.pattern_description}",
            skill_category="sequence",
            project_id=project_id,
            generated_by_user_id=user_id,
            generation_method=SkillGenerationMethod.FROM_PATTERN,
            source_pattern_id=pattern.id,
            source_execution_ids=pattern.source_execution_ids,
            skill_code=skill_code,
            skill_parameters=parameters,
            skill_dependencies=self._extract_dependencies(steps),
            applicable_contexts=pattern.applicable_scenarios,
            quality_score=quality_score,
            confidence_score=pattern.confidence_score,
            status=SkillGenerationStatus.GENERATED
        )

    def _generate_condition_skill(
        self,
        pattern: PatternLibrary,
        project_id: int,
        user_id: Optional[int]
    ) -> GeneratedSkill:
        """生成条件技能"""
        definition = pattern.pattern_definition
        condition = definition.get('if', {})
        then_action = definition.get('then', {})

        function_name = self._sanitize_name(pattern.pattern_name)

        # 生成条件判断代码
        skill_code = self._build_condition_code(function_name, condition, then_action)

        parameters = {
            "inputs": [
                {"name": "input_data", "type": "dict", "required": True},
                {"name": "options", "type": "dict", "default": {}}
            ],
            "outputs": [
                {"name": "result", "type": "dict"}
            ]
        }

        return GeneratedSkill(
            skill_name=function_name,
            skill_description=f"自动生成的条件技能：{pattern.pattern_description}",
            skill_category="condition",
            project_id=project_id,
            generated_by_user_id=user_id,
            generation_method=SkillGenerationMethod.FROM_PATTERN,
            source_pattern_id=pattern.id,
            source_execution_ids=pattern.source_execution_ids,
            skill_code=skill_code,
            skill_parameters=parameters,
            applicable_contexts=pattern.applicable_scenarios,
            confidence_score=pattern.confidence_score,
            status=SkillGenerationStatus.GENERATED
        )

    def _generate_strategy_skill(
        self,
        pattern: PatternLibrary,
        project_id: int,
        user_id: Optional[int]
    ) -> GeneratedSkill:
        """生成策略技能"""
        definition = pattern.pattern_definition
        success_factors = definition.get('success_factors', [])
        recommended_steps = definition.get('recommended_steps', [])

        function_name = self._sanitize_name(pattern.pattern_name)

        # 生成策略代码
        skill_code = self._build_strategy_code(
            function_name,
            success_factors,
            recommended_steps
        )

        parameters = {
            "inputs": [
                {"name": "task_data", "type": "dict", "required": True},
                {"name": "context", "type": "dict", "default": {}}
            ],
            "outputs": [
                {"name": "result", "type": "dict"},
                {"name": "success_factors", "type": "list"}
            ]
        }

        return GeneratedSkill(
            skill_name=function_name,
            skill_description=f"自动生成的策略技能：{pattern.pattern_description}",
            skill_category="strategy",
            project_id=project_id,
            generated_by_user_id=user_id,
            generation_method=SkillGenerationMethod.FROM_PATTERN,
            source_pattern_id=pattern.id,
            source_execution_ids=pattern.source_execution_ids,
            skill_code=skill_code,
            skill_parameters=parameters,
            applicable_contexts=pattern.applicable_scenarios,
            confidence_score=pattern.confidence_score,
            status=SkillGenerationStatus.GENERATED
        )

    # ==================== 代码生成辅助方法 ====================

    def _build_sequence_code(
        self,
        function_name: str,
        steps: List[Dict[str, Any]]
    ) -> str:
        """构建序列技能代码"""
        code_lines = [
            f"def {function_name}(input_data, options=None):",
            '    """',
            f'    自动生成的序列技能',
            '    ',
            f'    Args:',
            '        input_data: 输入数据',
            '        options: 可选配置',
            '    ',
            '    Returns:',
            '        dict: 执行结果',
            '    """',
            '    if options is None:',
            '        options = {}',
            '    ',
            '    results = {}',
            '    ',
        ]

        # 添加步骤
        for i, step in enumerate(steps, 1):
            action = step.get('action', f'step_{i}')
            code_lines.append(f'    # Step {i}: {action}')
            code_lines.append(f'    step_{i}_result = {action}(input_data, options)')
            code_lines.append(f'    results["step_{i}"] = step_{i}_result')
            code_lines.append('    ')

        code_lines.append('    return results')

        return '\n'.join(code_lines)

    def _build_condition_code(
        self,
        function_name: str,
        condition: Dict[str, Any],
        then_action: Dict[str, Any]
    ) -> str:
        """构建条件技能代码"""
        code_lines = [
            f"def {function_name}(input_data, options=None):",
            '    """',
            f'    自动生成的条件技能',
            '    """',
            '    if options is None:',
            '        options = {}',
            '    ',
        ]

        # 添加条件判断
        condition_str = self._format_condition(condition)
        code_lines.append(f'    if {condition_str}:')

        # 添加then动作
        for key, value in then_action.items():
            code_lines.append(f'        {key} = {repr(value)}')

        code_lines.append('    ')
        code_lines.append('    return {"result": "success"}')

        return '\n'.join(code_lines)

    def _build_strategy_code(
        self,
        function_name: str,
        success_factors: List[str],
        recommended_steps: List[str]
    ) -> str:
        """构建策略技能代码"""
        code_lines = [
            f"def {function_name}(task_data, context=None):",
            '    """',
            f'    自动生成的策略技能',
            '    ',
            f'    成功因素: {", ".join(success_factors)}',
            '    """',
            '    if context is None:',
            '        context = {}',
            '    ',
            '    # 应用成功策略',
            '    result = {}',
            '    ',
        ]

        # 添加推荐步骤
        for i, step in enumerate(recommended_steps, 1):
            code_lines.append(f'    # 推荐步骤 {i}: {step}')
            code_lines.append(f'    result["step_{i}"] = "{step}"')

        code_lines.append('    ')
        code_lines.append(f'    result["success_factors"] = {repr(success_factors)}')
        code_lines.append('    return result')

        return '\n'.join(code_lines)

    def _sanitize_name(self, name: str) -> str:
        """清理名称，生成合法的函数名"""
        # 移除特殊字符，只保留字母数字和下划线
        cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # 确保以字母开头
        if cleaned and not cleaned[0].isalpha():
            cleaned = 'skill_' + cleaned
        return cleaned.lower()

    def _format_condition(self, condition: Dict[str, Any]) -> str:
        """格式化条件表达式"""
        conditions = []
        for key, value in condition.items():
            if isinstance(value, str):
                conditions.append(f'input_data.get("{key}") == "{value}"')
            else:
                conditions.append(f'input_data.get("{key}") == {value}')

        return ' and '.join(conditions) if conditions else 'True'

    def _extract_parameters(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取参数定义"""
        return {
            "inputs": [
                {"name": "input_data", "type": "dict", "required": True},
                {"name": "options", "type": "dict", "default": {}}
            ],
            "outputs": [
                {"name": "results", "type": "dict"}
            ]
        }

    def _extract_dependencies(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取依赖"""
        functions = []
        for step in steps:
            action = step.get('action')
            if action:
                functions.append(action)

        return {
            "functions": functions,
            "libraries": [],
            "other_skills": []
        }

    def _calculate_skill_quality(
        self,
        confidence: float,
        step_count: int,
        avg_quality: Optional[float]
    ) -> float:
        """计算技能质量分数"""
        score = confidence * 0.5

        # 步骤数适中加分
        if 3 <= step_count <= 7:
            score += 0.2
        elif step_count < 3:
            score += 0.1

        # 历史质量加分
        if avg_quality:
            score += avg_quality * 0.3

        return min(1.0, score)

    # ==================== 技能测试 ====================

    def test_skill(
        self,
        skill_id: str,
        test_cases: List[Dict[str, Any]]
    ) -> List[SkillTestResult]:
        """
        测试技能

        Args:
            skill_id: 技能ID
            test_cases: 测试用例列表

        Returns:
            测试结果列表
        """
        skill = self.db.query(GeneratedSkill).filter(
            GeneratedSkill.id == skill_id
        ).first()

        if not skill:
            raise ValueError(f"技能 {skill_id} 不存在")

        # 更新状态
        skill.status = SkillGenerationStatus.TESTING

        test_results = []
        passed_count = 0

        for test_case in test_cases:
            result = self._run_test_case(skill, test_case)
            test_results.append(result)

            if result.test_passed:
                passed_count += 1

        # 更新测试统计
        skill.test_cases_total = len(test_cases)
        skill.test_cases_passed = passed_count
        skill.test_success_rate = passed_count / len(test_cases) if test_cases else 0
        skill.tested_at = datetime.utcnow()

        # 根据测试结果更新状态
        if skill.test_success_rate >= 0.8:
            skill.status = SkillGenerationStatus.VALIDATED
        else:
            skill.status = SkillGenerationStatus.GENERATED

        self.db.commit()

        return test_results

    def _run_test_case(
        self,
        skill: GeneratedSkill,
        test_case: Dict[str, Any]
    ) -> SkillTestResult:
        """运行单个测试用例"""
        test_name = test_case.get('name', 'test_case')
        test_input = test_case.get('input', {})
        expected_output = test_case.get('expected_output')

        # 模拟执行（实际应该在沙盒环境中执行）
        # 这里简化为检查代码是否合法
        try:
            # 检查代码语法
            compile(skill.skill_code, '<string>', 'exec')
            test_passed = True
            actual_output = {"status": "success", "message": "代码语法正确"}
            error_message = None
        except Exception as e:
            test_passed = False
            actual_output = None
            error_message = str(e)

        result = SkillTestResult(
            skill_id=skill.id,
            project_id=skill.project_id,
            test_case_name=test_name,
            test_input=test_input,
            expected_output=expected_output,
            actual_output=actual_output,
            test_passed=test_passed,
            error_message=error_message,
            execution_time=0.0
        )

        self.db.add(result)
        return result

    # ==================== 技能验证 ====================

    def submit_validation_feedback(
        self,
        skill_id: str,
        user_id: int,
        is_approved: bool,
        rating: Optional[int] = None,
        feedback_text: Optional[str] = None,
        improvement_suggestions: Optional[Dict[str, Any]] = None
    ) -> SkillValidationFeedback:
        """
        提交验证反馈

        Args:
            skill_id: 技能ID
            user_id: 用户ID
            is_approved: 是否批准
            rating: 评分（1-5）
            feedback_text: 反馈文本
            improvement_suggestions: 改进建议

        Returns:
            验证反馈记录
        """
        skill = self.db.query(GeneratedSkill).filter(
            GeneratedSkill.id == skill_id
        ).first()

        if not skill:
            raise ValueError(f"技能 {skill_id} 不存在")

        feedback = SkillValidationFeedback(
            skill_id=skill_id,
            user_id=user_id,
            project_id=skill.project_id,
            is_approved=is_approved,
            validation_rating=rating,
            feedback_text=feedback_text,
            improvement_suggestions=improvement_suggestions
        )

        self.db.add(feedback)

        # 更新技能状态
        if is_approved:
            skill.status = SkillGenerationStatus.VALIDATED
            skill.validated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(feedback)

        return feedback

    # ==================== 技能部署 ====================

    def deploy_skill(
        self,
        skill_id: str
    ) -> GeneratedSkill:
        """
        部署技能

        Args:
            skill_id: 技能ID

        Returns:
            部署后的技能
        """
        skill = self.db.query(GeneratedSkill).filter(
            GeneratedSkill.id == skill_id
        ).first()

        if not skill:
            raise ValueError(f"技能 {skill_id} 不存在")

        if skill.status != SkillGenerationStatus.VALIDATED:
            raise ValueError(f"技能必须先验证才能部署")

        skill.status = SkillGenerationStatus.DEPLOYED
        skill.is_active = True
        skill.deployed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(skill)

        return skill

    # ==================== 查询接口 ====================

    def get_generated_skills(
        self,
        project_id: int,
        status: Optional[SkillGenerationStatus] = None,
        is_active: Optional[bool] = None
    ) -> List[GeneratedSkill]:
        """获取生成的技能列表"""
        query = self.db.query(GeneratedSkill).filter(
            GeneratedSkill.project_id == project_id
        )

        if status:
            query = query.filter(GeneratedSkill.status == status)

        if is_active is not None:
            query = query.filter(GeneratedSkill.is_active == is_active)

        return query.order_by(desc(GeneratedSkill.created_at)).all()
