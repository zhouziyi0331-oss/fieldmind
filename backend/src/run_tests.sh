#!/bin/bash

# FieldMind Backend 测试运行脚本
# 运行完整的测试套件并生成报告

echo "=========================================="
echo "  FieldMind Backend 测试套件"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 pytest 是否安装
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}✗ pytest 未安装${NC}"
    echo "请运行: pip3 install pytest pytest-asyncio httpx"
    exit 1
fi

echo -e "${GREEN}✓ pytest 已安装${NC}"
echo ""

# 运行测试
echo "运行测试..."
echo "----------------------------------------"

python3 -m pytest tests/ -v --tb=short

TEST_EXIT_CODE=$?

echo ""
echo "=========================================="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过！${NC}"
else
    echo -e "${RED}✗ 部分测试失败${NC}"
fi

echo "=========================================="

exit $TEST_EXIT_CODE
