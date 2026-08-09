#!/bin/bash

BASE_URL="http://localhost:8000"
PROJECT_ID=1

echo "=========================================="
echo "链路十一测试：知识图谱+编年史"
echo "=========================================="

# 1. 构建知识图谱
echo ""
echo "1️⃣ 构建知识图谱（实体提取+关系抽取）"
curl -s -X POST "$BASE_URL/api/knowledge-graph/build" \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": $PROJECT_ID,
    \"force_rebuild\": false
  }" | jq '.'

echo ""
echo "等待3秒..."
sleep 3

# 2. 获取实体列表
echo ""
echo "2️⃣ 获取提取的实体列表"
curl -s "$BASE_URL/api/knowledge-graph/entities?project_id=$PROJECT_ID&limit=20" | jq '.'

# 3. 获取知识图谱统计
echo ""
echo "3️⃣ 获取知识图谱统计信息"
curl -s "$BASE_URL/api/knowledge-graph/stats?project_id=$PROJECT_ID" | jq '.'

# 4. 获取可视化数据
echo ""
echo "4️⃣ 获取知识图谱可视化数据（vis-network格式）"
curl -s "$BASE_URL/api/knowledge-graph/visualize?project_id=$PROJECT_ID&limit=50" | jq '.stats'

# 5. 构建时间线
echo ""
echo "5️⃣ 构建时间线（提取时间事件）"
curl -s -X POST "$BASE_URL/api/timeline/build" \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": $PROJECT_ID,
    \"force_rebuild\": false
  }" | jq '.'

echo ""
echo "等待2秒..."
sleep 2

# 6. 获取时间线事件
echo ""
echo "6️⃣ 获取时间线事件列表"
curl -s "$BASE_URL/api/timeline/events?project_id=$PROJECT_ID&limit=10" | jq '.'

# 7. 获取时间线统计
echo ""
echo "7️⃣ 获取时间线统计信息"
curl -s "$BASE_URL/api/timeline/stats?project_id=$PROJECT_ID" | jq '.'

echo ""
echo "=========================================="
echo "✅ 链路十一测试完成"
echo "=========================================="
