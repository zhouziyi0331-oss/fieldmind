"""
FieldMind完整集成实施脚本

一键执行所有集成步骤
"""
import os
import sys
import subprocess
from pathlib import Path

class IntegrationInstaller:
    """集成安装器"""

    def __init__(self, base_dir: str = "/Users/alwan/FieldMind"):
        self.base_dir = Path(base_dir)
        self.backend_dir = self.base_dir / "backend" / "src"
        self.app_dir = self.backend_dir / "app"

    def run(self):
        """执行完整集成"""
        print("🚀 开始FieldMind完整集成安装...")
        print("=" * 60)

        # 步骤1: 检查环境
        self.check_environment()

        # 步骤2: 安装依赖
        self.install_dependencies()

        # 步骤3: 配置数据库
        self.setup_database()

        # 步骤4: 创建必要文件
        self.create_integration_files()

        # 步骤5: 注册API路由
        self.register_api_routes()

        # 步骤6: 运行迁移
        self.run_migrations()

        # 步骤7: 验证安装
        self.verify_installation()

        print("\n" + "=" * 60)
        print("✅ 集成安装完成！")
        print("\n下一步:")
        print("1. 配置.env文件中的API keys")
        print("2. 启动应用: cd backend/src && python -m uvicorn app.main:app --reload")
        print("3. 访问 http://localhost:8000/docs 查看API文档")

    def check_environment(self):
        """检查环境"""
        print("\n📋 步骤1: 检查环境...")

        # 检查Python版本
        py_version = sys.version_info
        print(f"  Python版本: {py_version.major}.{py_version.minor}.{py_version.micro}")

        if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 8):
            raise Exception("❌ 需要Python 3.8+")

        # 检查PostgreSQL
        try:
            result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
            print(f"  PostgreSQL: {result.stdout.strip()}")
        except FileNotFoundError:
            print("  ⚠️ 未找到PostgreSQL，请确保已安装")

        # 检查目录
        if not self.backend_dir.exists():
            raise Exception(f"❌ 找不到backend目录: {self.backend_dir}")

        print("  ✅ 环境检查通过")

    def install_dependencies(self):
        """安装依赖"""
        print("\n📦 步骤2: 安装Python依赖...")

        requirements = [
            "pgvector",
            "watchdog",
            "ebooklib",
            "beautifulsoup4",
            "yt-dlp",
            "pdfplumber",
            "python-docx",
            "openai",
            "anthropic",
            "pyyaml"
        ]

        for package in requirements:
            print(f"  安装 {package}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True
            )

        print("  ✅ 依赖安装完成")

    def setup_database(self):
        """配置数据库"""
        print("\n🗄️ 步骤3: 配置数据库...")

        # 检查pgvector扩展
        print("  检查pgvector扩展...")

        db_name = os.getenv("POSTGRES_DB", "fieldmind")

        sql_commands = """
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
        CREATE EXTENSION IF NOT EXISTS btree_gin;
        """

        try:
            subprocess.run(
                ['psql', '-d', db_name, '-c', sql_commands],
                capture_output=True,
                check=True
            )
            print("  ✅ 数据库扩展已安装")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️ 数据库扩展安装失败，请手动执行:")
            print(f"     psql -d {db_name}")
            print(f"     {sql_commands}")

    def create_integration_files(self):
        """创建集成文件"""
        print("\n📝 步骤4: 创建集成文件...")

        # 创建core目录
        core_dir = self.app_dir / "core"
        core_dir.mkdir(exist_ok=True)

        # 创建integration_config.py
        config_file = core_dir / "integration_config.py"
        if not config_file.exists():
            config_content = '''"""统一集成配置"""
from pydantic import BaseSettings
from typing import Optional

class IntegrationConfig(BaseSettings):
    openai_api_key: Optional[str] = None
    obsidian_vault_path: Optional[str] = None
    embedding_model: str = "text-embedding-ada-002"

    class Config:
        env_file = ".env"
        env_prefix = "FIELDMIND_"

integration_config = IntegrationConfig()
'''
            config_file.write_text(config_content)
            print("  ✅ 创建 integration_config.py")

        # 创建dependencies.py
        deps_file = core_dir / "dependencies.py"
        if not deps_file.exists():
            deps_content = '''"""依赖注入"""
from fastapi import Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db

def get_vector_store(request: Request):
    if hasattr(request.app.state, 'integration_manager'):
        return request.app.state.integration_manager.vector_store
    raise HTTPException(status_code=503, detail="Not initialized")

def get_llm_enhancer(request: Request):
    if hasattr(request.app.state, 'integration_manager'):
        return request.app.state.integration_manager.llm_enhancer
    raise HTTPException(status_code=503, detail="Not initialized")
'''
            deps_file.write_text(deps_content)
            print("  ✅ 创建 dependencies.py")

    def register_api_routes(self):
        """注册API路由"""
        print("\n🔌 步骤5: 注册API路由...")

        main_file = self.app_dir / "main.py"

        if not main_file.exists():
            print("  ⚠️ 找不到main.py")
            return

        # 读取main.py
        content = main_file.read_text()

        # 检查是否已注册
        if "sbpack.router" in content:
            print("  ℹ️ 路由已注册，跳过")
            return

        # 准备插入的代码
        import_code = """
# ==================== 新增集成模块导入 ====================
try:
    from app.api import sbpack, skill_tree, obsidian, rag, llm
    INTEGRATION_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 集成模块导入失败: {e}")
    INTEGRATION_MODULES_AVAILABLE = False
"""

        register_code = """
# ==================== 注册集成模块路由 ====================
if INTEGRATION_MODULES_AVAILABLE:
    app.include_router(sbpack.router, prefix="/api/v1", tags=["SBPACK"])
    app.include_router(skill_tree.router, prefix="/api/v1", tags=["Skill Tree"])
    app.include_router(obsidian.router, prefix="/api/v1", tags=["Obsidian"])
    app.include_router(rag.router, prefix="/api/v1", tags=["RAG"])
    app.include_router(llm.router, prefix="/api/v1", tags=["LLM"])
    print("✅ 集成模块路由已注册")
"""

        # 在适当位置插入代码
        # 在imports后插入
        import_pos = content.find("from app.api import")
        if import_pos != -1:
            end_pos = content.find("\n\n", import_pos)
            content = content[:end_pos] + "\n" + import_code + content[end_pos:]

        # 在app创建后插入
        app_pos = content.find("app = FastAPI")
        if app_pos != -1:
            end_pos = content.find("\n\n", app_pos + 100)
            content = content[:end_pos] + "\n" + register_code + content[end_pos:]

        # 写回文件
        backup_file = main_file.with_suffix(".py.backup")
        main_file.rename(backup_file)
        main_file.write_text(content)

        print(f"  ✅ 已更新main.py (备份: {backup_file.name})")

    def run_migrations(self):
        """运行数据库迁移"""
        print("\n🔄 步骤6: 运行数据库迁移...")

        os.chdir(self.backend_dir)

        try:
            # 创建迁移
            print("  创建迁移...")
            subprocess.run(
                ["alembic", "revision", "--autogenerate", "-m", "complete_integration"],
                capture_output=True,
                check=True
            )

            # 执行迁移
            print("  执行迁移...")
            subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                check=True
            )

            print("  ✅ 数据库迁移完成")

        except subprocess.CalledProcessError as e:
            print(f"  ⚠️ 迁移失败: {e}")
            print("     请手动执行:")
            print("     cd backend/src")
            print("     alembic upgrade head")

    def verify_installation(self):
        """验证安装"""
        print("\n✔️ 步骤7: 验证安装...")

        # 检查文件
        files_to_check = [
            self.app_dir / "api" / "sbpack.py",
            self.app_dir / "api" / "rag.py",
            self.app_dir / "services" / "vector_store.py",
            self.app_dir / "services" / "knowledge_graph_builder.py",
            self.app_dir / "models" / "knowledge_graph.py"
        ]

        all_exist = True
        for file in files_to_check:
            if file.exists():
                print(f"  ✅ {file.name}")
            else:
                print(f"  ❌ 缺少: {file.name}")
                all_exist = False

        if all_exist:
            print("\n  🎉 所有文件就绪！")
        else:
            print("\n  ⚠️ 部分文件缺失，请检查")


if __name__ == "__main__":
    installer = IntegrationInstaller()
    try:
        installer.run()
    except Exception as e:
        print(f"\n❌ 安装失败: {e}")
        sys.exit(1)
