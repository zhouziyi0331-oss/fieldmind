#!/bin/bash

BASE_URL="http://localhost:8000"
PROJECT_ID=1
DOCUMENT_ID=1

echo "=========================================="
echo "链路十二测试：工作流编排"
echo "=========================================="

# 1. 列出工作流模板
echo ""
echo "1️⃣ 列出可用的工作流模板"
curl -s "$BASE_URL/api/workflows/templates/list" | jq '.'

# 2. 执行文档处理工作流
echo ""
echo "2️⃣ 执行文档处理工作流"
WORKFLOW_RESULT=$(curl -s -X POST "$BASE_URL/api/workflows/execute" \
  -H "Content-Type: application/json" \
  -d "{
    \"workflow_type\": \"document_processing\",
    \"project_id\": $PROJECT_ID,
    \"document_ids\": [$DOCUMENT_ID]
  }")

echo "$WORKFLOW_RESULT" | jq '.'
WORKFLOW_ID=$(echo "$WORKFLOW_RESULT" | jq -r '.workflow_id')

echo ""
echo "工作流ID: $WORKFLOW_ID"

# 3. 查询工作流状态
echo ""
echo "3️⃣ 查询工作流执行状态"
sleep 2
curl -s "$BASE_URL/api/workflows/$WORKFLOW_ID" | jq '.'

# 4. 执行知识图谱构建工作流
echo ""
echo "4️⃣ 执行知识图谱构建工作流"
KG_RESULT=$(curl -s -X POST "$BASE_URL/api/workflows/execute" \
  -H "Content-Type: application/json" \
  -d "{
    \"workflow_type\": \"knowledge_graph\",
    \"project_id\": $PROJECT_ID
  }")

echo "$KG_RESULT" | jq '.'
KG_WORKFLOW_ID=$(echo "$KG_RESULT" | jq -r '.workflow_id')

# 5. 查询知识图谱工作流状态
echo ""
echo "5️⃣ 查询知识图谱工作流状态"
sleep 3
curl -s "$BASE_URL/api/workflows/$KG_WORKFLOW_ID" | jq '.'

# 6. 执行完整分析工作流
echo ""
echo "6️⃣ 执行完整分析工作流"
FULL_RESULT=$(curl -s -X POST "$BASE_URL/api/workflows/execute" \
  -H "Content-Type: application/json" \
  -d "{
    \"workflow_type\": \"full_analysis\",
    \"project_id\": $PROJECT_ID
  }")

echo "$FULL_RESULT" | jq '.'

# 7. 列出所有工作流
echo ""
echo "7️⃣ 列出所有工作流执行记录"
curl -s "$BASE_URL/api/workflows/?limit=10" | jq '.'

# 8. 获取工作流统计
echo ""
echo "8️⃣ 获取工作流系统统计信息"
curl -s "$BASE_URL/api/workflows/stats" | jq '.'

# 9. 快捷接口测试
echo ""
echo "9️⃣ 测试快捷接口 - 快速构建知识图谱"
curl -s -X POST "$BASE_URL/api/workflows/quick/knowledge-graph?project_id=$PROJECT_ID" | jq '.'

echo ""
echo "=========================================="
echo "✅ 链路十二测试完成"
echo "=========================================="
