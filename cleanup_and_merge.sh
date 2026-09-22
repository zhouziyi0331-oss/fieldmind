#!/bin/bash

echo "=================================="
echo "FieldMind 版本整理和合并脚本"
echo "=================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 工作目录
MAIN_DIR="/Users/alwan/FieldMind"
BACKUP_DIR="/Users/alwan/FieldMind-Backup-20260818"
OLD_APP_HOME="/Users/alwan/FieldMind.app"
OLD_APP_BACKUP="/Users/alwan/FieldMind.app.old.20260819_111409"
FINAL_APP="/Applications/FieldMind.app"

echo "步骤 1: 检查主目录完整性"
echo "--------------------------------"

# 检查后端
if [ -f "$MAIN_DIR/backend/src/app/main.py" ]; then
    echo -e "${GREEN}✓${NC} 后端主文件存在"
else
    echo -e "${RED}✗${NC} 后端主文件缺失"
    exit 1
fi

# 检查前端源码
if [ -d "$MAIN_DIR/frontend/fieldmind-native" ]; then
    echo -e "${GREEN}✓${NC} 前端源码存在"
else
    echo -e "${RED}✗${NC} 前端源码缺失"
    exit 1
fi

echo ""
echo "步骤 2: 重新编译前端应用"
echo "--------------------------------"

cd "$MAIN_DIR/frontend/fieldmind-native"

# 编译 Release 版本
echo "正在编译..."
xcodebuild -scheme FieldMindNative \
    -configuration Release \
    -derivedDataPath ./build \
    clean build \
    CODE_SIGN_IDENTITY="-" \
    CODE_SIGNING_REQUIRED=NO \
    CODE_SIGNING_ALLOWED=NO

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} 编译成功"
else
    echo -e "${RED}✗${NC} 编译失败"
    exit 1
fi

echo ""
echo "步骤 3: 更新 /Applications/FieldMind.app"
echo "--------------------------------"

# 删除旧的应用
if [ -d "$FINAL_APP" ]; then
    echo "删除旧应用..."
    rm -rf "$FINAL_APP"
fi

# 复制新应用
echo "安装新应用..."
cp -R "$MAIN_DIR/frontend/fieldmind-native/build/Build/Products/Release/FieldMindNative.app" "$FINAL_APP"

if [ -d "$FINAL_APP" ]; then
    echo -e "${GREEN}✓${NC} 应用已安装到 /Applications/FieldMind.app"
else
    echo -e "${RED}✗${NC} 应用安装失败"
    exit 1
fi

echo ""
echo "步骤 4: 清理旧版本和备份"
echo "--------------------------------"

# 列出将要删除的内容
echo "以下内容将被删除："
echo "  - $BACKUP_DIR"
echo "  - $OLD_APP_HOME"
echo "  - $OLD_APP_BACKUP"
echo ""
echo -e "${YELLOW}按 Enter 继续删除，或 Ctrl+C 取消${NC}"
read

# 删除备份目录
if [ -d "$BACKUP_DIR" ]; then
    echo "删除 $BACKUP_DIR..."
    rm -rf "$BACKUP_DIR"
    echo -e "${GREEN}✓${NC} 已删除"
fi

# 删除 Home 目录中的旧应用
if [ -d "$OLD_APP_HOME" ]; then
    echo "删除 $OLD_APP_HOME..."
    rm -rf "$OLD_APP_HOME"
    echo -e "${GREEN}✓${NC} 已删除"
fi

# 删除旧的备份应用
if [ -d "$OLD_APP_BACKUP" ]; then
    echo "删除 $OLD_APP_BACKUP..."
    rm -rf "$OLD_APP_BACKUP"
    echo -e "${GREEN}✓${NC} 已删除"
fi

echo ""
echo "步骤 5: 创建启动脚本"
echo "--------------------------------"

# 创建启动脚本
cat > "$MAIN_DIR/启动FieldMind.command" << 'EOF'
#!/bin/bash

echo "正在启动 FieldMind..."
echo ""

# 启动后端
echo "1. 启动后端服务..."
cd /Users/alwan/FieldMind/backend

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 使用系统 Python 启动
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "   后端已启动 (PID: $BACKEND_PID)"
sleep 3

# 启动前端
echo "2. 启动前端应用..."
open /Applications/FieldMind.app

echo ""
echo "✓ FieldMind 已启动"
echo ""
echo "按 Ctrl+C 停止后端服务"

# 等待用户中断
wait $BACKEND_PID
EOF

chmod +x "$MAIN_DIR/启动FieldMind.command"

# 创建桌面快捷方式
cp "$MAIN_DIR/启动FieldMind.command" "/Users/alwan/Desktop/启动FieldMind.command"

echo -e "${GREEN}✓${NC} 已创建启动脚本"
echo "   - $MAIN_DIR/启动FieldMind.command"
echo "   - /Users/alwan/Desktop/启动FieldMind.command"

echo ""
echo "=================================="
echo -e "${GREEN}整理完成！${NC}"
echo "=================================="
echo ""
echo "现在你只需要："
echo "1. 双击桌面上的 '启动FieldMind.command' 启动完整系统"
echo "2. 或者分别启动："
echo "   - 后端: cd $MAIN_DIR/backend && python -m uvicorn app.main:app"
echo "   - 前端: 在 Launchpad 或 /Applications 中打开 FieldMind"
echo ""
echo "所有旧版本和备份已清理完毕。"
echo ""
