#!/bin/bash

echo "========================================="
echo "测试修复后的API端点"
echo "========================================="

# 测试1: 知识流水线API
echo -e "\n1. 知识流水线 - 获取所有流水线"
curl -s http://localhost:8000/api/knowledge-pipeline/pipelines | jq '.' 2>/dev/null || echo "需要认证或无数据"

# 测试2: 文档规范化API
echo -e "\n2. 文档规范化 - 获取规范化进度"
curl -s http://localhost:8000/api/v1/files/test-id/normalization-progress | jq '.' 2>/dev/null || echo "文件不存在（正常）"

# 测试3: 知识查询API - 实体查询
echo -e "\n3. 知识查询 - 查询实体（需要认证）"
curl -s http://localhost:8000/api/knowledge/entities?limit=5 | jq '.' 2>/dev/null

# 测试4: Reader生成API
echo -e "\n4. Reader - 获取Reader列表（需要认证）"
curl -s http://localhost:8000/api/reader/readers?limit=5 | jq '.' 2>/dev/null

# 测试5: 检查路由数量
echo -e "\n5. 统计API路由数量"
TOTAL=$(curl -s http://localhost:8000/openapi.json | jq '.paths | keys | length')
echo "总路由数: $TOTAL"

# 测试6: 验证没有双重前缀
echo -e "\n6. 检查是否存在双重前缀问题"
DOUBLE_PREFIX=$(curl -s http://localhost:8000/openapi.json | jq '.paths | keys[]' | grep -c "/api/api/" || true)
if [ "$DOUBLE_PREFIX" -eq 0 ]; then
    echo "✅ 没有双重前缀问题"
else
    echo "⚠️  发现 $DOUBLE_PREFIX 个双重前缀路由"
fi

echo -e "\n========================================="
echo "测试完成"
echo "========================================="
