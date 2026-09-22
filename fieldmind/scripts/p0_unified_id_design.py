#!/usr/bin/env python3
"""
P0 优化 Day 1: 统一 ID 体系设计

目标：
1. 定义全局唯一 ID 规范
2. 确保所有数据库使用统一 ID
3. 创建 ID 生成器
4. 设计数据主权架构
"""

import uuid
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class EntityType(Enum):
    """实体类型枚举"""
    PROJECT = "proj"
    USER = "user"
    DOCUMENT = "doc"
    CHUNK = "chk"
    ENTITY = "ent"
    RELATION = "rel"
    SKILL = "skl"
    PATTERN = "pat"
    EVENT = "evt"
    TOPIC = "top"


class UnifiedIDGenerator:
    """统一 ID 生成器"""

    @staticmethod
    def generate(entity_type: EntityType, metadata: Optional[Dict] = None) -> str:
        """
        生成全局唯一 ID

        格式: {prefix}_{uuid_short}
        示例: proj_a1b2c3d4, doc_e5f6g7h8

        Args:
            entity_type: 实体类型
            metadata: 可选元数据（用于生成可读性更好的 ID）

        Returns:
            全局唯一 ID
        """
        # 生成 UUID
        unique_id = str(uuid.uuid4()).replace('-', '')[:12]

        # 拼接前缀
        prefix = entity_type.value
        return f"{prefix}_{unique_id}"

    @staticmethod
    def generate_from_content(entity_type: EntityType, content: str) -> str:
        """
        从内容生成确定性 ID（幂等）

        用于：相同内容应该生成相同 ID 的场景
        """
        # 使用内容的 hash 生成确定性 ID
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:12]
        prefix = entity_type.value
        return f"{prefix}_{content_hash}"

    @staticmethod
    def validate(entity_id: str) -> bool:
        """验证 ID 格式"""
        if not entity_id or '_' not in entity_id:
            return False

        prefix, unique_part = entity_id.split('_', 1)

        # 检查前缀是否合法
        valid_prefixes = [e.value for e in EntityType]
        if prefix not in valid_prefixes:
            return False

        # 检查 ID 部分长度
        if len(unique_part) != 12:
            return False

        return True

    @staticmethod
    def extract_type(entity_id: str) -> Optional[EntityType]:
        """从 ID 提取实体类型"""
        if not UnifiedIDGenerator.validate(entity_id):
            return None

        prefix = entity_id.split('_')[0]
        for entity_type in EntityType:
            if entity_type.value == prefix:
                return entity_type

        return None


class DataSovereigntyArchitect:
    """数据主权架构设计器"""

    @staticmethod
    def get_architecture() -> Dict:
        """获取数据主权架构"""
        return {
            "architecture_version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "layers": {
                "sovereignty": {
                    "name": "数据主权层",
                    "database": "PostgreSQL",
                    "role": "所有结构化数据的唯一写入口",
                    "responsibilities": [
                        "所有数据的 CREATE、UPDATE、DELETE",
                        "维护数据完整性和一致性",
                        "生成全局唯一 ID",
                        "发布数据变更事件",
                    ],
                    "tables": [
                        "projects",
                        "users",
                        "documents",
                        "chunks",
                        "entities",
                        "relations",
                        "skills",
                        "patterns",
                    ],
                },
                "graph_index": {
                    "name": "图索引层",
                    "database": "Neo4j",
                    "role": "实体关系图查询",
                    "responsibilities": [
                        "从 PostgreSQL 同步实体和关系",
                        "提供图遍历和路径查询",
                        "计算中心性和社区发现",
                        "只读，不创建数据",
                    ],
                    "sync_from": "PostgreSQL.entities + PostgreSQL.relations",
                    "sync_strategy": "事件驱动 + 定时全量校验",
                },
                "vector_index": {
                    "name": "向量索引层",
                    "database": "ChromaDB",
                    "role": "语义相似度检索",
                    "responsibilities": [
                        "从 PostgreSQL 同步 chunk 文本和 embedding",
                        "提供向量相似度搜索",
                        "支持语义检索",
                        "只读，不创建数据",
                    ],
                    "sync_from": "PostgreSQL.chunks",
                    "sync_strategy": "事件驱动 + 增量更新",
                },
                "cache": {
                    "name": "缓存层",
                    "database": "Redis",
                    "role": "热点数据缓存",
                    "responsibilities": [
                        "缓存高频查询结果",
                        "缓存用户会话",
                        "缓存计算结果",
                        "有明确过期时间",
                    ],
                    "sync_from": "所有查询结果",
                    "sync_strategy": "按需缓存 + TTL 过期",
                },
            },
            "principles": [
                "单一主权：所有写操作只在 PostgreSQL",
                "统一 ID：四库使用相同的 ID 体系",
                "事件驱动：PostgreSQL 变更通过事件同步",
                "可重建：索引层可随时从主权层重建",
                "最终一致性：允许短暂延迟，保证最终一致",
            ],
            "data_flow": {
                "write": [
                    "Client → API",
                    "API → PostgreSQL (唯一写入)",
                    "PostgreSQL → Event Bus",
                    "Event Bus → Neo4j/ChromaDB/Redis (异步同步)",
                ],
                "read": [
                    "Client → API",
                    "API → Redis (检查缓存)",
                    "Redis Miss → Query Orchestrator",
                    "Orchestrator → PostgreSQL (主数据)",
                    "Orchestrator → Neo4j (图关系)",
                    "Orchestrator → ChromaDB (相似度)",
                    "Orchestrator → 合并结果 → Redis (写缓存)",
                    "Result → Client",
                ],
            },
        }


