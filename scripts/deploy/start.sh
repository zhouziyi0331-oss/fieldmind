#!/bin/bash
# 系统启动脚本

set -e

echo "==================================="
echo "知识脉络分析系统 - 启动脚本"
echo "==================================="

# 检查 Python 版本
echo ""
echo "检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $python_version"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo "未找到虚拟环境，正在创建..."
    python3 -m venv venv
    echo "✓ 虚拟环境创建成功"
fi

# 激活虚拟环境
echo ""
echo "激活虚拟环境..."
source venv/bin/activate
echo "✓ 虚拟环境已激活"

# 安装依赖
echo ""
echo "检查依赖..."
if [ ! -f ".dependencies_installed" ]; then
    echo "正在安装依赖包..."
    pip install -r requirements.txt
    touch .dependencies_installed
    echo "✓ 依赖安装完成"
else
    echo "✓ 依赖已安装"
fi

# 创建必要的目录
echo ""
echo "创建数据目录..."
mkdir -p data/uploads
mkdir -p data/processed
mkdir -p data/audio_extracts
mkdir -p data/chromadb
mkdir -p data/reports
echo "✓ 目录创建完成"

# 检查环境变量配置
if [ ! -f ".env" ]; then
    echo ""
    echo "警告: 未找到 .env 文件"
    echo "正在从 .env.example 创建 .env..."
    cp .env.example .env
    echo "✓ 已创建 .env 文件，请根据实际情况修改配置"
fi

# 初始化数据库
echo ""
echo "初始化数据库..."
python3 init_db.py
echo "✓ 数据库初始化完成"

# 检查外部服务
echo ""
echo "检查外部服务..."

# 检查 Redis
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✓ Redis 服务正常"
    else
        echo "✗ Redis 服务未运行"
        echo "  请运行: redis-server"
    fi
else
    echo "⚠ Redis 未安装"
fi

# 检查 Neo4j
if command -v neo4j &> /dev/null; then
    if neo4j status &> /dev/null; then
        echo "✓ Neo4j 服务正常"
    else
        echo "✗ Neo4j 服务未运行"
        echo "  请运行: neo4j start"
    fi
else
    echo "⚠ Neo4j 未安装"
fi

# 启动选项
echo ""
echo "==================================="
echo "选择启动模式:"
echo "1) 仅启动 API 服务"
echo "2) 启动 API + Celery Worker"
echo "3) 启动完整系统 (API + Celery Worker + Celery Beat)"
echo "==================================="
read -p "请选择 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "启动 API 服务..."
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
        ;;
    2)
        echo ""
        echo "启动 API 服务和 Celery Worker..."

        # 启动 Celery Worker (后台)
        celery -A app.tasks worker --loglevel=info --logfile=logs/celery_worker.log &
        CELERY_PID=$!
        echo "✓ Celery Worker 已启动 (PID: $CELERY_PID)"

        # 启动 API 服务 (前台)
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

        # 清理
        kill $CELERY_PID 2>/dev/null || true
        ;;
    3)
        echo ""
        echo "启动完整系统..."

        # 创建日志目录
        mkdir -p logs

        # 启动 Celery Worker (后台)
        celery -A app.tasks worker --loglevel=info --logfile=logs/celery_worker.log &
        CELERY_WORKER_PID=$!
        echo "✓ Celery Worker 已启动 (PID: $CELERY_WORKER_PID)"

        # 启动 Celery Beat (后台)
        celery -A app.tasks beat --loglevel=info --logfile=logs/celery_beat.log &
        CELERY_BEAT_PID=$!
        echo "✓ Celery Beat 已启动 (PID: $CELERY_BEAT_PID)"

        # 启动 API 服务 (前台)
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

        # 清理
        kill $CELERY_WORKER_PID 2>/dev/null || true
        kill $CELERY_BEAT_PID 2>/dev/null || true
        ;;
    *)
        echo "无效的选择"
        exit 1
        ;;
esac
