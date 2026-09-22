#!/bin/bash

#
# quick_start.sh
# FieldMind 快速启动指南 - 立即开始使用整合后的系统
#

echo "🚀 FieldMind 快速启动"
echo "===================="
echo ""

# 检查 Xcode 是否安装
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ 未找到 Xcode，请先安装 Xcode"
    exit 1
fi

# 检查后端 Python 环境
if [ ! -d "/Users/alwan/FieldMind/backend/venv" ]; then
    echo "⚠️  后端虚拟环境不存在，正在创建..."
    cd /Users/alwan/FieldMind/backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo "✅ 虚拟环境已创建"
fi

echo "📋 当前系统状态："
echo ""
echo "✅ 主项目位置: /Users/alwan/FieldMind/fieldmind/fieldmind.xcodeproj"
echo "✅ 后端位置: /Users/alwan/FieldMind/backend"
echo "✅ 备份位置: /Users/alwan/FieldMind/backup_20260919_111954"
echo ""

# 统计文件
SWIFT_COUNT=$(find /Users/alwan/FieldMind/fieldmind/fieldmind -name "*.swift" -type f | wc -l | tr -d ' ')
SERVICE_COUNT=$(find /Users/alwan/FieldMind/fieldmind/fieldmind/Services -name "*.swift" -type f | wc -l | tr -d ' ')
VM_COUNT=$(find /Users/alwan/FieldMind/fieldmind/fieldmind/ViewModels -name "*.swift" -type f | wc -l | tr -d ' ')

echo "📊 项目统计："
echo "   - Swift 文件总数: $SWIFT_COUNT"
echo "   - 服务层文件: $SERVICE_COUNT"
echo "   - ViewModel 文件: $VM_COUNT"
echo ""

echo "🎯 接下来的步骤："
echo ""
echo "【步骤 1】打开 Xcode 项目"
echo "   open /Users/alwan/FieldMind/fieldmind/fieldmind.xcodeproj"
echo ""
echo "【步骤 2】添加核心文件到 Xcode 项目"
echo "   必须添加的文件："
echo "   ✓ Core/UnifiedAppState.swift"
echo "   ✓ Core/DataPipeline/DataPipeline.swift"
echo "   ✓ Services/BackendService.swift"
echo "   ✓ Services/KnowledgeVaultService.swift"
echo "   ✓ Views/MainNavigationView.swift"
echo "   ✓ Views/KnowledgeVaultView.swift"
echo ""
echo "【步骤 3】启动后端服务"
echo "   cd /Users/alwan/FieldMind/backend"
echo "   source venv/bin/activate"
echo "   python -m uvicorn app.main:app --reload"
echo ""
echo "【步骤 4】编译运行"
echo "   在 Xcode 中："
echo "   ⌘+B 编译"
echo "   ⌘+R 运行"
echo ""

read -p "是否现在打开 Xcode 项目？(y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 正在打开 Xcode..."
    open /Users/alwan/FieldMind/fieldmind/fieldmind.xcodeproj

    echo ""
    echo "✅ Xcode 已打开"
    echo ""
    echo "📖 提示："
    echo "   1. 在 Xcode 左侧项目导航器中"
    echo "   2. 右键点击 'fieldmind' 文件夹"
    echo "   3. 选择 'Add Files to fieldmind...'"
    echo "   4. 导航到 fieldmind/fieldmind 目录"
    echo "   5. 选中上述核心文件并添加"
    echo ""

    read -p "是否启动后端服务？(y/n) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🐍 正在启动后端服务..."
        cd /Users/alwan/FieldMind/backend
        source venv/bin/activate
        echo ""
        echo "✅ 后端服务启动中..."
        echo "   访问 http://127.0.0.1:8000/docs 查看 API 文档"
        echo ""
        python -m uvicorn app.main:app --reload
    fi
else
    echo "👋 稍后见！"
    echo ""
    echo "📚 查看完整文档："
    echo "   /Users/alwan/FieldMind/FINAL_INTEGRATION_COMPLETE.md"
fi
