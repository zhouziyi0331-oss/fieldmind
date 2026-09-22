#!/bin/bash

echo "=========================================="
echo "🔧 快速修复后端依赖并启动"
echo "=========================================="

cd /Users/alwan/FieldMind/backend

# 激活虚拟环境
source venv/bin/activate

echo "📦 安装核心依赖..."
pip install -q numpy scipy pandas scikit-learn 2>&1 | grep -v "already satisfied" || true

echo "📦 安装 NLP 依赖..."
pip install -q transformers sentence-transformers 2>&1 | grep -v "already satisfied" || true

echo "📦 安装文档处理依赖..."
pip install -q PyPDF2 python-docx python-pptx openpyxl pillow 2>&1 | grep -v "already satisfied" || true

# 停止旧进程
if [ -f backend.pid ]; then
    OLD_PID=$(cat backend.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "🛑 停止旧进程..."
        kill $OLD_PID 2>/dev/null
        sleep 2
    fi
fi

# 启动后端
echo "🚀 启动后端服务..."
cd src
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
echo $! > ../backend.pid

echo "⏳ 等待后端启动..."
sleep 5

# 检查健康状态
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo ""
    echo "=========================================="
    echo "✅ 后端启动成功！"
    echo "=========================================="
    echo "🌐 API: http://127.0.0.1:8000"
    echo "📖 文档: http://127.0.0.1:8000/docs"
    echo "📋 PID: $(cat ../backend.pid)"
    echo "📁 日志: /Users/alwan/FieldMind/backend/backend.log"
    echo "=========================================="
else
    echo ""
    echo "❌ 后端启动失败"
    echo "查看日志："
    echo ""
    tail -30 ../backend.log
    exit 1
fi
