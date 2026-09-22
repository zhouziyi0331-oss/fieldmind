"""
Skill 服务
管理 Skill 的加载、执行和生命周期
"""
from typing import Dict, List, Any, Optional, Callable
import logging
from datetime import datetime
from pathlib import Path
import importlib.util
import inspect

logger = logging.getLogger(__name__)


class SkillService:
    """
    Skill 服务

    功能：
    - Skill 加载和卸载
    - Skill 执行
    - Skill 生命周期管理
    - Skill 依赖管理
    """
    def __init__(self, skill_dir: Optional[str] = None, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化 Skill 服务

        Args:
            skill_dir: Skill 目录路径
        """
        self.skill_dir = Path(skill_dir) if skill_dir else Path("skills")
        self.loaded_skills: Dict[str, Any] = {}
        self.skill_metadata: Dict[str, Dict[str, Any]] = {}
        logger.info(f"Skill 服务已初始化 (skill_dir={self.skill_dir})")

    def load_skill(self, skill_name: str, skill_path: Optional[str] = None) -> bool:
        """
        加载一个 Skill

        Args:
            skill_name: Skill 名称
            skill_path: Skill 文件路径（可选）

        Returns:
            是否加载成功
        """
        try:
            if skill_path is None:
                skill_path = self.skill_dir / f"{skill_name}.py"
            else:
                skill_path = Path(skill_path)

            if not skill_path.exists():
                logger.error(f"Skill 文件不存在: {skill_path}")
                return False

            # 动态加载模块
            spec = importlib.util.spec_from_file_location(skill_name, skill_path)
            if spec is None or spec.loader is None:
                logger.error(f"无法加载 Skill: {skill_name}")
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找 Skill 类（必须有 execute 方法）
            skill_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if hasattr(obj, 'execute') and callable(getattr(obj, 'execute')):
                    skill_class = obj
                    break

            if skill_class is None:
                logger.error(f"Skill {skill_name} 没有 execute 方法")
                return False

            # 实例化 Skill
            skill_instance = skill_class()

            # 保存到已加载列表
            self.loaded_skills[skill_name] = skill_instance

            # 保存元数据
            self.skill_metadata[skill_name] = {
                "name": skill_name,
                "path": str(skill_path),
                "loaded_at": datetime.now().isoformat(),
                "class_name": skill_class.__name__,
                "description": getattr(skill_class, "__doc__", "")
            }

            logger.info(f"✓ Skill '{skill_name}' 加载成功")
            return True

        except Exception as e:
            logger.error(f"✗ Skill '{skill_name}' 加载失败: {e}")
            return False

    def unload_skill(self, skill_name: str) -> bool:
        """
        卸载一个 Skill

        Args:
            skill_name: Skill 名称

        Returns:
            是否卸载成功
        """
        if skill_name not in self.loaded_skills:
            logger.warning(f"Skill '{skill_name}' 未加载")
            return False

        del self.loaded_skills[skill_name]
        del self.skill_metadata[skill_name]

        logger.info(f"Skill '{skill_name}' 已卸载")
        return True

    def execute_skill(self, skill_name: str, input_data: Dict[str, Any]) -> Any:
        """
        执行 Skill

        Args:
            skill_name: Skill 名称
            input_data: 输入数据

        Returns:
            执行结果

        Raises:
            ValueError: 如果 Skill 不存在
        """
        if skill_name not in self.loaded_skills:
            raise ValueError(f"Skill '{skill_name}' 未加载")

        skill = self.loaded_skills[skill_name]

        try:
            result = skill.execute(input_data)
            logger.info(f"Skill '{skill_name}' 执行成功")
            return result

        except Exception as e:
            logger.error(f"Skill '{skill_name}' 执行失败: {e}")
            raise

    def list_loaded_skills(self) -> List[str]:
        """列出所有已加载的 Skill"""
        return list(self.loaded_skills.keys())

    def get_skill_metadata(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取 Skill 元数据"""
        return self.skill_metadata.get(skill_name)

    def load_all_skills(self) -> int:
        """
        加载目录下的所有 Skill

        Returns:
            成功加载的 Skill 数量
        """
        if not self.skill_dir.exists():
            logger.warning(f"Skill 目录不存在: {self.skill_dir}")
            return 0

        loaded_count = 0
        for skill_file in self.skill_dir.glob("*.py"):
            if skill_file.name.startswith("_"):
                continue

            skill_name = skill_file.stem
            if self.load_skill(skill_name, str(skill_file)):
                loaded_count += 1

        logger.info(f"加载了 {loaded_count} 个 Skill")
        return loaded_count

    def reload_skill(self, skill_name: str) -> bool:
        """
        重新加载 Skill

        Args:
            skill_name: Skill 名称

        Returns:
            是否重新加载成功
        """
        metadata = self.skill_metadata.get(skill_name)
        if metadata is None:
            return self.load_skill(skill_name)

        skill_path = metadata.get("path")
        self.unload_skill(skill_name)
        return self.load_skill(skill_name, skill_path)


# 全局 Skill 服务实例
_global_skill_service: Optional[SkillService] = None


def get_skill_service(skill_dir: Optional[str] = None) -> SkillService:
    """
    获取全局 Skill 服务实例

    Args:
        skill_dir: Skill 目录路径

    Returns:
        SkillService 实例
    """
    global _global_skill_service
    if _global_skill_service is None:
        _global_skill_service = SkillService(skill_dir)
    return _global_skill_service
