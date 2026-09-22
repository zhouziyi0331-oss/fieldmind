#!/bin/bash

# 修复 Main actor-isolated static property 'shared' 警告
# 需要在包含 static let shared 的类前添加 @MainActor

echo "开始修复 Main actor-isolated 警告..."

# 查找所有包含 static let shared 的文件
FILES=$(grep -rl "static let shared" Sources/ --include="*.swift")

for file in $FILES; do
    # 检查文件中是否有 static let shared
    if grep -q "static let shared" "$file"; then
        echo "处理: $file"
        
        # 查找包含 static let shared 的类/结构体定义
        # 在 class XXXManager: 或 struct XXX: 前添加 @MainActor（如果还没有）
        
        # 模式1: class ClassName: ObservableObject {
        # 模式2: class ClassName {
        # 模式3: final class ClassName: ObservableObject {
        
        # 如果类定义前没有 @MainActor，则添加
        perl -i -pe 's/^(final\s+)?class\s+(\w+Manager|\w+Service|\w+Logger)(\s*:\s*ObservableObject)?\s*\{/@MainActor\n$1class $2$3 {/g unless /\@MainActor/' "$file"
        perl -i -pe 's/^(final\s+)?class\s+(Modal|Toast|Loading|PageTransition)Manager(\s*:\s*ObservableObject)?\s*\{/@MainActor\n$1class $2Manager$3 {/g unless /\@MainActor/' "$file"
    fi
done

echo "完成！"
