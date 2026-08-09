#!/bin/bash

# 知识脉络分析系统 v2.0 - 停止脚本

echo "=========================================="
echo "  停止知识脉络分析系统"
echo "=========================================="
echo ""

# 停止后端 (端口 8000)
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "停止后端服务..."
    kill $(lsof -t -i:8000)
    echo "✓ 后端已停止"
else
    echo "○ 后端未运行"
fi

# 停止前端 (端口 8080)
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "停止前端服务..."
    kill $(lsof -t -i:8080)
    echo "✓ 前端已停止"
else
    echo "○ 前端未运行"
fi

# 停止 Celery Worker
if pgrep -f "celery.*worker" > /dev/null ; then
    echo "停止 Celery Worker..."
    pkill -f "celery.*worker"
    echo "✓ Celery Worker 已停止"
else
    echo "○ Celery Worker 未运行"
fi

# 停止 Celery Beat
if pgrep -f "celery.*beat" > /dev/null ; then
    echo "停止 Celery Beat..."
    pkill -f "celery.*beat"
    echo "✓ Celery Beat 已停止"
else
    echo "○ Celery Beat 未运行"
fi

echo ""
echo "=========================================="
echo "  所有服务已停止"
echo "=========================================="
