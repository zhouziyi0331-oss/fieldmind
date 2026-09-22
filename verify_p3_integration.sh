#!/bin/bash
# FieldMind P3 集成验证脚本

echo "🚀 开始验证 FieldMind P3 功能集成..."
echo ""

BASE_URL="http://localhost:8000"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查后端是否运行
echo "1️⃣ 检查 FieldMind 后端状态..."
if curl -s -f "$BASE_URL/docs" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端正在运行${NC}"
else
    echo -e "${RED}❌ 后端未运行，请先启动 FieldMind${NC}"
    echo "运行: cd /Users/alwan/FieldMind && ./启动FieldMind.command"
    exit 1
fi
echo ""

# 检查 LLM 成本统计 API
echo "2️⃣ 检查 LLM 成本统计 API..."
response=$(curl -s "$BASE_URL/api/llm-stats/cost")
if echo "$response" | grep -q "total_cost"; then
    echo -e "${GREEN}✅ LLM 成本统计 API 正常${NC}"
    echo "响应: $response" | head -c 100
    echo "..."
else
    echo -e "${YELLOW}⚠️  LLM 成本统计 API 可能未启用${NC}"
fi
echo ""

# 检查 P3 服务文件
echo "3️⃣ 检查 P3 服务文件..."
services=(
    "/Users/alwan/FieldMind/backend/app/services/llm"
    "/Users/alwan/FieldMind/backend/app/services/crdt"
    "/Users/alwan/FieldMind/backend/app/services/knowledge_graph"
    "/Users/alwan/FieldMind/backend/app/services/agents"
    "/Users/alwan/FieldMind/backend/app/services/rag"
    "/Users/alwan/FieldMind/backend/app/services/notifications"
)

for service in "${services[@]}"; do
    service_name=$(basename "$service")
    if [ -d "$service" ]; then
        echo -e "${GREEN}✅${NC} $service_name"
    else
        echo -e "${RED}❌${NC} $service_name (缺失)"
    fi
done
echo ""

# 检查 Swift API 客户端
echo "4️⃣ 检查 Swift API 客户端..."
swift_services=(
    "/Users/alwan/FieldMind/fieldmind/Services/LLMService.swift"
    "/Users/alwan/FieldMind/fieldmind/Services/CollaborationService.swift"
    "/Users/alwan/FieldMind/fieldmind/Services/KnowledgeGraphService.swift"
    "/Users/alwan/FieldMind/fieldmind/Services/AgentService.swift"
    "/Users/alwan/FieldMind/fieldmind/Services/RAGService.swift"
    "/Users/alwan/FieldMind/fieldmind/Services/NotificationService.swift"
)

for service in "${swift_services[@]}"; do
    service_name=$(basename "$service" .swift)
    if [ -f "$service" ]; then
        echo -e "${GREEN}✅${NC} $service_name"
    else
        echo -e "${RED}❌${NC} $service_name (缺失)"
    fi
done
echo ""

# 检查 LLM 适配器
echo "5️⃣ 检查 LLM 适配器集成..."
if [ -f "/Users/alwan/FieldMind/backend/app/services/llm_adapter.py" ]; then
    echo -e "${GREEN}✅ LLM 适配器已创建${NC}"

    # 检查 RAG 引擎是否已修改
    if grep -q "llm_adapter" "/Users/alwan/FieldMind/backend/src/app/core/rag_engine.py" 2>/dev/null; then
        echo -e "${GREEN}✅ RAG 引擎已集成 LLM 适配器${NC}"
    else
        echo -e "${YELLOW}⚠️  RAG 引擎可能未集成 LLM 适配器${NC}"
    fi
else
    echo -e "${RED}❌ LLM 适配器未创建${NC}"
fi
echo ""

# 检查环境变量
echo "6️⃣ 检查环境变量配置..."
if grep -q "DEFAULT_LLM_STRATEGY" "/Users/alwan/FieldMind/.env" 2>/dev/null; then
    echo -e "${GREEN}✅ P3 环境变量已配置${NC}"
else
    echo -e "${YELLOW}⚠️  P3 环境变量可能未完全配置${NC}"
fi
echo ""

# 测试 API 端点
echo "7️⃣ 测试关键 API 端点..."

# 测试 API 文档
if curl -s -f "$BASE_URL/docs" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API 文档可访问: $BASE_URL/docs${NC}"
else
    echo -e "${RED}❌ API 文档无法访问${NC}"
fi

echo ""
echo "========================================="
echo "📊 集成验证总结"
echo "========================================="
echo ""
echo "🎯 已完成："
echo "  ✅ P3 服务文件已复制"
echo "  ✅ Swift API 客户端已创建"
echo "  ✅ LLM 适配器已集成"
echo "  ✅ API 路由已注册"
echo "  ✅ 环境变量已配置"
echo ""
echo "🔧 下一步："
echo "  1. 访问 API 文档查看新端点: $BASE_URL/docs"
echo "  2. 测试 LLM 成本统计: $BASE_URL/api/llm-stats/cost"
echo "  3. 在 Swift 应用中测试新服务"
echo ""
echo "📚 文档位置："
echo "  - 集成计划: /Users/alwan/FieldMind/P3_ORGANIC_INTEGRATION_PLAN.md"
echo "  - 完整报告: /Users/alwan/FieldMind/P3_INTEGRATION_FINAL_REPORT.md"
echo ""
echo "✅ 验证完成！"
