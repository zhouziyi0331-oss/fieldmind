#!/bin/bash

echo "========================================="
echo "测试正确的API端点"
echo "========================================="

# 测试1: 知识流水线 - 列表
echo -e "\n1. 知识流水线 - 获取流水线列表"
curl -s http://localhost:8000/knowledge-pipeline/list | jq '.'

# 测试2: 知识查询 - 实体列表
echo -e "\n2. 知识查询 - 获取实体列表"
curl -s http://localhost:8000/knowledge/entities?limit=5 | jq '.'

# 测试3: 知识查询 - 事件列表
echo -e "\n3. 知识查询 - 获取事件列表"
curl -s http://localhost:8000/knowledge/events?limit=5 | jq '.'

# 测试4: Reader路由
echo -e "\n4. Reader路由"
curl -s http://localhost:8000/openapi.json | jq '.paths | keys[]' | grep reader

echo -e "\n========================================="
echo "API测试完成"
echo "========================================="
