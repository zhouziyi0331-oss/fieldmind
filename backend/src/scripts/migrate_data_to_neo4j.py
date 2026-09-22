"""
Migrate Data to Neo4j - 将 SQLite 数据迁移到 Neo4j

迁移内容：
1. document_chunks → Chunk 节点
2. entities → Entity 节点（Person, Location, CulturalAsset 等）
3. entity_relations → 关系
4. chunk_keywords → 关键词关系
"""

import sqlite3
from neo4j import GraphDatabase
import json
import logging
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataMigrator:
    """数据迁移器"""

    def __init__(self,
                 sqlite_path="data/fieldmind.db",
                 neo4j_uri="bolt://localhost:7687",
                 neo4j_user="neo4j",
                 neo4j_password="fieldmind2024"):
        """
        初始化迁移器

        Args:
            sqlite_path: SQLite 数据库路径
            neo4j_uri: Neo4j 连接地址
            neo4j_user: Neo4j 用户名
            neo4j_password: Neo4j 密码
        """
        self.sqlite_conn = sqlite3.connect(sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row  # 返回字典

        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

        logger.info(f"✅ SQLite: {sqlite_path}")
        logger.info(f"✅ Neo4j: {neo4j_uri}")

    def close(self):
        """关闭连接"""
        self.sqlite_conn.close()
        self.neo4j_driver.close()

    def migrate_chunks(self, project_id: int = None):
        """
        迁移 chunks

        Args:
            project_id: 只迁移指定项目的 chunks（可选）
        """
        logger.info(f"\n{'='*60}")
        logger.info("迁移 Chunks")
        logger.info(f"{'='*60}\n")

        cursor = self.sqlite_conn.cursor()

        if project_id:
            cursor.execute("""
                SELECT id, chunk_text, dimension_category, cluster_id, project_id,
                       semantic_density, coherence_score, information_gain
                FROM document_chunks
                WHERE project_id = ?
            """, (project_id,))
        else:
            cursor.execute("""
                SELECT id, chunk_text, dimension_category, cluster_id, project_id,
                       semantic_density, coherence_score, information_gain
                FROM document_chunks
            """)

        chunks = cursor.fetchall()
        logger.info(f"📊 共 {len(chunks)} 个 chunks 待迁移")

        if len(chunks) == 0:
            logger.warning("⚠️  没有 chunks 可迁移")
            return

        with self.neo4j_driver.session() as session:
            for i, chunk in enumerate(chunks):
                chunk_id = chunk['id']
                text = chunk['chunk_text']
                dimension = chunk['dimension_category']
                cluster_id = chunk['cluster_id']
                project_id = chunk['project_id']
                semantic_density = chunk['semantic_density']
                coherence_score = chunk['coherence_score']
                information_gain = chunk['information_gain']

                # 创建 Chunk 节点
                session.run("""
                    CREATE (c:Chunk {
                        chunk_id: $chunk_id,
                        text: $text,
                        dimension_category: $dimension,
                        cluster_id: $cluster_id,
                        project_id: $project_id,
                        semantic_density: $semantic_density,
                        coherence_score: $coherence_score,
                        information_gain: $information_gain
                    })
                """, chunk_id=str(chunk_id), text=text, dimension=dimension,
                     cluster_id=cluster_id, project_id=project_id,
                     semantic_density=semantic_density, coherence_score=coherence_score,
                     information_gain=information_gain)

                if (i + 1) % 100 == 0:
                    logger.info(f"  进度: {i + 1}/{len(chunks)}")

        logger.info(f"✅ {len(chunks)} 个 chunks 已迁移")

    def migrate_entities(self):
        """迁移实体"""
        logger.info(f"\n{'='*60}")
        logger.info("迁移 Entities")
        logger.info(f"{'='*60}\n")

        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT id, name, entity_type, properties
            FROM entities
        """)

        entities = cursor.fetchall()
        logger.info(f"📊 共 {len(entities)} 个实体待迁移")

        if len(entities) == 0:
            logger.warning("⚠️  没有实体可迁移")
            return

        with self.neo4j_driver.session() as session:
            for i, entity in enumerate(entities):
                entity_id = entity['id']
                name = entity['name']
                entity_type = entity['entity_type']
                properties = entity['properties']

                # 解析属性
                try:
                    props = json.loads(properties) if properties else {}
                except:
                    props = {}

                props['entity_id'] = str(entity_id)
                props['name'] = name

                # 动态创建节点（根据 entity_type）
                session.run(f"""
                    CREATE (e:{entity_type} $props)
                """, props=props)

                if (i + 1) % 100 == 0:
                    logger.info(f"  进度: {i + 1}/{len(entities)}")

        logger.info(f"✅ {len(entities)} 个实体已迁移")

    def migrate_relations(self):
        """迁移关系"""
        logger.info(f"\n{'='*60}")
        logger.info("迁移 Relations")
        logger.info(f"{'='*60}\n")

        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT source_entity_id, target_entity_id, relation_type, properties
            FROM entity_relations
        """)

        relations = cursor.fetchall()
        logger.info(f"📊 共 {len(relations)} 个关系待迁移")

        if len(relations) == 0:
            logger.warning("⚠️  没有关系可迁移")
            return

        with self.neo4j_driver.session() as session:
            for i, relation in enumerate(relations):
                source_id = relation['source_entity_id']
                target_id = relation['target_entity_id']
                rel_type = relation['relation_type']
                properties = relation['properties']

                try:
                    props = json.loads(properties) if properties else {}
                except:
                    props = {}

                # 创建关系
                try:
                    session.run(f"""
                        MATCH (a {{entity_id: $source_id}})
                        MATCH (b {{entity_id: $target_id}})
                        CREATE (a)-[r:{rel_type} $props]->(b)
                    """, source_id=str(source_id), target_id=str(target_id), props=props)
                except Exception as e:
                    logger.warning(f"  ⚠️  关系创建失败: {source_id} -> {target_id}, {e}")

                if (i + 1) % 100 == 0:
                    logger.info(f"  进度: {i + 1}/{len(relations)}")

        logger.info(f"✅ {len(relations)} 个关系已迁移")

    def migrate_chunk_keywords(self):
        """迁移 chunk 关键词"""
        logger.info(f"\n{'='*60}")
        logger.info("迁移 Chunk Keywords")
        logger.info(f"{'='*60}\n")

        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT chunk_id, keyword, tfidf_score, is_top
            FROM chunk_keywords
        """)

        keywords = cursor.fetchall()
        logger.info(f"📊 共 {len(keywords)} 个关键词待迁移")

        if len(keywords) == 0:
            logger.warning("⚠️  没有关键词可迁移")
            return

        with self.neo4j_driver.session() as session:
            for i, kw in enumerate(keywords):
                chunk_id = kw['chunk_id']
                keyword = kw['keyword']
                tfidf_score = kw['tfidf_score']
                is_top = kw['is_top']

                # 创建 Keyword 节点（如果不存在）
                session.run("""
                    MERGE (k:Keyword {text: $keyword})
                """, keyword=keyword)

                # 创建 HAS_KEYWORD 关系
                session.run("""
                    MATCH (c:Chunk {chunk_id: $chunk_id})
                    MATCH (k:Keyword {text: $keyword})
                    CREATE (c)-[r:HAS_KEYWORD {
                        tfidf_score: $tfidf_score,
                        is_top: $is_top
                    }]->(k)
                """, chunk_id=str(chunk_id), keyword=keyword,
                     tfidf_score=tfidf_score, is_top=is_top)

                if (i + 1) % 500 == 0:
                    logger.info(f"  进度: {i + 1}/{len(keywords)}")

        logger.info(f"✅ {len(keywords)} 个关键词已迁移")

    def show_statistics(self):
        """显示迁移统计"""
        logger.info(f"\n{'='*60}")
        logger.info("Neo4j 数据统计")
        logger.info(f"{'='*60}\n")

        with self.neo4j_driver.session() as session:
            # 各类型节点数量
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)

            logger.info("节点统计:")
            for record in result:
                logger.info(f"  {record['label']}: {record['count']}")

            # 各类型关系数量
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)

            logger.info("\n关系统计:")
            for record in result:
                logger.info(f"  {record['type']}: {record['count']}")

    def run_migration(self, project_id: int = None):
        """
        执行完整迁移

        Args:
            project_id: 只迁移指定项目（可选）
        """
        logger.info(f"\n{'='*60}")
        logger.info("开始数据迁移：SQLite → Neo4j")
        if project_id:
            logger.info(f"项目 ID: {project_id}")
        logger.info(f"{'='*60}\n")

        self.migrate_chunks(project_id)
        self.migrate_entities()
        self.migrate_relations()
        self.migrate_chunk_keywords()

        logger.info(f"\n{'='*60}")
        logger.info("✅ 数据迁移完成")
        logger.info(f"{'='*60}\n")

        self.show_statistics()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='迁移数据到 Neo4j')
    parser.add_argument('--sqlite', default='data/fieldmind.db', help='SQLite 数据库路径')
    parser.add_argument('--uri', default='bolt://localhost:7687', help='Neo4j URI')
    parser.add_argument('--user', default='neo4j', help='用户名')
    parser.add_argument('--password', default='fieldmind2024', help='密码')
    parser.add_argument('--project', type=int, help='只迁移指定项目的数据')

    args = parser.parse_args()

    migrator = DataMigrator(
        sqlite_path=args.sqlite,
        neo4j_uri=args.uri,
        neo4j_user=args.user,
        neo4j_password=args.password
    )

    try:
        migrator.run_migration(project_id=args.project)
    finally:
        migrator.close()


if __name__ == "__main__":
    main()
