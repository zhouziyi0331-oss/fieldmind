#!/bin/bash

# FieldMind 前端文件集成到 Xcode 脚本
# 此脚本将前端文件复制到正确的 Xcode 项目位置

echo "====== FieldMind 前端集成脚本 ======"
echo ""

XCODE_PROJECT_DIR="/Users/alwan/FieldMind"

# 检查 Xcode 项目是否存在
if [ ! -d "$XCODE_PROJECT_DIR/FieldMind.xcodeproj" ]; then
    echo "❌ Xcode 项目未找到"
    echo "请确保项目位于: $XCODE_PROJECT_DIR"
    exit 1
fi

# 1. 创建目录结构
echo "1. 创建目录结构..."
mkdir -p "$XCODE_PROJECT_DIR/FieldMind/DesignSystem"
mkdir -p "$XCODE_PROJECT_DIR/FieldMind/Components"
mkdir -p "$XCODE_PROJECT_DIR/FieldMind/Views"

# 2. 复制设计系统文件
echo "2. 复制设计系统文件..."
if [ -f "$XCODE_PROJECT_DIR/FieldMindDesignSystem/Colors.swift" ]; then
    cp "$XCODE_PROJECT_DIR/FieldMindDesignSystem/Colors.swift" "$XCODE_PROJECT_DIR/FieldMind/DesignSystem/"
    echo "  ✅ Colors.swift"
else
    echo "  ❌ Colors.swift 未找到"
fi

if [ -f "$XCODE_PROJECT_DIR/FieldMindDesignSystem/Spacing.swift" ]; then
    cp "$XCODE_PROJECT_DIR/FieldMindDesignSystem/Spacing.swift" "$XCODE_PROJECT_DIR/FieldMind/DesignSystem/"
    echo "  ✅ Spacing.swift"
else
    echo "  ❌ Spacing.swift 未找到"
fi

if [ -f "$XCODE_PROJECT_DIR/FieldMindDesignSystem/Typography.swift" ]; then
    cp "$XCODE_PROJECT_DIR/FieldMindDesignSystem/Typography.swift" "$XCODE_PROJECT_DIR/FieldMind/DesignSystem/"
    echo "  ✅ Typography.swift"
else
    echo "  ❌ Typography.swift 未找到"
fi

# 3. 复制组件文件
echo ""
echo "3. 复制组件文件..."
for component in FMCard.swift FMAccordion.swift FMSearchField.swift; do
    if [ -f "$XCODE_PROJECT_DIR/Components/$component" ]; then
        cp "$XCODE_PROJECT_DIR/Components/$component" "$XCODE_PROJECT_DIR/FieldMind/Components/"
        echo "  ✅ $component"
    else
        echo "  ❌ $component 未找到"
    fi
done

# 4. 复制页面文件
echo ""
echo "4. 复制页面文件..."
for view in DashboardView.swift DocumentListView.swift DocumentUploadView.swift ChatView.swift ProjectDetailView.swift; do
    if [ -f "$XCODE_PROJECT_DIR/Views/$view" ]; then
        cp "$XCODE_PROJECT_DIR/Views/$view" "$XCODE_PROJECT_DIR/FieldMind/Views/"
        echo "  ✅ $view"
    else
        echo "  ❌ $view 未找到"
    fi
done

echo ""
echo "====== 文件复制完成 ======"
echo ""
echo "⚠️  重要提示："
echo "1. 在 Xcode 中打开项目"
echo "2. 右键项目 → Add Files to \"FieldMind\""
echo "3. 选择以下目录："
echo "   - FieldMind/DesignSystem/"
echo "   - FieldMind/Components/"
echo "   - FieldMind/Views/"
echo "4. 确保勾选 \"Copy items if needed\" 和 \"Add to targets: FieldMind\""
echo "5. Build 项目 (Cmd+B)"
echo "6. 运行 'python3 smart_system_check.py' 验证完成度"
echo ""

# 5. 生成文件列表
echo "已复制的文件："
echo ""
echo "设计系统 (3 个):"
ls -1 "$XCODE_PROJECT_DIR/FieldMind/DesignSystem/" 2>/dev/null | sed 's/^/  - /'
echo ""
echo "组件 (3 个):"
ls -1 "$XCODE_PROJECT_DIR/FieldMind/Components/" 2>/dev/null | sed 's/^/  - /'
echo ""
echo "页面 (5 个):"
ls -1 "$XCODE_PROJECT_DIR/FieldMind/Views/" 2>/dev/null | sed 's/^/  - /'
echo ""
