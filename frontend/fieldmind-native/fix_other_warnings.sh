#!/bin/bash

echo "开始修复其他类型的警告..."

# 1. 修复 "Result of 'try?' is unused" 警告
echo "修复 'Result of try? is unused' 警告..."

# 查找所有包含 try? 但未使用结果的行
FILES=$(find Sources -name "*.swift" -type f)

for file in $FILES; do
    # 修复 try? XXX.seekToEnd() 类型的警告
    # 在这些语句前添加 _ = 来明确忽略结果
    if grep -q "^\s*try?" "$file"; then
        echo "  处理: $file"
        
        # 修复独立的 try? 语句（没有赋值）
        sed -i '' 's/^\(\s*\)try?\([^=]*\)$/\1_ = try?\2/g' "$file"
        
        # 但要避免修复已经有 let/var/_ = 的行
        sed -i '' 's/^\(\s*\)\(let\|var\|_\s*=\)\s*_ = try?/\1\2 try?/g' "$file"
    fi
done

# 2. 修复 "Variable was never mutated" 警告
echo ""
echo "修复 'Variable was never mutated' 警告..."

for file in $FILES; do
    # 查找 var xxx = 但从未修改的变量，替换为 let
    # 这个比较复杂，需要逐个检查
    
    # 简单模式：var updated = model 后面直接 return updated（从未修改）
    if grep -q "var updated = " "$file"; then
        echo "  检查: $file"
        # 如果 var updated 后面只有 return updated，替换为 let
        sed -i '' '/var updated = /,/return updated/{s/var updated =/let updated =/;}' "$file"
    fi
    
    # 修复 var result 从未改变的情况
    if grep -q "var result = " "$file"; then
        sed -i '' '/var result = /,/return result/{/var result =/{N;/return result/s/var result =/let result =/;}}' "$file"
    fi
done

# 3. 修复 "Initialization of immutable value 'now' was never used" 警告
echo ""
echo "修复未使用的变量警告..."

for file in $FILES; do
    # 查找定义但从未使用的变量，在变量名前添加 _
    if grep -q "let now = Date()" "$file"; then
        echo "  处理: $file"
        sed -i '' 's/let now = Date()/let _ = Date()/g' "$file"
    fi
    
    # 其他未使用的变量
    if grep -q "let calendar = Calendar" "$file"; then
        sed -i '' 's/let calendar = Calendar/let _ = Calendar/g' "$file"
    fi
done

echo ""
echo "完成！"
