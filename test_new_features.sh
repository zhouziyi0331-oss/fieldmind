#!/bin/bash

# FieldMind 新功能测试脚本
# 测试知识图谱和时间线功能

echo "========================================="
echo "FieldMind 新功能测试"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查后端服务
echo "📡 检查后端服务..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ 后端服务运行正常${NC}"
else
    echo -e "${RED}❌ 后端服务未运行${NC}"
    exit 1
fi

echo ""

# 测试项目列表
echo "📊 获取项目列表..."
PROJECTS=$(curl -s http://localhost:8000/api/projects)
PROJECT_COUNT=$(echo $PROJECTS | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
echo -e "${GREEN}✅ 找到 $PROJECT_COUNT 个项目${NC}"

# 选择测试项目（使用项目ID 2）
TEST_PROJECT_ID=2

echo ""
echo "========================================="
echo "测试知识图谱功能"
echo "========================================="

# 测试知识图谱
echo ""
echo "🌳 测试项目 $TEST_PROJECT_ID 的知识图谱..."
GRAPH_DATA=$(curl -s http://localhost:8000/api/knowledge-graph/projects/$TEST_PROJECT_ID/graph)

if echo $GRAPH_DATA | grep -q "nodes"; then
    NODE_COUNT=$(echo $GRAPH_DATA | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['statistics']['total_nodes'])" 2>/dev/null || echo "0")
    EDGE_COUNT=$(echo $GRAPH_DATA | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['statistics']['total_edges'])" 2>/dev/null || echo "0")
    echo -e "${GREEN}✅ 知识图谱构建成功${NC}"
    echo "   节点数: $NODE_COUNT"
    echo "   边数: $EDGE_COUNT"

    # 显示节点类型分布
    echo "   节点类型分布:"
    echo $GRAPH_DATA | python3 -c "import sys, json; data=json.load(sys.stdin); [print(f'     - {k}: {v}') for k, v in data['statistics']['node_types'].items()]" 2>/dev/null
else
    echo -e "${YELLOW}⚠️  知识图谱为空或出错${NC}"
fi

# 测试关键词提取
echo ""
echo "🔑 测试项目 $TEST_PROJECT_ID 的关键词提取..."
KEYWORDS=$(curl -s http://localhost:8000/api/knowledge-graph/projects/$TEST_PROJECT_ID/keywords?top_k=10)

if echo $KEYWORDS | grep -q "text"; then
    KEYWORD_COUNT=$(echo $KEYWORDS | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo -e "${GREEN}✅ 关键词提取成功${NC}"
    echo "   关键词数: $KEYWORD_COUNT"
    echo "   前5个关键词:"
    echo $KEYWORDS | python3 -c "import sys, json; data=json.load(sys.stdin); [print(f'     - {item[\"text\"]}') for item in data[:5]]" 2>/dev/null
else
    echo -e "${YELLOW}⚠️  关键词为空或出错${NC}"
fi

echo ""
echo "========================================="
echo "测试时间线功能"
echo "========================================="

# 测试时间线
echo ""
echo "⏱️  测试项目 $TEST_PROJECT_ID 的时间线..."
TIMELINE_DATA=$(curl -s http://localhost:8000/api/timeline/projects/$TEST_PROJECT_ID/events)

if echo $TIMELINE_DATA | grep -q "events"; then
    EVENT_COUNT=$(echo $TIMELINE_DATA | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['statistics']['total_events'])" 2>/dev/null || echo "0")
    echo -e "${GREEN}✅ 时间线查询成功${NC}"
    echo "   事件数: $EVENT_COUNT"

    if [ "$EVENT_COUNT" -gt "0" ]; then
        echo "   时间范围:"
        echo $TIMELINE_DATA | python3 -c "import sys, json; data=json.load(sys.stdin); dr=data['statistics']['date_range']; print(f'     起: {dr[\"start\"]}') if dr else None; print(f'     止: {dr[\"end\"]}') if dr else None" 2>/dev/null

        echo "   前3个事件:"
        echo $TIMELINE_DATA | python3 -c "import sys, json; data=json.load(sys.stdin); [print(f'     - {e[\"date_string\"]}: {e[\"description\"][:50]}...') for e in data['events'][:3]]" 2>/dev/null
    else
        echo -e "${YELLOW}   ℹ️  该项目暂无时间事件（文档中未包含日期信息）${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  时间线为空或出错${NC}"
fi

# 测试分组时间线
echo ""
echo "📅 测试分组时间线（按年份）..."
GROUPED_DATA=$(curl -s http://localhost:8000/api/timeline/projects/$TEST_PROJECT_ID/events/grouped?group_by=year)

if echo $GROUPED_DATA | grep -q "groups"; then
    GROUP_COUNT=$(echo $GROUPED_DATA | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['groups']))" 2>/dev/null || echo "0")
    echo -e "${GREEN}✅ 分组时间线查询成功${NC}"
    echo "   分组数: $GROUP_COUNT"
else
    echo -e "${YELLOW}⚠️  分组时间线为空或出错${NC}"
fi

echo ""
echo "========================================="
echo "测试前端集成"
echo "========================================="

echo ""
echo "🌐 检查前端服务..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 前端服务运行正常${NC}"
else
    echo -e "${RED}❌ 前端服务未运行${NC}"
fi

echo ""
echo "========================================="
echo "测试完成"
echo "========================================="
echo ""
echo "📌 访问链接:"
echo "   前端界面: http://localhost:3000"
echo "   知识图谱: http://localhost:3000/projects/$TEST_PROJECT_ID/knowledge-graph"
echo "   时间线: http://localhost:3000/projects/$TEST_PROJECT_ID/timeline"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "✨ 所有核心功能测试完成！"
