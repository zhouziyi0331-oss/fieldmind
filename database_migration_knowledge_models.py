"""
数据库迁移脚本 - 添加Knowledge Pipeline相关表
用于合并fieldmind子目录后的数据库更新

执行方式：
    python database_migration_knowledge_models.py

回滚方式：
    python database_migration_knowledge_models.py --rollback
"""

import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/fieldmind")

# 创建表的SQL语句
CREATE_TABLES_SQL = """
-- 1. 流水线执行记录表
CREATE TABLE IF NOT EXISTS pipeline_executions (
    id VARCHAR PRIMARY KEY,
    document_id VARCHAR NOT NULL,
    project_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    current_step VARCHAR,
    start_time TIMESTAMP NOT NULL DEFAULT NOW(),
    end_time TIMESTAMP,
    duration FLOAT,
    results JSONB,
    errors JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_executions_document_id ON pipeline_executions(document_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_executions_project_id ON pipeline_executions(project_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_executions_status ON pipeline_executions(status);

-- 2. 知识实体表
CREATE TABLE IF NOT EXISTS knowledge_entities (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    type VARCHAR NOT NULL,
    document_id VARCHAR NOT NULL,
    project_id VARCHAR NOT NULL,
    aliases VARCHAR[],
    attributes JSONB,
    confidence FLOAT DEFAULT 1.0,
    importance FLOAT DEFAULT 0.5,
    mention_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_entities_name ON knowledge_entities(name);
CREATE INDEX IF NOT EXISTS idx_knowledge_entities_type ON knowledge_entities(type);
CREATE INDEX IF NOT EXISTS idx_knowledge_entities_document_id ON knowledge_entities(document_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_entities_project_id ON knowledge_entities(project_id);

-- 3. 知识关系表
CREATE TABLE IF NOT EXISTS knowledge_relations (
    id VARCHAR PRIMARY KEY,
    type VARCHAR NOT NULL,
    source_entity_id VARCHAR NOT NULL,
    target_entity_id VARCHAR NOT NULL,
    document_id VARCHAR NOT NULL,
    project_id VARCHAR NOT NULL,
    evidence TEXT[],
    pattern VARCHAR,
    confidence FLOAT DEFAULT 1.0,
    strength FLOAT DEFAULT 1.0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (source_entity_id) REFERENCES knowledge_entities(id) ON DELETE CASCADE,
    FOREIGN KEY (target_entity_id) REFERENCES knowledge_entities(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_knowledge_relations_type ON knowledge_relations(type);
CREATE INDEX IF NOT EXISTS idx_knowledge_relations_source ON knowledge_relations(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relations_target ON knowledge_relations(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relations_document_id ON knowledge_relations(document_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relations_project_id ON knowledge_relations(project_id);

-- 4. 知识事件表
CREATE TABLE IF NOT EXISTS knowledge_events (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    type VARCHAR NOT NULL,
    document_id VARCHAR NOT NULL,
    project_id VARCHAR NOT NULL,
    participants VARCHAR[],
    time_expression VARCHAR,
    time_normalized TIMESTAMP,
    location VARCHAR,
    description TEXT,
    confidence FLOAT DEFAULT 1.0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_events_name ON knowledge_events(name);
CREATE INDEX IF NOT EXISTS idx_knowledge_events_type ON knowledge_events(type);
CREATE INDEX IF NOT EXISTS idx_knowledge_events_document_id ON knowledge_events(document_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_events_project_id ON knowledge_events(project_id);

-- 5. 本体概念表
CREATE TABLE IF NOT EXISTS ontology_concepts (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    parent_id VARCHAR,
    level INTEGER DEFAULT 0,
    project_id VARCHAR NOT NULL,
    instances VARCHAR[],
    attributes JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (parent_id) REFERENCES ontology_concepts(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_ontology_concepts_name ON ontology_concepts(name);
CREATE INDEX IF NOT EXISTS idx_ontology_concepts_parent_id ON ontology_concepts(parent_id);
CREATE INDEX IF NOT EXISTS idx_ontology_concepts_project_id ON ontology_concepts(project_id);

-- 6. 知识单元表
CREATE TABLE IF NOT EXISTS knowledge_units (
    id VARCHAR PRIMARY KEY,
    content TEXT NOT NULL,
    type VARCHAR NOT NULL,
    document_id VARCHAR NOT NULL,
    project_id VARCHAR NOT NULL,
    entities VARCHAR[],
    relations VARCHAR[],
    events VARCHAR[],
    source_text TEXT,
    confidence FLOAT DEFAULT 1.0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_units_type ON knowledge_units(type);
CREATE INDEX IF NOT EXISTS idx_knowledge_units_document_id ON knowledge_units(document_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_units_project_id ON knowledge_units(project_id);
"""

