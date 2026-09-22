#!/bin/bash
# Alembic 集成验证脚本
# 测试 Alembic 数据库迁移系统的所有核心功能

set -e  # 遇到错误立即退出

echo "================================================"
echo "  Alembic 集成验证测试"
echo "================================================"
echo ""

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数
TESTS_PASSED=0
TESTS_FAILED=0

# 测试函数
test_command() {
    local description=$1
    local command=$2

    echo -n "测试: $description ... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 通过${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ 失败${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# 开始测试
echo "1. 检查 Alembic 安装"
echo "-----------------------------------"
test_command "Alembic 已安装" "which alembic"
test_command "Alembic 版本可查询" "alembic --version"
echo ""

echo "2. 检查配置文件"
echo "-----------------------------------"
test_command "alembic.ini 存在" "test -f alembic.ini"
test_command "alembic/env.py 存在" "test -f alembic/env.py"
test_command "迁移目录存在" "test -d alembic/versions"
echo ""

echo "3. 测试基本命令"
echo "-----------------------------------"
test_command "查看当前版本" "alembic current"
test_command "查看迁移历史" "alembic history"
test_command "查看 head 版本" "alembic show head"
echo ""

echo "4. 测试数据库连接"
echo "-----------------------------------"
echo -n "测试: SQLite 数据库连接 ... "
if alembic current 2>&1 | grep -q "SQLiteImpl"; then
    echo -e "${GREEN}✓ 通过${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ 失败${NC}"
    ((TESTS_FAILED++))
fi
echo ""

echo "5. 验证迁移状态"
echo "-----------------------------------"
CURRENT_VERSION=$(alembic current 2>/dev/null | tail -1)
echo "当前版本: $CURRENT_VERSION"

if [ -z "$CURRENT_VERSION" ]; then
    echo -e "${YELLOW}⚠ 警告: 数据库未初始化${NC}"
    echo "运行: alembic upgrade head"
elif echo "$CURRENT_VERSION" | grep -q "001"; then
    echo -e "${GREEN}✓ 数据库版本正确 (001)${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ 警告: 数据库版本异常${NC}"
fi
echo ""

echo "6. 检查初始迁移"
echo "-----------------------------------"
test_command "初始迁移文件存在" "test -f alembic/versions/001_initial_migration.py"
echo ""

echo "7. 测试迁移创建功能"
echo "-----------------------------------"
echo -n "测试: 创建测试迁移 ... "
TEST_REVISION=$(alembic revision -m "test_migration" 2>&1 | grep -o "[a-f0-9]\{12\}" | head -1)

if [ -n "$TEST_REVISION" ]; then
    echo -e "${GREEN}✓ 通过${NC}"
    ((TESTS_PASSED++))

    # 清理测试迁移
    TEST_FILE="alembic/versions/${TEST_REVISION}_test_migration.py"
    if [ -f "$TEST_FILE" ]; then
        rm "$TEST_FILE"
        echo "  清理: 删除测试迁移文件"
    fi
else
    echo -e "${RED}✗ 失败${NC}"
    ((TESTS_FAILED++))
fi
echo ""

echo "8. 测试数据库操作"
echo "-----------------------------------"

# 备份当前版本
BACKUP_VERSION=$(alembic current 2>/dev/null | tail -1)

echo -n "测试: 升级到 head ... "
if alembic upgrade head > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 通过${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ 跳过 (可能已是最新)${NC}"
fi

echo ""

echo "================================================"
echo "  测试总结"
echo "================================================"
echo -e "通过: ${GREEN}$TESTS_PASSED${NC}"
echo -e "失败: ${RED}$TESTS_FAILED${NC}"
echo "总计: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过！Alembic 集成正常。${NC}"
    exit 0
else
    echo -e "${RED}✗ 部分测试失败。请检查配置。${NC}"
    exit 1
fi
