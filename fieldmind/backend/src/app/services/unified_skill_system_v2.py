"""
统一技能系统 V2 (Unified Skill System V2)

完全整合的技能管理系统
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.skills.skill_registry import (
    SkillRegistry, Skill, SkillType, SkillStatus, create_skill_registry
)
from app.core.skills.skill_executor import (
    SkillExecutor, ExecutionResult, SandboxConfig, get_skill_executor
)
from app.core.skills.skill_recommender import (
    SkillRecommender, SkillRecommendation, create_skill_recommender
)

logger = logging.getLogger(__name__)


class UnifiedSkillSystemV2:
    """统一技能系统 V2"""

    def __init__(self, db: Session):
        """
        初始化统一技能系统

        Args:
            db: 数据库会话
        """
        self.db = db

        # 核心组件
        self.registry = create_skill_registry(db)
        self.executor = get_skill_executor()
        self.recommender = create_skill_recommender(self.registry)

        # 连接执行器和注册中心
        self.executor.set_skill_registry(self.registry)

        # 技能生成器和优化器（延迟加载）
        self._generator = None
        self._optimizer = None

        logger.info("✅ 统一技能系统V2初始化完成")

    @property
    def generator(self):
        """技能生成器（延迟加载）"""
        if self._generator is None:
            try:
                from app.services.skill_generator import SkillGenerator
                self._generator = SkillGenerator(self.db)
                logger.debug("✅ 技能生成器已加载")
            except Exception as e:
                logger.warning(f"⚠️ 技能生成器加载失败: {e}")
        return self._generator

    @property
    def optimizer(self):
        """技能优化器（延迟加载）"""
        if self._optimizer is None:
            try:
                from app.services.skill_optimizer import SkillOptimizer
                self._optimizer = SkillOptimizer(self.db)
                logger.debug("✅ 技能优化器已加载")
            except Exception as e:
                logger.warning(f"⚠️ 技能优化器加载失败: {e}")
        return self._optimizer

    # ==================== 技能管理 ====================

    def register_skill(
        self,
        skill: Skill
    ) -> bool:
        """
        注册技能

        Args:
            skill: 技能对象

        Returns:
            是否成功
        """
        return self.registry.register_skill(skill)

    def get_skill(
        self,
        skill_id: str
    ) -> Optional[Skill]:
        """
        获取技能

        Args:
            skill_id: 技能ID

        Returns:
            技能对象
        """
        return self.registry.get_skill(skill_id)

    def list_skills(
        self,
        skill_type: Optional[SkillType] = None,
        status: Optional[SkillStatus] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Skill]:
        """
        列出技能

        Args:
            skill_type: 技能类型过滤
            status: 状态过滤
            category: 类别过滤
            limit: 返回数量限制

        Returns:
            技能列表
        """
        return self.registry.list_skills(
            skill_type=skill_type,
            status=status,
            category=category,
            limit=limit
        )

    def search_skills(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Skill]:
        """
        搜索技能

        Args:
            query: 搜索查询
            top_k: 返回数量

        Returns:
            匹配的技能列表
        """
        return self.registry.search_skills(
            query=query,
            top_k=top_k
        )

    # ==================== 技能执行 ====================

    async def execute_skill(
        self,
        skill_id: str,
        input_data: Dict[str, Any],
        sandbox_config: Optional[SandboxConfig] = None
    ) -> ExecutionResult:
        """
        执行技能

        Args:
            skill_id: 技能ID
            input_data: 输入数据
            sandbox_config: 沙盒配置

        Returns:
            执行结果
        """
        logger.info(f"🚀 执行技能: {skill_id}")

        # 1. 获取技能
        skill = self.registry.get_skill(skill_id)
        if not skill:
            return ExecutionResult(
                success=False,
                output=None,
                error=f"技能未找到: {skill_id}"
            )

        # 2. 执行技能
        result = await self.executor.execute(
            skill=skill,
            input_data=input_data,
            sandbox_config=sandbox_config
        )

        return result

    async def execute_skill_by_name(
        self,
        skill_name: str,
        input_data: Dict[str, Any],
        sandbox_config: Optional[SandboxConfig] = None
    ) -> ExecutionResult:
        """
        通过名称执行技能

        Args:
            skill_name: 技能名称
            input_data: 输入数据
            sandbox_config: 沙盒配置

        Returns:
            执行结果
        """
        # 搜索技能
        skills = self.registry.search_skills(skill_name, top_k=1)

        if not skills:
            return ExecutionResult(
                success=False,
                output=None,
                error=f"技能未找到: {skill_name}"
            )

        return await self.execute_skill(
            skill_id=skills[0].id,
            input_data=input_data,
            sandbox_config=sandbox_config
        )

    # ==================== 技能推荐 ====================

    def recommend_skills(
        self,
        context: Dict[str, Any],
        top_k: int = 5,
        min_score: float = 0.3
    ) -> List[SkillRecommendation]:
        """
        推荐技能

        Args:
            context: 上下文信息
            top_k: 返回前K个推荐
            min_score: 最低分数阈值

        Returns:
            推荐的技能列表
        """
        return self.recommender.recommend(
            context=context,
            top_k=top_k,
            min_score=min_score
        )

    def recommend_similar_skills(
        self,
        skill_id: str,
        top_k: int = 5
    ) -> List[SkillRecommendation]:
        """
        推荐相似技能

        Args:
            skill_id: 参考技能ID
            top_k: 返回数量

        Returns:
            相似的技能列表
        """
        return self.recommender.recommend_by_similarity(
            reference_skill_id=skill_id,
            top_k=top_k
        )

    # ==================== 技能生成 ====================

    async def generate_skill_from_execution(
        self,
        execution_id: str,
        skill_name: Optional[str] = None
    ) -> Optional[Skill]:
        """
        从执行追踪生成技能

        Args:
            execution_id: 执行追踪ID
            skill_name: 技能名称（可选）

        Returns:
            生成的技能
        """
        if not self.generator:
            logger.error("❌ 技能生成器未加载")
            return None

        try:
            logger.info(f"🔧 从执行追踪生成技能: {execution_id}")

            # 调用生成器
            generated_skill_data = await self.generator.generate_from_execution(
                execution_id=execution_id,
                skill_name=skill_name
            )

            if not generated_skill_data:
                return None

            # 转换为Skill对象并注册
            skill = self._convert_generated_to_skill(generated_skill_data)

            if self.registry.register_skill(skill):
                logger.info(f"✅ 技能生成并注册成功: {skill.name}")
                return skill

        except Exception as e:
            logger.error(f"❌ 技能生成失败: {e}", exc_info=True)

        return None

    def _convert_generated_to_skill(
        self,
        generated_data: Dict[str, Any]
    ) -> Skill:
        """从生成数据转换为Skill对象"""
        return Skill(
            id=str(generated_data.get('id', '')),
            name=generated_data.get('name', ''),
            type=SkillType.GENERATED,
            status=SkillStatus.TESTING,
            description=generated_data.get('description', ''),
            category=generated_data.get('skill_type'),
            code=generated_data.get('implementation'),
            parameters=generated_data.get('parameters', {}),
            quality_score=generated_data.get('quality_score', 0.0)
        )

    # ==================== 技能优化 ====================

    async def optimize_skill(
        self,
        skill_id: str
    ) -> Optional[Skill]:
        """
        优化技能

        Args:
            skill_id: 技能ID

        Returns:
            优化后的技能
        """
        if not self.optimizer:
            logger.error("❌ 技能优化器未加载")
            return None

        try:
            logger.info(f"⚡ 优化技能: {skill_id}")

            # 获取原技能
            original_skill = self.registry.get_skill(skill_id)
            if not original_skill:
                logger.error(f"❌ 技能未找到: {skill_id}")
                return None

            # 调用优化器
            optimized_data = await self.optimizer.optimize(skill_id)

            if not optimized_data:
                return None

            # 创建新版本
            optimized_skill = Skill(
                id=f"{skill_id}_v{self._get_next_version(original_skill)}",
                name=original_skill.name,
                type=original_skill.type,
                status=SkillStatus.TESTING,
                description=original_skill.description,
                category=original_skill.category,
                code=optimized_data.get('optimized_code'),
                parameters=original_skill.parameters,
                version=self._get_next_version(original_skill),
                parent_id=skill_id
            )

            # 注册优化后的技能
            if self.registry.register_skill(optimized_skill):
                logger.info(f"✅ 技能优化成功: {optimized_skill.name}")
                return optimized_skill

        except Exception as e:
            logger.error(f"❌ 技能优化失败: {e}", exc_info=True)

        return None

    def _get_next_version(self, skill: Skill) -> str:
        """获取下一个版本号"""
        # 简单版本号递增
        try:
            major, minor, patch = skill.version.split('.')
            new_patch = str(int(patch) + 1)
            return f"{major}.{minor}.{new_patch}"
        except:
            return "1.0.1"

    # ==================== 统计和分析 ====================

    def get_popular_skills(self, limit: int = 10) -> List[Skill]:
        """获取热门技能"""
        return self.recommender.get_popular_skills(limit=limit)

    def get_high_quality_skills(
        self,
        limit: int = 10,
        min_usage: int = 5
    ) -> List[Skill]:
        """获取高质量技能"""
        return self.recommender.get_high_quality_skills(
            limit=limit,
            min_usage=min_usage
        )

    def get_skill_statistics(
        self,
        skill_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取技能统计

        Args:
            skill_id: 技能ID（None=全局统计）

        Returns:
            统计信息
        """
        if skill_id:
            # 单个技能统计
            skill = self.registry.get_skill(skill_id)
            if not skill:
                return {'error': '技能未找到'}

            return {
                'skill_id': skill.id,
                'skill_name': skill.name,
                'usage_count': skill.usage_count,
                'success_count': skill.success_count,
                'failure_count': skill.failure_count,
                'success_rate': (
                    skill.success_count / skill.usage_count
                    if skill.usage_count > 0 else 0
                ),
                'avg_execution_time': skill.avg_execution_time,
                'quality_score': skill.quality_score
            }
        else:
            # 全局统计
            all_skills = self.registry.list_skills(limit=10000)

            total_usage = sum(s.usage_count for s in all_skills)
            total_success = sum(s.success_count for s in all_skills)

            return {
                'total_skills': len(all_skills),
                'manual_skills': len([s for s in all_skills if s.type == SkillType.MANUAL]),
                'generated_skills': len([s for s in all_skills if s.type == SkillType.GENERATED]),
                'active_skills': len([s for s in all_skills if s.status == SkillStatus.ACTIVE]),
                'total_usage': total_usage,
                'total_success': total_success,
                'overall_success_rate': (
                    total_success / total_usage
                    if total_usage > 0 else 0
                )
            }

    # ==================== 系统状态 ====================

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'registry': self.registry.get_registry_status(),
            'executor': self.executor.get_executor_status(),
            'recommender': self.recommender.get_recommender_status(),
            'generator_loaded': self._generator is not None,
            'optimizer_loaded': self._optimizer is not None,
            'timestamp': datetime.utcnow().isoformat()
        }


# 工厂函数
def create_unified_skill_system_v2(db: Session) -> UnifiedSkillSystemV2:
    """创建统一技能系统V2实例"""
    return UnifiedSkillSystemV2(db)