# 删除表的SQL语句（回滚用）
DROP_TABLES_SQL = """
DROP TABLE IF EXISTS knowledge_units CASCADE;
DROP TABLE IF EXISTS ontology_concepts CASCADE;
DROP TABLE IF EXISTS knowledge_events CASCADE;
DROP TABLE IF EXISTS knowledge_relations CASCADE;
DROP TABLE IF EXISTS knowledge_entities CASCADE;
DROP TABLE IF EXISTS pipeline_executions CASCADE;
"""


def check_table_exists(engine, table_name):
    """检查表是否存在"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def migrate_up(engine):
    """执行迁移 - 创建表"""
    print("开始执行数据库迁移...")
    print("=" * 60)

    with engine.connect() as conn:
        # 检查表是否已存在
        tables_to_create = [
            'pipeline_executions',
            'knowledge_entities',
            'knowledge_relations',
            'knowledge_events',
            'ontology_concepts',
            'knowledge_units'
        ]

        existing_tables = []
        for table in tables_to_create:
            if check_table_exists(engine, table):
                existing_tables.append(table)

        if existing_tables:
            print(f"⚠️ 以下表已存在，将跳过创建：")
            for table in existing_tables:
                print(f"   - {table}")
            print()
            response = input("是否继续执行迁移？(y/n): ")
            if response.lower() != 'y':
                print("❌ 迁移已取消")
                return False

        # 执行创建表SQL
        print("正在创建表...")
        try:
            conn.execute(text(CREATE_TABLES_SQL))
            conn.commit()
            print("✅ 所有表创建成功！")
            print()
            print("已创建的表：")
            for table in tables_to_create:
                print(f"   ✓ {table}")
            return True
        except Exception as e:
            print(f"❌ 创建表失败: {e}")
            conn.rollback()
            return False


def migrate_down(engine):
    """回滚迁移 - 删除表"""
    print("⚠️ 警告：即将删除以下表及其所有数据：")
    print("   - pipeline_executions")
    print("   - knowledge_entities")
    print("   - knowledge_relations")
    print("   - knowledge_events")
    print("   - ontology_concepts")
    print("   - knowledge_units")
    print()
    response = input("确认删除？(yes/no): ")

    if response.lower() != 'yes':
        print("❌ 回滚已取消")
        return False

    print("正在删除表...")
    with engine.connect() as conn:
        try:
            conn.execute(text(DROP_TABLES_SQL))
            conn.commit()
            print("✅ 所有表已删除")
            return True
        except Exception as e:
            print(f"❌ 删除表失败: {e}")
            conn.rollback()
            return False


def main():
    """主函数"""
    print("=" * 60)
    print("FieldMind Knowledge Models 数据库迁移脚本")
    print("=" * 60)
    print()
    print(f"数据库连接: {DATABASE_URL.replace(DATABASE_URL.split('@')[0].split('//')[1], '***')}")
    print()

    # 创建数据库引擎
    try:
        engine = create_engine(DATABASE_URL)
        print("✅ 数据库连接成功")
        print()
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return 1

    # 检查是否为回滚模式
    if '--rollback' in sys.argv:
        success = migrate_down(engine)
    else:
        success = migrate_up(engine)

    print()
    print("=" * 60)
    if success:
        print("✅ 迁移完成")
    else:
        print("❌ 迁移失败")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
