#!/bin/bash

echo "正在停止 FieldMind..."
echo ""

# 停止前端应用
echo "1. 停止前端应用..."
pkill -f "FieldMind.app/Contents/MacOS"
if [ $? -eq 0 ]; then
    echo "   ✓ 前端已停止"
else
    echo "   前端未运行"
fi

# 停止后端服务
echo "2. 停止后端服务..."
pkill -f "uvicorn app.main:app"
if [ $? -eq 0 ]; then
    echo "   ✓ 后端已停止"
else
    echo "   后端未运行"
fi

echo ""
echo "✓ FieldMind 已完全停止"
