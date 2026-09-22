"""
关键词配置模块
为了支持关键词分类功能，将关键词相关配置放在这个包中
同时保持与原有 app.config 的兼容性
"""

# 重新导出原有的 settings，保持向后兼容
import sys
from pathlib import Path

# 导入父级 config.py 中的 settings
parent_dir = Path(__file__).parent.parent
config_file = parent_dir / "config.py"

if config_file.exists():
    # 动态导入 config.py 模块
    import importlib.util
    spec = importlib.util.spec_from_file_location("_config_module", config_file)
    _config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_config_module)

    # 导出 settings 和 Settings
    settings = _config_module.settings
    Settings = _config_module.Settings

    # 导出其他常用变量
    APP_DIR = _config_module.APP_DIR
    BACKEND_SRC_DIR = _config_module.BACKEND_SRC_DIR
    DATA_DIR = _config_module.DATA_DIR

# 导入关键词分类配置
from .keyword_categories import (
    KeywordCategory,
    CATEGORY_INFO,
    CATEGORY_WEIGHTS,
    get_all_categories,
    get_category_description,
    get_category_examples,
    get_extraction_hints
)

__all__ = [
    'settings',
    'Settings',
    'APP_DIR',
    'BACKEND_SRC_DIR',
    'DATA_DIR',
    'KeywordCategory',
    'CATEGORY_INFO',
    'CATEGORY_WEIGHTS',
    'get_all_categories',
    'get_category_description',
    'get_category_examples',
    'get_extraction_hints'
]
