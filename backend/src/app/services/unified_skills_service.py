"""
统一技能服务

整合 skills 和 skill_generation 两个技能系统
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.logging import logger
from app.models.generated_skill import GeneratedSkill, SkillGenerationStatus


class UnifiedSkillsService:
    """统一技能服务 - 整合手动定义和自动生成的技能"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    # ==================== 技能获取 ====================

    def get(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """
        获取技能（自动判断是手动还是生成的）

        Args:
            skill_id: 技能ID

        Returns:
            技能信息
        """
        # 1. 先尝试从生成的技能中查找
        generated_skill = self.db.query(GeneratedSkill).filter(
            GeneratedSkill.id == skill_id,
            GeneratedSkill.is_active == True
        ).first()

        if generated_skill:
            return self._convert_generated_skill(generated_skill)

        # 2. 再尝试从手动定义的技能中查找
        manual_skill = self._get_manual_skill(skill_id)
        if manual_skill:
            return manual_skill

        return None

    def list_all(
        self,
        category: Optional[str] = None,
        include_generated: bool = True,
        include_manual: bool = True,
        project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        列出所有技能

        Args:
            category: 技能类别
            include_generated: 是否包含自动生成的技能
            include_manual: 是否包含手动定义的技能
            project_id: 项目ID

        Returns:
            技能列表
        """
        skills = []

        # 1. 获取生成的技能
        if include_generated:
            query = self.db.query(GeneratedSkill).filter(
                GeneratedSkill.is_active == True,
                GeneratedSkill.status == SkillGenerationStatus.DEPLOYED
            )

            if project_id:
                query = query.filter(GeneratedSkill.project_id == project_id)

            if category:
                query = query.filter(GeneratedSkill.skill_category == category)

            generated_skills = query.all()
            skills.extend([
                self._convert_generated_skill(s) for s in generated_skills
            ])

        # 2. 获取手动定义的技能
        if include_manual:
            manual_skills = self._list_manual_skills(
                category=category,
                project_id=project_id
            )
            skills.extend(manual_skills)

        # 按名称排序
        skills.sort(key=lambda x: x.get("name", ""))

        return skills

    # ==================== 技能执行 ====================

    def execute(
        self,
        skill_id: str,
        input_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        执行技能

        Args:
            skill_id: 技能ID
            input_data: 输入数据
            user_id: 用户ID

        Returns:
            执行结果
        """
        skill = self.get(skill_id)
        if not skill:
            raise ValueError(f"技能 {skill_id} 不存在")

        logger.info(f"执行技能: {skill['name']} ({skill_id})")

        start_time = datetime.utcnow()

        try:
            # 根据技能来源执行
            if skill["source"] == "generated":
                result = self._execute_generated_skill(skill, input_data)
            else:
                result = self._execute_manual_skill(skill, input_data)

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # 更新使用统计
            self._update_skill_stats(skill_id, success=True)

            return {
                "success": True,
                "skill_id": skill_id,
                "skill_name": skill["name"],
                "result": result,
                "execution_time": execution_time
            }

        except Exception as e:
            logger.error(f"技能执行失败: {e}")

            # 更新失败统计
            self._update_skill_stats(skill_id, success=False)

            return {
                "success": False,
                "skill_id": skill_id,
                "skill_name": skill["name"],
                "error": str(e),
                "execution_time": (datetime.utcnow() - start_time).total_seconds()
            }

    def _execute_generated_skill(
        self,
        skill: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Any:
        """执行自动生成的技能"""
        skill_code = skill.get("code", "")

        # 创建安全的执行环境
        safe_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "range": range,
                "enumerate": enumerate,
            }
        }

        safe_locals = {
            "input_data": input_data,
            "result": None
        }

        # 执行技能代码
        try:
            exec(skill_code, safe_globals, safe_locals)
            return safe_locals.get("result")
        except Exception as e:
            raise RuntimeError(f"技能代码执行错误: {e}")

    def _execute_manual_skill(
        self,
        skill: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Any:
        """执行手动定义的技能"""
        # 从skills模块获取技能实现
        skill_name = skill.get("name")

        try:
            # 动态导入技能模块
            from app.api.v1 import skills as skills_module
            # 这里需要实际的技能执行逻辑
            # 暂时返回基础响应
            return {
                "message": f"手动技能 {skill_name} 执行",
                "input": input_data
            }
        except Exception as e:
            raise RuntimeError(f"手动技能执行错误: {e}")

    # ==================== 技能管理 ====================

    def create_manual_skill(
        self,
        name: str,
        description: str,
        category: str,
        implementation: str,
        parameters: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """
        创建手动定义的技能

        Args:
            name: 技能名称
            description: 描述
            category: 类别
            implementation: 实现代码
            parameters: 参数定义
            user_id: 创建者ID

        Returns:
            创建的技能
        """
        # 这里应该存储到手动技能表
        # 暂时返回基础信息
        skill_id = f"manual_{datetime.utcnow().timestamp()}"

        return {
            "id": skill_id,
            "name": name,
            "description": description,
            "category": category,
            "source": "manual",
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat()
        }

    def update_skill(
        self,
        skill_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新技能

        Args:
            skill_id: 技能ID
            updates: 更新内容

        Returns:
            更新后的技能
        """
        skill = self.get(skill_id)
        if not skill:
            raise ValueError(f"技能 {skill_id} 不存在")

        # 根据来源更新
        if skill["source"] == "generated":
            return self._update_generated_skill(skill_id, updates)
        else:
            return self._update_manual_skill(skill_id, updates)

    def delete_skill(self, skill_id: str) -> bool:
        """
        删除技能

        Args:
            skill_id: 技能ID

        Returns:
            是否成功
        """
        skill = self.get(skill_id)
        if not skill:
            return False

        if skill["source"] == "generated":
            # 软删除生成的技能
            generated_skill = self.db.query(GeneratedSkill).filter(
                GeneratedSkill.id == skill_id
            ).first()

            if generated_skill:
                generated_skill.is_active = False
                self.db.commit()
                return True

        else:
            # 删除手动技能
            return self._delete_manual_skill(skill_id)

        return False

    # ==================== 技能搜索 ====================

    def search_skills(
        self,
        query: str,
        category: Optional[str] = None,
        min_quality: float = 0.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索技能

        Args:
            query: 搜索关键词
            category: 类别过滤
            min_quality: 最小质量分数
            limit: 返回数量

        Returns:
            技能列表
        """
        results = []

        # 搜索生成的技能
        generated_query = self.db.query(GeneratedSkill).filter(
            GeneratedSkill.is_active == True,
            GeneratedSkill.status == SkillGenerationStatus.DEPLOYED
        )

        if min_quality > 0:
            generated_query = generated_query.filter(
                GeneratedSkill.quality_score >= min_quality
            )

        if category:
            generated_query = generated_query.filter(
                GeneratedSkill.skill_category == category
            )

        # 关键词搜索
        search_term = f"%{query}%"
        generated_query = generated_query.filter(
            (GeneratedSkill.skill_name.ilike(search_term)) |
            (GeneratedSkill.skill_description.ilike(search_term))
        )

        generated_skills = generated_query.limit(limit).all()
        results.extend([
            self._convert_generated_skill(s) for s in generated_skills
        ])

        # 搜索手动技能
        # TODO: 实现手动技能搜索

        return results[:limit]

    # ==================== 辅助方法 ====================

    def _convert_generated_skill(self, skill: GeneratedSkill) -> Dict[str, Any]:
        """转换生成的技能为统一格式"""
        return {
            "id": skill.id,
            "name": skill.skill_name,
            "description": skill.skill_description,
            "category": skill.skill_category,
            "source": "generated",
            "code": skill.skill_code,
            "parameters": skill.skill_parameters,
            "quality_score": skill.quality_score,
            "usage_count": skill.usage_count,
            "success_rate": skill.success_count / (skill.success_count + skill.failure_count) if (skill.success_count + skill.failure_count) > 0 else 0,
            "created_at": skill.created_at.isoformat(),
            "is_active": skill.is_active
        }

    def _get_manual_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取手动定义的技能"""
        # TODO: 从手动技能表获取
        return None

    def _list_manual_skills(
        self,
        category: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """列出手动定义的技能"""
        # TODO: 从手动技能表列出
        return []

    def _update_generated_skill(
        self,
        skill_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新生成的技能"""
        skill = self.db.query(GeneratedSkill).filter(
            GeneratedSkill.id == skill_id
        ).first()

        if not skill:
            raise ValueError(f"技能 {skill_id} 不存在")

        # 更新允许的字段
        if "description" in updates:
            skill.skill_description = updates["description"]

        if "is_active" in updates:
            skill.is_active = updates["is_active"]

        self.db.commit()
        self.db.refresh(skill)

        return self._convert_generated_skill(skill)

    def _update_manual_skill(
        self,
        skill_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新手动技能"""
        # TODO: 实现手动技能更新
        return {}

    def _delete_manual_skill(self, skill_id: str) -> bool:
        """删除手动技能"""
        # TODO: 实现手动技能删除
        return False

    def _update_skill_stats(self, skill_id: str, success: bool):
        """更新技能使用统计"""
        skill = self.db.query(GeneratedSkill).filter(
            GeneratedSkill.id == skill_id
        ).first()

        if skill:
            skill.usage_count += 1
            if success:
                skill.success_count += 1
            else:
                skill.failure_count += 1

            self.db.commit()

    # ==================== 技能推荐 ====================

    def recommend_skills(
        self,
        context: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        根据上下文推荐技能

        Args:
            context: 上下文信息（任务类型、输入数据等）
            limit: 返回数量

        Returns:
            推荐的技能列表
        """
        # 简单实现：返回质量最高的技能
        skills = self.db.query(GeneratedSkill).filter(
            GeneratedSkill.is_active == True,
            GeneratedSkill.status == SkillGenerationStatus.DEPLOYED
        ).order_by(
            GeneratedSkill.quality_score.desc()
        ).limit(limit).all()

        return [self._convert_generated_skill(s) for s in skills]
