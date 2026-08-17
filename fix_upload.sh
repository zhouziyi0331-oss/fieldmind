#!/bin/bash
# 修复文件上传功能

echo "🔧 修复 FieldMind 文件上传功能..."

INDEX_FILE="/Users/alwan/FieldMind.app/Contents/Resources/index.html"

# 备份
cp "$INDEX_FILE" "$INDEX_FILE.backup2"

# 修复文件输入框的onchange事件
# 将: onchange="handleFileSelect(this.files)"
# 改为: onchange="handleFileSelect(event)"

sed -i '' 's/onchange="handleFileSelect(this\.files)"/onchange="handleFileSelect(event)"/g' "$INDEX_FILE"

echo "✅ 修复完成！"
echo "📝 修改内容:"
echo "  - 修复了文件输入框的事件处理"
echo ""
echo "🚀 现在重新打开应用测试上传功能"
