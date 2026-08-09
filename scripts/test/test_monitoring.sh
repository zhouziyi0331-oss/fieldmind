#!/bin/bash
# 测试监控系统集成

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

passed=0
failed=0

run_test() {
    local name=$1
    local command=$2

    echo -n "Testing $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((passed++))
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((failed++))
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "FieldMind Monitoring System Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================================
# Stage 1: 配置文件验证
# ============================================================================
echo "Stage 1: Configuration Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test "Prometheus config exists" "test -f prometheus.yml"
run_test "Alertmanager config exists" "test -f alertmanager.yml"
run_test "Monitoring compose file exists" "test -f docker-compose.monitoring.yml"
run_test "Alert rules directory exists" "test -d alerts"
run_test "Application alerts exist" "test -f alerts/application.yml"
run_test "Database alerts exist" "test -f alerts/database.yml"
run_test "Infrastructure alerts exist" "test -f alerts/infrastructure.yml"

echo ""

# ============================================================================
# Stage 2: Python模块检查
# ============================================================================
echo "Stage 2: Python Modules"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test "Metrics module exists" "test -f app/core/metrics.py"
run_test "Metrics middleware exists" "test -f app/middleware/metrics_middleware.py"
run_test "Metrics API exists" "test -f app/api/metrics.py"

# 检查metrics.py语法
run_test "Metrics module syntax" "python3 -m py_compile app/core/metrics.py"
run_test "Metrics middleware syntax" "python3 -m py_compile app/middleware/metrics_middleware.py"
run_test "Metrics API syntax" "python3 -m py_compile app/api/metrics.py"

echo ""

# ============================================================================
# Stage 3: 导入测试
# ============================================================================
echo "Stage 3: Import Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test "Import metrics module" "python3 -c 'from app.core.metrics import http_requests_total'"
run_test "Import metrics middleware" "python3 -c 'from app.middleware.metrics_middleware import MetricsMiddleware'"
run_test "Import prometheus_client" "python3 -c 'import prometheus_client'"

echo ""

# ============================================================================
# Stage 4: Grafana仪表板
# ============================================================================
echo "Stage 4: Grafana Dashboards"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test "Grafana directories exist" "test -d grafana/dashboards && test -d grafana/provisioning"
run_test "Infrastructure dashboard exists" "test -f grafana/dashboards/infrastructure.json"
run_test "Application dashboard exists" "test -f grafana/dashboards/application.json"
run_test "Datasource config exists" "test -f grafana/provisioning/datasources/prometheus.yml"
run_test "Dashboard provisioning config exists" "test -f grafana/provisioning/dashboards/dashboards.yml"

# 验证JSON格式
run_test "Infrastructure dashboard JSON valid" "python3 -m json.tool grafana/dashboards/infrastructure.json"
run_test "Application dashboard JSON valid" "python3 -m json.tool grafana/dashboards/application.json"

echo ""

# ============================================================================
# Stage 5: YAML配置验证
# ============================================================================
echo "Stage 5: YAML Configuration Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查YAML语法
run_test "Prometheus config YAML valid" "python3 -c 'import yaml; yaml.safe_load(open(\"prometheus.yml\"))'"
run_test "Alertmanager config YAML valid" "python3 -c 'import yaml; yaml.safe_load(open(\"alertmanager.yml\"))'"
run_test "Application alerts YAML valid" "python3 -c 'import yaml; yaml.safe_load(open(\"alerts/application.yml\"))'"
run_test "Database alerts YAML valid" "python3 -c 'import yaml; yaml.safe_load(open(\"alerts/database.yml\"))'"
run_test "Infrastructure alerts YAML valid" "python3 -c 'import yaml; yaml.safe_load(open(\"alerts/infrastructure.yml\"))'"
run_test "Docker compose monitoring YAML valid" "python3 -c 'import yaml; yaml.safe_load(open(\"docker-compose.monitoring.yml\"))'"

echo ""

# ============================================================================
# Stage 6: 启动脚本
# ============================================================================
echo "Stage 6: Scripts"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test "Monitoring start script exists" "test -f start_monitoring.sh"
run_test "Start script is executable" "test -x start_monitoring.sh"

echo ""

# ============================================================================
# Stage 7: Docker检查 (可选)
# ============================================================================
echo "Stage 7: Docker Environment (optional)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker is installed"
    run_test "Docker is running" "docker info"

    if command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}✓${NC} docker-compose is installed"
        run_test "Monitoring compose config valid" "docker-compose -f docker-compose.monitoring.yml config"
    else
        echo -e "${YELLOW}⚠${NC} docker-compose not installed (optional)"
    fi
else
    echo -e "${YELLOW}⚠${NC} Docker not installed (optional for testing)"
fi

echo ""

# ============================================================================
# 结果汇总
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test Results"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Total tests: $((passed + failed))"
echo -e "${GREEN}Passed: $passed${NC}"
echo -e "${RED}Failed: $failed${NC}"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "🚀 Ready to start monitoring stack:"
    echo "   ./start_monitoring.sh"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "Please fix the issues before starting the monitoring stack."
    exit 1
fi
