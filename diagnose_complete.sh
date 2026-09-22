#!/bin/bash

echo "=========================================="
echo "FieldMind 完整诊断"
echo "=========================================="
echo ""

# 1. 检查后端是否运行
echo "1. 检查后端服务..."
if lsof -i :8013 | grep LISTEN > /dev/null; then
    echo "✅ 后端正在运行 (端口 8013)"
else
    echo "❌ 后端未运行"
    exit 1
fi

# 2. 测试后端API
echo ""
echo "2. 测试后端API..."

echo "  - 照片列表API:"
curl -s "http://127.0.0.1:8013/api/photos?project_id=1" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    print('    ✅ 返回格式: {success: true, data: {...}}')
    if 'photos' in data.get('data', {}):
        print(f\"    ✅ 照片数量: {len(data['data']['photos'])}\")
else:
    print('    ❌ 格式错误')
" 2>&1

echo "  - 表格列表API:"
curl -s "http://127.0.0.1:8013/api/v1/projects/1/tables/" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    print('    ✅ 返回格式: {success: true, data: {...}}')
    if 'tables' in data.get('data', {}):
        print(f\"    ✅ 表格数量: {len(data['data']['tables'])}\")
elif 'tables' in data:
    print('    ⚠️  返回格式: {tables: [...]} (无包装)')
    print(f\"    ✅ 表格数量: {len(data['tables'])}\")
else:
    print('    ❌ 格式错误')
" 2>&1

echo "  - 表格统计API:"
curl -s "http://127.0.0.1:8013/api/v1/projects/1/tables/statistics/" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    print('    ✅ 返回格式: {success: true, data: {...}}')
    stats = data.get('data', {})
    print(f\"    ✅ 统计数据: total_tables={stats.get('total_tables')}\")
else:
    print('    ❌ 格式错误')
" 2>&1

# 3. 检查应用是否运行
echo ""
echo "3. 检查应用状态..."
if ps aux | grep "FieldMind.app" | grep -v grep > /dev/null; then
    PID=$(ps aux | grep "FieldMind.app" | grep -v grep | awk '{print $2}')
    echo "✅ 应用正在运行 (PID: $PID)"
else
    echo "❌ 应用未运行"
    exit 1
fi

# 4. 测试应用的网络连接能力
echo ""
echo "4. 测试应用的网络权限..."
codesign -d --entitlements - /Applications/FieldMind.app/Contents/MacOS/FieldMindNative 2>/dev/null | grep -A 5 "com.apple.security.network"
if [ $? -eq 0 ]; then
    echo "✅ 应用有网络权限"
else
    echo "⚠️  无法验证网络权限"
fi

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="
