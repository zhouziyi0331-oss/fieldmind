"""
Skill 加载器
动态加载和热更新 Skill
"""
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import importlib
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

logger = logging.getLogger(__name__)


class SkillFileHandler(FileSystemEventHandler):
    """Skill 文件变化处理器"""

    def __init__(self, loader):
        self.loader = loader

    def on_modified(self, event):
        """文件修改时触发"""
        if event.is_directory:
            return

        if event.src_path.endswith('.py'):
            skill_name = Path(event.src_path).stem
            logger.info(f"检测到 Skill 文件变化: {skill_name}")
            self.loader.reload_skill(skill_name)


class SkillLoader:
    """
    Skill 动态加载器

    功能：
    - 动态加载 Python 模块作为 Skill
    - 热重载（文件变化时自动重新加载）
    - 依赖管理
    - 版本控制
    """

    def __init__(self, skill_dirs: List[str] = None, watch: bool = False):
        """
        初始化 Skill 加载器

        Args:
            skill_dirs: Skill 目录列表
            watch: 是否监听文件变化（热重载）
        """
        self.skill_dirs = [Path(d) for d in (skill_dirs or ["skills"])]
        self.watch = watch
        self.loaded_modules: Dict[str, Any] = {}
        self.skill_info: Dict[str, Dict[str, Any]] = {}
        self.observer: Optional[Observer] = None

        logger.info(f"Skill 加载器已初始化 (dirs={skill_dirs}, watch={watch})")

        if watch:
            self.start_watching()

    def load_skill(self, skill_name: str, skill_path: Optional[Path] = None) -> bool:
        """
        加载一个 Skill

        Args:
            skill_name: Skill 名称
            skill_path: Skill 文件路径（可选）

        Returns:
            是否加载成功
        """
        try:
            # 查找 Skill 文件
            if skill_path is None:
                skill_path = self._find_skill_file(skill_name)
                if skill_path is None:
                    logger.error(f"找不到 Skill: {skill_name}")
                    return False

            # 构建模块名
            module_name = f"skills.{skill_name}"

            # 如果已加载，先卸载
            if module_name in sys.modules:
                del sys.modules[module_name]

            # 动态导入模块
            spec = importlib.util.spec_from_file_location(module_name, skill_path)
            if spec is None or spec.loader is None:
                logger.error(f"无法创建模块规范: {skill_name}")
                return False

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # 保存模块信息
            self.loaded_modules[skill_name] = module
            self.skill_info[skill_name] = {
                "name": skill_name,
                "path": str(skill_path),
                "module_name": module_name,
                "version": getattr(module, "__version__", "1.0.0"),
                "description": getattr(module, "__doc__", ""),
                "loaded_at": datetime.now().isoformat()
            }

            logger.info(f"✓ Skill '{skill_name}' 加载成功")
            return True

        except Exception as e:
            logger.error(f"✗ Skill '{skill_name}' 加载失败: {e}")
            return False

    def reload_skill(self, skill_name: str) -> bool:
        """
        重新加载 Skill

        Args:
            skill_name: Skill 名称

        Returns:
            是否重新加载成功
        """
        if skill_name not in self.loaded_modules:
            return self.load_skill(skill_name)

        skill_info = self.skill_info.get(skill_name)
        if skill_info is None:
            return False

        skill_path = Path(skill_info["path"])
        return self.load_skill(skill_name, skill_path)

    def unload_skill(self, skill_name: str) -> bool:
        """
        卸载 Skill

        Args:
            skill_name: Skill 名称

        Returns:
            是否卸载成功
        """
        if skill_name not in self.loaded_modules:
            return False

        skill_info = self.skill_info[skill_name]
        module_name = skill_info["module_name"]

        if module_name in sys.modules:
            del sys.modules[module_name]

        del self.loaded_modules[skill_name]
        del self.skill_info[skill_name]

        logger.info(f"Skill '{skill_name}' 已卸载")
        return True

    def load_all(self) -> int:
        """
        加载所有目录下的 Skill

        Returns:
            成功加载的 Skill 数量
        """
        loaded_count = 0

        for skill_dir in self.skill_dirs:
            if not skill_dir.exists():
                logger.warning(f"Skill 目录不存在: {skill_dir}")
                continue

            for skill_file in skill_dir.glob("*.py"):
                if skill_file.name.startswith("_"):
                    continue

                skill_name = skill_file.stem
                if self.load_skill(skill_name, skill_file):
                    loaded_count += 1

        logger.info(f"共加载 {loaded_count} 个 Skill")
        return loaded_count

    def get_skill(self, skill_name: str) -> Optional[Any]:
        """获取已加载的 Skill 模块"""
        return self.loaded_modules.get(skill_name)

    def list_skills(self) -> List[str]:
        """列出所有已加载的 Skill"""
        return list(self.loaded_modules.keys())

    def get_skill_info(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取 Skill 信息"""
        return self.skill_info.get(skill_name)

    def start_watching(self):
        """开始监听文件变化"""
        if self.observer is not None:
            return

        self.observer = Observer()
        handler = SkillFileHandler(self)

        for skill_dir in self.skill_dirs:
            if skill_dir.exists():
                self.observer.schedule(handler, str(skill_dir), recursive=False)

        self.observer.start()
        logger.info("Skill 文件监听已启动")

    def stop_watching(self):
        """停止监听文件变化"""
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("Skill 文件监听已停止")

    def _find_skill_file(self, skill_name: str) -> Optional[Path]:
        """在所有目录中查找 Skill 文件"""
        for skill_dir in self.skill_dirs:
            skill_file = skill_dir / f"{skill_name}.py"
            if skill_file.exists():
                return skill_file
        return None

    def __del__(self):
        """析构函数"""
        if self.observer is not None:
            self.stop_watching()


# 导入 datetime
from datetime import datetime


# 全局加载器实例
_global_loader: Optional[SkillLoader] = None


def get_skill_loader(skill_dirs: List[str] = None, watch: bool = False) -> SkillLoader:
    """
    获取全局 Skill 加载器实例

    Args:
        skill_dirs: Skill 目录列表
        watch: 是否监听文件变化

    Returns:
        SkillLoader 实例
    """
    global _global_loader
    if _global_loader is None:
        _global_loader = SkillLoader(skill_dirs, watch)
    return _global_loader
