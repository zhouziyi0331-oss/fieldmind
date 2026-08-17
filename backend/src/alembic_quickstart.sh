#!/bin/bash
# Alembic 数据库迁移快速启动脚本

set -e

echo "🚀 FieldMind Backend - Alembic 数据库迁移工具"
echo "=============================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Alembic 是否安装
if ! python3 -m alembic --version &> /dev/null; then
    echo -e "${RED}❌ Alembic 未安装${NC}"
    echo "正在安装 Alembic..."
    pip install alembic==1.15.2
    echo -e "${GREEN}✅ Alembic 安装完成${NC}"
fi

# 显示菜单
show_menu() {
    echo ""
    echo "请选择操作："
    echo "  1) 查看当前迁移状态"
    echo "  2) 应用所有迁移 (upgrade head)"
    echo "  3) 回滚上一个迁移 (downgrade -1)"
    echo "  4) 查看迁移历史"
    echo "  5) 创建新迁移（自动检测变更）"
    echo "  6) 回滚到初始状态 (downgrade base)"
    echo "  7) 显示帮助"
    echo "  q) 退出"
    echo ""
}

# 查看当前状态
check_current() {
    echo -e "${YELLOW}📊 当前迁移状态：${NC}"
    python3 -m alembic current
    echo ""
    echo -e "${YELLOW}📋 数据库表：${NC}"
    python3 -c "
import sys
sys.path.insert(0, '.')
from app.core.database import Base
from app.models import *
print(f'共有 {len(Base.metadata.tables)} 个表：')
for table_name in sorted(Base.metadata.tables.keys()):
    print(f'  - {table_name}')
" 2>/dev/null || echo "无法连接到数据库"
}

# 应用迁移
upgrade_head() {
    echo -e "${YELLOW}⬆️  正在应用所有迁移...${NC}"
    python3 -m alembic upgrade head
    echo -e "${GREEN}✅ 迁移应用完成${NC}"
}

# 回滚迁移
downgrade_one() {
    echo -e "${YELLOW}⬇️  正在回滚上一个迁移...${NC}"
    python3 -m alembic downgrade -1
    echo -e "${GREEN}✅ 回滚完成${NC}"
}

# 查看历史
show_history() {
    echo -e "${YELLOW}📜 迁移历史：${NC}"
    python3 -m alembic history --verbose
}

# 创建新迁移
create_migration() {
    echo -e "${YELLOW}📝 创建新迁移${NC}"
    read -p "请输入迁移描述: " description
    if [ -z "$description" ]; then
        echo -e "${RED}❌ 描述不能为空${NC}"
        return
    fi
    echo "正在生成迁移脚本..."
    python3 -m alembic revision --autogenerate -m "$description"
    echo -e "${GREEN}✅ 迁移脚本已创建${NC}"
    echo "请检查生成的文件后再应用迁移"
}

# 回滚到初始
downgrade_base() {
    echo -e "${RED}⚠️  警告：这将回滚所有迁移并删除所有表！${NC}"
    read -p "确定要继续吗？(yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        echo -e "${YELLOW}⬇️  正在回滚所有迁移...${NC}"
        python3 -m alembic downgrade base
        echo -e "${GREEN}✅ 已回滚到初始状态${NC}"
    else
        echo "操作已取消"
    fi
}

# 显示帮助
show_help() {
    echo -e "${GREEN}📖 Alembic 常用命令：${NC}"
    echo ""
    echo "查看状态："
    echo "  alembic current              - 查看当前版本"
    echo "  alembic history              - 查看迁移历史"
    echo ""
    echo "应用迁移："
    echo "  alembic upgrade head         - 升级到最新版本"
    echo "  alembic upgrade +1           - 升级一个版本"
    echo "  alembic upgrade 001          - 升级到指定版本"
    echo ""
    echo "回滚迁移："
    echo "  alembic downgrade -1         - 回滚一个版本"
    echo "  alembic downgrade 001        - 回滚到指定版本"
    echo "  alembic downgrade base       - 回滚所有迁移"
    echo ""
    echo "创建迁移："
    echo "  alembic revision --autogenerate -m \"描述\"  - 自动检测变更"
    echo "  alembic revision -m \"描述\"                 - 手动创建迁移"
    echo ""
    echo -e "${YELLOW}💡 提示：${NC}"
    echo "  - 始终先在开发环境测试迁移"
    echo "  - 生产环境迁移前备份数据库"
    echo "  - 审查自动生成的迁移脚本"
    echo "  - 详细文档请查看 ALEMBIC_GUIDE.md"
}

# 主循环
main() {
    while true; do
        show_menu
        read -p "请输入选项: " choice

        case $choice in
            1)
                check_current
                ;;
            2)
                upgrade_head
                ;;
            3)
                downgrade_one
                ;;
            4)
                show_history
                ;;
            5)
                create_migration
                ;;
            6)
                downgrade_base
                ;;
            7)
                show_help
                ;;
            q|Q)
                echo "👋 再见！"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 无效选项，请重试${NC}"
                ;;
        esac
    done
}

# 如果有参数，直接执行命令
if [ $# -gt 0 ]; then
    case $1 in
        current)
            check_current
            ;;
        upgrade)
            upgrade_head
            ;;
        downgrade)
            downgrade_one
            ;;
        history)
            show_history
            ;;
        help)
            show_help
            ;;
        *)
            echo -e "${RED}❌ 未知命令: $1${NC}"
            echo "用法: $0 [current|upgrade|downgrade|history|help]"
            exit 1
            ;;
    esac
else
    # 交互模式
    main
fi
