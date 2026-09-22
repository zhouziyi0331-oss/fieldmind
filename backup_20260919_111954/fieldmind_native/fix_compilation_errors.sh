#!/bin/bash

echo "修复编译错误..."

# 1. 恢复错误地替换的 calendar 和 now
echo "恢复 calendar 和 now 变量..."

FILES="Sources/Pages/ChatPage.swift Sources/Pages/ConversationsPage.swift Sources/Pages/DashboardPage.swift Sources/ViewModels/ConversationViewModel.swift Sources/ViewModels/TimelineViewModel.swift"

for file in $FILES; do
    if [ -f "$file" ]; then
        echo "  修复: $file"
        # 恢复 let _ = Calendar 为 let calendar = Calendar
        sed -i '' 's/let _ = Calendar/let calendar = Calendar/g' "$file"
        # 恢复 let _ = Date() 为 let now = Date()（只在需要使用的地方）
        sed -i '' 's/let _ = Date()/let now = Date()/g' "$file"
    fi
done

# 2. 修复 DebugWindow.swift 中的 updated 变量
echo ""
echo "修复 DebugWindow 中的 updated 变量..."
file="Sources/Components/DebugWindow.swift"
if [ -f "$file" ]; then
    # 查找并恢复需要修改的 updated 为 var
    sed -i '' 's/let updated = model$/var updated = model/g' "$file"
fi

# 3. 修复剩余的 onChange 警告
echo ""
echo "修复剩余的 onChange 警告..."
sed -i '' 's/\.onChange(of: \([^)]*\)) {$/\.onChange(of: \1) { oldValue, newValue in/g' Sources/Pages/ConversationsPage.swift
sed -i '' 's/\.onChange(of: \([^)]*\)) {$/\.onChange(of: \1) { oldValue, newValue in/g' Sources/Pages/WorkflowPage.swift

echo ""
echo "完成！"
