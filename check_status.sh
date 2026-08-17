#!/bin/bash

# FieldMind 系统状态检查脚本

echo "🔍 检查 FieldMind 系统状态..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 检查函数
check_service() {
    local service_name=$1
    local process_name=$2
    local port=$3

    echo -e "${BLUE}━━━ $service_name ━━━${NC}"

    # 检查进程
    if pgrep -f "$process_name" > /dev/null; then
        local pid=$(pgrep -f "$process_name" | head -1)
        echo -e "进程状态: ${GREEN}✓ 运行中${NC} (PID: $pid)"
    else
        echo -e "进程状态: ${RED}✗ 未运行${NC}"
    fi

    # 检查端口
    if [ -n "$port" ]; then
        if lsof -i :"$port" > /dev/null 2>&1; then
            echo -e "端口 $port: ${GREEN}✓ 监听中${NC}"
        else
            echo -e "端口 $port: ${RED}✗ 未监听${NC}"
        fi
    fi

    echo ""
}

# 检查 URL 可访问性
check_url() {
    local url=$1
    local name=$2

    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|401\|404"; then
        echo -e "$name: ${GREEN}✓ 可访问${NC} ($url)"
    else
        echo -e "$name: ${RED}✗ 无法访问${NC} ($url)"
    fi
}

# 1. 检查 Redis
check_service "Redis" "redis-server" "6379"

# 2. 检查 PostgreSQL
if command -v psql &> /dev/null; then
    check_service "PostgreSQL" "postgres" "5432"
else
    echo -e "${BLUE}━━━ PostgreSQL ━━━${NC}"
    echo -e "状态: ${YELLOW}! 未安装（使用 SQLite）${NC}"
    echo ""
fi

# 3. 检查后端服务
check_service "后端 API (FastAPI)" "uvicorn app.main:app" "8000"
check_url "http://localhost:8000/health" "健康检查"
check_url "http://localhost:8000/docs" "API 文档"

# 4. 检查 Celery Worker
check_service "Celery Worker" "celery.*app.celery_app" ""

# 5. 检查 Web 前端
check_service "Web 前端" "python.*http.server 8080" "8080"
check_url "http://localhost:8080" "前端页面"

# 6. 检查磁盘空间
echo -e "${BLUE}━━━ 系统资源 ━━━${NC}"
df -h ~/FieldMind-Rebuild | tail -1 | awk '{print "磁盘空间: " $4 " 可用 / " $2 " 总计"}'

# 7. 检查数据库文件
if [ -f ~/FieldMind-Rebuild/fieldmind-backend/data/fieldmind.db ]; then
    db_size=$(du -h ~/FieldMind-Rebuild/fieldmind-backend/data/fieldmind.db | cut -f1)
    echo -e "数据库大小: ${GREEN}$db_size${NC}"
else
    echo -e "数据库: ${YELLOW}! 未创建${NC}"
fi

echo ""

# 8. macOS 应用状态
echo -e "${BLUE}━━━ macOS 应用 ━━━${NC}"
if [ -d ~/Desktop/FieldMindApp ]; then
    if [ -f ~/Desktop/FieldMindApp/.build/debug/FieldMind ]; then
        app_size=$(du -h ~/Desktop/FieldMindApp/.build/debug/FieldMind | cut -f1)
        echo -e "编译状态: ${GREEN}✓ 已编译${NC} ($app_size)"
        echo "启动命令: cd ~/Desktop/FieldMindApp && swift run"
    else
        echo -e "编译状态: ${YELLOW}! 未编译或编译中${NC}"
        echo "编译命令: cd ~/Desktop/FieldMindApp && swift build"
    fi
else
    echo -e "应用状态: ${RED}✗ 目录不存在${NC}"
fi

echo ""

# 9. 显示最近的日志
echo -e "${BLUE}━━━ 最近日志 ━━━${NC}"
if [ -f ~/FieldMind-Rebuild/fieldmind-backend/logs/app.log ]; then
    echo "最后 5 条日志:"
    tail -5 ~/FieldMind-Rebuild/fieldmind-backend/logs/app.log
else
    echo -e "${YELLOW}! 日志文件不存在${NC}"
fi

echo ""
echo "================================================"
echo "完整日志查看: tail -f ~/FieldMind-Rebuild/fieldmind-backend/logs/app.log"
echo "================================================"
