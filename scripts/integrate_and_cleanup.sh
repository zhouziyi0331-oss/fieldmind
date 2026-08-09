#!/bin/bash
#
# FieldMind 整合验证和清理脚本
# 功能：验证整合成功后，安全删除旧项目
#

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║         FieldMind 整合验证和清理工具                        ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "第一步：验证整合完整性"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. 检查新位置的文件
echo "1. 检查 Desktop App 是否已迁移..."
if [ -d ~/FieldMind-Rebuild/fieldmind-desktop/Sources/FieldMind ]; then
    check_pass "Desktop App 已迁移到新位置"
else
    check_fail "Desktop App 迁移失败"
    exit 1
fi

# 2. 检查关键文件
echo ""
echo "2. 检查关键文件..."
FILES=(
    "Sources/FieldMind/Views/KeywordSearchView.swift"
    "Sources/FieldMind/Views/CreativeAnalysisView.swift"
    "Sources/FieldMind/Views/BusinessAnalysisView.swift"
    "Sources/FieldMind/Services/APIService.swift"
    "Sources/FieldMind/Models/NewFeatures.swift"
    "Sources/FieldMind/Views/MediaPlayerView.swift"
    "Sources/FieldMind/Services/ReportExporter.swift"
)

cd ~/FieldMind-Rebuild/fieldmind-desktop
all_files_ok=true
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        check_pass "$file"
    else
        check_fail "$file 缺失"
        all_files_ok=false
    fi
done

if [ "$all_files_ok" = false ]; then
    echo ""
    check_fail "文件完整性检查失败！"
    exit 1
fi

# 3. 检查后端状态
echo ""
echo "3. 检查后端状态..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    check_pass "后端正在运行"
else
    check_warn "后端未运行（需要手动启动）"
fi

# 4. 统计文件数量
echo ""
echo "4. 统计项目文件..."
desktop_files=$(find ~/FieldMind-Rebuild/fieldmind-desktop/Sources -name "*.swift" | wc -l | tr -d ' ')
check_pass "Swift 文件数量: $desktop_files"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "第二步：显示待删除的旧项目"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 显示待删除项目大小
echo "待删除的旧项目："
echo ""
if [ -d ~/FieldMind-Core ]; then
    size=$(du -sh ~/FieldMind-Core | cut -f1)
    echo "  📁 ~/FieldMind-Core/          ($size)"
else
    echo "  ✅ ~/FieldMind-Core/ 已删除或不存在"
fi

if [ -d ~/Desktop/FieldMindApp ]; then
    size=$(du -sh ~/Desktop/FieldMindApp | cut -f1)
    echo "  📁 ~/Desktop/FieldMindApp/    ($size)"
else
    echo "  ✅ ~/Desktop/FieldMindApp/ 已删除或不存在"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "第三步：删除确认"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$1" = "--auto-delete" ]; then
    echo "⚠️  自动删除模式..."
    DO_DELETE="yes"
else
    echo "⚠️  即将删除旧项目（此操作不可逆）"
    echo ""
    read -p "是否确认删除？(输入 yes 继续): " DO_DELETE
fi

echo ""

if [ "$DO_DELETE" = "yes" ]; then
    echo "开始删除..."
    echo ""

    # 删除 FieldMind-Core
    if [ -d ~/FieldMind-Core ]; then
        echo "删除 ~/FieldMind-Core/..."
        rm -rf ~/FieldMind-Core
        check_pass "~/FieldMind-Core/ 已删除"
    fi

    # 删除 Desktop/FieldMindApp
    if [ -d ~/Desktop/FieldMindApp ]; then
        echo "删除 ~/Desktop/FieldMindApp/..."
        rm -rf ~/Desktop/FieldMindApp
        check_pass "~/Desktop/FieldMindApp/ 已删除"
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    check_pass "清理完成！"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🎉 FieldMind 整合成功！"
    echo ""
    echo "最终项目位置："
    echo "  ~/FieldMind-Rebuild/"
    echo ""
    echo "启动方式："
    echo "  后端: cd ~/FieldMind-Rebuild/fieldmind-backend && python3 -m uvicorn app.main_simple:app --port 8000 --reload"
    echo "  前端: cd ~/FieldMind-Rebuild/fieldmind-desktop && swift run"
    echo ""
else
    echo "❌ 取消删除"
    echo ""
    echo "提示：确认整合无误后，可以手动删除："
    echo "  rm -rf ~/FieldMind-Core"
    echo "  rm -rf ~/Desktop/FieldMindApp"
    echo ""
    echo "或者再次运行此脚本并输入 'yes'"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "脚本执行完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
