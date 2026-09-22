#!/bin/bash

#
# deep_integration.sh
# FieldMind 深度整合执行脚本
#

set -e

PROJECT_ROOT="/Users/alwan/FieldMind"
MAIN_PROJECT="$PROJECT_ROOT/fieldmind/fieldmind"
NATIVE_PROJECT="$PROJECT_ROOT/frontend/fieldmind-native"
BACKEND="$PROJECT_ROOT/backend"

echo "🚀 开始 FieldMind 深度整合..."
echo ""

# ============================================================
# 第一步：分析现有架构
# ============================================================
echo "📊 [1/8] 分析现有架构..."

# 统计现有文件
MAIN_SWIFT_COUNT=$(find "$MAIN_PROJECT" -name "*.swift" -type f 2>/dev/null | wc -l)
NATIVE_SWIFT_COUNT=$(find "$NATIVE_PROJECT/Sources" -name "*.swift" -type f 2>/dev/null | wc -l)
BACKEND_PY_COUNT=$(find "$BACKEND/src" -name "*.py" -type f 2>/dev/null | wc -l)

echo "   主项目 Swift 文件: $MAIN_SWIFT_COUNT"
echo "   Native 项目 Swift 文件: $NATIVE_SWIFT_COUNT"
echo "   后端 Python 文件: $BACKEND_PY_COUNT"
echo ""

# ============================================================
# 第二步：创建备份
# ============================================================
echo "💾 [2/8] 创建备份..."

BACKUP_DIR="$PROJECT_ROOT/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp -r "$MAIN_PROJECT" "$BACKUP_DIR/fieldmind_main"
cp -r "$NATIVE_PROJECT" "$BACKUP_DIR/fieldmind_native"

echo "   备份已保存到: $BACKUP_DIR"
echo ""

# ============================================================
# 第三步：分析重复和冲突
# ============================================================
echo "🔍 [3/8] 分析重复和冲突..."

# 查找重复的文件名
DUPLICATE_FILES=$(comm -12 \
    <(find "$MAIN_PROJECT" -name "*.swift" -type f -exec basename {} \; | sort | uniq) \
    <(find "$NATIVE_PROJECT/Sources" -name "*.swift" -type f -exec basename {} \; | sort | uniq))

DUPLICATE_COUNT=$(echo "$DUPLICATE_FILES" | grep -v '^$' | wc -l | tr -d ' ')

echo "   发现 $DUPLICATE_COUNT 个重复文件名"
if [ "$DUPLICATE_COUNT" -gt 0 ]; then
    echo "   重复文件："
    echo "$DUPLICATE_FILES" | head -10
fi
echo ""

# ============================================================
# 第四步：智能合并服务层
# ============================================================
echo "🔧 [4/8] 智能合并服务层..."

# 创建统一服务目录
mkdir -p "$MAIN_PROJECT/Services/Unified"

# 合并策略：
# 1. 如果主项目没有，从 native 复制
# 2. 如果两边都有，保留主项目的，native 的重命名为 *_Native.swift

