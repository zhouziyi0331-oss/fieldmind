#!/bin/bash
# FieldMind 生产环境部署脚本

set -e  # 遇到错误立即退出

echo "================================================"
echo "  FieldMind 生产环境部署"
echo "================================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ 请使用 root 权限运行此脚本${NC}"
    exit 1
fi

# 检查 Docker 和 Docker Compose
echo -e "\n${YELLOW}[1/8] 检查依赖...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose 未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker 和 Docker Compose 已安装${NC}"

# 检查环境变量文件
echo -e "\n${YELLOW}[2/8] 检查环境配置...${NC}"
if [ ! -f .env.production ]; then
    echo -e "${RED}❌ .env.production 文件不存在${NC}"
    echo -e "${YELLOW}请复制 .env.production.template 为 .env.production 并填入实际值${NC}"
    exit 1
fi

# 检查关键环境变量
source .env.production
if [ "$SECRET_KEY" == "CHANGE_THIS_TO_RANDOM_SECRET_KEY" ]; then
    echo -e "${RED}❌ 请修改 .env.production 中的 SECRET_KEY${NC}"
    exit 1
fi

if [ "$DB_PASSWORD" == "CHANGE_THIS_STRONG_PASSWORD" ]; then
    echo -e "${RED}❌ 请修改 .env.production 中的 DB_PASSWORD${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 环境配置检查通过${NC}"

# 创建必要的目录
echo -e "\n${YELLOW}[3/8] 创建必要目录...${NC}"
mkdir -p nginx/ssl
mkdir -p prometheus
mkdir -p grafana/dashboards
mkdir -p grafana/datasources
mkdir -p backups
echo -e "${GREEN}✅ 目录创建完成${NC}"

# 备份旧版本（如果存在）
echo -e "\n${YELLOW}[4/8] 备份数据...${NC}"
if [ -d "data" ]; then
    BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    tar -czf "backups/$BACKUP_NAME" data/
    echo -e "${GREEN}✅ 数据已备份到 backups/$BACKUP_NAME${NC}"
else
    echo -e "${YELLOW}⏭️  无需备份（首次部署）${NC}"
fi

# 停止旧容器
echo -e "\n${YELLOW}[5/8] 停止旧容器...${NC}"
docker-compose -f docker-compose.prod.yml down || true
echo -e "${GREEN}✅ 旧容器已停止${NC}"

# 拉取最新镜像
echo -e "\n${YELLOW}[6/8] 拉取镜像...${NC}"
docker-compose -f docker-compose.prod.yml pull
echo -e "${GREEN}✅ 镜像拉取完成${NC}"

# 构建并启动服务
echo -e "\n${YELLOW}[7/8] 启动服务...${NC}"
docker-compose -f docker-compose.prod.yml up -d --build
echo -e "${GREEN}✅ 服务已启动${NC}"

# 等待服务就绪
echo -e "\n${YELLOW}[8/8] 等待服务就绪...${NC}"
sleep 10

# 运行数据库迁移
echo -e "${YELLOW}运行数据库迁移...${NC}"
docker-compose -f docker-compose.prod.yml exec -T backend python migrations/add_performance_indexes.py || true

# 健康检查
echo -e "\n${YELLOW}执行健康检查...${NC}"
for i in {1..30}; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo -e "${GREEN}✅ 后端服务健康检查通过${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ 后端服务健康检查失败${NC}"
        echo -e "${YELLOW}查看日志: docker-compose -f docker-compose.prod.yml logs backend${NC}"
        exit 1
    fi
    sleep 2
done

# 显示状态
echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}  部署成功！${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "服务访问地址:"
echo "  - 后端 API: http://localhost:8000"
echo "  - API 文档: http://localhost:8000/docs"
echo "  - Grafana: http://localhost:3001 (admin / ${GRAFANA_PASSWORD})"
echo "  - Prometheus: http://localhost:9090"
echo ""
echo "查看日志:"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "停止服务:"
echo "  docker-compose -f docker-compose.prod.yml down"
echo ""
echo "重启服务:"
echo "  docker-compose -f docker-compose.prod.yml restart"
echo ""

# 显示容器状态
echo "容器状态:"
docker-compose -f docker-compose.prod.yml ps
