#!/bin/bash

# FieldMind 系统状态检查脚本

echo "========================================="
echo "FieldMind 系统状态检查"
echo "========================================="
echo ""

# 检查后端
echo "📡 检查后端服务..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端服务运行正常 (http://localhost:8000)"
    curl -s http://localhost:8000/health | python3 -m json.tool
else
    echo "❌ 后端服务未运行"
fi
echo ""

# 检查前端
echo "🌐 检查前端服务..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务运行正常 (http://localhost:3000)"
else
    echo "❌ 前端服务未运行"
fi
echo ""

# 统计项目
echo "📊 项目统计..."
curl -s http://localhost:8000/api/projects | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'✅ 项目总数: {data[\"total\"]}')
    for p in data['projects']:
        print(f'   • {p[\"name\"]} (ID: {p[\"id\"]}, 文档: {p.get(\"document_count\", 0)})')
except Exception as e:
    print(f'❌ 获取项目数据失败: {e}')
"
echo ""

# API端点测试
echo "🔌 API端点测试..."
echo "  测试 GET /api/projects..."
if curl -s -f http://localhost:8000/api/projects > /dev/null; then
    echo "  ✅ 项目列表 API"
else
    echo "  ❌ 项目列表 API"
fi

echo "  测试 GET /"
if curl -s -f http://localhost:8000/ > /dev/null; then
    echo "  ✅ 根路径 API"
else
    echo "  ❌ 根路径 API"
fi
echo ""

# 服务URL
echo "========================================="
echo "访问地址"
echo "========================================="
echo "🌐 前端界面: http://localhost:3000"
echo "📝 API文档: http://localhost:8000/docs"
echo "🔍 健康检查: http://localhost:8000/health"
echo "📊 项目列表: http://localhost:3000/projects"
echo ""

# 功能状态
echo "========================================="
echo "功能状态"
echo "========================================="
echo "✅ 项目管理 - 完全可用"
echo "✅ 文档上传 - 完全可用"
echo "✅ 文档转换 - 完全可用"
echo "✅ 长期记忆 - 部分可用（需API密钥优化）"
echo "⚠️  AI对话 - 需要API密钥"
echo "⚠️  智能分析 - 需要API密钥"
echo "🚧 知识图谱 - 待开发"
echo "🚧 时间线 - 待开发"
echo ""

echo "========================================="
echo "快速测试命令"
echo "========================================="
echo ""
echo "# 创建新项目"
echo "curl -X POST http://localhost:8000/api/projects \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"name\":\"我的项目\",\"description\":\"测试\"}'"
echo ""
echo "# 上传文档到项目ID=2"
echo "curl -X POST http://localhost:8000/api/documents/upload \\"
echo "  -F 'project_id=2' \\"
echo "  -F 'file=@/path/to/your/file.txt'"
echo ""