for service_file in "$NATIVE_PROJECT/Sources/Services"/*.swift; do
    if [ -f "$service_file" ]; then
        filename=$(basename "$service_file")

        if [ ! -f "$MAIN_PROJECT/Services/$filename" ]; then
            # 不存在，直接复制
            cp "$service_file" "$MAIN_PROJECT/Services/"
            echo "   ✅ 复制: $filename"
        else
            # 存在，需要合并
            echo "   ⚠️  冲突: $filename (需要手动审查)"
            # 保留 native 版本以供参考
            cp "$service_file" "$MAIN_PROJECT/Services/Unified/${filename%.swift}_Native.swift"
        fi
    fi
done

echo ""

# ============================================================
# 第五步：合并 ViewModels
# ============================================================
echo "🎨 [5/8] 合并 ViewModels..."

mkdir -p "$MAIN_PROJECT/ViewModels/Unified"

for vm_file in "$NATIVE_PROJECT/Sources/ViewModels"/*.swift; do
    if [ -f "$vm_file" ]; then
        filename=$(basename "$vm_file")

        if [ ! -f "$MAIN_PROJECT/ViewModels/$filename" ]; then
            cp "$vm_file" "$MAIN_PROJECT/ViewModels/"
            echo "   ✅ 复制: $filename"
        else
            echo "   ⚠️  冲突: $filename"
            cp "$vm_file" "$MAIN_PROJECT/ViewModels/Unified/${filename%.swift}_Native.swift"
        fi
    fi
done

echo ""

# ============================================================
# 第六步：整合 Pages
# ============================================================
echo "📄 [6/8] 整合 Pages..."

# Native 有 47 个页面，主项目可能只有部分
# 策略：全部复制到主项目，但放在 Pages/Native 子目录

mkdir -p "$MAIN_PROJECT/Pages/Native"

cp -r "$NATIVE_PROJECT/Sources/Pages"/* "$MAIN_PROJECT/Pages/Native/" 2>/dev/null || true

PAGES_COUNT=$(find "$MAIN_PROJECT/Pages/Native" -name "*.swift" -type f | wc -l)
echo "   ✅ 整合了 $PAGES_COUNT 个页面"
echo ""

# ============================================================
# 第七步：生成整合报告
# ============================================================
echo "📊 [7/8] 生成整合报告..."

REPORT_FILE="$PROJECT_ROOT/INTEGRATION_REPORT_$(date +%Y%m%d_%H%M%S).md"

cat > "$REPORT_FILE" << EOF
# FieldMind 深度整合报告

生成时间: $(date)

## 📊 文件统计

### 整合前
- 主项目 Swift 文件: $MAIN_SWIFT_COUNT
- Native 项目 Swift 文件: $NATIVE_SWIFT_COUNT
- 后端 Python 文件: $BACKEND_PY_COUNT

### 整合后
- 总 Swift 文件: $(find "$MAIN_PROJECT" -name "*.swift" -type f | wc -l | tr -d ' ')

## ⚠️  需要手动处理的冲突

### 服务层冲突
EOF

# 列出冲突文件
for conflict in "$MAIN_PROJECT/Services/Unified"/*_Native.swift; do
    if [ -f "$conflict" ]; then
        echo "- $(basename "$conflict")" >> "$REPORT_FILE"
    fi
done

cat >> "$REPORT_FILE" << EOF

### ViewModels 冲突
EOF

for conflict in "$MAIN_PROJECT/ViewModels/Unified"/*_Native.swift; do
    if [ -f "$conflict" ]; then
        echo "- $(basename "$conflict")" >> "$REPORT_FILE"
    fi
done

cat >> "$REPORT_FILE" << EOF

## ✅ 下一步操作

1. **在 Xcode 中审查冲突文件**
   - 比较主版本和 Native 版本
   - 合并有用的功能
   - 删除冗余代码

2. **更新导入和依赖**
   - 确保所有 import 语句正确
   - 解决编译错误

3. **测试整合后的功能**
   - 运行所有测试
   - 手动测试关键流程

4. **清理冗余文件**
   - 删除 frontend/fieldmind-native 目录
   - 保留一份备份

## 📁 备份位置

$BACKUP_DIR

## 🔧 核心架构文件

已创建以下核心文件：
- UnifiedAppState.swift - 统一状态管理
- DataPipeline.swift - 数据通道系统
- BackendService.swift - 后端服务管理
- KnowledgeVaultService.swift - 知识库服务
- DistillationService.swift - 蒸馏服务

## 🎯 架构优势

1. **单一状态树**: 所有状态通过 UnifiedAppState 管理
2. **数据通道分离**: 干净数据和脏数据独立处理
3. **跨模块关联**: 知识单元、笔记、SOP 深度关联
4. **自动化流程**: 上传→蒸馏→笔记→图谱 全自动
5. **统一服务层**: 所有服务接口一致

EOF

echo "   ✅ 报告已保存: $REPORT_FILE"
echo ""

# ============================================================
# 第八步：更新 Xcode 项目（生成脚本）
# ============================================================
echo "🔨 [8/8] 生成 Xcode 更新脚本..."

cat > "$PROJECT_ROOT/update_xcode_project.sh" << 'XCODE_SCRIPT'
#!/bin/bash

echo "📱 更新 Xcode 项目..."
echo ""
echo "⚠️  此脚本需要手动执行以下步骤："
echo ""
echo "1. 打开 Xcode 项目:"
echo "   open /Users/alwan/FieldMind/fieldmind/fieldmind.xcodeproj"
echo ""
echo "2. 添加新文件到项目:"
echo "   - Core/UnifiedAppState.swift"
echo "   - Core/DataPipeline/DataPipeline.swift"
echo "   - Services/ (所有新服务)"
echo "   - ViewModels/ (所有新 ViewModel)"
echo "   - Pages/Native/ (所有页面)"
echo ""
echo "3. 解决冲突文件:"
echo "   - 比较 Services/Unified/*_Native.swift"
echo "   - 比较 ViewModels/Unified/*_Native.swift"
echo "   - 保留最佳实现，删除冗余"
echo ""
echo "4. 更新 fieldmindApp.swift:"
echo "   - 使用 UnifiedAppState.shared"
echo "   - 初始化所有服务"
echo ""
echo "5. 编译并测试:"
echo "   - ⌘+B 编译"
echo "   - 解决编译错误"
echo "   - ⌘+R 运行"
echo ""
XCODE_SCRIPT

chmod +x "$PROJECT_ROOT/update_xcode_project.sh"

echo ""
echo "✅ 深度整合完成！"
echo ""
echo "📋 下一步操作："
echo ""
echo "1. 查看整合报告:"
echo "   open $REPORT_FILE"
echo ""
echo "2. 更新 Xcode 项目:"
echo "   $PROJECT_ROOT/update_xcode_project.sh"
echo ""
echo "3. 在 Xcode 中处理冲突文件"
echo ""
echo "4. 测试整合后的系统"
echo ""
echo "5. 确认无误后，删除旧项目:"
echo "   rm -rf $NATIVE_PROJECT"
echo "   (备份在 $BACKUP_DIR)"
echo ""
echo "🎉 准备开始使用统一的 FieldMind 系统！"
echo ""