class DatabaseSchemaDesigner:
    """数据库表结构设计器"""

    @staticmethod
    def get_postgresql_schema() -> Dict:
        """PostgreSQL 主权层表结构"""
        return {
            "tables": {
                "projects": {
                    "description": "项目主表",
                    "columns": {
                        "id": "VARCHAR(20) PRIMARY KEY -- proj_{uuid12}",
                        "name": "VARCHAR(255) NOT NULL",
                        "description": "TEXT",
                        "created_by": "VARCHAR(20) REFERENCES users(id)",
                        "created_at": "TIMESTAMP DEFAULT NOW()",
                        "updated_at": "TIMESTAMP DEFAULT NOW()",
                        "status": "VARCHAR(20) DEFAULT 'active'",
                        "metadata": "JSONB -- 扩展字段",
                    },
                    "indexes": ["created_by", "status", "created_at"],
                },
                "documents": {
                    "description": "文档主表",
                    "columns": {
                        "id": "VARCHAR(20) PRIMARY KEY -- doc_{uuid12}",
                        "project_id": "VARCHAR(20) REFERENCES projects(id)",
                        "title": "VARCHAR(500) NOT NULL",
                        "content": "TEXT",
                        "file_path": "VARCHAR(1000)",
                        "file_size": "BIGINT",
                        "file_type": "VARCHAR(50)",
                        "created_by": "VARCHAR(20) REFERENCES users(id)",
                        "created_at": "TIMESTAMP DEFAULT NOW()",
                        "updated_at": "TIMESTAMP DEFAULT NOW()",
                        "status": "VARCHAR(20) DEFAULT 'active'",
                        "metadata": "JSONB",
                    },
                    "indexes": ["project_id", "created_by", "status"],
                },
                "chunks": {
                    "description": "文档切片表（增强版）",
                    "columns": {
                        "id": "VARCHAR(20) PRIMARY KEY -- chk_{uuid12}",
                        "document_id": "VARCHAR(20) REFERENCES documents(id)",
                        "project_id": "VARCHAR(20) REFERENCES projects(id)",
                        "text": "TEXT NOT NULL",
                        "position": "INTEGER",
                        "word_count": "INTEGER",

                        # 新增：说话人信息
                        "speaker": "VARCHAR(255) -- 说话人标识",
                        "speaker_role": "VARCHAR(100) -- 说话人角色",

                        # 新增：时间戳
                        "timestamp_start": "FLOAT -- 音频/视频起始时间（秒）",
                        "timestamp_end": "FLOAT -- 结束时间",

                        # 新增：情感量化
                        "sentiment_polarity": "FLOAT -- 情感极性 [-1, 1]",
                        "sentiment_subjectivity": "FLOAT -- 主观性 [0, 1]",
                        "emotion_scores": "JSONB -- 多维情绪分数",

                        # 新增：维度分类
                        "dimension_category": "VARCHAR(100) -- 一级维度",
                        "dimension_sub_category": "VARCHAR(100) -- 二级维度",
                        "dimension_confidence": "FLOAT -- 分类置信度",

                        # 新增：实体预标注
                        "entities": "JSONB -- [{id, name, type, confidence}]",
                        "keywords": "JSONB -- 关键词列表",

                        # 向量
                        "embedding": "VECTOR(1536) -- 向量表示",

                        # 质量评分
                        "quality_score": "FLOAT",

                        # 元数据
                        "created_at": "TIMESTAMP DEFAULT NOW()",
                        "updated_at": "TIMESTAMP DEFAULT NOW()",
                        "metadata": "JSONB",
                    },
                    "indexes": [
                        "document_id",
                        "project_id",
                        "dimension_category",
                        "speaker",
                        "quality_score",
                    ],
                    "notes": [
                        "chunk 从诞生起就携带完整信息",
                        "切分时同步完成：说话人标注、情绪量化、实体识别、维度归类",
                        "任何一个 chunk，都能直接回答：谁说的、什么情绪、属于什么维度、涉及什么实体",
                    ],
                },
                "entities": {
                    "description": "实体主表（增强版）",
                    "columns": {
                        "id": "VARCHAR(20) PRIMARY KEY -- ent_{uuid12}",
                        "project_id": "VARCHAR(20) REFERENCES projects(id)",
                        "name": "VARCHAR(255) NOT NULL",
                        "type": "VARCHAR(50) -- person/organization/location/concept",
                        "description": "TEXT",

                        # 新增：生命周期信息
                        "mention_count": "INTEGER DEFAULT 0 -- 提及次数",
                        "sentiment_avg": "FLOAT -- 平均情感值",
                        "first_appearance": "TIMESTAMP -- 首次出现时间",
                        "last_appearance": "TIMESTAMP -- 最后出现时间",

                        # 新增：关联信息
                        "related_entities": "JSONB -- 关联实体列表",
                        "related_events": "JSONB -- 关联事件列表",
                        "timeline": "JSONB -- 时间线 [{date, event, context, sentiment}]",

                        # 统计
                        "importance_score": "FLOAT -- 重要性评分",
                        "centrality_score": "FLOAT -- 中心性评分",

                        # 元数据
                        "created_at": "TIMESTAMP DEFAULT NOW()",
                        "updated_at": "TIMESTAMP DEFAULT NOW()",
                        "metadata": "JSONB",
                    },
                    "indexes": [
                        "project_id",
                        "type",
                        "mention_count",
                        "importance_score",
                    ],
                    "notes": [
                        "实体节点携带生命周期信息",
                        "不只是'名字'，而是'名字 + 提及次数 + 情绪变化 + 关联事件'",
                    ],
                },
                "relations": {
                    "description": "关系主表",
                    "columns": {
                        "id": "VARCHAR(20) PRIMARY KEY -- rel_{uuid12}",
                        "project_id": "VARCHAR(20) REFERENCES projects(id)",
                        "source_entity_id": "VARCHAR(20) REFERENCES entities(id)",
                        "target_entity_id": "VARCHAR(20) REFERENCES entities(id)",
                        "relation_type": "VARCHAR(100) NOT NULL",
                        "description": "TEXT",
                        "confidence": "FLOAT",
                        "evidence_chunks": "JSONB -- 支持证据的 chunk_id 列表",
                        "created_at": "TIMESTAMP DEFAULT NOW()",
                        "updated_at": "TIMESTAMP DEFAULT NOW()",
                        "metadata": "JSONB",
                    },
                    "indexes": [
                        "project_id",
                        "source_entity_id",
                        "target_entity_id",
                        "relation_type",
                    ],
                },
                "skills": {
                    "description": "Skill 库（增强版）",
                    "columns": {
                        "id": "VARCHAR(20) PRIMARY KEY -- skl_{uuid12}",
                        "name": "VARCHAR(255) NOT NULL",
                        "skill_type": "VARCHAR(50) -- process/decision/solution/lesson_learned",
                        "description": "TEXT",

                        # 新增：来源追踪
                        "source_project_id": "VARCHAR(20) -- 从哪个项目生成",
                        "source_data": "JSONB -- 基于哪些数据",
                        "auto_generated": "BOOLEAN DEFAULT FALSE -- 是否自动生成",

                        # 新增：版本控制
                        "version": "VARCHAR(20) DEFAULT 'v1.0'",
                        "parent_skill_id": "VARCHAR(20) -- 上一版本",

                        # 新增：使用统计
                        "usage_count": "INTEGER DEFAULT 0",
                        "success_count": "INTEGER DEFAULT 0",
                        "feedback_score": "FLOAT -- 用户反馈评分",

                        # 规则定义
                        "rules": "JSONB -- [{condition, action, weight}]",
                        "template": "TEXT",
                        "parameters": "JSONB",

                        # 元数据
                        "created_at": "TIMESTAMP DEFAULT NOW()",
                        "updated_at": "TIMESTAMP DEFAULT NOW()",
                        "metadata": "JSONB",
                    },
                    "indexes": [
                        "skill_type",
                        "source_project_id",
                        "usage_count",
                        "auto_generated",
                    ],
                    "notes": [
                        "Skill 从分析中自动生长",
                        "记录来源项目、基于数据、版本号",
                        "用户反馈自动调整权重",
                    ],
                },
                "knowledge_base": {
                    "description": "组织知识库",
                    "columns": {
                        "id": "VARCHAR(20) PRIMARY KEY",
                        "type": "VARCHAR(50) -- case/template/insight/lesson",
                        "title": "VARCHAR(500) NOT NULL",
                        "content": "TEXT",
                        "source_project_id": "VARCHAR(20)",
                        "source_report_id": "VARCHAR(20)",
                        "tags": "JSONB -- 标签列表",
                        "related_skills": "JSONB -- 关联的 Skill ID 列表",
                        "reuse_count": "INTEGER DEFAULT 0",
                        "quality_score": "FLOAT",
                        "created_at": "TIMESTAMP DEFAULT NOW()",
                        "updated_at": "TIMESTAMP DEFAULT NOW()",
                        "metadata": "JSONB",
                    },
                    "indexes": ["type", "source_project_id", "reuse_count"],
                    "notes": [
                        "报告结论回流为'组织知识库'",
                        "新项目自动推荐相似案例、模板、Skill",
                    ],
                },
            }
        }

    @staticmethod
    def get_neo4j_schema() -> Dict:
        """Neo4j 图索引层结构"""
        return {
            "nodes": {
                "Entity": {
                    "properties": {
                        "id": "从 PostgreSQL 同步的 entity_id",
                        "name": "实体名称",
                        "type": "实体类型",
                        "mention_count": "提及次数",
                        "sentiment_avg": "平均情感",
                        "importance_score": "重要性评分",
                    },
                    "sync_from": "PostgreSQL.entities",
                },
                "Chunk": {
                    "properties": {
                        "id": "从 PostgreSQL 同步的 chunk_id",
                        "text": "文本内容",
                        "dimension_category": "维度分类",
                    },
                    "sync_from": "PostgreSQL.chunks",
                },
            },
            "relationships": {
                "RELATES_TO": {
                    "properties": {
                        "id": "从 PostgreSQL 同步的 relation_id",
                        "relation_type": "关系类型",
                        "confidence": "置信度",
                    },
                    "sync_from": "PostgreSQL.relations",
                },
                "MENTIONED_IN": {
                    "properties": {
                        "chunk_id": "chunk ID",
                        "position": "位置",
                    },
                    "description": "实体在 chunk 中被提及",
                },
            },
            "notes": [
                "Neo4j 只做同步和查询，不创建数据",
                "所有节点和关系的 ID 与 PostgreSQL 一致",
                "提供图遍历、路径查询、社区发现等功能",
            ],
        }

    @staticmethod
    def get_chromadb_schema() -> Dict:
        """ChromaDB 向量索引层结构"""
        return {
            "collections": {
                "chunks": {
                    "ids": "从 PostgreSQL 同步的 chunk_id",
                    "documents": "chunk 文本",
                    "embeddings": "向量表示",
                    "metadatas": {
                        "document_id": "文档 ID",
                        "project_id": "项目 ID",
                        "dimension_category": "维度分类",
                        "quality_score": "质量分",
                    },
                    "sync_from": "PostgreSQL.chunks",
                },
            },
            "notes": [
                "ChromaDB 只做向量检索，不创建数据",
                "所有 ID 与 PostgreSQL 一致",
                "提供语义相似度搜索",
            ],
        }


