#!/bin/bash
# FieldMind 服务启动脚本

echo "🚀 启动 FieldMind 服务..."

# 检查 Redis
echo "📡 检查 Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis 未运行，正在启动..."
    redis-server --daemonize yes
    sleep 2
fi
echo "✅ Redis 运行中"

# 检查 Neo4j
echo "📊 检查 Neo4j..."
if ! neo4j status > /dev/null 2>&1; then
    echo "⚠️  Neo4j 未运行，请手动启动: neo4j start"
else
    echo "✅ Neo4j 运行中"
fi

# 检查 Ollama
echo "🤖 检查 Ollama..."
if ! curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
    echo "⚠️  Ollama 未运行，请手动启动: ollama serve"
else
    echo "✅ Ollama 运行中"
fi

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p data/chromadb
mkdir -p data/whoosh
mkdir -p data/uploads/documents
mkdir -p data/uploads/audio
mkdir -p data/visualizations
mkdir -p data/reports

echo ""
echo "✨ 依赖服务检查完成！"
echo ""
echo "现在可以启动以下服务："
echo ""
echo "1. Celery Worker (任务队列):"
echo "   cd fieldmind-backend && celery -A app.celery_app worker --loglevel=info --queues=documents,audio,crawler,rag,graph,reports,default"
echo ""
echo "2. FastAPI Server (API 服务):"
echo "   cd fieldmind-backend && python -m app.main"
echo ""
echo "3. 访问 API 文档: http://localhost:8000/docs"
