#!/bin/bash

echo "正在启动 FieldMind..."
echo ""

# 启动后端
echo "1. 启动后端服务..."
cd /Users/alwan/FieldMind/backend

# 使用系统 Python 启动
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "   后端已启动 (PID: $BACKEND_PID)"
sleep 3

# 启动前端
echo "2. 启动前端应用..."
open /Applications/FieldMind.app

echo ""
echo "✓ FieldMind 已启动"
echo ""
echo "按 Ctrl+C 停止后端服务"

# 等待用户中断
wait $BACKEND_PID
