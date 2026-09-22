#!/bin/bash
# FieldMind 基础设施快速启动脚本

set -e

echo "======================================"
echo "FieldMind 基础设施启动"
echo "======================================"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 启动所有服务
echo ""
echo "启动服务..."
docker-compose up -d

# 等待服务启动
echo ""
echo "等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "======================================"
echo "服务状态检查"
echo "======================================"

# 检查MinIO
if curl -s http://localhost:9000/minio/health/live > /dev/null; then
    echo "✅ MinIO: 运行中"
    echo "   API: http://localhost:9000"
    echo "   Console: http://localhost:9001"
    echo "   用户名: minioadmin"
    echo "   密码: minioadmin"
else
    echo "❌ MinIO: 未运行"
fi

# 检查MySQL
if docker exec fieldmind-mysql mysqladmin ping -h localhost --silent > /dev/null 2>&1; then
    echo "✅ MySQL: 运行中"
    echo "   地址: localhost:3306"
    echo "   数据库: fieldmind"
    echo "   用户名: fieldmind"
    echo "   密码: fieldmind123"
else
    echo "❌ MySQL: 未运行"
fi

# 检查Redis
if docker exec fieldmind-redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis: 运行中"
    echo "   地址: localhost:6379"
else
    echo "❌ Redis: 未运行"
fi

echo ""
echo "======================================"
echo "下一步操作"
echo "======================================"
echo "1. 配置环境变量："
echo "   cp .env.example .env"
echo "   编辑 .env 文件"
echo ""
echo "2. 运行数据库迁移："
echo "   python src/app/core/migrate.py migrate"
echo ""
echo "3. 测试对象存储："
echo "   python test_storage.py"
echo ""
echo "4. 查看服务日志："
echo "   docker-compose logs -f"
echo ""
echo "5. 停止所有服务："
echo "   docker-compose down"
echo ""
