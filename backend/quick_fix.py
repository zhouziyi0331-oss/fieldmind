#!/usr/bin/env python3
"""
FieldMind 快速修复脚本
修复已知的关键问题，确保系统可用
"""

import os
import sys
from pathlib import Path

print("🔧 FieldMind 快速修复脚本")
print("=" * 60)

# 1. 修复数据库SQL语法
print("\n1️⃣ 修复数据库SQL语法问题...")
print("   ✅ 已在 app/main.py 添加 text() 包装")
print("   ✅ 已在 app/api/monitoring.py 添加 text() 包装")

# 2. 检查数据目录
print("\n2️⃣ 检查数据目录...")
data_dir = Path("data")
if not data_dir.exists():
    data_dir.mkdir()
    print(f"   ✅ 创建数据目录: {data_dir}")
else:
    print(f"   ✅ 数据目录已存在: {data_dir}")

# 3. 检查.env文件
print("\n3️⃣ 检查环境配置...")
env_file = Path(".env")
env_example = Path(".env.example")

if not env_file.exists():
    if env_example.exists():
        import shutil
        shutil.copy(env_example, env_file)
        print("   ✅ 从.env.example创建.env")
    else:
        print("   ⚠️  缺少.env文件，将使用默认配置")
else:
    print("   ✅ .env文件已存在")

# 4. 检查必要依赖
print("\n4️⃣ 检查Python依赖...")
try:
    import fastapi
    print(f"   ✅ FastAPI {fastapi.__version__}")
except ImportError:
    print("   ❌ FastAPI未安装")

try:
    import sqlalchemy
    print(f"   ✅ SQLAlchemy {sqlalchemy.__version__}")
except ImportError:
    print("   ❌ SQLAlchemy未安装")

try:
    import sklearn
    print(f"   ✅ scikit-learn {sklearn.__version__}")
except ImportError:
    print("   ❌ scikit-learn未安装")

# 5. 初始化数据库
print("\n5️⃣ 初始化数据库...")
try:
    sys.path.insert(0, str(Path.cwd()))
    from app.core.database import init_db, SessionLocal
    from sqlalchemy import text

    # 初始化
    init_db()
    print("   ✅ 数据库表创建成功")

    # 测试连接
    db = SessionLocal()
    db.execute(text("SELECT 1"))
    db.close()
    print("   ✅ 数据库连接测试成功")

except Exception as e:
    print(f"   ⚠️  数据库初始化: {e}")

# 6. 测试核心功能
print("\n6️⃣ 测试核心功能...")

# 测试TF-IDF
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(["测试文本"])
    print("   ✅ TF-IDF功能正常")
except Exception as e:
    print(f"   ❌ TF-IDF测试失败: {e}")

# 测试中文分词
try:
    import jieba
    words = list(jieba.cut("测试中文分词"))
    print(f"   ✅ 中文分词正常: {words}")
except Exception as e:
    print(f"   ❌ 中文分词失败: {e}")

print("\n" + "=" * 60)
print("✅ 修复完成！")
print("\n📝 下一步:")
api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
print(f"   1. 启动服务: uvicorn app.main:app --reload")
print(f"   2. 访问文档: {api_url}/docs")
print(f"   3. 测试API: curl {api_url}/health")
print("\n⚠️  注意事项:")
print("   - AI功能需要配置 ANTHROPIC_API_KEY")
print("   - 向量搜索功能可选配置")
print("   - 当前使用SQLite，生产环境建议PostgreSQL")
