#!/bin/bash

# FieldMind 完整数据采集和处理脚本
# 步骤1：上传大量文件
# 步骤2：运行实体抽取
# 步骤3：运行关系抽取
# 步骤4：迁移到 Neo4j
# 步骤5：验证结果

set -e

echo "============================================================"
echo "FieldMind 完整数据采集和处理"
echo "============================================================"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cd /Users/alwan/FieldMind/backend/src

# 步骤1：运行实体抽取
echo -e "${YELLOW}步骤1: 运行实体抽取${NC}"
python3 app/services/entity_extraction_service.py --db data/fieldmind.db

ENTITY_COUNT=$(sqlite3 data/fieldmind.db "SELECT COUNT(*) FROM entities;")
echo -e "${GREEN}✅ 实体数量: $ENTITY_COUNT${NC}"
echo ""

# 步骤2：运行关系抽取
echo -e "${YELLOW}步骤2: 运行关系抽取${NC}"

# 检查 entity_relations 表是否存在
TABLE_EXISTS=$(sqlite3 data/fieldmind.db "SELECT name FROM sqlite_master WHERE type='table' AND name='entity_relations';" | wc -l)

if [ "$TABLE_EXISTS" -eq 0 ]; then
    echo "创建 entity_relations 表..."
    sqlite3 data/fieldmind.db "
    CREATE TABLE entity_relations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_entity_id VARCHAR(36) NOT NULL,
        target_entity_id VARCHAR(36) NOT NULL,
        relation_type VARCHAR(50) NOT NULL,
        properties JSON,
        confidence FLOAT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX idx_entity_relations_source ON entity_relations(source_entity_id);
    CREATE INDEX idx_entity_relations_target ON entity_relations(target_entity_id);
    CREATE INDEX idx_entity_relations_type ON entity_relations(relation_type);
    "
fi

python3 scripts/relation_extraction_standalone.py --db data/fieldmind.db

RELATION_COUNT=$(sqlite3 data/fieldmind.db "SELECT COUNT(*) FROM entity_relations;")
echo -e "${GREEN}✅ 关系数量: $RELATION_COUNT${NC}"
echo ""

# 步骤3：迁移到 Neo4j
echo -e "${YELLOW}步骤3: 迁移到 Neo4j${NC}"

# 检查 Neo4j 是否运行
if ! docker ps | grep -q fieldmind-neo4j; then
    echo -e "${RED}❌ Neo4j 未运行，请先启动: docker start fieldmind-neo4j${NC}"
    exit 1
fi

# 清空并重新导入
python3 scripts/import_ontology_to_neo4j.py \
    --uri bolt://localhost:7687 \
    --user neo4j \
    --password fieldmind2024 \
    --schema ontology/schema.json \
    --clear

python3 scripts/migrate_data_to_neo4j.py \
    --sqlite data/fieldmind.db \
    --uri bolt://localhost:7687 \
    --user neo4j \
    --password fieldmind2024

echo ""

# 步骤4：验证结果
echo -e "${YELLOW}步骤4: 验证结果${NC}"

# SQLite 统计
echo "SQLite 数据统计:"
echo "  Chunks: $(sqlite3 data/fieldmind.db 'SELECT COUNT(*) FROM document_chunks;')"
echo "  实体: $(sqlite3 data/fieldmind.db 'SELECT COUNT(*) FROM entities;')"
echo "  关系: $(sqlite3 data/fieldmind.db 'SELECT COUNT(*) FROM entity_relations;')"
echo ""

# Neo4j 统计
echo "Neo4j 数据统计:"
NEO4J_STATS=$(docker exec fieldmind-neo4j cypher-shell -u neo4j -p fieldmind2024 "
MATCH (n)
WITH labels(n)[0] as label, count(n) as count
RETURN label, count
ORDER BY count DESC;
" 2>/dev/null || echo "无法连接")

echo "$NEO4J_STATS"
echo ""

# 完成
echo "============================================================"
echo -e "${GREEN}✅ 完整数据处理完成！${NC}"
echo "============================================================"
echo ""
echo "下一步："
echo "  1. 访问 Neo4j Browser: http://localhost:7474"
echo "  2. 测试语义查询 API"
echo "  3. 查看数据可视化"
echo ""
