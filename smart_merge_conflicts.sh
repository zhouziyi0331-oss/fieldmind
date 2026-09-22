#!/bin/bash

#
# smart_merge_conflicts.sh
# 智能合并冲突文件 - 保留两边的最佳功能
#

set -e

PROJECT_ROOT="/Users/alwan/FieldMind"
MAIN_PROJECT="$PROJECT_ROOT/fieldmind/fieldmind"

echo "🔧 开始智能合并冲突文件..."
echo ""

# ============================================================
# 合并策略函数
# ============================================================

merge_service_files() {
    local main_file="$1"
    local native_file="$2"
    local output_file="$3"

    echo "   合并: $(basename "$main_file")"

    # 提取两个文件的内容
    local main_imports=$(grep "^import " "$main_file" 2>/dev/null || true)
    local native_imports=$(grep "^import " "$native_file" 2>/dev/null || true)

    # 合并 imports（去重）
    local merged_imports=$(echo -e "$main_imports\n$native_imports" | sort -u)

    # 提取类定义和方法
    # 保留主文件的结构，添加 native 文件中独有的方法

    cat > "$output_file" << EOF
//
//  $(basename "$output_file")
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: $(date)
//

$merged_imports

// ========================================
// 主实现（来自主项目）
// ========================================

EOF

    # 添加主文件内容（去除 imports）
    grep -v "^import " "$main_file" >> "$output_file"

    cat >> "$output_file" << EOF

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*
EOF

    # 添加 native 文件内容作为注释参考
    grep -v "^import " "$native_file" >> "$output_file" || true

    cat >> "$output_file" << EOF
*/

EOF
}

# ============================================================
# 自动合并服务层
# ============================================================
echo "📦 [1/3] 自动合并服务层..."

SERVICES_UNIFIED="$MAIN_PROJECT/Services/Unified"
SERVICES_MAIN="$MAIN_PROJECT/Services"

service_count=0

