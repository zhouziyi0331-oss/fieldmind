#!/bin/bash
# FieldMind 停止脚本

echo "停止 FieldMind 服务..."
docker-compose -f docker-compose.prod.yml down
echo "✓ 服务已停止"
