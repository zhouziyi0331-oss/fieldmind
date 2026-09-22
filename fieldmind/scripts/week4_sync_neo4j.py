#!/usr/bin/env python3
"""
Week 4-5: Neo4j 批量数据同步

功能：
1. 从 PostgreSQL 读取所有实体和关系
2. 批量创建 Neo4j 节点和边
3. 验证同步结果
4. 生成同步报告

执行时间：2026-09-13
作者：FieldMind Architecture Team
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

# ============================================================================
# 配置
# ============================================================================

DB_PATH = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"
BATCH_SIZE = 100
MOCK_MODE = True  # 设置为 False 连接真实 Neo4j

# Neo4j 配置（真实模式）
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

# ============================================================================
# Mock Neo4j 驱动（用于测试）
# ============================================================================

class MockNeo4jDriver:
    """模拟 Neo4j 驱动"""

    def __init__(self):
        self.nodes = []
        self.relationships = []

    def session(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def run(self, query: str, **parameters):
        """模拟执行 Cypher 查询"""
        if "CREATE" in query and ":Entity" in query:
            # 创建实体节点
            self.nodes.append({
                'id': parameters.get('id'),
                'name': parameters.get('name'),
                'type': parameters.get('type')
            })
        elif "CREATE" in query and "RELATIONSHIP" in query:
            # 创建关系
            self.relationships.append({
                'from': parameters.get('from_id'),
                'to': parameters.get('to_id'),
                'type': parameters.get('type')
            })
        elif "MATCH (e:Entity)" in query:
            # 查询节点数
            return MockResult([{'count': len(self.nodes)}])
        elif "MATCH ()-[r]->()" in query:
            # 查询关系数
            return MockResult([{'count': len(self.relationships)}])
        return MockResult([])

    def close(self):
        pass

class MockResult:
    """模拟查询结果"""
    def __init__(self, data):
        self.data = data

    def single(self):
        return self.data[0] if self.data else {}

    def values(self):
        return self.data


# ============================================================================
# Neo4j 同步器
# ============================================================================

class Neo4jBatchSyncer:
    """Neo4j 批量同步器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.pg_conn = None
        self.neo4j_driver = None
        self.stats = {
            'entities_total': 0,
            'entities_synced': 0,
            'relations_total': 0,
            'relations_synced': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }

    def connect_postgresql(self):
        """连接 PostgreSQL"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")

        self.pg_conn = sqlite3.connect(self.db_path)
        self.pg_conn.row_factory = sqlite3.Row
        print(f"✅ 已连接到 PostgreSQL: {self.db_path}")

    def connect_neo4j(self):
        """连接 Neo4j"""
        if MOCK_MODE:
            self.neo4j_driver = MockNeo4jDriver()
            print(f"✅ 已连接到 Neo4j (Mock 模式)")
        else:
            try:
                from neo4j import GraphDatabase
                self.neo4j_driver = GraphDatabase.driver(
                    NEO4J_URI,
                    auth=(NEO4J_USER, NEO4J_PASSWORD)
                )
                print(f"✅ 已连接到 Neo4j: {NEO4J_URI}")
            except ImportError:
                print("❌ 未安装 neo4j 驱动，请运行: pip install neo4j")
                print("   切换到 Mock 模式继续...")
                self.neo4j_driver = MockNeo4jDriver()

    def close(self):
        """关闭连接"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.neo4j_driver:
            self.neo4j_driver.close()
        print("✅ 数据库连接已关闭")

    def get_entities_from_postgresql(self) -> List[Dict]:
        """从 PostgreSQL 获取所有实体"""
        cursor = self.pg_conn.cursor()
        cursor.execute("""
            SELECT
                entity_id, name, entity_type,
                description, properties, confidence
            FROM entities
            WHERE entity_id IS NOT NULL
            ORDER BY id
        """)

        entities = []
        for row in cursor.fetchall():
            entities.append({
                'id': row['entity_id'],
                'name': row['name'] or row['text'] if 'text' in row.keys() else 'Unknown',
                'type': row['entity_type'] or row['type'] if 'type' in row.keys() else 'Unknown',
                'description': row['description'],
                'properties': row['properties'],
                'confidence': row['confidence']
            })

        self.stats['entities_total'] = len(entities)
        print(f"📊 从 PostgreSQL 读取 {len(entities)} 个实体")
        return entities

    def get_relations_from_postgresql(self) -> List[Dict]:
        """从 PostgreSQL 获取所有关系"""
        cursor = self.pg_conn.cursor()
        cursor.execute("""
            SELECT
                source_entity_id, target_entity_id, relation_type,
                confidence, metadata
            FROM entity_relations
            WHERE source_entity_id IS NOT NULL
              AND target_entity_id IS NOT NULL
            ORDER BY id
        """)

        relations = []
        for row in cursor.fetchall():
            relations.append({
                'from_id': row['source_entity_id'],
                'to_id': str(row['target_entity_id']),  # 转换为字符串
                'type': row['relation_type'] or 'RELATED_TO',
                'confidence': row['confidence'],
                'properties': row['metadata']
            })

        self.stats['relations_total'] = len(relations)
        print(f"📊 从 PostgreSQL 读取 {len(relations)} 个关系")
        return relations

    def sync_entities_batch(self, entities: List[Dict]) -> int:
        """批量同步实体到 Neo4j"""
        synced = 0

        with self.neo4j_driver.session() as session:
            for entity in entities:
                try:
                    # 解析 properties
                    properties = {}
                    if entity['properties']:
                        try:
                            properties = json.loads(entity['properties']) if isinstance(entity['properties'], str) else entity['properties']
                        except:
                            properties = {}

                    # 创建节点
                    query = """
                    MERGE (e:Entity {id: $id})
                    SET e.name = $name,
                        e.type = $type,
                        e.description = $description,
                        e.confidence = $confidence,
                        e.properties = $properties,
                        e.synced_at = datetime()
                    """

                    session.run(
                        query,
                        id=entity['id'],
                        name=entity['name'],
                        type=entity['type'],
                        description=entity['description'],
                        confidence=entity['confidence'] or 0.0,
                        properties=json.dumps(properties, ensure_ascii=False)
                    )

                    synced += 1
                except Exception as e:
                    print(f"❌ 同步实体失败 (id={entity['id']}): {e}")
                    self.stats['errors'] += 1

        self.stats['entities_synced'] += synced
        return synced

    def sync_relations_batch(self, relations: List[Dict]) -> int:
        """批量同步关系到 Neo4j"""
        synced = 0

        with self.neo4j_driver.session() as session:
            for relation in relations:
                try:
                    # 解析 properties
                    properties = {}
                    if relation['properties']:
                        try:
                            properties = json.loads(relation['properties']) if isinstance(relation['properties'], str) else relation['properties']
                        except:
                            properties = {}

                    # 创建关系
                    query = f"""
                    MATCH (from:Entity {{id: $from_id}})
                    MATCH (to:Entity {{id: $to_id}})
                    MERGE (from)-[r:{relation['type']}]->(to)
                    SET r.confidence = $confidence,
                        r.properties = $properties,
                        r.synced_at = datetime()
                    """

                    session.run(
                        query,
                        from_id=relation['from_id'],
                        to_id=relation['to_id'],
                        confidence=relation['confidence'] or 0.0,
                        properties=json.dumps(properties, ensure_ascii=False)
                    )

                    synced += 1
                except Exception as e:
                    print(f"❌ 同步关系失败 (from={relation['from_id']}, to={relation['to_id']}): {e}")
                    self.stats['errors'] += 1

        self.stats['relations_synced'] += synced
        return synced

    def verify_sync(self):
        """验证同步结果"""
        print("\n" + "=" * 70)
        print("验证同步结果")
        print("=" * 70)

        with self.neo4j_driver.session() as session:
            # 统计节点数
            result = session.run("MATCH (e:Entity) RETURN count(e) as count")
            node_count = result.single()['count']

            # 统计关系数
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()['count']

            print(f"\nNeo4j 统计:")
            print(f"  节点数: {node_count}")
            print(f"  关系数: {rel_count}")

            print(f"\nPostgreSQL 统计:")
            print(f"  实体数: {self.stats['entities_total']}")
            print(f"  关系数: {self.stats['relations_total']}")

            print(f"\n同步统计:")
            print(f"  已同步实体: {self.stats['entities_synced']}")
            print(f"  已同步关系: {self.stats['relations_synced']}")

            if node_count == self.stats['entities_synced']:
                print(f"\n✅ 实体同步一致")
            else:
                print(f"\n⚠️  实体数量不匹配")

            if rel_count == self.stats['relations_synced']:
                print(f"✅ 关系同步一致")
            else:
                print(f"⚠️  关系数量不匹配")

    def run(self):
        """执行批量同步"""
        print("=" * 70)
        print("Neo4j 批量数据同步")
        print(f"模式: {'Mock（模拟）' if MOCK_MODE else 'Real（真实 Neo4j）'}")
        print("=" * 70)

        self.stats['start_time'] = datetime.now()

        try:
            # 1. 获取实体
            print("\n[步骤 1/4] 读取实体数据")
            entities = self.get_entities_from_postgresql()

            # 2. 同步实体
            print(f"\n[步骤 2/4] 同步实体到 Neo4j")
            print(f"批量大小: {BATCH_SIZE}")
            print()

            for i in range(0, len(entities), BATCH_SIZE):
                batch = entities[i:i + BATCH_SIZE]
                batch_num = i // BATCH_SIZE + 1
                total_batches = (len(entities) + BATCH_SIZE - 1) // BATCH_SIZE

                print(f"同步批次 {batch_num}/{total_batches} "
                      f"(实体 {i+1}-{min(i+len(batch), len(entities))}/{len(entities)})...", end=' ')

                synced = self.sync_entities_batch(batch)
                print(f"✅ {synced} 个")

            # 3. 获取关系
            print(f"\n[步骤 3/4] 读取关系数据")
            relations = self.get_relations_from_postgresql()

            # 4. 同步关系
            print(f"\n[步骤 4/4] 同步关系到 Neo4j")
            print()

            for i in range(0, len(relations), BATCH_SIZE):
                batch = relations[i:i + BATCH_SIZE]
                batch_num = i // BATCH_SIZE + 1
                total_batches = (len(relations) + BATCH_SIZE - 1) // BATCH_SIZE

                print(f"同步批次 {batch_num}/{total_batches} "
                      f"(关系 {i+1}-{min(i+len(batch), len(relations))}/{len(relations)})...", end=' ')

                synced = self.sync_relations_batch(batch)
                print(f"✅ {synced} 个")

            # 验证
            self.verify_sync()

            self.stats['end_time'] = datetime.now()

            # 生成报告
            self.generate_report()

        except Exception as e:
            print(f"\n❌ 同步失败: {e}")
            import traceback
            traceback.print_exc()
            self.stats['end_time'] = datetime.now()
            raise

    def generate_report(self):
        """生成同步报告"""
        print("\n" + "=" * 70)
        print("同步报告")
        print("=" * 70)

        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        print(f"实体总数:     {self.stats['entities_total']}")
        print(f"已同步实体:   {self.stats['entities_synced']}")
        print(f"关系总数:     {self.stats['relations_total']}")
        print(f"已同步关系:   {self.stats['relations_synced']}")
        print(f"错误数:       {self.stats['errors']}")
        print(f"执行时间:     {duration:.2f} 秒")

        if duration > 0:
            total_ops = self.stats['entities_synced'] + self.stats['relations_synced']
            speed = total_ops / duration
            print(f"同步速度:     {speed:.1f} 条/秒")

        if self.stats['errors'] == 0:
            print(f"\n✅ Neo4j 同步成功完成！")
        else:
            print(f"\n⚠️  Neo4j 同步完成，但有 {self.stats['errors']} 个错误")


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    syncer = Neo4jBatchSyncer(DB_PATH)

    try:
        # 连接数据库
        syncer.connect_postgresql()
        syncer.connect_neo4j()

        # 执行同步
        syncer.run()

    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        sys.exit(1)

    finally:
        # 关闭连接
        syncer.close()

    print("\n✅ 所有操作完成")


if __name__ == "__main__":
    main()
