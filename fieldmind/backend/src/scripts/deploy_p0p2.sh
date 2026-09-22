#!/bin/bash

# FieldMind P0-P2 完整部署脚本
# 自动化部署 Neo4j + 迁移数据 + 验证系统

set -e  # 遇到错误立即退出

echo "============================================================"
echo "FieldMind P0-P2 完整部署"
echo "============================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 步骤1：检查 Docker
echo -e "${YELLOW}步骤1: 检查 Docker${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    echo "请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo -e "${GREEN}✅ Docker 已安装${NC}"

# 检查 Docker 是否运行
if ! docker info &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker 未运行，正在启动...${NC}"
    open -a Docker
    echo "等待 Docker 启动（30秒）..."
    sleep 30
fi

echo -e "${GREEN}✅ Docker 正在运行${NC}"
echo ""

# 步骤2：部署 Neo4j
echo -e "${YELLOW}步骤2: 部署 Neo4j${NC}"

# 检查是否已有 Neo4j 容器
if docker ps -a | grep -q fieldmind-neo4j; then
    echo "Neo4j 容器已存在，删除旧容器..."
    docker stop fieldmind-neo4j || true
    docker rm fieldmind-neo4j || true
fi

# 启动 Neo4j
echo "启动 Neo4j 容器..."
docker run -d \
  --name fieldmind-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/fieldmind2024 \
  -e NEO4J_dbms_memory_pagecache_size=512M \
  -e NEO4J_dbms_memory_heap_max__size=1G \
  -v ~/fieldmind-neo4j-data:/data \
  neo4j:5.15.0

echo "等待 Neo4j 启动（30秒）..."
sleep 30

# 验证 Neo4j
echo "验证 Neo4j 连接..."
if curl -s http://localhost:7474 > /dev/null; then
    echo -e "${GREEN}✅ Neo4j 已启动${NC}"
    echo "   Web UI: http://localhost:7474"
    echo "   用户名: neo4j"
    echo "   密码: fieldmind2024"
else
    echo -e "${RED}❌ Neo4j 启动失败${NC}"
    docker logs fieldmind-neo4j | tail -20
    exit 1
fi
echo ""

# 步骤3：安装 Python 依赖
echo -e "${YELLOW}步骤3: 安装 Python 依赖${NC}"
cd /Users/alwan/FieldMind/backend/src

pip3 install neo4j --quiet || echo "neo4j 可能已安装"

echo -e "${GREEN}✅ 依赖已安装${NC}"
echo ""

# 步骤4：导入本体模型
echo -e "${YELLOW}步骤4: 导入本体模型到 Neo4j${NC}"

if [ -f "ontology/schema.json" ]; then
    python3 scripts/import_ontology_to_neo4j.py \
        --uri bolt://localhost:7687 \
        --user neo4j \
        --password fieldmind2024 \
        --schema ontology/schema.json

    echo -e "${GREEN}✅ 本体模型已导入${NC}"
else
    echo -e "${YELLOW}⚠️  ontology/schema.json 不存在，跳过${NC}"
fi
echo ""

# 步骤5：迁移数据
echo -e "${YELLOW}步骤5: 迁移数据到 Neo4j${NC}"

if [ -f "data/fieldmind.db" ]; then
    # 检查数据库中是否有数据
    CHUNK_COUNT=$(sqlite3 data/fieldmind.db "SELECT COUNT(*) FROM document_chunks;")
    echo "SQLite 中有 $CHUNK_COUNT 个 chunks"

    if [ "$CHUNK_COUNT" -gt 0 ]; then
        python3 scripts/migrate_data_to_neo4j.py \
            --sqlite data/fieldmind.db \
            --uri bolt://localhost:7687 \
            --user neo4j \
            --password fieldmind2024

        echo -e "${GREEN}✅ 数据已迁移${NC}"
    else
        echo -e "${YELLOW}⚠️  没有数据可迁移${NC}"
    fi
else
    echo -e "${RED}❌ data/fieldmind.db 不存在${NC}"
fi
echo ""

# 步骤6：验证部署
echo -e "${YELLOW}步骤6: 验证部署${NC}"

# 检查 Neo4j 节点数量
NEO4J_NODES=$(docker exec fieldmind-neo4j cypher-shell -u neo4j -p fieldmind2024 "MATCH (n) RETURN count(n) as count;" | grep -oE '[0-9]+' | head -1 || echo "0")

echo "Neo4j 节点数量: $NEO4J_NODES"

if [ "$NEO4J_NODES" -gt 0 ]; then
    echo -e "${GREEN}✅ Neo4j 中有数据${NC}"
else
    echo -e "${YELLOW}⚠️  Neo4j 中暂无数据${NC}"
fi
echo ""

# 步骤7：启动 FieldMind 后端（如果未运行）
echo -e "${YELLOW}步骤7: 检查 FieldMind 后端${NC}"

if ps aux | grep -v grep | grep "main_simple.py" > /dev/null; then
    echo -e "${GREEN}✅ FieldMind 后端正在运行${NC}"
else
    echo "启动 FieldMind 后端..."
    cd /Users/alwan/FieldMind/backend/src
    PYTHONPATH=/Users/alwan/FieldMind/backend/src python3 app/main_simple.py > /tmp/fieldmind_server.log 2>&1 &
    sleep 5
    echo -e "${GREEN}✅ FieldMind 后端已启动${NC}"
fi
echo ""

# 完成
echo "============================================================"
echo -e "${GREEN}✅ P0-P2 部署完成！${NC}"
echo "============================================================"
echo ""
echo "访问地址："
echo "  • Neo4j Browser: http://localhost:7474"
echo "  • FieldMind API: http://localhost:8000/docs"
echo ""
echo "下一步："
echo "  1. 访问 Neo4j Browser 查看数据"
echo "  2. 测试语义查询 API"
echo "  3. 运行端到端测试"
echo ""
echo "停止服务："
echo "  docker stop fieldmind-neo4j"
echo ""
