#!/bin/bash

echo "========================================="
echo "测试新集成的API端点"
echo "========================================="

# 测试1: 知识流水线API
echo -e "\n1. 测试知识流水线状态查询"
curl -s http://localhost:8000/api/knowledge-pipeline/pipelines | jq '.' || echo "失败"

# 测试2: 文档规范化API
echo -e "\n2. 测试文档规范化状态"
curl -s http://localhost:8000/api/api/v1/files/normalization/test-file-id | jq '.' || echo "失败或无数据"

# 测试3: 知识查询API
echo -e "\n3. 测试知识实体查询"
curl -s http://localhost:8000/api/knowledge/entities?limit=5 | jq '.' || echo "失败"

# 测试4: Reader生成API
echo -e "\n4. 测试Reader列表"
curl -s http://localhost:8000/api/reader/readers?limit=5 | jq '.' || echo "失败"

# 测试5: 检查所有路由
echo -e "\n5. 获取所有已注册路由"
curl -s http://localhost:8000/openapi.json | jq '.paths | keys | length'

echo -e "\n========================================="
echo "测试完成"
echo "========================================="
