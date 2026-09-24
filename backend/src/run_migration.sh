#!/bin/bash
# FieldMind数据库迁移脚本

echo "🔄 开始数据库迁移..."

# 进入backend/src目录
cd "$(dirname "$0")"

# 创建迁移
echo "📝 创建迁移文件..."
alembic revision --autogenerate -m "add_integration_tables"

# 执行迁移
echo "⬆️  执行迁移..."
alembic upgrade head

echo "✅ 迁移完成！"