def generate_id_migration_script():
    """生成 ID 迁移脚本"""
    script = """-- ID 统一迁移脚本
-- 用途：将现有数据库的 ID 迁移到统一格式

-- 1. 备份现有数据
CREATE TABLE projects_backup AS SELECT * FROM projects;
CREATE TABLE documents_backup AS SELECT * FROM documents;
CREATE TABLE chunks_backup AS SELECT * FROM chunks;
CREATE TABLE entities_backup AS SELECT * FROM entities;
CREATE TABLE relations_backup AS SELECT * FROM relations;

-- 2. 添加新 ID 列
ALTER TABLE projects ADD COLUMN new_id VARCHAR(20);
ALTER TABLE documents ADD COLUMN new_id VARCHAR(20);
ALTER TABLE chunks ADD COLUMN new_id VARCHAR(20);
ALTER TABLE entities ADD COLUMN new_id VARCHAR(20);
ALTER TABLE relations ADD COLUMN new_id VARCHAR(20);

-- 3. 生成新 ID
UPDATE projects SET new_id = 'proj_' || substring(md5(id::text || created_at::text) from 1 for 12);
UPDATE documents SET new_id = 'doc_' || substring(md5(id::text || created_at::text) from 1 for 12);
UPDATE chunks SET new_id = 'chk_' || substring(md5(id::text || created_at::text) from 1 for 12);
UPDATE entities SET new_id = 'ent_' || substring(md5(id::text || created_at::text) from 1 for 12);
UPDATE relations SET new_id = 'rel_' || substring(md5(id::text || created_at::text) from 1 for 12);

-- 4. 创建 ID 映射表（用于外键更新）
CREATE TABLE id_mapping (
    table_name VARCHAR(50),
    old_id TEXT,
    new_id VARCHAR(20),
    PRIMARY KEY (table_name, old_id)
);

INSERT INTO id_mapping SELECT 'projects', id, new_id FROM projects;
INSERT INTO id_mapping SELECT 'documents', id, new_id FROM documents;
INSERT INTO id_mapping SELECT 'chunks', id, new_id FROM chunks;
INSERT INTO id_mapping SELECT 'entities', id, new_id FROM entities;
INSERT INTO id_mapping SELECT 'relations', id, new_id FROM relations;

-- 5. 更新外键引用
-- 示例：更新 documents 表的 project_id
UPDATE documents d
SET project_id = m.new_id
FROM id_mapping m
WHERE m.table_name = 'projects'
  AND m.old_id = d.project_id;

-- 6. 替换主键
ALTER TABLE projects DROP CONSTRAINT projects_pkey;
ALTER TABLE projects DROP COLUMN id;
ALTER TABLE projects RENAME COLUMN new_id TO id;
ALTER TABLE projects ADD PRIMARY KEY (id);

-- 重复以上步骤，迁移所有表...

-- 7. 验证
SELECT 'projects' AS table_name, COUNT(*) AS count FROM projects
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'chunks', COUNT(*) FROM chunks
UNION ALL
SELECT 'entities', COUNT(*) FROM entities
UNION ALL
SELECT 'relations', COUNT(*) FROM relations;

-- 8. 清理
-- 确认无误后，删除备份表
-- DROP TABLE projects_backup;
-- DROP TABLE documents_backup;
-- ...
"""
    return script


