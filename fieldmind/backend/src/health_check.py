#!/usr/bin/env python3
"""
FieldMind 系统健康检查脚本
用于诊断：PostgreSQL、ChromaDB、Whisper、向量化模型是否正常工作

使用方法:
    python health_check.py
"""

import sys
import os

# 添加项目路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

print("=" * 70)
print("🏥 FieldMind 系统健康检查")
print("=" * 70)

# ===== 检查1: PostgreSQL/SQLite数据库连接 =====
print("\n[1/5] 📊 检查数据库连接...")
try:
    from app.core.database import SessionLocal, engine
    from app.models.project import ProjectDocument
    from sqlalchemy import text

    db = SessionLocal()

    # 测试连接
    db.execute(text("SELECT 1"))

    # 检查表是否存在
    doc_count = db.query(ProjectDocument).count()

    print(f"✅ 数据库连接成功")
    print(f"   - 数据库URL: {engine.url}")
    print(f"   - project_documents表记录数: {doc_count}")

    db.close()

except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    print(f"   错误类型: {type(e).__name__}")

# ===== 检查2: ChromaDB向量数据库 =====
print("\n[2/5] 🗄️  检查ChromaDB向量数据库...")
try:
    from app.core.rag_engine import rag_engine

    if rag_engine and rag_engine.collection:
        count = rag_engine.collection.count()
        print(f"✅ ChromaDB连接成功")
        print(f"   - Collection名称: {rag_engine.collection.name}")
        print(f"   - 向量记录数: {count}")

        # 测试查询
        if count > 0:
            test_results = rag_engine.collection.get(limit=1)
            print(f"   - 测试查询: 成功获取1条记录")
    else:
        print(f"❌ ChromaDB未初始化")

except Exception as e:
    print(f"❌ ChromaDB连接失败: {e}")
    print(f"   错误类型: {type(e).__name__}")

# ===== 检查3: Sentence-Transformers向量化模型 =====
print("\n[3/5] 🧮 检查Sentence-Transformers模型...")
try:
    from sentence_transformers import SentenceTransformer

    print("   正在加载模型...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    # 测试编码
    test_text = "这是一个测试句子"
    embedding = model.encode(test_text)

    print(f"✅ 向量化模型加载成功")
    print(f"   - 模型名称: paraphrase-multilingual-MiniLM-L12-v2")
    print(f"   - 向量维度: {len(embedding)}")
    print(f"   - 测试编码: 成功 (输入='{test_text}', 输出向量维度={len(embedding)})")

except ImportError as e:
    print(f"❌ 模型库未安装: {e}")
    print(f"   请运行: pip install sentence-transformers")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    print(f"   错误类型: {type(e).__name__}")

# ===== 检查4: Whisper语音识别模型 =====
print("\n[4/5] 🎤 检查Whisper语音识别模型...")
try:
    import whisper

    print("   正在加载Whisper base模型...")
    model = whisper.load_model("base")

    print(f"✅ Whisper模型加载成功")
    print(f"   - 模型大小: base (139MB)")
    print(f"   - 支持语言: 多语言 (自动检测)")

    # 如果有测试音频文件，可以测试转录
    test_audio = "/tmp/ultimate_test.mp3"
    if os.path.exists(test_audio):
        print(f"   正在测试转录...")
        result = model.transcribe(test_audio)
        text = result.get('text', '').strip()
        print(f"   - 测试转录: 成功")
        print(f"   - 转录文本: {text[:50]}{'...' if len(text) > 50 else ''}")

except ImportError as e:
    print(f"❌ Whisper未安装: {e}")
    print(f"   请运行: pip install openai-whisper")
except Exception as e:
    print(f"❌ Whisper模型加载失败: {e}")
    print(f"   错误类型: {type(e).__name__}")

# ===== 检查5: API服务可用性 =====
print("\n[5/5] 🌐 检查API服务...")
try:
    import requests

    # 测试健康检查端点
    api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    response = requests.get(f"{api_url}/health", timeout=5)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ API服务运行正常")
        print(f"   - 状态: {data.get('status')}")
        print(f"   - 响应时间: {data.get('response_time_ms', 0):.2f}ms")

        services = data.get('services', {})
        for service, status in services.items():
            icon = "✅" if status == "ok" else "⚠️"
            print(f"   - {service}: {icon} {status}")
    else:
        print(f"❌ API返回异常状态码: {response.status_code}")

except requests.exceptions.ConnectionError:
    print(f"❌ API服务未启动或无法连接")
    print(f"   请确认后端是否运行在 {api_url}")
except Exception as e:
    print(f"❌ API检查失败: {e}")

# ===== 总结 =====
print("\n" + "=" * 70)
print("📋 健康检查完成")
print("=" * 70)

print("""
🔍 诊断建议:
1. 如果数据库 ❌: 检查 DATABASE_URL 配置，确认数据库文件存在
2. 如果ChromaDB ❌: 检查 CHROMA_PERSIST_DIR，确认目录权限
3. 如果模型 ❌: 运行 pip install sentence-transformers openai-whisper
4. 如果API ❌: 运行 uvicorn app.main:app --host 0.0.0.0 --port 8000

💡 验证完整链路:
   python health_check.py && python /tmp/ultimate_test.py

📝 查看实时日志:
   tail -f /tmp/backend_clean.log
""")
