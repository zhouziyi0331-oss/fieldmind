#!/bin/bash
# Locust 压力测试运行脚本

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "  FieldMind 压力测试"
echo "=========================================="
echo ""

# 检查 Locust
if ! command -v locust &> /dev/null; then
    echo -e "${YELLOW}⚠️  Locust 未安装，正在安装...${NC}"
    pip install locust
fi

# 检查后端服务
echo "1. 检查后端服务..."
if ! curl -sf http://localhost:8000/health/live > /dev/null 2>&1; then
    echo -e "${RED}❌ 后端服务未运行${NC}"
    echo "请先启动后端服务"
    exit 1
fi
echo -e "${GREEN}✅ 后端服务正常${NC}"

# 测试模式选择
echo ""
echo "请选择测试模式:"
echo "  1) 快速测试 (10用户, 1分钟)"
echo "  2) 标准测试 (50用户, 5分钟)"
echo "  3) 压力测试 (100用户, 10分钟)"
echo "  4) 峰值测试 (200用户, 15分钟)"
echo "  5) 持久测试 (50用户, 60分钟)"
echo "  6) Web UI 模式"
echo ""
read -p "选择 (1-6): " choice

case $choice in
    1)
        echo -e "${GREEN}🚀 启动快速测试...${NC}"
        locust -f tests/load/locustfile.py \
            --host=http://localhost:8000 \
            --users=10 \
            --spawn-rate=2 \
            --run-time=1m \
            --headless \
            --html=load_test_report_quick.html
        ;;
    2)
        echo -e "${GREEN}🚀 启动标准测试...${NC}"
        locust -f tests/load/locustfile.py \
            --host=http://localhost:8000 \
            --users=50 \
            --spawn-rate=5 \
            --run-time=5m \
            --headless \
            --html=load_test_report_standard.html
        ;;
    3)
        echo -e "${GREEN}🚀 启动压力测试...${NC}"
        locust -f tests/load/locustfile.py \
            --host=http://localhost:8000 \
            --users=100 \
            --spawn-rate=10 \
            --run-time=10m \
            --headless \
            --html=load_test_report_stress.html
        ;;
    4)
        echo -e "${GREEN}🚀 启动峰值测试...${NC}"
        locust -f tests/load/locustfile.py \
            --host=http://localhost:8000 \
            --users=200 \
            --spawn-rate=20 \
            --run-time=15m \
            --headless \
            --html=load_test_report_peak.html
        ;;
    5)
        echo -e "${GREEN}🚀 启动持久测试...${NC}"
        locust -f tests/load/locustfile.py \
            --host=http://localhost:8000 \
            --users=50 \
            --spawn-rate=5 \
            --run-time=60m \
            --headless \
            --html=load_test_report_endurance.html
        ;;
    6)
        echo -e "${GREEN}🚀 启动 Web UI 模式...${NC}"
        echo ""
        echo "访问 http://localhost:8089 来控制测试"
        echo "按 Ctrl+C 停止测试"
        echo ""
        locust -f tests/load/locustfile.py \
            --host=http://localhost:8000
        ;;
    *)
        echo -e "${RED}❌ 无效选择${NC}"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo -e "${GREEN}✅ 测试完成${NC}"
echo "=========================================="
echo ""
echo "报告文件已生成，请查看 HTML 报告"
