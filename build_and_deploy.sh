#!/bin/bash

# FieldMind 完整构建和部署脚本
# 构建 React 前端 + Swift 原生应用 + 自动部署到桌面

set -e  # 遇到错误立即退出

echo "========================================"
echo "FieldMind 完整构建部署脚本"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="/Users/alwan/FieldMind"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
NATIVE_DIR="$FRONTEND_DIR/fieldmind-native"
DESKTOP_APP="/Users/alwan/Desktop/FieldMind.app"

# 步骤 1: 清理旧构建
echo -e "${BLUE}[1/6] 清理旧构建文件...${NC}"
cd "$FRONTEND_DIR"
rm -rf dist/
rm -rf node_modules/.vite/
echo -e "${GREEN}✓ 清理完成${NC}"
echo ""

# 步骤 2: 构建 React 前端
echo -e "${BLUE}[2/6] 构建 React 前端...${NC}"
cd "$FRONTEND_DIR"

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}安装前端依赖...${NC}"
    npm install
fi

# 构建生产版本
echo "开始构建生产版本..."
npm run build

if [ ! -f "dist/index.html" ]; then
    echo -e "${RED}✗ 前端构建失败！${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 前端构建成功${NC}"
echo -e "  文件位置: $FRONTEND_DIR/dist/"
ls -lh dist/ | grep -E "index.html|assets"
echo ""

# 步骤 3: 创建嵌入式资源目录
echo -e "${BLUE}[3/6] 准备嵌入式资源...${NC}"

# 为 Swift 应用创建 Resources 目录
RESOURCES_DIR="$NATIVE_DIR/Sources/Resources"
mkdir -p "$RESOURCES_DIR"

# 复制构建好的前端到 Resources
FRONTEND_RESOURCES="$RESOURCES_DIR/frontend"
rm -rf "$FRONTEND_RESOURCES"
cp -r "$FRONTEND_DIR/dist" "$FRONTEND_RESOURCES"

echo -e "${GREEN}✓ 资源准备完成${NC}"
echo -e "  资源位置: $FRONTEND_RESOURCES"
echo ""

# 步骤 4: 更新 Swift 代码以使用嵌入式资源
echo -e "${BLUE}[4/6] 更新 Swift WebView 加载逻辑...${NC}"

cat > "$NATIVE_DIR/Sources/Views/WebViewLoader.swift" << 'EOF'
import Foundation
import WebKit

extension WebViewManager {
    /// 加载前端 - 优先使用嵌入式资源
    func loadEmbeddedFrontend() {
        let frontendURL: String

        // 开发模式：使用 Vite 开发服务器
        if ProcessInfo.processInfo.environment["FIELDMIND_DEV"] == "true" {
            frontendURL = "http://localhost:3000"
            DebugLogger.shared.log("使用开发服务器", type: .info, details: frontendURL, category: "webview")
        }
        // 生产模式：使用嵌入式资源
        else if let resourcePath = Bundle.main.resourcePath {
            let frontendPath = "\(resourcePath)/frontend"
            let indexPath = "\(frontendPath)/index.html"

            if FileManager.default.fileExists(atPath: indexPath) {
                frontendURL = "file://\(indexPath)"
                DebugLogger.shared.log("使用嵌入式前端", type: .success, details: frontendURL, category: "webview")
            } else {
                // 回退：使用项目目录的构建文件
                let fallbackPath = "/Users/alwan/FieldMind/frontend/dist/index.html"
                if FileManager.default.fileExists(atPath: fallbackPath) {
                    frontendURL = "file://\(fallbackPath)"
                    DebugLogger.shared.log("使用项目构建文件", type: .warning, details: frontendURL, category: "webview")
                } else {
                    DebugLogger.shared.log("前端文件不存在", type: .error, category: "webview")
                    return
                }
            }
        } else {
            DebugLogger.shared.log("无法获取资源路径", type: .error, category: "webview")
            return
        }

        if let url = URL(string: frontendURL) {
            let request = URLRequest(url: url)
            webView.load(request)
        }
    }
}
EOF

echo -e "${GREEN}✓ Swift 代码更新完成${NC}"
echo ""

# 步骤 5: 编译 Swift 原生应用
echo -e "${BLUE}[5/6] 编译 Swift 原生应用...${NC}"
cd "$NATIVE_DIR"

