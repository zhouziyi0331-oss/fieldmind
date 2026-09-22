"""
技能注册中心 (Skill Registry)

统一管理手动技能和自动生成技能
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SkillType(Enum):
    """技能类型"""
    MANUAL = "manual"          # 手动定义
    GENERATED = "generated"    # 自动生成
    HYBRID = "hybrid"          # 混合型


class SkillStatus(Enum):
    """技能状态"""
    DRAFT = "draft"            # 草稿
    TESTING = "testing"        # 测试中
    ACTIVE = "active"          # 活跃
    DEPRECATED = "deprecated"  # 已废弃
    ARCHIVED = "archived"      # 已归档


@dataclass
class Skill:
    """技能数据结构"""
    id: str                                    # 技能ID
    name: str                                  # 技能名称
    type: SkillType                            # 技能类型
    status: SkillStatus                        # 技能状态
    description: str                           # 描述
    category: Optional[str] = None             # 类别
    tags: List[str] = field(default_factory=list)  # 标签

    # 执行相关
    code: Optional[str] = None                 # 技能代码
    workflow_prompt: Optional[str] = None      # 工作流提示词
    parameters: Dict[str, Any] = field(default_factory=dict)  # 参数定义

    # 统计
    usage_count: int = 0                       # 使用次数
    success_count: int = 0                     # 成功次数
    failure_count: int = 0                     # 失败次数
    avg_execution_time: float = 0.0            # 平均执行时间
    quality_score: float = 0.0                 # 质量分数

    # 版本
    version: str = "1.0.0"                     # 版本号
    parent_id: Optional[str] = None            # 父技能ID（用于版本追踪）

    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None           # 创建者ID

    # 其他
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'status': self.status.value,
            'description': self.description,
            'category': self.category,
            'tags': self.tags,
            'code': self.code,
            'workflow_prompt': self.workflow_prompt,
            'parameters': self.parameters,
            'usage_count': self.usage_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'avg_execution_time': self.avg_execution_time,
            'quality_score': self.quality_score,
            'version': self.version,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'metadata': self.metadata
        }


class SkillRegistry:
    """技能注册中心"""

    def __init__(self, db: Session):
        """
        初始化技能注册中心

        Args:
            db: 数据库会话
        """
        self.db = db
        self._cache: Dict[str, Skill] = {}  # 内存缓存
        self._manual_skills: Dict[str, Skill] = {}  # 手动技能

        logger.info("✅ 技能注册中心初始化")

    # ==================== 技能注册 ====================

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
        try:
            logger.info(
                f"📝 注册技能: {skill.name} "
                f"(type={skill.type.value}, id={skill.id})"
            )

            # 1. 验证技能
            if not self._validate_skill(skill):
                logger.error(f"❌ 技能验证失败: {skill.id}")
                return False

            # 2. 保存到数据库或内存
            if skill.type == SkillType.MANUAL:
                # 手动技能保存到内存
                self._manual_skills[skill.id] = skill
            elif skill.type == SkillType.GENERATED:
                # 生成技能保存到数据库（已在生成时保存）
                pass

            # 3. 更新缓存
            self._cache[skill.id] = skill

            logger.info(f"✅ 技能注册成功: {skill.name}")
            return True

        except Exception as e:
            logger.error(f"❌ 技能注册失败: {e}", exc_info=True)
            return False

    def _validate_skill(self, skill: Skill) -> bool:
        """验证技能完整性"""
        # 必需字段检查
        if not skill.id or not skill.name:
            logger.warning("⚠️ 技能缺少必需字段: id或name")
            return False

        # 执行代码检查
        if skill.type == SkillType.GENERATED:
            if not skill.code:
                logger.warning(f"⚠️ 生成技能 {skill.id} 缺少代码")
                return False

        return True

    # ==================== 技能获取 ====================

    def get_skill(
        self,
        skill_id: str,
        use_cache: bool = True
    ) -> Optional[Skill]:
        """
        获取技能

        Args:
            skill_id: 技能ID
            use_cache: 是否使用缓存

        Returns:
            技能对象
        """
        # 1. 检查缓存
        if use_cache and skill_id in self._cache:
            logger.debug(f"✅ 从缓存获取技能: {skill_id}")
            return self._cache[skill_id]

        # 2. 从手动技能获取
        if skill_id in self._manual_skills:
            skill = self._manual_skills[skill_id]
            self._cache[skill_id] = skill
            return skill

        # 3. 从数据库获取生成技能
        try:
            from app.models.generated_skill import GeneratedSkill, SkillGenerationStatus

            db_skill = self.db.query(GeneratedSkill).filter(
                GeneratedSkill.id == skill_id
            ).first()

            if db_skill:
                skill = self._convert_from_db(db_skill)
                self._cache[skill_id] = skill
                return skill

        except Exception as e:
            logger.error(f"❌ 从数据库获取技能失败: {e}")

        logger.warning(f"⚠️ 技能未找到: {skill_id}")
        return None

    def _convert_from_db(self, db_skill) -> Skill:
        """从数据库模型转换为Skill对象"""
        from app.models.generated_skill import SkillGenerationStatus

        # 状态映射
        status_mapping = {
            SkillGenerationStatus.DRAFT: SkillStatus.DRAFT,
            SkillGenerationStatus.TESTING: SkillStatus.TESTING,
            SkillGenerationStatus.DEPLOYED: SkillStatus.ACTIVE,
            SkillGenerationStatus.FAILED: SkillStatus.DEPRECATED
        }

        return Skill(
            id=str(db_skill.id),
            name=db_skill.name,
            type=SkillType.GENERATED,
            status=status_mapping.get(db_skill.status, SkillStatus.DRAFT),
            description=db_skill.description or "",
            category=db_skill.skill_type,
            tags=db_skill.tags or [],
            code=db_skill.implementation,
            parameters=db_skill.parameters or {},
            usage_count=db_skill.usage_count or 0,
            success_count=db_skill.success_count or 0,
            failure_count=db_skill.failure_count or 0,
            quality_score=db_skill.quality_score or 0.0,
            version=db_skill.version or "1.0.0",
            created_at=db_skill.created_at,
            updated_at=db_skill.updated_at,
            metadata=db_skill.metadata or {}
        )

    # ==================== 技能列表 ====================

    def list_skills(
        self,
        skill_type: Optional[SkillType] = None,
        status: Optional[SkillStatus] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Skill]:
        """
        列出技能

        Args:
            skill_type: 技能类型过滤
            status: 状态过滤
            category: 类别过滤
            tags: 标签过滤
            limit: 返回数量限制

        Returns:
            技能列表
        """
        logger.debug(
            f"📋 列出技能: type={skill_type}, "
            f"status={status}, category={category}"
        )

        all_skills = []

        # 1. 从手动技能获取
        if skill_type is None or skill_type == SkillType.MANUAL:
            all_skills.extend(self._manual_skills.values())

        # 2. 从数据库获取生成技能
        if skill_type is None or skill_type == SkillType.GENERATED:
            try:
                from app.models.generated_skill import GeneratedSkill

                query = self.db.query(GeneratedSkill)

                # 状态过滤
                if status:
                    # TODO: 添加状态映射过滤
                    pass

                # 类别过滤
                if category:
                    query = query.filter(GeneratedSkill.skill_type == category)

                db_skills = query.limit(limit).all()

                for db_skill in db_skills:
                    skill = self._convert_from_db(db_skill)
                    all_skills.append(skill)

            except Exception as e:
                logger.error(f"❌ 从数据库获取技能列表失败: {e}")

        # 3. 应用过滤器
        filtered_skills = all_skills

        if status:
            filtered_skills = [s for s in filtered_skills if s.status == status]

        if category:
            filtered_skills = [s for s in filtered_skills if s.category == category]

        if tags:
            filtered_skills = [
                s for s in filtered_skills
                if any(tag in s.tags for tag in tags)
            ]

        # 4. 限制数量
        result = filtered_skills[:limit]

        logger.debug(f"✅ 返回 {len(result)} 个技能")
        return result

    # ==================== 技能搜索 ====================

    def search_skills(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10
    ) -> List[Skill]:
        """
        搜索技能

        Args:
            query: 搜索查询
            filters: 过滤条件
            top_k: 返回数量

        Returns:
            匹配的技能列表
        """
        logger.debug(f"🔍 搜索技能: query='{query}'")

        # 获取所有技能
        all_skills = self.list_skills(limit=1000)

        # 计算相关度
        scored_skills = []
        query_lower = query.lower()

        for skill in all_skills:
            score = 0.0

            # 名称匹配
            if query_lower in skill.name.lower():
                score += 10.0

            # 描述匹配
            if skill.description and query_lower in skill.description.lower():
                score += 5.0

            # 标签匹配
            for tag in skill.tags:
                if query_lower in tag.lower():
                    score += 3.0

            # 类别匹配
            if skill.category and query_lower in skill.category.lower():
                score += 2.0

            # 质量分数加权
            score += skill.quality_score * 0.5

            # 使用频率加权
            if skill.usage_count > 0:
                score += min(skill.usage_count * 0.1, 5.0)

            if score > 0:
                scored_skills.append((skill, score))

        # 排序
        scored_skills.sort(key=lambda x: x[1], reverse=True)

        # 返回top_k
        result = [skill for skill, score in scored_skills[:top_k]]

        logger.debug(f"✅ 搜索到 {len(result)} 个技能")
        return result

    # ==================== 版本管理 ====================

    def get_skill_versions(
        self,
        skill_id: str
    ) -> List[Skill]:
        """
        获取技能的所有版本

        Args:
            skill_id: 技能ID

        Returns:
            版本列表（按时间倒序）
        """
        logger.debug(f"📚 获取技能版本: {skill_id}")

        versions = []

        # 从数据库获取版本历史
        try:
            from app.models.generated_skill import GeneratedSkill

            # 获取主技能
            main_skill = self.get_skill(skill_id)
            if main_skill:
                versions.append(main_skill)

            # 获取所有子版本（parent_id指向此技能）
            # TODO: 需要在GeneratedSkill模型中添加parent_id字段
            # 当前简化实现：只返回主版本

        except Exception as e:
            logger.error(f"❌ 获取技能版本失败: {e}")

        logger.debug(f"✅ 找到 {len(versions)} 个版本")
        return versions

    # ==================== 技能更新 ====================

    def update_skill_stats(
        self,
        skill_id: str,
        success: bool,
        execution_time: Optional[float] = None
    ):
        """
        更新技能统计

        Args:
            skill_id: 技能ID
            success: 是否成功
            execution_time: 执行时间
        """
        skill = self.get_skill(skill_id)
        if not skill:
            return

        # 更新统计
        skill.usage_count += 1
        if success:
            skill.success_count += 1
        else:
            skill.failure_count += 1

        # 更新平均执行时间
        if execution_time is not None:
            if skill.avg_execution_time == 0:
                skill.avg_execution_time = execution_time
            else:
                # 移动平均
                skill.avg_execution_time = (
                    skill.avg_execution_time * 0.9 + execution_time * 0.1
                )

        # 重新计算质量分数
        if skill.usage_count > 0:
            success_rate = skill.success_count / skill.usage_count
            skill.quality_score = success_rate * 100

        skill.updated_at = datetime.utcnow()

        # 更新数据库（如果是生成技能）
        if skill.type == SkillType.GENERATED:
            try:
                from app.models.generated_skill import GeneratedSkill

                db_skill = self.db.query(GeneratedSkill).filter(
                    GeneratedSkill.id == skill_id
                ).first()

                if db_skill:
                    db_skill.usage_count = skill.usage_count
                    db_skill.success_count = skill.success_count
                    db_skill.failure_count = skill.failure_count
                    db_skill.quality_score = skill.quality_score
                    db_skill.updated_at = skill.updated_at
                    self.db.commit()

            except Exception as e:
                logger.error(f"❌ 更新数据库统计失败: {e}")

    # ==================== 管理接口 ====================

    def get_registry_status(self) -> Dict[str, Any]:
        """获取注册中心状态"""
        return {
            'total_skills': len(self._cache),
            'manual_skills': len(self._manual_skills),
            'cached_skills': len(self._cache),
            'timestamp': datetime.utcnow().isoformat()
        }

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("✅ 技能缓存已清空")


# 工厂函数
def create_skill_registry(db: Session) -> SkillRegistry:
    """创建技能注册中心实例"""
    return SkillRegistry(db)
