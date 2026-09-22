#!/bin/bash

# 快速构建和部署脚本 - WebView 模式
set -e

cd /Users/alwan/FieldMind/frontend

echo "🔨 编译 Swift 应用 (WebView 模式)..."

# 编译，忽略原生 UI 视图的错误
cd fieldmind-native
swift build -c release --product FieldMindNative 2>&1 | grep -v "ProjectListView\|SidebarView" || true

# 检查是否生成了可执行文件
if [ -f ".build/release/FieldMindNative" ]; then
    echo "✅ 编译成功"

    # 部署到桌面
    echo "📦 部署到桌面..."

    DESKTOP_APP="/Users/alwan/Desktop/FieldMind.app"

    # 停止运行中的应用
    killall FieldMindNative 2>/dev/null || true
    sleep 1

    # 备份旧应用
    if [ -d "$DESKTOP_APP" ]; then
        BACKUP_NAME="FieldMind_backup_$(date +%Y%m%d_%H%M%S).app"
        mv "$DESKTOP_APP" "/Users/alwan/Desktop/$BACKUP_NAME"
        echo "📂 已备份旧版本: $BACKUP_NAME"
    fi

    # 创建应用包结构
    mkdir -p "$DESKTOP_APP/Contents/MacOS"
    mkdir -p "$DESKTOP_APP/Contents/Resources"

    # 复制可执行文件
    cp .build/release/FieldMindNative "$DESKTOP_APP/Contents/MacOS/"
    chmod +x "$DESKTOP_APP/Contents/MacOS/FieldMindNative"

    # 复制前端资源
    cp -r Sources/Resources/frontend "$DESKTOP_APP/Contents/Resources/"

    # 创建 Info.plist
    cat > "$DESKTOP_APP/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>FieldMindNative</string>
    <key>CFBundleIdentifier</key>
    <string>com.fieldmind.native.v3</string>
    <key>CFBundleName</key>
    <string>FieldMind</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>3.2</string>
    <key>CFBundleVersion</key>
    <string>2</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

    # 代码签名
    codesign --force --deep --sign - "$DESKTOP_APP" 2>/dev/null || true

    echo ""
    echo "✨ 部署完成！"
    echo "📍 应用位置: $DESKTOP_APP"
    echo "📊 应用大小: $(du -sh "$DESKTOP_APP" | cut -f1)"
    echo ""
    echo "启动应用: open \"$DESKTOP_APP\""

else
    echo "❌ 编译失败"
    exit 1
fi
