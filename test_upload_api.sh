#!/bin/bash

echo "========================================="
echo "FieldMind 文件上传功能测试"
echo "========================================="
echo ""

# 创建测试文件
echo "1. 创建测试文件..."
cat > /tmp/test_audio.txt << 'EOF'
测试音频文件内容
访谈记录：村民访谈
时间：2024-03-20
EOF

cat > /tmp/test_doc.txt << 'EOF'
测试文档
田野调研笔记
关键词：布依族、山歌、传统文化
EOF

echo "✅ 测试文件已创建"
echo ""

# 测试上传文件1
echo "2. 测试上传文件1 (test_audio.txt)..."
RESPONSE1=$(curl -s -X POST http://localhost:5000/api/files/upload \
  -F "project_id=1" \
  -F "file=@/tmp/test_audio.txt")

if echo "$RESPONSE1" | grep -q "filename"; then
    echo "✅ 文件1上传成功"
    echo "   文件名: $(echo $RESPONSE1 | grep -o '"filename":"[^"]*"' | cut -d'"' -f4)"
    echo "   关键词: $(echo $RESPONSE1 | grep -o '"keywords":\[[^]]*\]')"
else
    echo "❌ 文件1上传失败"
    echo "   响应: $RESPONSE1"
fi
echo ""

# 测试上传文件2
echo "3. 测试上传文件2 (test_doc.txt)..."
RESPONSE2=$(curl -s -X POST http://localhost:5000/api/files/upload \
  -F "project_id=1" \
  -F "file=@/tmp/test_doc.txt")

if echo "$RESPONSE2" | grep -q "filename"; then
    echo "✅ 文件2上传成功"
    echo "   文件名: $(echo $RESPONSE2 | grep -o '"filename":"[^"]*"' | cut -d'"' -f4)"
    echo "   关键词: $(echo $RESPONSE2 | grep -o '"keywords":\[[^]]*\]')"
else
    echo "❌ 文件2上传失败"
    echo "   响应: $RESPONSE2"
fi
echo ""

# 获取文件列表
echo "4. 获取文件列表..."
FILES=$(curl -s http://localhost:5000/api/files?project_id=1)
FILE_COUNT=$(echo "$FILES" | grep -o '"filename"' | wc -l | xargs)

echo "✅ 当前项目共有 $FILE_COUNT 个文件"
echo ""

# 显示最近上传的文件
echo "5. 最近上传的文件："
echo "$FILES" | grep -o '"filename":"[^"]*"' | tail -5 | cut -d'"' -f4 | while read filename; do
    echo "   - $filename"
done
echo ""

echo "========================================="
echo "测试完成！"
echo "========================================="
echo ""
echo "现在请在浏览器中："
echo "1. 点击左侧 '材料导入' 菜单"
echo "2. 查看文件列表中是否显示刚才上传的文件"
echo "3. 尝试拖拽一个文件到上传区域"
echo "4. 检查浏览器控制台（F12）是否有错误"
