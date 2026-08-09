#!/bin/bash
# FieldMind 一键启动脚本

echo "启动 FieldMind..."

# 启动后端
echo "1. 启动后端服务..."
cd ~/FieldMind
source venv/bin/activate
cd backend/src
python -m app.main &
BACKEND_PID=$!

sleep 3

# 检查后端是否启动成功
if curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "✓ 后端启动成功 (PID: $BACKEND_PID)"
else
    echo "✗ 后端启动失败"
    exit 1
fi

# 启动桌面应用
echo "2. 启动桌面应用..."
open ~/FieldMind/FieldMind.app

echo ""
echo "✓ FieldMind 已启动！"
echo "  后端: http://127.0.0.1:8000"
echo "  桌面应用已打开"
echo ""
echo "停止服务: kill $BACKEND_PID"
