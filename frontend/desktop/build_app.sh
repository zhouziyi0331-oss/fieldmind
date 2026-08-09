#!/bin/bash
# 构建可执行的macOS应用

echo "🔨 开始构建FieldMind桌面应用..."

# 1. 编译Swift代码
echo "1️⃣ 编译Swift代码..."
swift build -c release

if [ $? -ne 0 ]; then
    echo "❌ 编译失败"
    exit 1
fi

# 2. 创建.app bundle结构
echo "2️⃣ 创建应用包结构..."
APP_NAME="FieldMindNative"
APP_PATH="$APP_NAME.app"
rm -rf "$APP_PATH"

mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# 3. 复制可执行文件
echo "3️⃣ 复制可执行文件..."
cp .build/release/FieldMind "$APP_PATH/Contents/MacOS/$APP_NAME"
chmod +x "$APP_PATH/Contents/MacOS/$APP_NAME"

# 4. 创建Info.plist
echo "4️⃣ 创建Info.plist..."
cat > "$APP_PATH/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.fieldmind.native</string>
    <key>CFBundleName</key>
    <string>FieldMind</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

# 5. 设置图标（如果有的话）
# cp icon.icns "$APP_PATH/Contents/Resources/"

echo "✅ 构建完成！"
echo "📦 应用位置: $(pwd)/$APP_PATH"
echo "🚀 双击打开: open $APP_PATH"
echo ""
echo "或者移动到应用程序文件夹:"
echo "   cp -r $APP_PATH /Applications/"
