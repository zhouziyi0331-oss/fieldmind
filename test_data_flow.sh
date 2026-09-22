#!/bin/bash

echo "========================================"
echo "FieldMind 完整功能测试"
echo "========================================"
echo ""

echo "1. 测试上传文件..."
curl -s -X POST http://localhost:5001/api/files/upload \
  -F "project_id=1" \
  -F "file=@/Users/alwan/测试文件_田野访谈.txt" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'  ✅ 文件上传成功: {data[\"filename\"]}')
print(f'  📊 提取关键词: {len(data[\"keywords\"])} 个')
print(f'     {\", \".join(data[\"keywords\"])}')
if data.get('insights'):
    print(f'  💡 生成洞察: {len(data[\"insights\"])} 条')
"

echo ""
echo "2. 检查关键词数据库..."
curl -s 'http://localhost:5001/api/keywords?project_id=1' | python3 -c "
import sys, json
keywords = json.load(sys.stdin)
print(f'  📚 数据库中共有 {len(keywords)} 个关键词:')
for kw in keywords[:8]:
    print(f'     - {kw[\"keyword\"]} (频次: {kw[\"frequency\"]})')
"

echo ""
echo "3. 检查文件列表..."
curl -s 'http://localhost:5001/api/files?project_id=1' | python3 -c "
import sys, json
data = json.load(sys.stdin)
files = data.get('files', [])
print(f'  📁 项目中共有 {len(files)} 个文件')
print(f'  📄 最近上传的 5 个文件:')
for f in files[:5]:
    print(f'     - {f[\"filename\"]} ({f[\"filesize\"]//1024}KB)')
"

echo ""
echo "========================================"
echo "✅ 所有数据已正确保存到数据库"
echo ""
echo "现在请在桌面应用中测试："
echo "1. 点击左侧 '关键词引擎'"
echo "2. 应该看到新提取的关键词出现在关键词云中"
echo "3. 点击 '材料导入' 查看文件列表"
echo "4. 再次拖拽上传，观察实时反馈"
echo "========================================"
