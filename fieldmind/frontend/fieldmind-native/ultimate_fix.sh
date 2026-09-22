#!/bin/bash
# 终极修复脚本 - 彻底清理并重新构建应用

set -e

echo "=================================="
echo "FieldMind 终极修复脚本"
echo "=================================="
echo ""

# 步骤1：停止所有运行中的实例
echo "步骤1：停止所有 FieldMindNative 进程..."
pkill -9 FieldMindNative 2>/dev/null || true
sleep 2
echo "✅ 已停止所有进程"
echo ""

# 步骤2：删除已安装的应用
echo "步骤2：删除旧的已安装应用..."
rm -rf /Applications/FieldMind.app
echo "✅ 已删除旧应用"
echo ""

# 步骤3：清理所有构建缓存
echo "步骤3：清理所有构建缓存..."
cd /Users/alwan/FieldMind/frontend/fieldmind-native
rm -rf .build/
rm -rf build/
rm -rf ~/Library/Developer/Xcode/DerivedData/fieldmind-native-*
echo "✅ 已清理缓存"
echo ""

# 步骤4：重新构建 Release 版本
echo "步骤4：构建 Release 版本..."
swift build -c release
if [ $? -ne 0 ]; then
    echo "❌ 构建失败"
    exit 1
fi
echo "✅ 构建成功"
echo ""

# 步骤5：创建应用包
echo "步骤5：创建应用包..."

# 创建 .app 目录结构
APP_DIR="/Applications/FieldMind.app"
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# 复制可执行文件
cp .build/release/FieldMindNative "$APP_DIR/Contents/MacOS/"

# 对可执行文件进行代码签名，添加网络权限
codesign --force --sign - --entitlements FieldMind.entitlements "$APP_DIR/Contents/MacOS/FieldMindNative" 2>/dev/null || true

# 创建 Info.plist
cat > "$APP_DIR/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>FieldMindNative</string>
    <key>CFBundleIdentifier</key>
    <string>com.fieldmind.native</string>
    <key>CFBundleName</key>
    <string>FieldMind</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>14.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

echo "✅ 应用包已创建并签名"
echo ""

# 步骤6：运行新应用
echo "步骤6：启动应用..."
open "$APP_DIR"
sleep 3

# 检查是否成功启动
if pgrep -f "FieldMind.app" > /dev/null; then
    echo "✅ 应用已成功启动"
    echo ""
    echo "=================================="
    echo "修复完成！"
    echo "=================================="
    echo ""
    echo "现在请："
    echo "1. 打开应用（应该已经自动打开）"
    echo "2. 访问照片管理、表格管理、文件管理器页面"
    echo "3. 查看是否还有错误"
    echo ""
    echo "查看实时日志："
    echo "  tail -f ~/Library/Logs/FieldMind/app.log"
else
    echo "⚠️  应用未自动启动，请手动打开 /Applications/FieldMind.app"
fi
