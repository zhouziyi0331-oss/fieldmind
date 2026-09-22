"""
Import Ontology to Neo4j - 将本体模型导入到 Neo4j

功能：
1. 读取 ontology/schema.json
2. 在 Neo4j 中创建约束和索引
3. 创建实体节点类型
4. 创建关系类型
"""

from neo4j import GraphDatabase
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OntologyImporter:
    """本体模型导入器"""

    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="fieldmind2024"):
        """
        初始化导入器

        Args:
            uri: Neo4j 连接地址
            user: 用户名
            password: 密码
        """
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            logger.info(f"✅ 连接到 Neo4j: {uri}")
        except Exception as e:
            logger.error(f"❌ 连接 Neo4j 失败: {e}")
            raise

    def close(self):
        """关闭连接"""
        self.driver.close()

    def test_connection(self):
        """测试连接"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as num")
                num = result.single()['num']
                logger.info(f"✅ Neo4j 连接测试成功: {num}")
                return True
        except Exception as e:
            logger.error(f"❌ Neo4j 连接测试失败: {e}")
            return False

    def clear_database(self):
        """清空数据库（可选）"""
        logger.warning("⚠️  准备清空数据库...")

        with self.driver.session() as session:
            # 删除所有节点和关系
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("✅ 数据库已清空")

    def import_schema(self, schema_path="ontology/schema.json"):
        """
        导入 schema 定义

        Args:
            schema_path: schema 文件路径
        """
        logger.info(f"\n{'='*60}")
        logger.info("开始导入本体模型到 Neo4j")
        logger.info(f"{'='*60}\n")

        # 读取 schema
        schema_file = Path(schema_path)
        if not schema_file.exists():
            logger.error(f"❌ Schema 文件不存在: {schema_path}")
            return

        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)

        logger.info(f"📄 Schema 版本: {schema.get('version')}")
        logger.info(f"📝 描述: {schema.get('description')}")

        with self.driver.session() as session:
            # 1. 创建实体类型的约束和索引
            logger.info(f"\n{'='*60}")
            logger.info("创建实体约束和索引")
            logger.info(f"{'='*60}\n")

            for entity in schema['entities']:
                entity_type = entity['entity_type']
                id_field = entity['id_field']

                # 创建唯一性约束
                try:
                    session.run(f"""
                        CREATE CONSTRAINT constraint_{entity_type}_{id_field} IF NOT EXISTS
                        FOR (n:{entity_type})
                        REQUIRE n.{id_field} IS UNIQUE
                    """)
                    logger.info(f"  ✅ {entity_type}.{id_field} - 唯一性约束")
                except Exception as e:
                    logger.warning(f"  ⚠️  {entity_type} 约束创建失败: {e}")

                # 创建索引（其他字段）
                attributes = entity.get('attributes', {})
                if isinstance(attributes, dict):
                    for attr_name, attr_def in attributes.items():
                        if isinstance(attr_def, dict) and attr_def.get('indexed', False):
                            try:
                                session.run(f"""
                                    CREATE INDEX index_{entity_type}_{attr_name} IF NOT EXISTS
                                    FOR (n:{entity_type})
                                    ON (n.{attr_name})
                                """)
                                logger.info(f"  ✅ {entity_type}.{attr_name} - 索引")
                            except Exception as e:
                                logger.warning(f"  ⚠️  {entity_type}.{attr_name} 索引创建失败: {e}")

            # 2. 创建关系类型索引
            logger.info(f"\n{'='*60}")
            logger.info("关系类型定义")
            logger.info(f"{'='*60}\n")

            for relation in schema['relations']:
                relation_type = relation['relation_type']
                source = relation.get('source', relation.get('source_entity'))
                target = relation.get('target', relation.get('target_entity'))
                cardinality = relation.get('cardinality', 'many-to-many')

                logger.info(f"  ✅ {source} -[{relation_type}]-> {target} ({cardinality})")

        logger.info(f"\n{'='*60}")
        logger.info("✅ 本体模型导入完成")
        logger.info(f"{'='*60}\n")

        # 3. 显示统计信息
        self.show_statistics()

    def show_statistics(self):
        """显示数据库统计信息"""
        logger.info(f"\n{'='*60}")
        logger.info("Neo4j 数据库统计")
        logger.info(f"{'='*60}\n")

        with self.driver.session() as session:
            # 节点数量
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()['count']
            logger.info(f"  节点数量: {node_count}")

            # 关系数量
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()['count']
            logger.info(f"  关系数量: {rel_count}")

            # 约束数量
            result = session.run("SHOW CONSTRAINTS")
            constraints = list(result)
            logger.info(f"  约束数量: {len(constraints)}")

            # 索引数量
            result = session.run("SHOW INDEXES")
            indexes = list(result)
            logger.info(f"  索引数量: {len(indexes)}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='导入本体模型到 Neo4j')
    parser.add_argument('--uri', default='bolt://localhost:7687', help='Neo4j URI')
    parser.add_argument('--user', default='neo4j', help='用户名')
    parser.add_argument('--password', default='fieldmind2024', help='密码')
    parser.add_argument('--schema', default='ontology/schema.json', help='Schema 文件路径')
    parser.add_argument('--clear', action='store_true', help='清空数据库')

    args = parser.parse_args()

    importer = OntologyImporter(args.uri, args.user, args.password)

    try:
        # 测试连接
        if not importer.test_connection():
            logger.error("❌ Neo4j 连接失败，请检查：")
            logger.error("  1. Neo4j 是否已启动")
            logger.error("  2. 端口 7687 是否可访问")
            logger.error("  3. 用户名密码是否正确")
            return

        # 清空数据库（可选）
        if args.clear:
            importer.clear_database()

        # 导入 schema
        importer.import_schema(args.schema)

    finally:
        importer.close()


if __name__ == "__main__":
    main()
