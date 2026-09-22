#!/bin/bash
# FieldMind 启动脚本

set -e

echo "========================================="
echo "启动 FieldMind"
echo "========================================="

# 检查环境配置
if [ ! -f .env.production ]; then
    echo "错误: .env.production 不存在"
    echo "请先运行: ./setup_production.sh"
    exit 1
fi

# 检查是否已初始化数据库
if [ ! -f backend/data/.db_initialized ]; then
    echo "初始化数据库..."
    docker-compose -f docker-compose.prod.yml run --rm backend python init_db.py
    touch backend/data/.db_initialized
    echo "✓ 数据库初始化完成"
fi

# 启动服务
echo "启动 Docker 服务..."
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo "✓ FieldMind 已启动!"
echo ""
echo "访问地址:"
echo "  - 前端: http://localhost"
echo "  - API: http://localhost/api"
echo "  - API 文档: http://localhost/api/docs"
echo "  - Grafana 监控: http://localhost:3000"
echo ""
echo "查看日志: docker-compose -f docker-compose.prod.yml logs -f"
echo "停止服务: docker-compose -f docker-compose.prod.yml down"
