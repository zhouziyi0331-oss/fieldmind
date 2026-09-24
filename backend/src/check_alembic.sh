#!/bin/bash
echo "🔍 检查Alembic状态..."

# 检查alembic目录
if [ -d "alembic" ]; then
    echo "✅ Alembic目录存在"
else
    echo "❌ Alembic目录不存在"
    exit 1
fi

# 检查当前版本
echo ""
echo "📋 当前数据库版本:"
alembic current

echo ""
echo "📋 待执行的迁移:"
alembic history | head -20

echo ""
echo "✅ 准备执行迁移..."
