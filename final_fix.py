"""
FieldMind最终修复脚本

自动完成所有必要的连接和配置
"""
import sys
from pathlib import Path


class FieldMindFinalFix:
    """最终修复器"""

    def __init__(self):
        self.base_dir = Path("/Users/alwan/FieldMind")
        self.backend_dir = self.base_dir / "backend" / "src"
        self.app_dir = self.backend_dir / "app"

    def run(self):
        """执行所有修复"""
        print("🔧 FieldMind最终修复")
        print("=" * 60)

        # 1. 创建集成配置文件
        self.create_integration_config()

        # 2. 创建依赖注入文件
        self.create_dependencies()

        # 3. 注册新模块到main.py
        self.register_modules_in_main()

        # 4. 创建数据库迁移
        self.create_migration_command()

        print("\n" + "=" * 60)
        print("✅ 修复完成！")
        print("\n下一步:")
        print("1. cd /Users/alwan/FieldMind/backend/src")
        print("2. alembic revision --autogenerate -m 'add_integration_tables'")
        print("3. alembic upgrade head")
        print("4. python -m uvicorn app.main:app --reload")

    def create_integration_config(self):
        """创建集成配置"""
        print("\n📝 创建integration_config.py...")

        config_file = self.app_dir / "core" / "integration_config.py"
        config_file.parent.mkdir(exist_ok=True)

        content = '''"""统一集成配置管理"""
from pydantic_settings import BaseSettings
from typing import Optional


class IntegrationConfig(BaseSettings):
    """集成配置"""

    # LLM配置
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_llm_model: str = "gpt-4"

    # 嵌入模型
    embedding_model: str = "text-embedding-ada-002"
    embedding_dimension: int = 1536

    # Obsidian配置
    obsidian_vault_path: Optional[str] = None
    obsidian_sync_enabled: bool = False

    # RAG配置
    rag_top_k: int = 10
    rag_similarity_threshold: float = 0.7
    rag_context_max_tokens: int = 2000

    class Config:
        env_prefix = "FIELDMIND_"
        env_file = ".env"


# 全局配置实例
integration_config = IntegrationConfig()
'''

        config_file.write_text(content)
        print(f"  ✅ 创建: {config_file.relative_to(self.base_dir)}")

    def create_dependencies(self):
        """创建依赖注入"""
        print("\n📝 创建dependencies.py...")

        deps_file = self.app_dir / "core" / "dependencies.py"

        content = '''"""依赖注入函数"""
from fastapi import Depends, Request, HTTPException
from sqlalchemy.orm import Session


def get_vector_store(request: Request):
    """获取向量存储实例"""
    if hasattr(request.app.state, 'integration_manager'):
        manager = request.app.state.integration_manager
        if manager and manager.vector_store:
            return manager.vector_store
    raise HTTPException(status_code=503, detail="Vector store not initialized")


def get_graph_builder(request: Request):
    """获取知识图谱构建器"""
    if hasattr(request.app.state, 'integration_manager'):
        manager = request.app.state.integration_manager
        if manager and manager.graph_builder:
            return manager.graph_builder
    raise HTTPException(status_code=503, detail="Graph builder not initialized")


def get_llm_enhancer(request: Request):
    """获取LLM增强器"""
    if hasattr(request.app.state, 'integration_manager'):
        manager = request.app.state.integration_manager
        if manager and manager.llm_enhancer:
            return manager.llm_enhancer
    # 返回None而不是抛出异常，允许可选功能
    return None
'''

        deps_file.write_text(content)
        print(f"  ✅ 创建: {deps_file.relative_to(self.base_dir)}")

    def register_modules_in_main(self):
        """在main.py中注册新模块"""
        print("\n📝 注册模块到main.py...")

        main_file = self.app_dir / "main.py"
        if not main_file.exists():
            print("  ❌ main.py不存在")
            return

        content = main_file.read_text()

        # 检查是否已注册
        if "sbpack.router" in content:
            print("  ℹ️  模块已注册，跳过")
            return

        # 在导入部分添加
        import_addition = '''
# ==================== 新增集成模块 ====================
try:
    from app.api import sbpack, skill_tree, obsidian, rag, llm
    INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  集成模块未安装: {e}")
    INTEGRATION_AVAILABLE = False
'''

        # 查找合适的导入位置
        import_pos = content.rfind("from app.api import")
        if import_pos != -1:
            # 找到这行的结束位置
            end_pos = content.find("\n", import_pos)
            # 找到下一个空行
            next_line = content.find("\n\n", end_pos)
            if next_line != -1:
                content = content[:next_line] + "\n" + import_addition + content[next_line:]

        # 在路由注册部分添加
        register_addition = '''

# ==================== 注册集成模块路由 ====================
if INTEGRATION_AVAILABLE:
    try:
        app.include_router(sbpack.router, tags=["SBPACK"])
        app.include_router(skill_tree.router, tags=["Skill Tree"])
        app.include_router(obsidian.router, tags=["Obsidian"])
        app.include_router(rag.router, tags=["RAG"])
        app.include_router(llm.router, tags=["LLM"])
        logger.info("✅ 集成模块路由已注册")
    except Exception as e:
        logger.error(f"❌ 集成模块注册失败: {e}")
'''

        # 查找路由注册的位置
        router_pos = content.rfind("app.include_router(")
        if router_pos != -1:
            # 找到该段落的结束
            end_pos = content.find("\n\n", router_pos)
            if end_pos != -1:
                content = content[:end_pos] + register_addition + content[end_pos:]

        # 备份原文件
        backup = main_file.with_suffix(".py.bak")
        main_file.rename(backup)
        main_file.write_text(content)

        print(f"  ✅ 已更新main.py (备份: {backup.name})")

    def create_migration_command(self):
        """创建迁移命令脚本"""
        print("\n📝 创建迁移命令...")

        migrate_script = self.backend_dir / "run_migration.sh"

        content = '''#!/bin/bash
# FieldMind数据库迁移脚本

echo "🔄 开始数据库迁移..."

# 进入backend/src目录
cd "$(dirname "$0")"

# 创建迁移
echo "📝 创建迁移文件..."
alembic revision --autogenerate -m "add_integration_tables"

# 执行迁移
echo "⬆️  执行迁移..."
alembic upgrade head

echo "✅ 迁移完成！"
'''

        migrate_script.write_text(content)
        migrate_script.chmod(0o755)

        print(f"  ✅ 创建: {migrate_script.relative_to(self.base_dir)}")


if __name__ == "__main__":
    fixer = FieldMindFinalFix()
    fixer.run()
