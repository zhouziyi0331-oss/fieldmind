#!/bin/bash
# 启动监控栈

set -e

echo "🚀 Starting FieldMind Monitoring Stack..."
echo ""

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

# 检查docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed"
    exit 1
fi

# 创建网络（如果不存在）
if ! docker network ls | grep -q fieldmind-network; then
    echo "📡 Creating fieldmind-network..."
    docker network create fieldmind-network
fi

# 检查环境变量
if [ ! -f .env ]; then
    echo "⚠️  .env file not found, using defaults"
fi

# 启动监控服务
echo "🔧 Starting monitoring services..."
docker-compose -f docker-compose.monitoring.yml up -d

echo ""
echo "✅ Monitoring stack started successfully!"
echo ""
echo "📊 Access points:"
echo "  Prometheus:    http://localhost:9090"
echo "  Grafana:       http://localhost:3000 (admin/admin)"
echo "  Alertmanager:  http://localhost:9093"
echo ""
echo "📝 Checking service health..."
sleep 5

# 健康检查
check_service() {
    local name=$1
    local url=$2
    if curl -sf "$url" > /dev/null 2>&1; then
        echo "  ✓ $name is healthy"
    else
        echo "  ✗ $name is not responding"
    fi
}

check_service "Prometheus" "http://localhost:9090/-/healthy"
check_service "Grafana" "http://localhost:3000/api/health"
check_service "Alertmanager" "http://localhost:9093/-/healthy"

echo ""
echo "💡 Tips:"
echo "  - View logs: docker-compose -f docker-compose.monitoring.yml logs -f"
echo "  - Stop stack: docker-compose -f docker-compose.monitoring.yml down"
echo "  - Restart: docker-compose -f docker-compose.monitoring.yml restart"