# 检查是否有 Xcode
if ! command -v xcodebuild &> /dev/null; then
    echo -e "${YELLOW}警告: 未找到 xcodebuild，尝试使用 swift build...${NC}"

    # 使用 Swift Package Manager 构建
    swift build -c release

    BUILD_PATH="$NATIVE_DIR/.build/release/FieldMindNative"
else
    echo "使用 swift build 编译..."
    swift build -c release --arch arm64

    BUILD_PATH="$NATIVE_DIR/.build/release/FieldMindNative"
fi

if [ ! -f "$BUILD_PATH" ]; then
    echo -e "${RED}✗ Swift 应用编译失败！${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Swift 应用编译成功${NC}"
echo -e "  可执行文件: $BUILD_PATH"
file "$BUILD_PATH"
echo ""

# 步骤 6: 部署到桌面应用
echo -e "${BLUE}[6/6] 部署到桌面应用...${NC}"

# 创建应用目录结构
APP_CONTENTS="$DESKTOP_APP/Contents"
APP_MACOS="$APP_CONTENTS/MacOS"
APP_RESOURCES="$APP_CONTENTS/Resources"

# 停止运行中的应用
echo "停止运行中的 FieldMind 应用..."
killall FieldMindNative 2>/dev/null || true
sleep 1

# 备份旧应用
if [ -d "$DESKTOP_APP" ]; then
    BACKUP_NAME="FieldMind_backup_$(date +%Y%m%d_%H%M%S).app"
    echo "备份旧应用到: ~/Desktop/$BACKUP_NAME"
    mv "$DESKTOP_APP" "/Users/alwan/Desktop/$BACKUP_NAME"
fi

# 创建新的应用包
echo "创建新应用包..."
mkdir -p "$APP_MACOS"
mkdir -p "$APP_RESOURCES"

# 复制可执行文件
echo "复制可执行文件..."
cp "$BUILD_PATH" "$APP_MACOS/"
chmod +x "$APP_MACOS/FieldMindNative"

# 复制前端资源
echo "复制前端资源..."
cp -r "$FRONTEND_RESOURCES" "$APP_RESOURCES/"

# 创建 Info.plist
echo "创建 Info.plist..."
cat > "$APP_CONTENTS/Info.plist" << 'PLIST'
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
    <key>NSDocumentsFolderUsageDescription</key>
    <string>FieldMind 需要访问文档文件夹以导入和处理材料</string>
    <key>NSDownloadsFolderUsageDescription</key>
    <string>FieldMind 需要访问下载文件夹以导入材料</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>FieldMind 需要访问文件以处理您的材料</string>
</dict>
</plist>
PLIST

# 代码签名（如果需要）
echo "应用代码签名..."
codesign --force --deep --sign - "$DESKTOP_APP" 2>/dev/null || echo "跳过代码签名"

echo -e "${GREEN}✓ 部署完成${NC}"
echo ""

# 显示最终信息
echo "========================================"
echo -e "${GREEN}构建和部署成功完成！${NC}"
echo "========================================"
echo ""
echo "应用位置: $DESKTOP_APP"
echo "应用大小: $(du -sh "$DESKTOP_APP" | cut -f1)"
echo ""
echo "前端文件:"
ls -lh "$APP_RESOURCES/frontend/" | grep -E "index.html|assets"
echo ""
echo -e "${YELLOW}启动应用:${NC}"
echo "  双击桌面上的 FieldMind.app"
echo "  或运行: open \"$DESKTOP_APP\""
echo ""
echo -e "${YELLOW}开发模式:${NC}"
echo "  export FIELDMIND_DEV=true"
echo "  cd $FRONTEND_DIR && npm run dev"
echo "  然后启动应用将连接到开发服务器"
echo ""
echo -e "${BLUE}功能特性:${NC}"
echo "  ✓ 23 个核心页面"
echo "  ✓ 30+ UI 组件"
echo "  ✓ D3.js 知识图谱"
echo "  ✓ 实时数据可视化"
echo "  ✓ WebView + 原生混合架构"
echo "  ✓ 完整的 API 集成"
echo ""

# 自动打开应用（可选）
read -p "是否立即启动应用？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "启动 FieldMind..."
    open "$DESKTOP_APP"
fi

echo -e "${GREEN}完成！${NC}"
