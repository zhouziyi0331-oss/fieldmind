#!/bin/bash

echo "================================"
echo "FieldMind API 测试"
echo "================================"
echo ""

BASE_URL="http://localhost:8000"

# 1. 健康检查
echo "1. 健康检查"
curl -s $BASE_URL/health | python3 -m json.tool
echo ""
echo ""

# 2. 监控统计
echo "2. 监控统计"
curl -s $BASE_URL/monitoring/stats | python3 -m json.tool | head -20
echo ""
echo ""

# 3. 文档列表
echo "3. 文档列表（项目1）"
curl -s $BASE_URL/api/documents/projects/1/documents | python3 -m json.tool | head -30
echo ""
echo ""

# 4. WebSocket 端点检查
echo "4. WebSocket 端点"
echo "   端点: ws://localhost:8000/ws/1"
echo "   (需要 WebSocket 客户端测试)"
echo ""

echo "================================"
echo "测试完成"
echo "================================"
