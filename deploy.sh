#!/bin/bash

# FieldMind Deployment Script
# 用于部署FieldMind到生产环境

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
DEPLOY_ENV=${1:-production}
BUILD_IMAGE=${2:-true}

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}FieldMind Deployment Script${NC}"
echo -e "${GREEN}Environment: ${DEPLOY_ENV}${NC}"
echo -e "${GREEN}=====================================${NC}"

# 检查环境
check_requirements() {
    echo -e "${YELLOW}检查部署要求...${NC}"

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误: Docker未安装${NC}"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}错误: Docker Compose未安装${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Docker已安装${NC}"
    echo -e "${GREEN}✓ Docker Compose已安装${NC}"
}

# 检查环境配置文件
check_env_file() {
    echo -e "${YELLOW}检查环境配置...${NC}"

    if [ ! -f "fieldmind-backend/.env.${DEPLOY_ENV}" ]; then
        echo -e "${RED}错误: 环境配置文件不存在: .env.${DEPLOY_ENV}${NC}"
        echo -e "${YELLOW}请从 .env.example 创建配置文件${NC}"
        exit 1
    fi

    # 检查关键配置
    if grep -q "your-secret-key-change-in-production" "fieldmind-backend/.env.${DEPLOY_ENV}"; then
        echo -e "${RED}警告: SECRET_KEY未更改，请修改生产环境密钥！${NC}"
        if [ "$DEPLOY_ENV" = "production" ]; then
            exit 1
        fi
    fi

    echo -e "${GREEN}✓ 环境配置文件存在${NC}"
}

# 备份数据库
backup_database() {
    if [ "$DEPLOY_ENV" = "production" ]; then
        echo -e "${YELLOW}备份生产数据库...${NC}"

        BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"

        if [ -f "fieldmind-backend/data/fieldmind.db" ]; then
            cp "fieldmind-backend/data/fieldmind.db" "$BACKUP_DIR/"
            echo -e "${GREEN}✓ 数据库已备份到: $BACKUP_DIR${NC}"
        else
            echo -e "${YELLOW}! 未找到数据库文件（首次部署？）${NC}"
        fi
    fi
}

# 构建Docker镜像
build_images() {
    if [ "$BUILD_IMAGE" = "true" ]; then
        echo -e "${YELLOW}构建Docker镜像...${NC}"

        # 构建backend镜像
        if [ "$DEPLOY_ENV" = "production" ]; then
            docker build -t fieldmind/backend:latest \
                -f fieldmind-backend/Dockerfile.prod \
                fieldmind-backend/
        else
            docker build -t fieldmind/backend:latest \
                -f fieldmind-backend/Dockerfile \
                fieldmind-backend/
        fi

        echo -e "${GREEN}✓ Backend镜像构建完成${NC}"
    else
        echo -e "${YELLOW}跳过镜像构建${NC}"
    fi
}

# 启动服务
start_services() {
    echo -e "${YELLOW}启动服务...${NC}"

    # 复制环境配置
    cp "fieldmind-backend/.env.${DEPLOY_ENV}" "fieldmind-backend/.env"

    # 启动docker-compose
    docker-compose -f docker-compose.full.yml up -d

    echo -e "${GREEN}✓ 服务已启动${NC}"
}

# 运行数据库迁移
run_migrations() {
    echo -e "${YELLOW}运行数据库迁移...${NC}"

    # 等待backend启动
    echo "等待backend启动..."
    sleep 10

    # 运行Alembic迁移
    docker-compose -f docker-compose.full.yml exec -T backend \
        alembic upgrade head || true

    echo -e "${GREEN}✓ 数据库迁移完成${NC}"
}

# 健康检查
health_check() {
    echo -e "${YELLOW}执行健康检查...${NC}"

    MAX_RETRIES=30
    RETRY_COUNT=0

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 服务健康检查通过${NC}"
            return 0
        fi

        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "等待服务启动... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 2
    done

    echo -e "${RED}错误: 服务健康检查失败${NC}"
    docker-compose -f docker-compose.full.yml logs backend
    exit 1
}

# 显示部署信息
show_info() {
    echo -e "${GREEN}=====================================${NC}"
    echo -e "${GREEN}部署完成！${NC}"
    echo -e "${GREEN}=====================================${NC}"
    echo ""
    echo -e "API地址: ${GREEN}http://localhost:8000${NC}"
    echo -e "API文档: ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "Neo4j浏览器: ${GREEN}http://localhost:7474${NC}"
    echo ""
    echo -e "查看日志: ${YELLOW}docker-compose -f docker-compose.full.yml logs -f${NC}"
    echo -e "停止服务: ${YELLOW}docker-compose -f docker-compose.full.yml down${NC}"
    echo ""
}

# 主流程
main() {
    check_requirements
    check_env_file
    backup_database
    build_images
    start_services
    run_migrations
    health_check
    show_info
}

# 错误处理
trap 'echo -e "${RED}部署失败！${NC}"; exit 1' ERR

# 执行主流程
main
