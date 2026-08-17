#!/bin/bash

# FieldMind 系统停止脚本

echo "🛑 停止 FieldMind 系统..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# 读取保存的 PID
BACKEND_PID=$(cat /tmp/fieldmind_backend.pid 2>/dev/null)
CELERY_PID=$(cat /tmp/fieldmind_celery.pid 2>/dev/null)
FRONTEND_PID=$(cat /tmp/fieldmind_frontend.pid 2>/dev/null)

# 停止后端服务
if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "停止后端服务 (PID: $BACKEND_PID)..."
    kill "$BACKEND_PID"
    echo -e "${GREEN}✓ 后端服务已停止${NC}"
else
    echo "后端服务未运行或已停止"
fi

# 停止 Celery Worker
if [ -n "$CELERY_PID" ] && kill -0 "$CELERY_PID" 2>/dev/null; then
    echo "停止 Celery Worker (PID: $CELERY_PID)..."
    kill "$CELERY_PID"
    echo -e "${GREEN}✓ Celery Worker 已停止${NC}"
else
    echo "Celery Worker 未运行或已停止"
fi

# 停止前端服务
if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo "停止前端服务 (PID: $FRONTEND_PID)..."
    kill "$FRONTEND_PID"
    echo -e "${GREEN}✓ 前端服务已停止${NC}"
else
    echo "前端服务未运行或已停止"
fi

# 清理 PID 文件
rm -f /tmp/fieldmind_backend.pid
rm -f /tmp/fieldmind_celery.pid
rm -f /tmp/fieldmind_frontend.pid

# 查找并停止其他可能的进程
echo ""
echo "检查其他相关进程..."
pkill -f "uvicorn app.main:app" 2>/dev/null && echo "已停止 uvicorn 进程"
pkill -f "celery.*app.celery_app" 2>/dev/null && echo "已停止 celery 进程"
pkill -f "python.*http.server 8080" 2>/dev/null && echo "已停止前端 http.server 进程"

echo ""
echo -e "${GREEN}✅ FieldMind 系统已完全停止${NC}"
