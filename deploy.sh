#!/bin/bash

echo "====== FieldMind 部署脚本 ======"
echo ""

# 1. 后端部署
echo "1. 部署后端..."
cd backend/src

# 备份
mkdir -p _backup
cp app/services/background_tasks.py _backup/background_tasks.py.bak 2>/dev/null || echo "  原文件不存在，跳过备份"

# 检查重构文件是否存在
if [ -f "app/services/background_tasks_refactored.py" ]; then
    cp app/services/background_tasks_refactored.py app/services/background_tasks.py
    echo "  ✅ background_tasks 已更新"
else
    echo "  ⏭ background_tasks_refactored.py 不存在"
fi

if [ -f "app/services/enhanced_chat_service_refactored.py" ]; then
    cp app/services/enhanced_chat_service_refactored.py app/services/enhanced_chat_service.py
    echo "  ✅ enhanced_chat_service 已更新"
else
    echo "  ⏭ enhanced_chat_service_refactored.py 不存在"
fi

if [ -f "app/core/audit_refactored.py" ]; then
    cp app/core/audit_refactored.py app/core/audit.py
    echo "  ✅ audit 已更新"
else
    echo "  ⏭ audit_refactored.py 不存在"
fi

if [ -f "app/api/reports_refactored.py" ]; then
    cp app/api/reports_refactored.py app/api/reports_real.py
    echo "  ✅ reports 已更新"
else
    echo "  ⏭ reports_refactored.py 不存在"
fi

# 2. 格式化代码
echo ""
echo "2. 格式化新增代码..."
python3 -m black app/services/dlt_pipeline.py app/services/markitdown_converter.py --quiet 2>/dev/null && echo "  ✅ 代码格式化完成" || echo "  ⏭ black 未安装，跳过格式化"

# 3. 验证文件
echo ""
echo "3. 验证新增文件..."
cd ../..

files_to_check=(
    "backend/src/app/core/api_gateway.py"
    "backend/src/app/api/v1/api_management.py"
    "backend/src/app/services/knowledge_graph_enhanced.py"
    "backend/src/app/services/dlt_pipeline.py"
    "backend/src/app/services/markitdown_converter.py"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file 不存在"
    fi
done

echo ""
echo "====== 部署完成 ======"
echo ""
echo "下一步："
echo "1. 运行 'python3 smart_system_check.py' 检查完成度"
echo "2. 在 Xcode 中集成前端文件"
echo "3. 测试新功能"
