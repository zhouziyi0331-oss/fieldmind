#!/bin/bash

#
# build_unified_app.sh
# 构建统一的 FieldMind.app，包含 Swift 前端和 Python 后端
#

set -e

echo "🚀 开始构建统一的 FieldMind 应用..."

# 配置
PROJECT_ROOT="/Users/alwan/FieldMind"
XCODE_PROJECT="$PROJECT_ROOT/fieldmind/fieldmind.xcodeproj"
BACKEND_DIR="$PROJECT_ROOT/backend"
BUILD_DIR="$PROJECT_ROOT/build"
APP_NAME="FieldMind"

# 清理旧构建
echo "🧹 清理旧构建..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# 1. 构建 Swift 应用
echo "📱 构建 Swift 应用..."
cd "$PROJECT_ROOT/fieldmind"
xcodebuild -project fieldmind.xcodeproj \
    -scheme fieldmind \
    -configuration Release \
    -derivedDataPath "$BUILD_DIR/DerivedData" \
    build

# 找到构建的 .app
APP_PATH=$(find "$BUILD_DIR/DerivedData" -name "$APP_NAME.app" -type d | head -1)

if [ -z "$APP_PATH" ]; then
    echo "❌ 未找到构建的应用"
    exit 1
fi

echo "✅ 应用构建完成: $APP_PATH"

# 2. 创建后端 venv 并打包
echo "🐍 准备 Python 后端..."
cd "$BACKEND_DIR"

# 创建干净的 venv
BACKEND_VENV="$BUILD_DIR/backend_venv"
python3 -m venv "$BACKEND_VENV"
source "$BACKEND_VENV/bin/activate"

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 3. 将后端复制到 app bundle
echo "📦 打包后端到应用..."
RESOURCES_DIR="$APP_PATH/Contents/Resources"
mkdir -p "$RESOURCES_DIR/backend"

# 复制后端代码
cp -r "$BACKEND_DIR/src" "$RESOURCES_DIR/backend/"
cp -r "$BACKEND_DIR/requirements.txt" "$RESOURCES_DIR/backend/"

# 复制 venv（只保留必要文件）
mkdir -p "$RESOURCES_DIR/backend/venv"
cp -r "$BACKEND_VENV/lib" "$RESOURCES_DIR/backend/venv/"
cp -r "$BACKEND_VENV/bin" "$RESOURCES_DIR/backend/venv/"

# 创建启动脚本
cat > "$RESOURCES_DIR/backend/start_backend.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
source venv/bin/activate
exec python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
EOF

chmod +x "$RESOURCES_DIR/backend/start_backend.sh"

# 4. 复制数据库和配置
echo "💾 复制数据和配置..."
mkdir -p "$RESOURCES_DIR/data"
if [ -f "$BACKEND_DIR/fieldmind.db" ]; then
    cp "$BACKEND_DIR/fieldmind.db" "$RESOURCES_DIR/data/"
fi

# 创建知识库目录
mkdir -p "$RESOURCES_DIR/vault"

# 5. 更新 Info.plist（添加必要权限）
echo "⚙️  更新应用配置..."
INFO_PLIST="$APP_PATH/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Add :NSAppleEventsUsageDescription string 'FieldMind 需要运行后端服务'" "$INFO_PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :NSLocalNetworkUsageDescription string 'FieldMind 需要访问本地网络服务'" "$INFO_PLIST" 2>/dev/null || true

# 6. 复制到桌面
echo "📋 复制应用到桌面..."
DESKTOP_APP="/Users/alwan/Desktop/FieldMind_Apps/$APP_NAME.app"
rm -rf "$DESKTOP_APP"
cp -r "$APP_PATH" "$DESKTOP_APP"

# 7. 创建启动脚本
echo "🔧 创建启动脚本..."
cat > "/Users/alwan/Desktop/FieldMind_Apps/启动FieldMind.command" << 'EOF'
#!/bin/bash
open "/Users/alwan/Desktop/FieldMind_Apps/FieldMind.app"
EOF

chmod +x "/Users/alwan/Desktop/FieldMind_Apps/启动FieldMind.command"

# 8. 创建停止脚本
cat > "/Users/alwan/Desktop/FieldMind_Apps/停止FieldMind.command" << 'EOF'
#!/bin/bash
killall FieldMind 2>/dev/null
pkill -f "uvicorn app.main:app" 2>/dev/null
echo "✅ FieldMind 已停止"
sleep 2
EOF

chmod +x "/Users/alwan/Desktop/FieldMind_Apps/停止FieldMind.command"

echo ""
echo "✅ 构建完成！"
echo ""
echo "📦 应用位置: $DESKTOP_APP"
echo "📁 应用大小: $(du -sh "$DESKTOP_APP" | cut -f1)"
echo ""
echo "🚀 启动方式："
echo "   1. 双击桌面的 FieldMind.app"
echo "   2. 或运行: /Users/alwan/Desktop/FieldMind_Apps/启动FieldMind.command"
echo ""
echo "🛑 停止方式："
echo "   运行: /Users/alwan/Desktop/FieldMind_Apps/停止FieldMind.command"
echo ""

# 9. 创建卸载脚本
cat > "/Users/alwan/Desktop/FieldMind_Apps/卸载LaunchAgent.sh" << 'EOF'
#!/bin/bash
launchctl unload ~/Library/LaunchAgents/com.fieldmind.backend.v3.plist 2>/dev/null
rm ~/Library/LaunchAgents/com.fieldmind.backend.v3.plist 2>/dev/null
echo "✅ LaunchAgent 已卸载"
EOF

chmod +x "/Users/alwan/Desktop/FieldMind_Apps/卸载LaunchAgent.sh"

echo "📝 提示："
echo "   - 首次启动可能需要在系统偏好设置中授权"
echo "   - 后端会自动在应用启动时启动"
echo "   - 数据保存在应用 Resources 目录"
echo ""
