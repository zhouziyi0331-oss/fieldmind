#!/bin/bash
# 强制重新编译和运行桌面应用

echo "=================================="
echo "强制重新编译 FieldMind 桌面应用"
echo "=================================="
echo ""

cd /Users/alwan/FieldMind/frontend/fieldmind-native

echo "步骤1：清理旧的构建产物..."
rm -rf .build/
rm -rf build/
echo "✅ 清理完成"
echo ""

echo "步骤2：重新编译..."
swift build --configuration release
if [ $? -eq 0 ]; then
    echo "✅ 编译成功"
else
    echo "❌ 编译失败"
    exit 1
fi
echo ""

echo "步骤3：找到可执行文件..."
EXECUTABLE=$(find .build -name "FieldMindNative" -type f -perm +111 | head -1)
if [ -z "$EXECUTABLE" ]; then
    echo "❌ 找不到可执行文件"
    exit 1
fi
echo "✅ 找到: $EXECUTABLE"
echo ""

echo "步骤4：运行应用..."
echo "   应用会在新窗口打开"
echo "   请查看控制台输出（在终端中）"
echo ""
$EXECUTABLE