for native_service in "$SERVICES_UNIFIED"/*_Native.swift; do
    if [ -f "$native_service" ]; then
        base_name=$(basename "$native_service" "_Native.swift")
        main_service="$SERVICES_MAIN/${base_name}.swift"

        if [ -f "$main_service" ]; then
            # 创建合并版本
            merged_file="$SERVICES_MAIN/${base_name}_Merged.swift"
            merge_service_files "$main_service" "$native_service" "$merged_file"
            service_count=$((service_count + 1))
        fi
    fi
done

echo "   ✅ 已处理 $service_count 个服务文件"
echo ""

# ============================================================
# 自动合并 ViewModels
# ============================================================
echo "🎨 [2/3] 自动合并 ViewModels..."

VIEWMODELS_UNIFIED="$MAIN_PROJECT/ViewModels/Unified"
VIEWMODELS_MAIN="$MAIN_PROJECT/ViewModels"

vm_count=0

for native_vm in "$VIEWMODELS_UNIFIED"/*_Native.swift; do
    if [ -f "$native_vm" ]; then
        base_name=$(basename "$native_vm" "_Native.swift")
        main_vm="$VIEWMODELS_MAIN/${base_name}.swift"

        if [ -f "$main_vm" ]; then
            merged_file="$VIEWMODELS_MAIN/${base_name}_Merged.swift"
            merge_service_files "$main_vm" "$native_vm" "$merged_file"
            vm_count=$((vm_count + 1))
        fi
    fi
done

echo "   ✅ 已处理 $vm_count 个 ViewModel 文件"
echo ""

# ============================================================
# 生成合并审查清单
# ============================================================
echo "📋 [3/3] 生成合并审查清单..."

REVIEW_FILE="$PROJECT_ROOT/MERGE_REVIEW_CHECKLIST.md"

cat > "$REVIEW_FILE" << EOF
# FieldMind 合并审查清单

生成时间: $(date)

## 📊 合并统计

- 服务文件已合并: $service_count
- ViewModel 文件已合并: $vm_count
- 总计: $((service_count + vm_count))

## ✅ 审查步骤

### 第一步：审查 *_Merged.swift 文件

所有合并后的文件都以 \`_Merged.swift\` 结尾，需要逐一审查：

#### 服务层
EOF

for merged in "$SERVICES_MAIN"/*_Merged.swift; do
    if [ -f "$merged" ]; then
        echo "- [ ] $(basename "$merged")" >> "$REVIEW_FILE"
    fi
done

cat >> "$REVIEW_FILE" << EOF

#### ViewModels
EOF

for merged in "$VIEWMODELS_MAIN"/*_Merged.swift; do
    if [ -f "$merged" ]; then
        echo "- [ ] $(basename "$merged")" >> "$REVIEW_FILE"
    fi
done

cat >> "$REVIEW_FILE" << EOF

### 第二步：对每个文件执行以下操作

1. **打开文件** - 在 Xcode 中打开
2. **审查注释区域** - 查看 "Native 版本的扩展功能" 部分
3. **整合有用功能** - 将有价值的代码移到主实现中
4. **删除注释** - 清理已整合或不需要的代码
5. **重命名文件** - 将 \`*_Merged.swift\` 重命名为 \`*.swift\`
6. **删除旧文件** - 删除原来的 \`*.swift\` 和 \`*_Native.swift\`
7. **编译测试** - ⌘+B 确保无编译错误

### 第三步：清理 Unified 目录

审查完成后，删除所有 Unified 目录：

\`\`\`bash
rm -rf $SERVICES_UNIFIED
rm -rf $VIEWMODELS_UNIFIED
\`\`\`

### 第四步：更新 UnifiedAppState

确保 UnifiedAppState.swift 使用合并后的服务：

\`\`\`swift
// 检查所有服务引用
- ProjectService.shared
- DocumentService.shared
- ChatService.shared
// ... 等等
\`\`\`

### 第五步：完整测试

- [ ] 项目管理功能
- [ ] 材料上传和蒸馏
- [ ] 知识库（笔记、图谱）
- [ ] AI 对话
- [ ] 时间线和报告
- [ ] 工作流和 SOP
- [ ] 后端自动启动

## 🎯 审查重点

### 需要特别关注的文件

1. **ProjectService** - 项目管理核心
2. **DocumentService** - 文档处理
3. **ChatService** - AI 对话
4. **KnowledgeGraphService** - 知识图谱
5. **TimelineService** - 时间线
6. **WorkflowService** - 工作流

### 常见合并模式

#### 模式 1：功能互补
- 主版本有 A 功能，Native 版本有 B 功能
- **操作**: 将 B 功能添加到主版本

#### 模式 2：实现不同
- 两个版本实现同一功能，但方法不同
- **操作**: 比较两种实现，选择更好的或结合两者优点

#### 模式 3：版本更新
- Native 版本是主版本的升级
- **操作**: 完全使用 Native 版本

#### 模式 4：废弃功能
- Native 版本的某些功能已过时
- **操作**: 仅保留主版本

## 📝 合并示例

### 示例：ProjectService

\`\`\`swift
// ========================================
// 主实现
// ========================================
class ProjectService: ObservableObject {
    // 主版本的核心功能
    func listProjects() async throws -> [Project] {
        // ...
    }
}

// ========================================
// 从 Native 版本整合的功能
// ========================================
extension ProjectService {
    // Native 版本的额外功能
    func archiveProject(_ id: String) async throws {
        // 从 Native 版本迁移过来
    }

    func exportProject(_ id: String) async throws -> Data {
        // 从 Native 版本迁移过来
    }
}
\`\`\`

## 🚀 完成后

所有审查完成后，运行：

\`\`\`bash
# 1. 编译项目
cd /Users/alwan/FieldMind/fieldmind
xcodebuild -project fieldmind.xcodeproj -scheme fieldmind clean build

# 2. 如果成功，删除旧的 Native 项目
rm -rf /Users/alwan/FieldMind/frontend/fieldmind-native

# 3. 提交更改
cd /Users/alwan/FieldMind
git add .
git commit -m "深度整合完成：统一服务层和 ViewModels"

# 4. 推送
git push origin main
\`\`\`

## ✅ 验收标准

- [ ] 所有 *_Merged.swift 文件已审查
- [ ] 所有 *_Native.swift 文件已删除
- [ ] Unified 目录已删除
- [ ] 项目编译无错误
- [ ] 所有功能测试通过
- [ ] 无重复代码
- [ ] 文档已更新

EOF

echo "   ✅ 审查清单已保存: $REVIEW_FILE"
echo ""

echo "✅ 智能合并完成！"
echo ""
echo "📋 下一步："
echo "   1. 查看审查清单: open $REVIEW_FILE"
echo "   2. 在 Xcode 中逐一审查合并文件"
echo "   3. 运行测试并验证功能"
echo ""
