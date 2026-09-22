#!/bin/bash

# FieldMind 知识脉络和业态分析 - 快速启动脚本

echo "========================================="
echo "FieldMind 知识脉络和业态分析系统"
echo "快速启动脚本"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/alwan/FieldMind"
BACKEND_DIR="$PROJECT_ROOT/backend/src"

# 检查是否已经启动
check_server() {
    curl -s http://localhost:8000/docs > /dev/null 2>&1
    return $?
}

echo -e "${BLUE}步骤 1/4: 检查后端服务状态${NC}"
if check_server; then
    echo -e "${GREEN}✓ 后端服务已启动${NC}"
    echo ""
else
    echo -e "${YELLOW}○ 后端服务未启动，正在启动...${NC}"

    # 启动后端服务
    cd "$BACKEND_DIR"

    # 检查依赖
    echo "检查 Python 依赖..."
    pip list | grep -q jieba
    if [ $? -ne 0 ]; then
        echo "安装 jieba..."
        pip install jieba -q
    fi

    # 后台启动服务
    nohup python api_server.py > "$PROJECT_ROOT/backend_server.log" 2>&1 &
    SERVER_PID=$!

    echo "等待服务启动..."
    for i in {1..10}; do
        sleep 2
        if check_server; then
            echo -e "${GREEN}✓ 后端服务启动成功 (PID: $SERVER_PID)${NC}"
            echo "  日志文件: $PROJECT_ROOT/backend_server.log"
            break
        fi
        echo -n "."
    done

    if ! check_server; then
        echo -e "${RED}✗ 后端服务启动失败，请检查日志${NC}"
        echo "  日志文件: $PROJECT_ROOT/backend_server.log"
        exit 1
    fi
    echo ""
fi

echo -e "${BLUE}步骤 2/4: 初始化示例数据${NC}"
echo "为项目 1 创建示例数据..."

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/projects/1/enrich)
SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

if [ "$SUCCESS" = "True" ]; then
    echo -e "${GREEN}✓ 数据初始化成功${NC}"

    # 显示统计信息
    echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    result = data['data']
    print(f\"  创建的示例 chunks: {result.get('created_chunks', 0)}\")
    stats = result.get('enrichment_stats', {})
    print(f\"  增强的 chunks: {stats.get('enriched', 0)}/{stats.get('total', 0)}\")
" 2>/dev/null
else
    echo -e "${YELLOW}○ 数据可能已存在，跳过初始化${NC}"
fi
echo ""

echo -e "${BLUE}步骤 3/4: 验证 API 功能${NC}"

# 测试知识脉络 API
echo -n "测试知识脉络 API... "
RESPONSE=$(curl -s http://localhost:8000/api/v1/projects/1/knowledge-network)
SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

if [ "$SUCCESS" = "True" ]; then
    echo -e "${GREEN}✓${NC}"

    # 显示统计
    echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    stats = data['data']['statistics']
    print(f\"    大脉络: {stats['dimension_count']} | 子脉络: {stats['sub_dimension_count']}\")
    print(f\"    材料: {stats['material_count']} | 关键词: {stats['keyword_count']}\")
" 2>/dev/null
else
    echo -e "${RED}✗${NC}"
fi

# 测试业态分析 API
echo -n "测试业态分析 API... "
RESPONSE=$(curl -s http://localhost:8000/api/v1/projects/1/business-analysis/existing)
SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

if [ "$SUCCESS" = "True" ]; then
    echo -e "${GREEN}✓${NC}"

    # 显示业态数量
    echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    businesses = data['data']['businesses']
    print(f\"    现有业态: {len(businesses)} 个\")
    if businesses:
        top = businesses[0]
        print(f\"    Top 1: {top['name']} ({top['score']:.1f}分)\")
" 2>/dev/null
else
    echo -e "${RED}✗${NC}"
fi
echo ""

echo -e "${BLUE}步骤 4/4: 系统信息${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✓ 系统启动完成！${NC}"
echo ""
echo "🌐 访问地址:"
echo "  • API 文档: ${BLUE}http://localhost:8000/docs${NC}"
echo "  • 知识脉络: ${BLUE}http://localhost:8000/api/v1/projects/1/knowledge-network${NC}"
echo "  • 业态分析: ${BLUE}http://localhost:8000/api/v1/projects/1/business-analysis/existing${NC}"
echo ""
echo "📱 前端应用:"
echo "  • 打开 FieldMind 应用"
echo "  • 点击侧边栏「知识脉络」查看知识网络"
echo "  • 点击侧边栏「业态分析」查看业态推演"
echo ""
echo "🧪 测试命令:"
echo "  • 完整测试: ${YELLOW}./test_knowledge_business.sh${NC}"
echo "  • 停止服务: ${YELLOW}pkill -f api_server.py${NC}"
echo ""
echo "📖 完整文档:"
echo "  • ${YELLOW}KNOWLEDGE_BUSINESS_GUIDE.md${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
