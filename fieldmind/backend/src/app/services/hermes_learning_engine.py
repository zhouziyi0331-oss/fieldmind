"""
Hermes Learning Engine - 自学习引擎
整合 NousResearch Hermes Agent 的自学习能力到 FieldMind

核心能力：
1. 工具使用学习（Tool Learning）
2. 经验记忆持久化（Experience Memory）
3. 反馈循环优化（Feedback Loop）
4. 技能自动进化（Skill Evolution）
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class LearningType(str, Enum):
    """学习类型"""
    TOOL_USAGE = "tool_usage"          # 工具使用学习
    PATTERN_RECOGNITION = "pattern"     # 模式识别
    ERROR_CORRECTION = "error"          # 错误纠正
    WORKFLOW_OPTIMIZATION = "workflow"  # 工作流优化
    SKILL_CREATION = "skill"            # 技能创建


class FeedbackScore(str, Enum):
    """反馈评分"""
    EXCELLENT = "excellent"  # 5分
    GOOD = "good"            # 4分
    NEUTRAL = "neutral"      # 3分
    POOR = "poor"            # 2分
    FAILED = "failed"        # 1分


@dataclass
class LearningExperience:
    """学习经验记录"""
    experience_id: str
    project_id: int
    learning_type: LearningType

    # 上下文
    context: Dict[str, Any]  # 任务上下文、输入数据
    action: Dict[str, Any]   # 执行的动作（工具调用、参数等）
    result: Dict[str, Any]   # 执行结果

    # 反馈
    feedback_score: Optional[FeedbackScore] = None
    feedback_reason: Optional[str] = None

    # 学习输出
    learned_pattern: Optional[Dict[str, Any]] = None  # 学到的模式
    skill_update: Optional[Dict[str, Any]] = None     # 技能更新

    # 元数据
    created_at: datetime = field(default_factory=datetime.utcnow)
    success: bool = True
    execution_time: float = 0.0

    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        data['learning_type'] = self.learning_type.value
        if self.feedback_score:
            data['feedback_score'] = self.feedback_score.value
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class LearnedSkill:
    """学习到的技能"""
    skill_id: str
    skill_name: str
    skill_type: str  # "tool_chain", "workflow", "pattern"

    # 技能定义
    description: str
    trigger_conditions: List[Dict[str, Any]]  # 触发条件
    action_sequence: List[Dict[str, Any]]     # 动作序列

    # 性能指标
    success_rate: float = 0.0
    avg_execution_time: float = 0.0
    usage_count: int = 0

    # 学习元数据
    learned_from: List[str] = field(default_factory=list)  # 经验ID列表
    confidence_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data


class HermesLearningEngine:
    """
    Hermes 自学习引擎

    核心流程：
    1. 记录执行经验 (record_experience)
    2. 分析反馈 (analyze_feedback)
    3. 提取模式 (extract_patterns)
    4. 生成/更新技能 (update_skills)
    5. 应用学习 (apply_learning)
    """

    def __init__(
        self,
        storage_path: str = "./data/hermes_learning",
        enable_auto_learning: bool = True
    ):
        """
        初始化学习引擎

        Args:
            storage_path: 学习数据存储路径
            enable_auto_learning: 是否启用自动学习
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.enable_auto_learning = enable_auto_learning

        # 内存缓存
        self.experiences: List[LearningExperience] = []
        self.skills: Dict[str, LearnedSkill] = {}

        # 加载已有的学习数据
        self._load_learning_data()

        logger.info(f"✅ Hermes Learning Engine 已初始化 (存储: {self.storage_path})")

    def _load_learning_data(self):
        """加载已有的学习数据"""
        try:
            # 加载经验
            experiences_file = self.storage_path / "experiences.jsonl"
            if experiences_file.exists():
                with open(experiences_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            exp_data = json.loads(line)
                            # 简化版：只保存最近1000条
                            if len(self.experiences) < 1000:
                                # 转换回 LearningExperience 对象
                                exp_data['learning_type'] = LearningType(exp_data['learning_type'])
                                if exp_data.get('feedback_score'):
                                    exp_data['feedback_score'] = FeedbackScore(exp_data['feedback_score'])
                                exp_data['created_at'] = datetime.fromisoformat(exp_data['created_at'])

                                experience = LearningExperience(**exp_data)
                                self.experiences.append(experience)

            # 加载技能
            skills_file = self.storage_path / "skills.json"
            if skills_file.exists():
                with open(skills_file, 'r', encoding='utf-8') as f:
                    skills_data = json.load(f)
                    for skill_id, skill_dict in skills_data.items():
                        skill_dict['last_updated'] = datetime.fromisoformat(skill_dict['last_updated'])
                        self.skills[skill_id] = LearnedSkill(**skill_dict)

            logger.info(f"✅ 已加载 {len(self.experiences)} 条经验，{len(self.skills)} 个技能")

        except Exception as e:
            logger.warning(f"⚠️ 加载学习数据失败: {e}")
            import traceback
            traceback.print_exc()

    def record_experience(
        self,
        project_id: int,
        learning_type: LearningType,
        context: Dict[str, Any],
        action: Dict[str, Any],
        result: Dict[str, Any],
        success: bool = True,
        execution_time: float = 0.0
    ) -> str:
        """
        记录一次执行经验

        Returns:
            experience_id
        """
        experience = LearningExperience(
            experience_id=f"exp_{datetime.utcnow().timestamp()}_{project_id}",
            project_id=project_id,
            learning_type=learning_type,
            context=context,
            action=action,
            result=result,
            success=success,
            execution_time=execution_time
        )

        # 保存到内存
        self.experiences.append(experience)

        # 持久化
        self._persist_experience(experience)

        # 自动学习
        if self.enable_auto_learning and success:
            self._try_auto_learn(experience)

        logger.info(f"✅ 记录经验: {experience.experience_id} ({learning_type.value})")
        return experience.experience_id

    def _persist_experience(self, experience: LearningExperience):
        """持久化经验"""
        try:
            experiences_file = self.storage_path / "experiences.jsonl"
            with open(experiences_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(experience.to_dict(), ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"❌ 持久化经验失败: {e}")

    def _try_auto_learn(self, experience: LearningExperience):
        """尝试自动学习"""
        # TODO: 实现自动模式提取和技能生成
        pass

    def get_similar_experiences(
        self,
        context: Dict[str, Any],
        learning_type: Optional[LearningType] = None,
        limit: int = 5
    ) -> List[LearningExperience]:
        """
        获取相似的历史经验（用于迁移学习）

        Returns:
            相似度最高的经验列表
        """
        # TODO: 实现语义相似度匹配
        # 目前简化版：返回同类型的最近经验
        filtered = [
            exp for exp in self.experiences
            if learning_type is None or exp.learning_type == learning_type
        ]
        return filtered[-limit:]

    def suggest_action(
        self,
        context: Dict[str, Any],
        learning_type: LearningType
    ) -> Optional[Dict[str, Any]]:
        """
        基于历史经验建议下一步动作

        Returns:
            建议的动作，或 None
        """
        similar_exp = self.get_similar_experiences(context, learning_type, limit=3)

        if not similar_exp:
            return None

        # 简化版：返回成功率最高的动作
        successful = [exp for exp in similar_exp if exp.success]
        if successful:
            return successful[-1].action

        return None

    def register_skill(self, skill: LearnedSkill) -> str:
        """注册一个学习到的技能"""
        self.skills[skill.skill_id] = skill
        self._persist_skills()
        logger.info(f"✅ 注册技能: {skill.skill_name} ({skill.skill_id})")
        return skill.skill_id

    def _persist_skills(self):
        """持久化技能库"""
        try:
            skills_file = self.storage_path / "skills.json"
            skills_data = {
                skill_id: skill.to_dict()
                for skill_id, skill in self.skills.items()
            }
            with open(skills_file, 'w', encoding='utf-8') as f:
                json.dump(skills_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 持久化技能失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取学习统计"""
        return {
            "total_experiences": len(self.experiences),
            "total_skills": len(self.skills),
            "success_rate": sum(1 for exp in self.experiences if exp.success) / len(self.experiences) if self.experiences else 0,
            "learning_types": {
                lt.value: sum(1 for exp in self.experiences if exp.learning_type == lt)
                for lt in LearningType
            }
        }


# 全局单例
_learning_engine: Optional[HermesLearningEngine] = None

def get_learning_engine() -> HermesLearningEngine:
    """获取全局学习引擎实例"""
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = HermesLearningEngine()
    return _learning_engine
