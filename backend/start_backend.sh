#!/bin/bash

cd /Users/alwan/FieldMind/backend

# 停止旧进程
if [ -f backend.pid ]; then
    OLD_PID=$(cat backend.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "停止旧进程 (PID: $OLD_PID)..."
        kill $OLD_PID
        sleep 2
    fi
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate

# 安装核心依赖（跳过有问题的包）
echo "安装核心依赖..."
pip install -q fastapi uvicorn sqlalchemy pymysql pydantic pydantic-settings python-multipart aiofiles

# 设置 PYTHONPATH 并启动
export PYTHONPATH=/Users/alwan/FieldMind/backend/src

echo "启动后端服务..."
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
echo $! > backend.pid

echo "等待后端启动..."
sleep 3

# 检查健康状态
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "✅ 后端启动成功！"
    echo "🌐 API: http://127.0.0.1:8000"
    echo "📖 文档: http://127.0.0.1:8000/docs"
    echo "📋 PID: $(cat backend.pid)"
else
    echo "❌ 后端启动失败，查看日志："
    tail -20 backend.log
    exit 1
fi
