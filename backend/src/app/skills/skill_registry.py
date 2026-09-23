"""
Skills Registry - 管理和加载所有蒸馏Skills
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import importlib.util
import inspect


class SkillRegistry:
    """Skills注册表，负责加载和管理所有蒸馏Skills"""

    def __init__(self):
        self._skills: Dict[str, Any] = {}
        self._skill_metadata: Dict[str, Dict[str, Any]] = {}

    def register_skill(self, name: str, skill_class: Any, metadata: Optional[Dict[str, Any]] = None):
        """注册一个Skill"""
        self._skills[name] = skill_class
        self._skill_metadata[name] = metadata or {}

    def get_skill(self, name: str) -> Optional[Any]:
        """获取已注册的Skill"""
        return self._skills.get(name)

    def list_skills(self) -> List[str]:
        """列出所有已注册的Skills"""
        return list(self._skills.keys())

    def get_metadata(self, name: str) -> Dict[str, Any]:
        """获取Skill的元数据"""
        return self._skill_metadata.get(name, {})

    def load_from_directory(self, directory: Path):
        """从目录加载所有Skills"""
        if not directory.exists():
            return

        for file_path in directory.glob("*.py"):
            if file_path.stem.startswith("_"):
                continue

            # 动态导入模块
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 查找Skill类（通常以Skill结尾）
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and name.endswith("Skill"):
                        skill_name = file_path.stem
                        metadata = getattr(obj, "METADATA", {})
                        self.register_skill(skill_name, obj, metadata)


# 全局注册表实例
_global_registry = SkillRegistry()


def get_registry() -> SkillRegistry:
    """获取全局Skills注册表"""
    return _global_registry


def initialize_distillation_skills():
    """初始化蒸馏相关的Skills"""
    from .extract_knowledge_points import ExtractKnowledgePointsSkill
    from .extract_cangjie_skills import ExtractCangjieSkillsSkill
    from .extract_insights import ExtractInsightsSkill
    from .extract_quotes import ExtractQuotesSkill
    from .extract_cases import ExtractCasesSkill
    from .extract_actions import ExtractActionsSkill

    registry = get_registry()

    # 注册所有蒸馏Skills
    registry.register_skill("extract_knowledge_points", ExtractKnowledgePointsSkill, {
        "type": "knowledge_track",
        "output_type": "洞察",
        "methodology": "SBPACK 2.0"
    })

    registry.register_skill("extract_cangjie_skills", ExtractCangjieSkillsSkill, {
        "type": "skill_track",
        "output_type": "方法论",
        "methodology": "Cangjie v2.0.0"
    })

    registry.register_skill("extract_insights", ExtractInsightsSkill, {
        "type": "frequency_analysis",
        "output_type": "洞察",
        "methodology": "Entity + Event Analysis"
    })

    registry.register_skill("extract_quotes", ExtractQuotesSkill, {
        "type": "text_extraction",
        "output_type": "原话",
        "methodology": "Quote Mining"
    })

    registry.register_skill("extract_cases", ExtractCasesSkill, {
        "type": "pattern_matching",
        "output_type": "案例",
        "methodology": "Keyword Matching"
    })

    registry.register_skill("extract_actions", ExtractActionsSkill, {
        "type": "gap_analysis",
        "output_type": "行动建议",
        "methodology": "Gap + Trend Analysis"
    })

    return registry
