#!/bin/bash

# FieldMind 知识脉络和业态分析测试脚本

BASE_URL="http://localhost:8000"
PROJECT_ID=1

echo "========================================="
echo "FieldMind 知识脉络和业态分析测试"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试函数
test_api() {
    local name=$1
    local url=$2
    local method=${3:-GET}

    echo -n "测试 $name ... "

    if [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
            -H "Content-Type: application/json" \
            -d '{}')
    else
        response=$(curl -s -w "\n%{http_code}" "$url")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ 成功${NC} (HTTP $http_code)"
        return 0
    else
        echo -e "${RED}✗ 失败${NC} (HTTP $http_code)"
        echo "响应内容: $body"
        return 1
    fi
}

# 1. 测试数据增强状态
echo "1. 检查数据增强状态"
test_api "数据增强状态" "${BASE_URL}/api/v1/projects/${PROJECT_ID}/enrichment-status"
echo ""

# 2. 执行数据增强（如果需要）
echo "2. 执行数据增强"
test_api "数据增强" "${BASE_URL}/api/v1/projects/${PROJECT_ID}/enrich" "POST"
echo ""

# 等待数据增强完成
echo "等待数据处理完成..."
sleep 3
echo ""

# 3. 测试知识脉络API
echo "3. 测试知识脉络 API"
test_api "知识网络全景" "${BASE_URL}/api/v1/projects/${PROJECT_ID}/knowledge-network"
echo ""

# 4. 测试节点详情
echo "4. 测试节点详情 API"
test_api "节点详情(节点1)" "${BASE_URL}/api/v1/projects/${PROJECT_ID}/knowledge-network/nodes/1"
echo ""

# 5. 测试现有业态
echo "5. 测试现有业态分析 API"
test_api "现有业态" "${BASE_URL}/api/v1/projects/${PROJECT_ID}/business-analysis/existing"
echo ""

# 6. 测试可能业态
echo "6. 测试可能业态推演 API"
test_api "可能业态" "${BASE_URL}/api/v1/projects/${PROJECT_ID}/business-analysis/potential"
echo ""

# 7. 测试AI评估
echo "7. 测试 AI 综合评估 API"
curl -s -X POST "${BASE_URL}/api/v1/projects/${PROJECT_ID}/business-analysis/ai-evaluation" \
    -H "Content-Type: application/json" \
    -d '{
        "business_type": "existing",
        "business_name": "传统农业"
    }' | python3 -m json.tool > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ AI评估 API 成功${NC}"
else
    echo -e "${RED}✗ AI评估 API 失败${NC}"
fi
echo ""

# 8. 获取详细数据示例
echo "========================================="
echo "获取知识网络数据（前5个节点）"
echo "========================================="
curl -s "${BASE_URL}/api/v1/projects/${PROJECT_ID}/knowledge-network" | \
    python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    stats = data['data']['statistics']
    nodes = data['data']['nodes'][:5]

    print('统计数据:')
    print(f\"  大脉络: {stats['dimension_count']}\")
    print(f\"  子脉络: {stats['sub_dimension_count']}\")
    print(f\"  支撑材料: {stats['material_count']}\")
    print(f\"  关键词: {stats['keyword_count']}\")
    print()
    print('节点列表（前5个）:')
    for node in nodes:
        print(f\"  [{node['id']}] {node['name']} - {node['material_count']}份材料\")
else:
    print('请求失败:', data.get('message'))
" 2>/dev/null || echo "无法解析数据"
echo ""

echo "========================================="
echo "获取现有业态数据（前3个）"
echo "========================================="
curl -s "${BASE_URL}/api/v1/projects/${PROJECT_ID}/business-analysis/existing" | \
    python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    businesses = data['data']['businesses'][:3]

    print('现有业态:')
    for biz in businesses:
        print(f\"  {biz['name']}: {biz['score']:.1f}分\")
        print(f\"    覆盖度: {biz['coverage']:.1f}% | 情感: {biz['emotion']:.1f}% | 趋势: {biz['trend']:.1f}%\")
        print(f\"    支撑材料: {biz['material_count']}份\")
else:
    print('请求失败:', data.get('message'))
" 2>/dev/null || echo "无法解析数据"
echo ""

echo "========================================="
echo "获取可能业态数据（前3个）"
echo "========================================="
curl -s "${BASE_URL}/api/v1/projects/${PROJECT_ID}/business-analysis/potential" | \
    python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    businesses = data['data']['potential_businesses'][:3]

    print('可能业态:')
    for biz in businesses:
        print(f\"  {biz['name']}: {biz['feasibility_score']:.1f}分\")
        print(f\"    {biz['description']}\")
        print(f\"    关键词频次: {biz['keyword_frequency']} | 政策支持: {biz['policy_support']:.1f}%\")
else:
    print('请求失败:', data.get('message'))
" 2>/dev/null || echo "无法解析数据"
echo ""

echo "========================================="
echo "测试完成！"
echo "========================================="
echo ""
echo "如果所有测试通过，你可以："
echo "1. 访问前端应用查看可视化页面"
echo "2. 点击侧边栏的「知识脉络」查看知识网络"
echo "3. 点击侧边栏的「业态分析」查看业态推演"
echo ""
