#!/bin/bash
# FieldMind 停止脚本

echo "停止 FieldMind..."

# 停止后端
pkill -f "python -m app.main"

# 停止桌面应用
pkill -f "FieldMind"

echo "✓ FieldMind 已停止"