def main():
    """生成 P0 优化设计文档"""
    print("=" * 70)
    print("P0 优化 Day 1: 统一 ID 体系设计")
    print("=" * 70)

    output_dir = "/Users/alwan/Downloads/FieldMind/fieldmind/p0_optimization"
    import os
    os.makedirs(output_dir, exist_ok=True)

    # 1. 生成 ID 规范文档
    print("\n📐 生成 ID 规范...")

    id_spec = {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "entity_types": [
            {
                "type": e.name,
                "prefix": e.value,
                "example": f"{e.value}_a1b2c3d4e5f6",
                "description": f"{e.name} 的全局唯一标识符",
            }
            for e in EntityType
        ],
        "format": {
            "pattern": "{prefix}_{uuid12}",
            "prefix_length": "3-4 chars",
            "uuid_length": "12 chars (hex)",
            "total_length": "16-17 chars",
        },
        "rules": [
            "所有数据库必须使用相同的 ID",
            "ID 一旦生成，永不改变",
            "禁止各数据库自行生成 ID",
            "从 PostgreSQL 获取 ID 后，同步到其他库",
        ],
        "validation": {
            "regex": "^(proj|user|doc|chk|ent|rel|skl|pat|evt|top)_[a-f0-9]{12}$",
            "examples_valid": [
                "proj_a1b2c3d4e5f6",
                "doc_1234567890ab",
                "chk_fedcba098765",
            ],
            "examples_invalid": [
                "project_123",  # 前缀错误
                "doc_abc",  # UUID 太短
                "doc_ABCDEF123456",  # UUID 大写
            ],
        },
    }

    with open(f"{output_dir}/unified_id_specification.json", 'w') as f:
        json.dump(id_spec, f, indent=2)

    print(f"   ✓ ID 规范: {output_dir}/unified_id_specification.json")

    # 2. 生成数据主权架构文档
    print("\n🏛️  生成数据主权架构...")

    architect = DataSovereigntyArchitect()
    architecture = architect.get_architecture()

    with open(f"{output_dir}/data_sovereignty_architecture.json", 'w') as f:
        json.dump(architecture, f, indent=2)

    print(f"   ✓ 架构文档: {output_dir}/data_sovereignty_architecture.json")

    # 3. 生成数据库表结构
    print("\n💾 生成数据库表结构...")

    designer = DatabaseSchemaDesigner()

    pg_schema = designer.get_postgresql_schema()
    with open(f"{output_dir}/postgresql_schema.json", 'w') as f:
        json.dump(pg_schema, f, indent=2)

    neo4j_schema = designer.get_neo4j_schema()
    with open(f"{output_dir}/neo4j_schema.json", 'w') as f:
        json.dump(neo4j_schema, f, indent=2)

    chromadb_schema = designer.get_chromadb_schema()
    with open(f"{output_dir}/chromadb_schema.json", 'w') as f:
        json.dump(chromadb_schema, f, indent=2)

    print(f"   ✓ PostgreSQL 表结构: {output_dir}/postgresql_schema.json")
    print(f"   ✓ Neo4j 表结构: {output_dir}/neo4j_schema.json")
    print(f"   ✓ ChromaDB 表结构: {output_dir}/chromadb_schema.json")

    # 4. 生成迁移脚本
    print("\n🔄 生成迁移脚本...")

    migration_script = generate_id_migration_script()
    with open(f"{output_dir}/id_migration.sql", 'w') as f:
        f.write(migration_script)

    print(f"   ✓ 迁移脚本: {output_dir}/id_migration.sql")

    # 5. 生成 Python ID 生成器
    print("\n🐍 生成 Python ID 生成器...")

    id_generator_code = '''"""
统一 ID 生成器

使用示例:
    from id_generator import UnifiedIDGenerator, EntityType

    # 生成项目 ID
    project_id = UnifiedIDGenerator.generate(EntityType.PROJECT)
    # 输出: proj_a1b2c3d4e5f6

    # 验证 ID
    is_valid = UnifiedIDGenerator.validate(project_id)
    # 输出: True

    # 提取类型
    entity_type = UnifiedIDGenerator.extract_type(project_id)
    # 输出: EntityType.PROJECT
"""
''' + open(__file__, 'r').read().split('class UnifiedIDGenerator:')[1].split('class DataSovereigntyArchitect:')[0]

    with open(f"{output_dir}/id_generator.py", 'w') as f:
        f.write(id_generator_code)

    print(f"   ✓ ID 生成器: {output_dir}/id_generator.py")

    # 6. 生成设计文档
    print("\n📖 生成设计文档...")

    design_doc = f"""# P0 优化：统一 ID 体系与数据主权架构

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 一、统一 ID 规范

### 1.1 ID 格式

**格式**: `{{prefix}}_{{uuid12}}`

**示例**:
- 项目: `proj_a1b2c3d4e5f6`
- 文档: `doc_1234567890ab`
- Chunk: `chk_fedcba098765`
- 实体: `ent_aabbccddee00`

### 1.2 实体类型前缀

| 实体类型 | 前缀 | 示例 |
|---------|------|------|
| 项目 | `proj` | `proj_a1b2c3d4e5f6` |
| 用户 | `user` | `user_123456789abc` |
| 文档 | `doc` | `doc_abcdef012345` |
| Chunk | `chk` | `chk_111222333444` |
| 实体 | `ent` | `ent_aabbccddee00` |
| 关系 | `rel` | `rel_112233445566` |
| Skill | `skl` | `skl_aabbcc112233` |
| 模式 | `pat` | `pat_123abc456def` |

### 1.3 规则

1. ✅ **所有数据库使用相同 ID**
   - PostgreSQL、Neo4j、ChromaDB、Redis 都用同一套 ID
   - 不允许各数据库自行生成 ID

2. ✅ **PostgreSQL 是 ID 唯一生成源**
   - 所有 ID 在 PostgreSQL 生成
   - 其他数据库从 PostgreSQL 同步

3. ✅ **ID 永不改变**
   - ID 一旦生成，永久有效
   - 不随数据迁移、重建而改变

4. ✅ **ID 可验证**
   - 通过正则表达式验证格式
   - 可从 ID 提取实体类型

---

## 二、数据主权架构

### 2.1 四层架构

```
┌──────────────────────────────────────────────────────────────┐
│                     数据主权架构                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  主权层 (PostgreSQL)                               │    │
│  │  - 所有结构化数据的唯一写入口                       │    │
│  │  - 生成全局唯一 ID                                  │    │
│  │  - 发布数据变更事件                                 │    │
│  └────────────────┬───────────────────────────────────┘    │
│                   │ (事件驱动同步)                         │
│  ┌────────────────▼───────────────────────────────────┐    │
│  │  索引层                                             │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │  Neo4j (图查询)                              │  │    │
│  │  │  - 从 PostgreSQL 同步实体+关系               │  │    │
│  │  │  - 提供图遍历和路径查询                      │  │    │
│  │  │  - 只读，不创建数据                          │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │  ChromaDB (向量检索)                         │  │    │
│  │  │  - 从 PostgreSQL 同步 chunk+embedding        │  │    │
│  │  │  - 提供语义相似度搜索                        │  │    │
│  │  │  - 只读，不创建数据                          │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │  Redis (缓存)                                │  │    │
│  │  │  - 缓存高频查询结果                          │  │    │
│  │  │  - 有明确过期时间                            │  │    │
│  │  │  - 可随时清空重建                            │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 核心原则

| 原则 | 说明 |
|------|------|
| **单一主权** | 所有写操作只在 PostgreSQL |
| **统一 ID** | 四库使用相同的 ID 体系 |
| **事件驱动** | PostgreSQL 变更通过事件同步 |
| **可重建** | 索引层可随时从主权层重建 |
| **最终一致性** | 允许短暂延迟，保证最终一致 |

### 2.3 数据流

**写入流程**:
```
Client → API
    ↓
API → PostgreSQL (唯一写入)
    ↓
PostgreSQL → Event Bus
    ↓
Event Bus → Neo4j/ChromaDB/Redis (异步同步)
```

**查询流程**:
```
Client → API
    ↓
API → Redis (检查缓存)
    ↓ (缓存未命中)
Query Orchestrator
    ├─→ PostgreSQL (主数据)
    ├─→ Neo4j (图关系)
    └─→ ChromaDB (相似度)
    ↓
合并结果 → Redis (写缓存) → Client
```

---

## 三、增强的表结构

### 3.1 Chunks 表（增强版）

新增字段让 chunk 从诞生起就携带完整信息：

| 字段 | 类型 | 说明 |
|------|------|------|
| `speaker` | VARCHAR(255) | 说话人标识 |
| `speaker_role` | VARCHAR(100) | 说话人角色 |
| `timestamp_start` | FLOAT | 音频起始时间 |
| `timestamp_end` | FLOAT | 结束时间 |
| `sentiment_polarity` | FLOAT | 情感极性 [-1, 1] |
| `sentiment_subjectivity` | FLOAT | 主观性 [0, 1] |
| `emotion_scores` | JSONB | 多维情绪分数 |
| `dimension_category` | VARCHAR(100) | 一级维度 |
| `dimension_sub_category` | VARCHAR(100) | 二级维度 |
| `entities` | JSONB | 预标注实体 |
| `keywords` | JSONB | 关键词列表 |

**乘法效应**:
- 切分时同步完成：说话人标注、情绪量化、实体识别、维度归类
- 任何一个 chunk，都能直接回答：谁说的、什么情绪、属于什么维度、涉及什么实体

### 3.2 Entities 表（增强版）

新增字段让实体携带生命周期信息：

| 字段 | 类型 | 说明 |
|------|------|------|
| `mention_count` | INTEGER | 提及次数 |
| `sentiment_avg` | FLOAT | 平均情感值 |
| `first_appearance` | TIMESTAMP | 首次出现时间 |
| `last_appearance` | TIMESTAMP | 最后出现时间 |
| `related_entities` | JSONB | 关联实体列表 |
| `related_events` | JSONB | 关联事件列表 |
| `timeline` | JSONB | 时间线 |

**乘法效应**:
- 实体节点不只是"名字"，而是"名字 + 提及次数 + 情绪变化 + 关联事件"

### 3.3 Skills 表（增强版）

新增字段让 Skill 从分析中自动生长：

| 字段 | 类型 | 说明 |
|------|------|------|
| `source_project_id` | VARCHAR(20) | 从哪个项目生成 |
| `source_data` | JSONB | 基于哪些数据 |
| `auto_generated` | BOOLEAN | 是否自动生成 |
| `version` | VARCHAR(20) | 版本号 |
| `parent_skill_id` | VARCHAR(20) | 上一版本 |
| `usage_count` | INTEGER | 使用次数 |
| `success_count` | INTEGER | 成功次数 |
| `feedback_score` | FLOAT | 用户反馈评分 |

**乘法效应**:
- Skill 记录来源项目、基于数据、版本号
- 用户反馈自动调整权重

### 3.4 Knowledge Base 表（新增）

组织知识库，报告结论回流：

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | VARCHAR(50) | case/template/insight/lesson |
| `title` | VARCHAR(500) | 标题 |
| `content` | TEXT | 内容 |
| `source_project_id` | VARCHAR(20) | 来源项目 |
| `source_report_id` | VARCHAR(20) | 来源报告 |
| `related_skills` | JSONB | 关联 Skill |
| `reuse_count` | INTEGER | 复用次数 |

**乘法效应**:
- 报告结论自动进入知识库
- 新项目自动推荐相似案例、模板、Skill

---

## 四、实施步骤

### Phase 1: ID 统一（1周）

1. ✅ 定义 ID 规范
2. ⏳ 创建 ID 生成器
3. ⏳ 执行 ID 迁移脚本
4. ⏳ 验证四库 ID 一致性

### Phase 2: 表结构升级（1周）

1. ⏳ 升级 chunks 表
2. ⏳ 升级 entities 表
3. ⏳ 升级 skills 表
4. ⏳ 创建 knowledge_base 表

### Phase 3: 数据同步（1周）

1. ⏳ 实现事件总线
2. ⏳ 实现 PostgreSQL → Neo4j 同步
3. ⏳ 实现 PostgreSQL → ChromaDB 同步
4. ⏳ 实现 Redis 缓存策略

### Phase 4: API 收敛（1周）

1. ⏳ 确保所有写操作只通过 PostgreSQL
2. ⏳ 禁止其他库的直接写入
3. ⏳ 实现查询编排器
4. ⏳ 测试数据一致性

---

## 五、验证清单

- [ ] 所有实体 ID 符合统一格式
- [ ] PostgreSQL、Neo4j、ChromaDB、Redis 使用相同 ID
- [ ] 所有写操作只在 PostgreSQL 发生
- [ ] Neo4j 数据与 PostgreSQL 一致
- [ ] ChromaDB 数据与 PostgreSQL 一致
- [ ] Redis 缓存有明确过期时间
- [ ] chunk 携带完整信息（说话人、情绪、维度、实体）
- [ ] entity 携带生命周期信息
- [ ] skill 记录来源和版本
- [ ] knowledge_base 正常运作

---

**FieldMind P0 优化项目**
统一 ID 体系与数据主权架构
Version 1.0
"""

    with open(f"{output_dir}/P0_DESIGN_DOCUMENT.md", 'w') as f:
        f.write(design_doc)

    print(f"   ✓ 设计文档: {output_dir}/P0_DESIGN_DOCUMENT.md")

    print("\n" + "=" * 70)
    print("P0 优化设计文档生成完成")
    print("=" * 70)

    print(f"\n📁 输出目录: {output_dir}/")
    print(f"\n📊 生成文件:")
    print(f"  1. unified_id_specification.json - ID 规范")
    print(f"  2. data_sovereignty_architecture.json - 数据主权架构")
    print(f"  3. postgresql_schema.json - PostgreSQL 表结构")
    print(f"  4. neo4j_schema.json - Neo4j 表结构")
    print(f"  5. chromadb_schema.json - ChromaDB 表结构")
    print(f"  6. id_migration.sql - ID 迁移脚本")
    print(f"  7. id_generator.py - Python ID 生成器")
    print(f"  8. P0_DESIGN_DOCUMENT.md - 完整设计文档")

    print(f"\n🎯 下一步:")
    print(f"  1. 审查设计文档")
    print(f"  2. 执行 ID 迁移脚本")
    print(f"  3. 实现事件驱动同步")
    print(f"  4. 实现数据一致性检查")


if __name__ == "__main__":
    main()
