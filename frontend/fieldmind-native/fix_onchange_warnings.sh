#!/bin/bash

# 修复所有 onChange(of:perform:) 警告
# 旧语法: .onChange(of: value) { _ in
# 新语法: .onChange(of: value) { oldValue, newValue in

FILES=$(find Sources -name "*.swift" -type f)

for file in $FILES; do
    if grep -q "\.onChange(of:" "$file"; then
        echo "修复: $file"
        # 替换 .onChange(of: xxx) { _ in 为 .onChange(of: xxx) { oldValue, newValue in
        sed -i '' 's/\.onChange(of: \([^)]*\)) { _ in/.onChange(of: \1) { oldValue, newValue in/g' "$file"
    fi
done

echo "完成！"
