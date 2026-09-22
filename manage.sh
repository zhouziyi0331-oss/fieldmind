#!/bin/bash
# FieldMind 管理脚本

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

case "$1" in
    start)
        echo -e "${GREEN}🚀 启动 FieldMind...${NC}"
        docker-compose up -d
        echo -e "${GREEN}✅ 服务已启动${NC}"
        docker-compose ps
        ;;

    stop)
        echo -e "${YELLOW}🛑 停止 FieldMind...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ 服务已停止${NC}"
        ;;

    restart)
        echo -e "${YELLOW}🔄 重启 FieldMind...${NC}"
        docker-compose restart
        echo -e "${GREEN}✅ 服务已重启${NC}"
        ;;

    logs)
        service="${2:-backend}"
        echo -e "${GREEN}📋 查看 $service 日志...${NC}"
        docker-compose logs -f "$service"
        ;;

    status)
        echo -e "${GREEN}📊 服务状态:${NC}"
        docker-compose ps
        echo ""
        echo -e "${GREEN}💾 磁盘使用:${NC}"
        df -h | grep -E "Filesystem|/app"
        echo ""
        echo -e "${GREEN}🐳 Docker 资源:${NC}"
        docker stats --no-stream
        ;;

    health)
        echo -e "${GREEN}❤️  健康检查:${NC}"
        echo ""

        # 后端
        echo -n "  后端服务: "
        if curl -sf http://localhost:8000/health/live > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 运行中${NC}"
        else
            echo -e "${RED}❌ 不可用${NC}"
        fi

        # Redis
        echo -n "  Redis: "
        if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 运行中${NC}"
        else
            echo -e "${RED}❌ 不可用${NC}"
        fi

        # Prometheus
        echo -n "  Prometheus: "
        if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 运行中${NC}"
        else
            echo -e "${RED}❌ 不可用${NC}"
        fi

        # Grafana
        echo -n "  Grafana: "
        if curl -sf http://localhost:3001/api/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 运行中${NC}"
        else
            echo -e "${RED}❌ 不可用${NC}"
        fi
        ;;

    backup)
        timestamp=$(date +%Y%m%d_%H%M%S)
        backup_dir="backups/$timestamp"

        echo -e "${GREEN}💾 备份数据...${NC}"
        mkdir -p "$backup_dir"

        # 备份数据库
        cp -r backend/data "$backup_dir/"
        echo "  ✅ 数据库已备份"

        # 备份日志
        cp -r backend/logs "$backup_dir/"
        echo "  ✅ 日志已备份"

        # 压缩
        tar -czf "$backup_dir.tar.gz" -C backups "$timestamp"
        rm -rf "$backup_dir"

        echo -e "${GREEN}✅ 备份完成: $backup_dir.tar.gz${NC}"
        ;;

    restore)
        if [ -z "$2" ]; then
            echo -e "${RED}❌ 请指定备份文件${NC}"
            echo "用法: $0 restore backups/20260818_120000.tar.gz"
            exit 1
        fi

        backup_file="$2"
        if [ ! -f "$backup_file" ]; then
            echo -e "${RED}❌ 备份文件不存在: $backup_file${NC}"
            exit 1
        fi

        echo -e "${YELLOW}📥 恢复数据...${NC}"

        # 停止服务
        docker-compose down

        # 解压备份
        temp_dir=$(mktemp -d)
        tar -xzf "$backup_file" -C "$temp_dir"

        # 恢复数据
        cp -r "$temp_dir"/*/data backend/
        cp -r "$temp_dir"/*/logs backend/

        # 清理
        rm -rf "$temp_dir"

        # 重启服务
        docker-compose up -d

        echo -e "${GREEN}✅ 数据恢复完成${NC}"
        ;;

    update)
        echo -e "${YELLOW}⬆️  更新 FieldMind...${NC}"

        # 备份
        ./manage.sh backup

        # 拉取代码
        git pull

        # 重新构建
        docker-compose build --no-cache

        # 重启服务
        docker-compose down
        docker-compose up -d

        echo -e "${GREEN}✅ 更新完成${NC}"
        ;;

    clean)
        echo -e "${YELLOW}🧹 清理未使用的资源...${NC}"

        docker system prune -f
        docker volume prune -f

        echo -e "${GREEN}✅ 清理完成${NC}"
        ;;

    shell)
        service="${2:-backend}"
        echo -e "${GREEN}🐚 进入 $service 容器...${NC}"
        docker-compose exec "$service" /bin/bash
        ;;

    *)
        echo "FieldMind 管理脚本"
        echo ""
        echo "用法: $0 {命令} [选项]"
        echo ""
        echo "命令:"
        echo "  start           启动所有服务"
        echo "  stop            停止所有服务"
        echo "  restart         重启所有服务"
        echo "  logs [服务]     查看日志 (默认: backend)"
        echo "  status          查看服务状态"
        echo "  health          健康检查"
        echo "  backup          备份数据"
        echo "  restore <文件>  恢复数据"
        echo "  update          更新系统"
        echo "  clean           清理未使用资源"
        echo "  shell [服务]    进入容器 (默认: backend)"
        echo ""
        echo "示例:"
        echo "  $0 start"
        echo "  $0 logs backend"
        echo "  $0 backup"
        echo "  $0 restore backups/20260818_120000.tar.gz"
        exit 1
        ;;
esac
