#!/bin/bash
# 修复数据库迁移

cd /Users/alwan/FieldMind/backend/src

echo "1. 标记当前数据库状态..."
alembic stamp head

echo "2. 创建集成迁移..."
alembic revision -m "add_integration_tables" --autogenerate

echo "3. 执行迁移..."
alembic upgrade head

echo "✅ 迁移完成"
