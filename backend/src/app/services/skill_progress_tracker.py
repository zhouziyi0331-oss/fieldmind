"""
技能进度追踪服务

游戏化的技能学习系统：
- XP系统和等级提升
- 技能解锁机制
- 练习记录和统计
- 学习路径推荐
- 成就系统
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.models.skill_system import (
    SkillNode, SkillProgress, SkillRelation,
    SkillAchievement, UserAchievement, SkillPath
)

logger = logging.getLogger(__name__)


class SkillProgressTracker:
    """
    技能进度追踪器

    管理用户的技能学习进度和游戏化体验
    """

    # XP常量
    BASE_XP_PER_LEVEL = 100
    XP_MULTIPLIER = 1.5

    def __init__(self, db: Session):
        self.db = db

    def get_user_progress(self, user_id: int, skill_id: int) -> Optional[SkillProgress]:
        """获取用户在特定技能上的进度"""
        return self.db.query(SkillProgress).filter(
            SkillProgress.user_id == user_id,
            SkillProgress.skill_id == skill_id
        ).first()

    def start_learning(self, user_id: int, skill_id: int) -> Dict[str, Any]:
        """
        开始学习一个技能

        检查前置条件，如果满足则解锁
        """
        skill = self.db.query(SkillNode).filter(SkillNode.id == skill_id).first()
        if not skill:
            raise ValueError(f"Skill {skill_id} not found")

        # 检查是否已经开始学习
        progress = self.get_user_progress(user_id, skill_id)
        if progress:
            return {
                "success": False,
                "message": "Already started learning this skill",
                "progress": self._progress_to_dict(progress)
            }

        # 检查前置条件
        if not self._check_prerequisites(user_id, skill):
            prerequisites = self._get_prerequisite_names(skill)
            return {
                "success": False,
                "message": "Prerequisites not met",
                "required_skills": prerequisites
            }

        # 创建进度记录
        progress = SkillProgress(
            user_id=user_id,
            skill_id=skill_id,
            status='learning',
            started_at=datetime.utcnow(),
            current_xp=0,
            current_level=0,
            progress_percentage=0
        )

        self.db.add(progress)

        # 更新技能节点状态
        skill.status = 'learning'

        self.db.commit()

        logger.info(f"User {user_id} started learning skill {skill.name}")

        return {
            "success": True,
            "message": f"Started learning {skill.name}",
            "progress": self._progress_to_dict(progress)
        }

    def record_practice(
        self,
        user_id: int,
        skill_id: int,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        记录一次技能练习

        result格式：
        {
            "success": bool,
            "time_spent_minutes": int,
            "xp_earned": int (可选),
            "notes": str (可选)
        }
        """
        progress = self.get_user_progress(user_id, skill_id)
        if not progress:
            return {
                "success": False,
                "message": "Must start learning this skill first"
            }

        # 更新练习统计
        progress.practice_count += 1
        if result.get('success', False):
            progress.success_count += 1

        progress.success_rate = progress.success_count / progress.practice_count

        # 更新时间
        progress.time_spent_minutes += result.get('time_spent_minutes', 0)
        progress.last_practiced = datetime.utcnow()

        # 添加XP
        xp_earned = result.get('xp_earned', self._calculate_xp_reward(result))
        level_up = self._add_xp(progress, xp_earned)

        # 更新进度百分比
        progress.progress_percentage = self._calculate_progress(progress)

        # 检查是否达到完成或精通
        status_change = self._check_status_change(progress)

        self.db.commit()

        logger.info(f"User {user_id} practiced skill {skill_id}, earned {xp_earned} XP")

        response = {
            "success": True,
            "xp_earned": xp_earned,
            "level_up": level_up,
            "current_level": progress.current_level,
            "current_xp": progress.current_xp,
            "progress_percentage": progress.progress_percentage,
            "status": progress.status
        }

        if status_change:
            response["status_changed"] = status_change

        # 检查成就
        achievements = self._check_achievements(user_id, progress)
        if achievements:
            response["achievements_unlocked"] = achievements

        # 检查新解锁的技能
        unlocked = self._check_unlocks(user_id)
        if unlocked:
            response["skills_unlocked"] = unlocked

        return response

    def _check_prerequisites(self, user_id: int, skill: SkillNode) -> bool:
        """检查用户是否满足技能的前置条件"""
        if not skill.prerequisites:
            return True  # 没有前置条件

        # 获取前置技能ID列表
        prerequisite_ids = skill.prerequisites if isinstance(skill.prerequisites, list) else []

        if not prerequisite_ids:
            return True

        # 检查前置技能是否都已完成
        for prereq_id in prerequisite_ids:
            prereq_node = self.db.query(SkillNode).filter(
                SkillNode.skill_id == prereq_id
            ).first()

            if prereq_node:
                progress = self.get_user_progress(user_id, prereq_node.id)

                # 根据逻辑判断
                if skill.prerequisite_logic == 'all':
                    if not progress or progress.status not in ['completed', 'mastered']:
                        return False
                elif skill.prerequisite_logic == 'any':
                    if progress and progress.status in ['completed', 'mastered']:
                        return True

        # 如果是'any'逻辑且没有满足的前置技能
        if skill.prerequisite_logic == 'any' and prerequisite_ids:
            return False

        return True

    def _get_prerequisite_names(self, skill: SkillNode) -> List[str]:
        """获取前置技能的名称列表"""
        if not skill.prerequisites:
            return []

        names = []
        for prereq_id in skill.prerequisites:
            prereq_node = self.db.query(SkillNode).filter(
                SkillNode.skill_id == prereq_id
            ).first()
            if prereq_node:
                names.append(prereq_node.name)

        return names

    def _add_xp(self, progress: SkillProgress, xp: int) -> bool:
        """
        添加XP，检查是否升级

        返回: 是否升级
        """
        progress.current_xp += xp

        # 检查是否升级
        skill = self.db.query(SkillNode).filter(SkillNode.id == progress.skill_id).first()
        max_level = skill.max_level if skill else 100

        level_up = False
        while progress.current_xp >= skill.xp_to_next_level and progress.current_level < max_level:
            progress.current_xp -= skill.xp_to_next_level
            progress.current_level += 1
            level_up = True

            # 更新下一级所需XP
            skill.xp_to_next_level = int(
                self.BASE_XP_PER_LEVEL * (self.XP_MULTIPLIER ** progress.current_level)
            )

            logger.info(f"User {progress.user_id} leveled up skill {progress.skill_id} to level {progress.current_level}")

        return level_up

    def _calculate_xp_reward(self, result: Dict[str, Any]) -> int:
        """根据练习结果计算XP奖励"""
        base_xp = 10

        if result.get('success', False):
            base_xp *= 2

        # 时间加成
        time_spent = result.get('time_spent_minutes', 0)
        if time_spent > 0:
            base_xp += min(time_spent, 30)  # 最多30分钟加成

        return base_xp

    def _calculate_progress(self, progress: SkillProgress) -> float:
        """计算技能进度百分比"""
        # 基于练习次数、成功率、等级综合计算
        practice_score = min(progress.practice_count / 20, 1.0) * 30  # 最多30%
        success_score = progress.success_rate * 30  # 最多30%
        level_score = (progress.current_level / 100) * 40  # 最多40%

        return practice_score + success_score + level_score

    def _check_status_change(self, progress: SkillProgress) -> Optional[str]:
        """检查技能状态是否应该变化"""
        if progress.status == 'mastered':
            return None

        # 完成条件：练习10次以上，成功率>70%，等级>50
        if (progress.practice_count >= 10 and
            progress.success_rate >= 0.7 and
            progress.current_level >= 50):

            if progress.status != 'completed':
                progress.status = 'completed'
                progress.completed_at = datetime.utcnow()
                return 'completed'

        # 精通条件：练习20次以上，成功率>90%，等级>80
        if (progress.practice_count >= 20 and
            progress.success_rate >= 0.9 and
            progress.current_level >= 80):

            if progress.status != 'mastered':
                progress.status = 'mastered'
                progress.mastered_at = datetime.utcnow()
                progress.mastery_level = 5
                return 'mastered'

        return None

    def _check_achievements(
        self,
        user_id: int,
        progress: SkillProgress
    ) -> List[Dict[str, Any]]:
        """检查是否解锁新成就"""
        unlocked_achievements = []

        # 里程碑成就
        if progress.practice_count == 10:
            achievement = self._unlock_achievement(
                user_id,
                "practice_10",
                "练习达人",
                "完成10次技能练习"
            )
            if achievement:
                unlocked_achievements.append(achievement)

        # 连续练习成就
        if self._check_streak(user_id, progress.skill_id, days=7):
            achievement = self._unlock_achievement(
                user_id,
                "streak_7",
                "坚持不懈",
                "连续7天练习技能"
            )
            if achievement:
                unlocked_achievements.append(achievement)

        return unlocked_achievements

    def _unlock_achievement(
        self,
        user_id: int,
        achievement_id: str,
        name: str,
        description: str
    ) -> Optional[Dict[str, Any]]:
        """解锁成就"""
        # 检查成就是否存在
        achievement = self.db.query(SkillAchievement).filter(
            SkillAchievement.achievement_id == achievement_id
        ).first()

        if not achievement:
            # 创建成就
            achievement = SkillAchievement(
                achievement_id=achievement_id,
                name=name,
                description=description,
                xp_reward=50,
                rarity='common'
            )
            self.db.add(achievement)
            self.db.commit()

        # 检查用户是否已获得
        user_achievement = self.db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement.id
        ).first()

        if user_achievement:
            return None  # 已获得

        # 授予成就
        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement.id
        )
        self.db.add(user_achievement)
        self.db.commit()

        return {
            "id": achievement.achievement_id,
            "name": achievement.name,
            "description": achievement.description,
            "xp_reward": achievement.xp_reward
        }

    def _check_streak(self, user_id: int, skill_id: int, days: int) -> bool:
        """检查连续练习天数"""
        # 简化实现：检查最近N天是否都有练习记录
        # 实际应该查询练习历史记录
        return False  # TODO: 实现连续练习检查

    def _check_unlocks(self, user_id: int) -> List[Dict[str, Any]]:
        """检查是否有新技能被解锁"""
        unlocked = []

        # 查询所有锁定的技能
        locked_skills = self.db.query(SkillNode).filter(
            SkillNode.status == 'locked'
        ).all()

        for skill in locked_skills:
            if self._check_prerequisites(user_id, skill):
                skill.status = 'available'
                unlocked.append({
                    "id": skill.skill_id,
                    "name": skill.name,
                    "description": skill.description
                })

        if unlocked:
            self.db.commit()

        return unlocked

    def get_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取推荐学习的技能

        基于：
        1. 前置技能已完成
        2. 用户兴趣（已学习技能的类别）
        3. 技能难度匹配
        """
        # 获取用户已完成的技能
        completed_skills = self.db.query(SkillProgress).filter(
            SkillProgress.user_id == user_id,
            SkillProgress.status.in_(['completed', 'mastered'])
        ).all()

        completed_skill_ids = {p.skill_id for p in completed_skills}

        # 获取用户感兴趣的类别
        categories = self._get_user_interests(completed_skills)

        # 查询可学习的技能
        available_skills = self.db.query(SkillNode).filter(
            SkillNode.status == 'available',
            SkillNode.id.notin_(completed_skill_ids)
        ).all()

        recommendations = []
        for skill in available_skills:
            if self._check_prerequisites(user_id, skill):
                # 计算推荐分数
                score = self._calculate_recommendation_score(
                    skill,
                    categories,
                    completed_skills
                )

                recommendations.append({
                    "skill": {
                        "id": skill.skill_id,
                        "name": skill.name,
                        "description": skill.description,
                        "difficulty": skill.difficulty,
                        "estimated_hours": skill.estimated_hours
                    },
                    "score": score,
                    "reason": self._get_recommendation_reason(skill, categories)
                })

        # 按分数排序
        recommendations.sort(key=lambda x: x['score'], reverse=True)

        return recommendations[:10]  # 返回前10个推荐

    def _get_user_interests(self, completed_skills: List[SkillProgress]) -> Dict[str, int]:
        """分析用户兴趣类别"""
        categories = {}

        for progress in completed_skills:
            skill = self.db.query(SkillNode).filter(
                SkillNode.id == progress.skill_id
            ).first()

            if skill and skill.category:
                categories[skill.category] = categories.get(skill.category, 0) + 1

        return categories

    def _calculate_recommendation_score(
        self,
        skill: SkillNode,
        user_categories: Dict[str, int],
        completed_skills: List[SkillProgress]
    ) -> float:
        """计算推荐分数"""
        score = 0.0

        # 类别匹配加分
        if skill.category in user_categories:
            score += user_categories[skill.category] * 10

        # 难度匹配加分（根据用户水平）
        avg_level = sum(p.current_level for p in completed_skills) / len(completed_skills) if completed_skills else 0

        difficulty_match = {
            'beginner': 0 <= avg_level < 25,
            'intermediate': 25 <= avg_level < 50,
            'advanced': 50 <= avg_level < 75,
            'expert': avg_level >= 75
        }

        if difficulty_match.get(skill.difficulty, False):
            score += 20

        return score

    def _get_recommendation_reason(self, skill: SkillNode, categories: Dict[str, int]) -> str:
        """生成推荐理由"""
        if skill.category in categories:
            return f"与你已学习的{skill.category}技能相关"
        return "推荐给你的新技能"

    def _progress_to_dict(self, progress: SkillProgress) -> Dict[str, Any]:
        """将进度对象转换为字典"""
        skill = self.db.query(SkillNode).filter(SkillNode.id == progress.skill_id).first()

        return {
            "skill_id": skill.skill_id if skill else None,
            "skill_name": skill.name if skill else None,
            "status": progress.status,
            "progress_percentage": progress.progress_percentage,
            "current_level": progress.current_level,
            "current_xp": progress.current_xp,
            "practice_count": progress.practice_count,
            "success_rate": progress.success_rate,
            "time_spent_minutes": progress.time_spent_minutes,
            "last_practiced": progress.last_practiced.isoformat() if progress.last_practiced else None
        }
