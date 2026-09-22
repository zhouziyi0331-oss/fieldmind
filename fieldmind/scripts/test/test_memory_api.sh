#!/bin/bash
# Mem0 记忆系统API测试脚本

BASE_URL="http://localhost:8000/api/v1"
TOKEN=""

echo "============================================================"
echo "Mem0 记忆系统 API 测试"
echo "============================================================"

# 检查服务状态
echo -e "\n[1] 检查Mem0服务状态..."
curl -s -X GET "$BASE_URL/memory/status" | jq '.'

# 如果有TOKEN，执行认证测试
if [ -n "$TOKEN" ]; then
    echo -e "\n[2] 测试添加用户偏好..."
    curl -s -X POST "$BASE_URL/memory/preferences" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "preference": "用户喜欢详细的学术分析报告",
        "metadata": {"category": "report_style"}
      }' | jq '.'

    echo -e "\n[3] 测试添加项目上下文..."
    curl -s -X POST "$BASE_URL/memory/projects/context" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "project_id": 1,
        "context": "该项目研究十八洞村的山歌文化",
        "metadata": {"research_area": "ethnic_music"}
      }' | jq '.'

    echo -e "\n[4] 测试添加实体记忆..."
    curl -s -X POST "$BASE_URL/memory/entities" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "entity_name": "龙德成",
        "entity_type": "person",
        "description": "十八洞村村长，精准扶贫见证者",
        "project_id": 1
      }' | jq '.'

    echo -e "\n[5] 测试搜索记忆..."
    curl -s -X POST "$BASE_URL/memory/search" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "query": "十八洞村的山歌文化",
        "limit": 5
      }' | jq '.'

    echo -e "\n[6] 测试获取用户档案..."
    curl -s -X GET "$BASE_URL/memory/profile" \
      -H "Authorization: Bearer $TOKEN" | jq '.'
else
    echo -e "\n⚠️  TOKEN未设置，跳过认证测试"
    echo "使用方法："
    echo "  1. 注册/登录获取token"
    echo "  2. 设置TOKEN环境变量: export TOKEN='your_token_here'"
    echo "  3. 重新运行此脚本"
fi

echo -e "\n============================================================"
echo "✅ API测试完成"
echo "============================================================"
echo ""
echo "API文档: http://localhost:8000/docs#/memory"
