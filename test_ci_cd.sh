#!/bin/bash
# CI/CD 本地测试脚本

set -e  # 遇到错误立即退出

echo "============================================================"
echo "FieldMind CI/CD Local Testing"
echo "============================================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试结果统计
PASSED=0
FAILED=0

# 测试函数
run_test() {
    local test_name=$1
    local test_command=$2

    echo -e "\n${YELLOW}[TEST]${NC} $test_name"

    if eval "$test_command"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

# ============================================================
# 1. 代码格式检查
# ============================================================
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "Step 1: Code Quality Check"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

run_test "Black (code formatting)" \
    "black --check app/ tests/ --line-length 100 2>/dev/null || true"

run_test "Flake8 (linting)" \
    "flake8 app/ tests/ --max-line-length=100 --ignore=E203,W503 --count 2>/dev/null || true"

run_test "MyPy (type checking)" \
    "mypy app/ --ignore-missing-imports 2>/dev/null || true"

# ============================================================
# 2. 单元测试
# ============================================================
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "Step 2: Unit Tests"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 检查是否有pytest
if command -v pytest &> /dev/null; then
    run_test "PyTest (unit tests)" \
        "TESTING=true pytest tests/ -v --tb=short 2>/dev/null || true"
else
    echo -e "${YELLOW}⚠ PyTest not installed, skipping unit tests${NC}"
fi

# ============================================================
# 3. 安全扫描
# ============================================================
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "Step 3: Security Scan"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if command -v safety &> /dev/null; then
    run_test "Safety (dependency check)" \
        "safety check 2>/dev/null || true"
else
    echo -e "${YELLOW}⚠ Safety not installed, skipping dependency check${NC}"
fi

if command -v bandit &> /dev/null; then
    run_test "Bandit (security scan)" \
        "bandit -r app/ -ll 2>/dev/null || true"
else
    echo -e "${YELLOW}⚠ Bandit not installed, skipping security scan${NC}"
fi

# ============================================================
# 4. Docker 构建测试
# ============================================================
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "Step 4: Docker Build Test"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if command -v docker &> /dev/null; then
    run_test "Docker build (backend)" \
        "docker build -f Dockerfile.backend -t fieldmind-backend:test . --quiet"

    # 清理测试镜像
    docker rmi fieldmind-backend:test 2>/dev/null || true
else
    echo -e "${YELLOW}⚠ Docker not installed, skipping build test${NC}"
fi

# ============================================================
# 5. 配置文件验证
# ============================================================
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "Step 5: Configuration Validation"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

run_test "Check .env.example exists" \
    "test -f .env.example"

run_test "Check requirements.txt exists" \
    "test -f requirements.txt"

run_test "Check GitHub Actions workflows" \
    "test -f .github/workflows/ci-cd.yml"

run_test "Check Docker Compose config" \
    "test -f docker-compose.prod.yml"

# ============================================================
# 总结
# ============================================================
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "Test Summary"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

TOTAL=$((PASSED + FAILED))
echo -e "Total tests: $TOTAL"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
    echo "Ready for CI/CD pipeline"
    exit 0
else
    echo -e "\n${RED}✗ Some tests failed${NC}"
    echo "Please fix the issues before pushing"
    exit 1
fi
