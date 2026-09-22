#!/bin/bash

# FieldMind 前后端连接测试脚本

echo "=========================================="
echo "FieldMind 前后端连接测试"
echo "=========================================="
echo ""

API_BASE="http://localhost:8000"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试函数
test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}

    echo -n "测试 $name ... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
        echo -e "${GREEN}✓ 成功 ($http_code)${NC}"
        return 0
    else
        echo -e "${RED}✗ 失败 ($http_code)${NC}"
        echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
        return 1
    fi
}

echo "1. 前端资源测试"
echo "----------------------------------------"
test_endpoint "前端页面" "$API_BASE/"
test_endpoint "JavaScript" "$API_BASE/static/app.js"
test_endpoint "CSS样式" "$API_BASE/static/styles.css"
echo ""

echo "2. 系统健康检查"
echo "----------------------------------------"
test_endpoint "健康检查" "$API_BASE/health"
test_endpoint "监控指标" "$API_BASE/api/v1/metrics"
echo ""

echo "3. API 端点测试"
echo "----------------------------------------"
test_endpoint "项目列表" "$API_BASE/api/v1/projects/"
test_endpoint "文档列表" "$API_BASE/api/v1/documents/"
test_endpoint "知识脉络列表" "$API_BASE/api/v1/contexts/"
test_endpoint "对话会话列表" "$API_BASE/api/v1/chat/sessions"
echo ""

echo "4. API 响应格式检查"
echo "----------------------------------------"

echo -n "检查 Projects API 响应格式 ... "
projects_response=$(curl -s "$API_BASE/api/v1/projects/")
if echo "$projects_response" | python3 -c "import sys, json; data=json.load(sys.stdin); sys.exit(0 if 'data' in data or 'projects' in data else 1)" 2>/dev/null; then
    echo -e "${GREEN}✓ 格式正确${NC}"
else
    echo -e "${RED}✗ 格式错误${NC}"
    echo "$projects_response" | python3 -m json.tool
fi

echo -n "检查 Documents API 响应格式 ... "
documents_response=$(curl -s "$API_BASE/api/v1/documents/")
if echo "$documents_response" | python3 -c "import sys, json; data=json.load(sys.stdin); sys.exit(0 if 'documents' in data else 1)" 2>/dev/null; then
    echo -e "${GREEN}✓ 格式正确${NC}"
else
    echo -e "${RED}✗ 格式错误${NC}"
    echo "$documents_response" | python3 -m json.tool
fi

echo -n "检查 Contexts API 响应格式 ... "
contexts_response=$(curl -s "$API_BASE/api/v1/contexts/")
if echo "$contexts_response" | python3 -c "import sys, json; data=json.load(sys.stdin); sys.exit(0 if 'data' in data or 'contexts' in data else 1)" 2>/dev/null; then
    echo -e "${GREEN}✓ 格式正确${NC}"
else
    echo -e "${RED}✗ 格式错误${NC}"
    echo "$contexts_response" | python3 -m json.tool
fi

echo ""

echo "5. 创建测试数据"
echo "----------------------------------------"

echo -n "创建测试项目 ... "
project_response=$(curl -s -X POST "$API_BASE/api/v1/projects/" \
    -H "Content-Type: application/json" \
    -d '{"name":"前端测试项目","description":"用于测试前后端连接"}' \
    -w "\n%{http_code}")

project_http_code=$(echo "$project_response" | tail -n1)
project_body=$(echo "$project_response" | head -n-1)

if [ "$project_http_code" -eq 201 ]; then
    echo -e "${GREEN}✓ 创建成功${NC}"
    project_id=$(echo "$project_body" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
    echo "  项目 ID: $project_id"
else
    echo -e "${RED}✗ 创建失败 ($project_http_code)${NC}"
    echo "$project_body" | python3 -m json.tool 2>/dev/null || echo "$project_body"
fi

echo ""

echo "6. 文档上传测试"
echo "----------------------------------------"

# 创建测试文件
echo "这是一个测试文档，用于验证前后端文档上传功能。" > /tmp/test_document.txt

echo -n "上传测试文档 ... "
upload_response=$(curl -s -X POST "$API_BASE/api/v1/documents/upload" \
    -F "file=@/tmp/test_document.txt" \
    -F "title=前端测试文档" \
    -F "auto_process=true" \
    -w "\n%{http_code}")

upload_http_code=$(echo "$upload_response" | tail -n1)
upload_body=$(echo "$upload_response" | head -n-1)

if [ "$upload_http_code" -eq 201 ]; then
    echo -e "${GREEN}✓ 上传成功${NC}"
    doc_id=$(echo "$upload_body" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
    echo "  文档 ID: $doc_id"
else
    echo -e "${RED}✗ 上传失败 ($upload_http_code)${NC}"
    echo "$upload_body" | python3 -m json.tool 2>/dev/null || echo "$upload_body"
fi

# 清理测试文件
rm -f /tmp/test_document.txt

echo ""

echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""
echo "浏览器测试："
echo "1. 打开 http://localhost:8000/"
echo "2. 登录（用户名: demo, 密码: demo123）"
echo "3. 测试以下功能："
echo "   - 点击「新建项目」"
echo "   - 点击「上传文档」"
echo "   - 点击「创建脉络」"
echo "   - 发送对话消息"
echo ""
echo "开发者工具检查："
echo "- 按 F12 打开开发者工具"
echo "- 查看 Console 标签页的错误信息"
echo "- 查看 Network 标签页的请求响应"
echo ""
