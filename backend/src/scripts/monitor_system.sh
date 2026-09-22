#!/bin/bash

# FieldMind 系统状态监控脚本

echo "============================================================"
echo "FieldMind 系统状态监控"
echo "============================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. 检查服务状态
echo -e "${YELLOW}1. 服务状态${NC}"

# FieldMind 后端
if ps aux | grep -v grep | grep "main_simple.py" > /dev/null; then
    echo -e "  ${GREEN}✅ FieldMind 后端: 运行中${NC}"
else
    echo -e "  ${RED}❌ FieldMind 后端: 未运行${NC}"
fi

# Neo4j
if docker ps | grep fieldmind-neo4j > /dev/null; then
    echo -e "  ${GREEN}✅ Neo4j: 运行中${NC}"
else
    echo -e "  ${RED}❌ Neo4j: 未运行${NC}"
fi

echo ""

# 2. SQLite 数据统计
echo -e "${YELLOW}2. SQLite 数据统计${NC}"

if [ -f "/Users/alwan/FieldMind/backend/src/data/fieldmind.db" ]; then
    cd /Users/alwan/FieldMind/backend/src

    CHUNKS=$(sqlite3 data/fieldmind.db "SELECT COUNT(*) FROM document_chunks;" 2>/dev/null || echo "0")
    ENTITIES=$(sqlite3 data/fieldmind.db "SELECT COUNT(*) FROM entities;" 2>/dev/null || echo "0")
    RELATIONS=$(sqlite3 data/fieldmind.db "SELECT COUNT(*) FROM entity_relations;" 2>/dev/null || echo "0")
    KEYWORDS=$(sqlite3 data/fieldmind.db "SELECT COUNT(*) FROM chunk_keywords;" 2>/dev/null || echo "0")

    echo "  Chunks: $CHUNKS"
    echo "  实体: $ENTITIES"
    echo "  关系: $RELATIONS"
    echo "  关键词: $KEYWORDS"
else
    echo -e "  ${RED}❌ 数据库文件不存在${NC}"
fi

echo ""

# 3. Neo4j 数据统计
echo -e "${YELLOW}3. Neo4j 数据统计${NC}"

if docker ps | grep fieldmind-neo4j > /dev/null; then
    NEO4J_NODES=$(docker exec fieldmind-neo4j cypher-shell -u neo4j -p fieldmind2024 "MATCH (n) RETURN count(n) as count;" 2>/dev/null | grep -oE '[0-9]+' | head -1 || echo "0")
    NEO4J_RELS=$(docker exec fieldmind-neo4j cypher-shell -u neo4j -p fieldmind2024 "MATCH ()-[r]->() RETURN count(r) as count;" 2>/dev/null | grep -oE '[0-9]+' | head -1 || echo "0")

    echo "  节点: $NEO4J_NODES"
    echo "  关系: $NEO4J_RELS"

    # 节点类型分布
    echo ""
    echo "  节点类型分布:"
    docker exec fieldmind-neo4j cypher-shell -u neo4j -p fieldmind2024 "
    MATCH (n)
    WITH labels(n)[0] as label, count(n) as count
    RETURN label, count
    ORDER BY count DESC
    LIMIT 10;
    " 2>/dev/null | grep -v "^label" | grep -v "^$" | while read line; do
        echo "    $line"
    done
else
    echo -e "  ${RED}❌ Neo4j 未运行${NC}"
fi

echo ""

# 4. 系统资源
echo -e "${YELLOW}4. 系统资源${NC}"

if docker ps | grep fieldmind-neo4j > /dev/null; then
    NEO4J_MEMORY=$(docker stats fieldmind-neo4j --no-stream --format "{{.MemUsage}}" 2>/dev/null || echo "N/A")
    NEO4J_CPU=$(docker stats fieldmind-neo4j --no-stream --format "{{.CPUPerc}}" 2>/dev/null || echo "N/A")

    echo "  Neo4j 内存: $NEO4J_MEMORY"
    echo "  Neo4j CPU: $NEO4J_CPU"
fi

echo ""

# 5. 快速诊断
echo -e "${YELLOW}5. 快速诊断${NC}"

# 检查数据量是否足够
if [ "$CHUNKS" -lt 50 ]; then
    echo -e "  ${RED}⚠️  Chunks 数量不足（$CHUNKS < 50）${NC}"
    echo "     建议: 上传更多文件"
else
    echo -e "  ${GREEN}✅ Chunks 数量充足（$CHUNKS >= 50）${NC}"
fi

if [ "$ENTITIES" -lt 50 ]; then
    echo -e "  ${RED}⚠️  实体数量不足（$ENTITIES < 50）${NC}"
    echo "     建议: 改进实体抽取规则或上传更多文件"
else
    echo -e "  ${GREEN}✅ 实体数量充足（$ENTITIES >= 50）${NC}"
fi

if [ "$RELATIONS" -lt 100 ]; then
    echo -e "  ${RED}⚠️  关系数量不足（$RELATIONS < 100）${NC}"
    echo "     建议: 运行关系抽取或上传更多文件"
else
    echo -e "  ${GREEN}✅ 关系数量充足（$RELATIONS >= 100）${NC}"
fi

echo ""
echo "============================================================"
echo "监控完成"
echo "============================================================"
