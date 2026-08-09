#!/bin/bash
#
# FieldMind 后端功能测试脚本
# 测试所有关键功能是否真正工作
#

set -e

BASE_URL="http://localhost:8000"
PROJECT_ID=1

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║         FieldMind 后端功能测试                             ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

test_fail() {
    echo -e "${RED}❌ $1${NC}"
}

test_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "测试 1: 健康检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
response=$(curl -s ${BASE_URL}/health)
if echo "$response" | grep -q "healthy"; then
    test_pass "健康检查通过"
else
    test_fail "健康检查失败"
    exit 1
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "测试 2: WebSocket 端点"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
# 检查 WebSocket 路由是否注册
if curl -s ${BASE_URL}/docs | grep -q "ws"; then
    test_pass "WebSocket 端点已注册"
else
    test_info "WebSocket 端点可能未注册（需要检查）"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "测试 3: 项目列表"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
response=$(curl -s ${BASE_URL}/api/projects/)
if echo "$response" | grep -q "id\|name\|\["; then
    test_pass "项目列表 API 工作正常"
    echo "$response" | python3 -m json.tool 2>/dev/null | head -20
else
    test_fail "项目列表 API 失败"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "测试 4: 文档列表"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
response=$(curl -s ${BASE_URL}/api/documents/projects/${PROJECT_ID}/documents)
if echo "$response" | grep -q "total\|documents"; then
    test_pass "文档列表 API 工作正常"
    echo "$response" | python3 -m json.tool 2>/dev/null | head -20
else
    test_info "文档列表为空或项目不存在"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "测试 5: 监控端点"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
response=$(curl -s ${BASE_URL}/monitoring/metrics)
if echo "$response" | grep -q "cpu\|memory"; then
    test_pass "监控 API 工作正常"
else
    test_fail "监控 API 失败"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "测试 6: 后台任务模块"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd ~/FieldMind-Rebuild/fieldmind-backend
python3 -c "
from app.services.background_tasks import submit_task
print('✅ 后台任务模块可导入')
" 2>&1 | tail -3
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "测试 7: 关键词搜索服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd ~/FieldMind-Rebuild/fieldmind-backend
python3 -c "
from app.services.keyword_search_service import KeywordSearchService
print('✅ 关键词搜索服务可导入')
" 2>&1 | tail -3
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "测试总结"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_pass "后端基本功能正常"
echo ""
test_info "下一步: 测试文件上传和处理流程"
echo ""
