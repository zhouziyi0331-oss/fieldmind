#!/bin/bash

# FieldMind 系统启动脚本

echo "🚀 启动 FieldMind 完整系统..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在正确的目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 1. 检查 Redis
echo -e "${BLUE}📦 检查 Redis...${NC}"
if ! pgrep -x "redis-server" > /dev/null; then
    echo "启动 Redis..."
    brew services start redis 2>/dev/null || redis-server --daemonize yes
    sleep 2
else
    echo -e "${GREEN}✓ Redis 已运行${NC}"
fi

# 2. 检查 PostgreSQL (可选)
echo ""
echo -e "${BLUE}🗄️  检查 PostgreSQL...${NC}"
if command -v psql &> /dev/null; then
    if ! pgrep -x "postgres" > /dev/null; then
        echo "启动 PostgreSQL..."
        brew services start postgresql 2>/dev/null || true
        sleep 3
    else
        echo -e "${GREEN}✓ PostgreSQL 已运行${NC}"
    fi
else
    echo -e "${YELLOW}! PostgreSQL 未安装，将使用 SQLite${NC}"
fi

# 3. 激活虚拟环境
echo ""
echo -e "${BLUE}🐍 激活 Python 虚拟环境...${NC}"
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ 虚拟环境已激活${NC}"
else
    echo -e "${YELLOW}! 虚拟环境不存在，正在创建...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r fieldmind-backend/requirements.txt
fi

# 4. 初始化数据库
echo ""
echo -e "${BLUE}🔧 初始化数据库...${NC}"
cd fieldmind-backend
if [ ! -f "data/fieldmind.db" ]; then
    echo "创建数据库表..."
    python init_db.py
    echo -e "${GREEN}✓ 数据库初始化完成${NC}"
else
    echo -e "${GREEN}✓ 数据库已存在${NC}"
fi

# 5. 启动后端服务
echo ""
echo -e "${BLUE}🌐 启动后端 API 服务...${NC}"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo -e "${GREEN}✓ 后端服务启动中... (PID: $BACKEND_PID)${NC}"

# 等待后端启动
sleep 5

# 6. 启动 Celery Worker (可选)
echo ""
echo -e "${BLUE}⚙️  启动 Celery Worker...${NC}"
celery -A app.celery_app worker --loglevel=info &
CELERY_PID=$!
echo -e "${GREEN}✓ Celery Worker 启动中... (PID: $CELERY_PID)${NC}"

# 返回根目录
cd ..

# 7. 启动 Web 前端
echo ""
echo -e "${BLUE}🖥️  启动 Web 前端...${NC}"
cd frontend 2>/dev/null || mkdir -p frontend
if [ -f "index.html" ]; then
    python3 -m http.server 8080 &
    FRONTEND_PID=$!
    echo -e "${GREEN}✓ Web 前端启动中... (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${YELLOW}! 前端文件不存在${NC}"
    FRONTEND_PID=""
fi

cd ..

# 8. 显示系统信息
echo ""
echo "================================================"
echo -e "${GREEN}✅ FieldMind 系统启动完成！${NC}"
echo "================================================"
echo ""
echo "📡 服务访问地址："
echo "   后端 API: http://localhost:8000"
echo "   API 文档: http://localhost:8000/docs"
echo "   Web 前端: http://localhost:8080"
echo ""
echo "🍎 macOS 应用启动命令："
echo "   cd ~/Desktop/FieldMindApp && swift run"
echo ""
echo "📊 默认登录账号："
echo "   用户名: demo"
echo "   密码: demo123"
echo ""
echo "⚙️  运行中的进程："
echo "   后端服务 PID: $BACKEND_PID"
echo "   Celery Worker PID: $CELERY_PID"
if [ -n "$FRONTEND_PID" ]; then
    echo "   前端服务 PID: $FRONTEND_PID"
fi
echo ""
echo "🛑 停止所有服务："
echo "   ./stop_system.sh"
echo ""
echo "按 Ctrl+C 停止监控（服务将继续在后台运行）"
echo ""

# 保存 PID 到文件
echo "$BACKEND_PID" > /tmp/fieldmind_backend.pid
echo "$CELERY_PID" > /tmp/fieldmind_celery.pid
if [ -n "$FRONTEND_PID" ]; then
    echo "$FRONTEND_PID" > /tmp/fieldmind_frontend.pid
fi

# 监控日志（可选）
echo "📝 实时日志输出："
echo ""
tail -f fieldmind-backend/logs/app.log 2>/dev/null || echo "等待日志生成..."
