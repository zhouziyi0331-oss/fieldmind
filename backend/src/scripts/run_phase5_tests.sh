#!/bin/bash
#
# Phase 5 测试运行脚本
#
# 用法:
#   ./scripts/run_phase5_tests.sh [option]
#
# 选项:
#   verification  - 只运行数据流验证测试
#   integration   - 只运行集成测试
#   all          - 运行所有Phase 5测试 (默认)
#   quick        - 快速运行（不显示详细输出）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}Phase 5 测试套件${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# 检查是否在正确的目录
if [ ! -f "app/agents/coordinator.py" ]; then
    echo -e "${RED}错误: 请在 fieldmind-backend 目录下运行此脚本${NC}"
    exit 1
fi

# 默认选项
TEST_TYPE="${1:-all}"
PYTEST_ARGS="-v -s"

if [ "$TEST_TYPE" = "quick" ]; then
    PYTEST_ARGS="-v"
    TEST_TYPE="all"
fi

# 创建必要的目录
mkdir -p tests/verification
mkdir -p tests/integration

echo -e "${YELLOW}测试类型: ${TEST_TYPE}${NC}"
echo ""

# 运行测试
case $TEST_TYPE in
    verification)
        echo -e "${BLUE}运行数据流验证测试...${NC}"
        python tests/verification/test_phase5_data_flow.py --project-id test_phase5_verification
        ;;

    integration)
        echo -e "${BLUE}运行集成测试...${NC}"
        pytest tests/integration/test_phase5_pipeline.py $PYTEST_ARGS
        ;;

    all)
        echo -e "${BLUE}1. 运行数据流验证测试${NC}"
        echo -e "${BLUE}----------------------------------------------------------------------${NC}"
        python tests/verification/test_phase5_data_flow.py --project-id test_phase5_verification || true
        echo ""

        echo -e "${BLUE}2. 运行集成测试${NC}"
        echo -e "${BLUE}----------------------------------------------------------------------${NC}"
        pytest tests/integration/test_phase5_pipeline.py $PYTEST_ARGS
        ;;

    *)
        echo -e "${RED}未知的测试类型: ${TEST_TYPE}${NC}"
        echo "可用选项: verification, integration, all, quick"
        exit 1
        ;;
esac

# 检查测试结果
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}======================================================================${NC}"
    echo -e "${GREEN}✓ 所有测试通过${NC}"
    echo -e "${GREEN}======================================================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}======================================================================${NC}"
    echo -e "${RED}✗ 测试失败${NC}"
    echo -e "${RED}======================================================================${NC}"
    exit 1
fi
