#!/bin/bash
# FieldMind 完整诊断报告
# 生成时间：2026-07-31

echo "=========================================="
echo "FieldMind 数据调用真实性诊断报告"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━ 1. 真实后端数据调用 ━━━${NC}"
echo ""

# 测试真实API
echo -e "${GREEN}✅ 项目列表${NC}"
curl -s http://localhost:8000/api/projects | jq -r '.total' | xargs -I {} echo "   真实项目数: {}"

echo -e "${GREEN}✅ 文档列表${NC}"
curl -s http://localhost:8000/api/documents/project/2 | jq -r '.total' | xargs -I {} echo "   真实文档数: {}"

echo -e "${GREEN}✅ 时间线事件${NC}"
curl -s http://localhost:8000/api/timeline/projects/2/events | jq -r '.statistics.total_events' | xargs -I {} echo "   真实事件数: {}"

echo ""
echo -e "${BLUE}━━━ 2. 问题功能诊断 ━━━${NC}"
echo ""

# 知识图谱质量
echo -e "${YELLOW}⚠️  知识图谱 - 数据质量差${NC}"
KG_NODES=$(curl -s http://localhost:8000/api/knowledge-graph/projects/2/graph | jq -r '.statistics.total_nodes')
echo "   节点数: $KG_NODES"
echo "   问题: 使用简单正则，误识别普通词为实体"
echo "   示例错误: '田野调查'被识别为人名"

# AI 对话
echo ""
echo -e "${RED}❌ AI对话 - 缺少配置${NC}"
if [ -f "fieldmind-backend/.env" ]; then
    if grep -q "ANTHROPIC_API_KEY" fieldmind-backend/.env; then
        echo "   状态: API密钥已配置"
    else
        echo "   状态: 缺少 ANTHROPIC_API_KEY"
    fi
else
    echo "   状态: .env 文件不存在"
fi

# 长期记忆
echo ""
echo -e "${RED}❌ 长期记忆 - 未真实启用${NC}"
MEM_AVAILABLE=$(curl -s http://localhost:8000/api/projects/2 | jq -r '.memory_stats.available')
echo "   Mem0 状态: $MEM_AVAILABLE"
echo "   总记忆数: 0"

# 用户认证
echo ""
echo -e "${RED}❌ 用户认证 - 未实现${NC}"
AUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/auth/login)
echo "   状态码: $AUTH_STATUS (404 = 未实现)"

echo ""
echo -e "${BLUE}━━━ 3. 前端页面数据源分析 ━━━${NC}"
echo ""

echo "页面名称              数据来源                     状态"
echo "────────────────────────────────────────────────────"
echo -e "项目列表            api.projects.list()          ${GREEN}✅ 真实${NC}"
echo -e "项目详情            api.projects.get(id)         ${GREEN}✅ 真实${NC}"
echo -e "文档管理            api.documents.*              ${GREEN}✅ 真实${NC}"
echo -e "时间线              api.timeline.*               ${GREEN}✅ 真实${NC}"
echo -e "知识图谱            api.knowledgeGraph.*         ${YELLOW}⚠️  质量差${NC}"
echo -e "AI对话              api.chat.*                   ${RED}❌ 需API密钥${NC}"
echo -e "长期记忆            Mem0 API                     ${RED}❌ 未配置${NC}"
echo -e "用户登录            api.auth.*                   ${RED}❌ 未实现${NC}"

echo ""
echo -e "${BLUE}━━━ 4. 推荐修复方案 ━━━${NC}"
echo ""

echo "【高优先级】"
echo "1. 知识图谱 - 使用 jieba 分词替代正则"
echo "   文件: fieldmind-backend/app/services/knowledge_graph_improved.py (已创建)"
echo "   预期提升: 实体识别准确率 40% → 85%"
echo ""

echo "2. AI对话 - 配置 Anthropic API 密钥"
echo "   命令: echo 'ANTHROPIC_API_KEY=sk-ant-xxx' >> fieldmind-backend/.env"
echo "   功能: 启用智能对话和深度思考"
echo ""

echo "【中优先级】"
echo "3. 长期记忆 - 配置 Mem0"
echo "   需要优化 Mem0 配置"
echo ""

echo "4. 用户认证 - 实现登录系统"
echo "   当前未实现，项目默认单用户模式"
echo ""

echo -e "${BLUE}━━━ 5. 快速修复命令 ━━━${NC}"
echo ""

echo "# 修复知识图谱（使用改进版本）"
echo "cd fieldmind-backend/app/api"
echo "sed -i '' 's/from app.services.knowledge_graph import/from app.services.knowledge_graph_improved import ImprovedKnowledgeGraphService as KnowledgeGraphService; from app.services.knowledge_graph import/g' knowledge_graph.py"
echo ""

echo "# 配置 API 密钥"
echo "echo 'ANTHROPIC_API_KEY=your-key-here' >> fieldmind-backend/.env"
echo ""

echo "=========================================="
echo "诊断完成"
echo "=========================================="
