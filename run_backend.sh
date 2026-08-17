#!/bin/bash
# FieldMind后端启动脚本

echo "🚀 启动 FieldMind 后端服务..."
echo ""

# 激活虚拟环境
source venv/bin/activate

# 检查环境变量文件
if [ ! -f "fieldmind-backend/.env" ]; then
    echo "⚠️  未找到 .env 文件，复制模板..."
    cp fieldmind-backend/.env.example fieldmind-backend/.env
    echo "✅ 已创建 .env 文件，请编辑配置后重新运行"
    echo ""
    echo "需要配置的关键项："
    echo "  - OPENAI_API_KEY (必需 - 用于Whisper和RAG)"
    echo "  - DATABASE_URL (PostgreSQL连接)"
    echo "  - NEO4J_URI (Neo4j连接)"
    echo "  - REDIS_URL (Redis连接)"
    exit 1
fi

# 进入后端目录
cd fieldmind-backend

echo "📦 检查依赖..."
pip list | grep -E "fastapi|langchain|chromadb|neo4j" > /dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  安装后端依赖..."
    pip install -r requirements.txt
fi

echo ""
echo "🔍 检查数据库连接..."
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

checks = []

# PostgreSQL
db_url = os.getenv('DATABASE_URL', '')
if 'postgresql' in db_url:
    checks.append('✅ PostgreSQL 已配置')
else:
    checks.append('⚠️  PostgreSQL 未配置')

# Neo4j
neo4j_uri = os.getenv('NEO4J_URI', '')
if neo4j_uri:
    checks.append('✅ Neo4j 已配置')
else:
    checks.append('⚠️  Neo4j 未配置')

# Redis
redis_url = os.getenv('REDIS_URL', '')
if redis_url:
    checks.append('✅ Redis 已配置')
else:
    checks.append('⚠️  Redis 未配置')

# OpenAI API Key
openai_key = os.getenv('OPENAI_API_KEY', '')
if openai_key and len(openai_key) > 20:
    checks.append('✅ OpenAI API Key 已配置')
else:
    checks.append('⚠️  OpenAI API Key 未配置')

for check in checks:
    print(check)
" || echo "⚠️  无法检查配置 (dotenv未安装)"

echo ""
echo "🌐 启动 FastAPI 服务器..."
echo "   访问地址: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo "   ReDoc: http://localhost:8000/redoc"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
