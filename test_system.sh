#!/bin/bash
# FieldMind 完整测试脚本 - 验证前后端连接

set -e

echo "========================================="
echo "FieldMind 完整系统测试"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试结果统计
PASSED=0
FAILED=0

# 测试函数
test_step() {
    echo -n "测试: $1 ... "
}

test_pass() {
    echo -e "${GREEN}✓ 通过${NC}"
    ((PASSED++))
}

test_fail() {
    echo -e "${RED}✗ 失败${NC}"
    if [ ! -z "$1" ]; then
        echo "  原因: $1"
    fi
    ((FAILED++))
}

test_skip() {
    echo -e "${YELLOW}⊘ 跳过${NC}"
    if [ ! -z "$1" ]; then
        echo "  原因: $1"
    fi
}

echo "1. 环境检查"
echo "========================================="

# 检查 Docker
test_step "Docker 是否安装"
if command -v docker &> /dev/null; then
    test_pass
else
    test_fail "Docker 未安装"
fi

# 检查 Docker Compose
test_step "Docker Compose 是否安装"
if command -v docker-compose &> /dev/null; then
    test_pass
else
    test_fail "Docker Compose 未安装"
fi

# 检查 Node.js
test_step "Node.js 是否安装"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ 通过${NC} (版本: $NODE_VERSION)"
    ((PASSED++))
else
    test_fail "Node.js 未安装"
fi

# 检查 Python
test_step "Python 是否安装"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ 通过${NC} (版本: $PYTHON_VERSION)"
    ((PASSED++))
else
    test_fail "Python 未安装"
fi

echo ""
echo "2. 配置文件检查"
echo "========================================="

# 检查 .env
test_step ".env 配置文件"
if [ -f ".env" ]; then
    test_pass
else
    test_fail "缺少 .env 文件"
fi

# 检查 .env.production
test_step ".env.production 配置文件"
if [ -f ".env.production" ]; then
    test_pass
else
    test_fail "缺少 .env.production 文件"
fi

# 检查 docker-compose
test_step "docker-compose.yml"
if [ -f "docker-compose.yml" ]; then
    test_pass
else
    test_fail "缺少 docker-compose.yml"
fi

# 检查前端配置
test_step "前端 package.json"
if [ -f "frontend/package.json" ]; then
    test_pass
else
    test_fail "缺少 frontend/package.json"
fi

echo ""
echo "3. 后端检查"
echo "========================================="

# 检查后端文件
test_step "后端主文件 (main.py)"
if [ -f "main.py" ]; then
    test_pass
else
    test_fail "缺少 main.py"
fi

# 检查数据库模型
test_step "数据库模型目录"
if [ -d "backend/src/app/models" ]; then
    MODEL_COUNT=$(ls -1 backend/src/app/models/*.py 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${GREEN}✓ 通过${NC} (${MODEL_COUNT} 个模型文件)"
    ((PASSED++))
else
    test_fail "缺少 models 目录"
fi

# 检查 API 端点
test_step "API 端点目录"
if [ -d "app/api/v1" ]; then
    API_COUNT=$(ls -1 app/api/v1/*.py 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${GREEN}✓ 通过${NC} (${API_COUNT} 个 API 模块)"
    ((PASSED++))
else
    test_fail "缺少 api/v1 目录"
fi

echo ""
echo "4. 前端检查"
echo "========================================="

# 检查前端页面
test_step "前端页面组件"
if [ -d "frontend/src/pages" ]; then
    PAGE_COUNT=$(ls -1 frontend/src/pages/*.tsx 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${GREEN}✓ 通过${NC} (${PAGE_COUNT} 个页面)"
    ((PASSED++))
else
    test_fail "缺少 pages 目录"
fi

# 检查前端服务
test_step "前端 API 服务"
if [ -f "frontend/src/services/api.ts" ]; then
    test_pass
else
    test_fail "缺少 api.ts"
fi

# 检查前端路由
test_step "前端路由配置"
if [ -f "frontend/src/App.tsx" ]; then
    test_pass
else
    test_fail "缺少 App.tsx"
fi

echo ""
echo "5. macOS 原生应用检查"
echo "========================================="

# 检查原生应用
test_step "macOS .app 包"
if [ -d "$HOME/Desktop/FieldMind_Apps/FieldMind.app" ]; then
    test_pass
else
    test_fail ".app 包不存在"
fi

# 检查 Swift 源代码
test_step "Swift 源代码"
if [ -d "frontend/fieldmind-native/Sources" ]; then
    SWIFT_COUNT=$(find frontend/fieldmind-native/Sources -name "*.swift" | wc -l | tr -d ' ')
    echo -e "${GREEN}✓ 通过${NC} (${SWIFT_COUNT} 个 Swift 文件)"
    ((PASSED++))
else
    test_fail "缺少 Swift 源代码"
fi

echo ""
echo "6. 基础设施检查"
echo "========================================="

# 检查迁移脚本
test_step "数据库迁移配置"
if [ -f "migrations/env.py" ]; then
    test_pass
else
    test_fail "缺少迁移配置"
fi

# 检查初始化脚本
test_step "数据库初始化脚本"
if [ -f "backend/init_db.py" ]; then
    test_pass
else
    test_fail "缺少初始化脚本"
fi

# 检查 Nginx 配置
test_step "Nginx 配置文件"
if [ -f "nginx/nginx.conf" ]; then
    test_pass
else
    test_skip "nginx.conf 不存在 (可选)"
fi

# 检查监控配置
test_step "Prometheus 配置"
if [ -f "monitoring/prometheus.yml" ]; then
    test_pass
else
    test_skip "prometheus.yml 不存在 (可选)"
fi

echo ""
echo "7. Docker 服务状态"
echo "========================================="

# 检查 Docker 是否运行
test_step "Docker 守护进程"
if docker info &> /dev/null; then
    test_pass
else
    test_fail "Docker 未运行"
fi

# 检查容器状态
test_step "FieldMind 容器状态"
RUNNING_CONTAINERS=$(docker ps --filter "name=fieldmind" --format "{{.Names}}" | wc -l | tr -d ' ')
if [ "$RUNNING_CONTAINERS" -gt "0" ]; then
    echo -e "${GREEN}✓ 运行中${NC} (${RUNNING_CONTAINERS} 个容器)"
    ((PASSED++))
else
    test_skip "没有运行的容器"
fi

echo ""
echo "========================================="
echo "测试总结"
echo "========================================="
TOTAL=$((PASSED + FAILED))
echo -e "总计: ${TOTAL} 项测试"
echo -e "${GREEN}通过: ${PASSED}${NC}"
echo -e "${RED}失败: ${FAILED}${NC}"
echo ""

# 成功率
if [ $TOTAL -gt 0 ]; then
    SUCCESS_RATE=$((PASSED * 100 / TOTAL))
    echo "成功率: ${SUCCESS_RATE}%"
    echo ""
fi

# 给出建议
if [ $FAILED -gt 0 ]; then
    echo "⚠️  发现问题，建议:"
    echo "  1. 检查失败的测试项"
    echo "  2. 运行 ./setup_production.sh 完成初始化"
    echo "  3. 检查依赖是否安装完整"
    echo ""
    exit 1
else
    echo "✓ 所有测试通过!"
    echo ""
    echo "系统状态: 就绪 ✓"
    echo ""
    echo "下一步:"
    echo "  • 启动开发环境: docker-compose up -d"
    echo "  • 启动生产环境: ./start.sh"
    echo "  • 打开 macOS 应用: open ~/Desktop/FieldMind_Apps/FieldMind.app"
    echo ""
fi
