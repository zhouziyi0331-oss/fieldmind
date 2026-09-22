"""
Neo4j集成适配器
支持将NetworkX图谱导出到Neo4j，实现双引擎支持
"""

from neo4j import GraphDatabase
import logging
from typing import Optional, Dict, List
import networkx as nx
from app.core.config import settings

logger = logging.getLogger(__name__)


class Neo4jAdapter:
    """Neo4j数据库适配器"""

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """
        初始化Neo4j连接

        Args:
            uri: Neo4j服务器地址
            user: 用户名
            password: 密码
        """
        self.uri = uri or settings.neo4j.uri
        self.user = user or settings.neo4j.user
        self.password = password or settings.neo4j.password
        self.driver = None
        self.connected = False

    def connect(self):
        """连接到Neo4j"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # 测试连接
            with self.driver.session() as session:
                session.run("RETURN 1")
            self.connected = True
            logger.info(f"✅ 已连接到Neo4j: {self.uri}")
            return True

        except Exception as e:
            logger.warning(f"⚠️ 无法连接到Neo4j: {e}")
            self.connected = False
            return False

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            self.connected = False
            logger.info("Neo4j连接已关闭")

    def export_from_networkx(self, graph: nx.Graph) -> Dict:
        """
        将NetworkX图导出到Neo4j

        Args:
            graph: NetworkX图对象

        Returns:
            导出统计信息
        """
        if not self.connected:
            raise Exception("未连接到Neo4j，请先调用connect()")

        stats = {
            'nodes_created': 0,
            'relationships_created': 0,
            'errors': []
        }

        try:
            with self.driver.session() as session:
                # 清空现有数据（可选）
                # session.run("MATCH (n) DETACH DELETE n")

                # 创建节点
                for node_id, data in graph.nodes(data=True):
                    try:
                        query = """
                        MERGE (n:Entity {id: $id})
                        SET n.name = $name,
                            n.type = $type,
                            n.properties = $properties
                        """
                        session.run(query, {
                            'id': node_id,
                            'name': data.get('name', node_id),
                            'type': data.get('type', 'UNKNOWN'),
                            'properties': str({k: v for k, v in data.items() if k not in ['name', 'type']})
                        })
                        stats['nodes_created'] += 1

                    except Exception as e:
                        stats['errors'].append(f"创建节点失败 {node_id}: {e}")

                # 创建关系
                for source, target, data in graph.edges(data=True):
                    try:
                        relation_type = data.get('relation', 'RELATED').upper().replace(' ', '_')
                        query = f"""
                        MATCH (a:Entity {{id: $source}})
                        MATCH (b:Entity {{id: $target}})
                        MERGE (a)-[r:{relation_type}]->(b)
                        SET r.properties = $properties
                        """
                        session.run(query, {
                            'source': source,
                            'target': target,
                            'properties': str({k: v for k, v in data.items() if k != 'relation'})
                        })
                        stats['relationships_created'] += 1

                    except Exception as e:
                        stats['errors'].append(f"创建关系失败 {source}->{target}: {e}")

            logger.info(
                f"✅ 导出完成: {stats['nodes_created']} 节点, "
                f"{stats['relationships_created']} 关系"
            )

        except Exception as e:
            logger.error(f"❌ 导出到Neo4j失败: {e}")
            stats['errors'].append(str(e))

        return stats

    def query(self, cypher: str, parameters: Dict = None) -> List[Dict]:
        """
        执行Cypher查询

        Args:
            cypher: Cypher查询语句
            parameters: 查询参数

        Returns:
            查询结果列表
        """
        if not self.connected:
            raise Exception("未连接到Neo4j")

        try:
            with self.driver.session() as session:
                result = session.run(cypher, parameters or {})
                return [dict(record) for record in result]

        except Exception as e:
            logger.error(f"查询失败: {e}")
            raise

    def get_statistics(self) -> Dict:
        """获取Neo4j图谱统计"""
        if not self.connected:
            return {'error': '未连接'}

        try:
            with self.driver.session() as session:
                # 节点数
                node_count = session.run("MATCH (n) RETURN count(n) as count").single()['count']

                # 关系数
                rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']

                # 节点类型分布
                type_dist = session.run("""
                    MATCH (n:Entity)
                    RETURN n.type as type, count(n) as count
                    ORDER BY count DESC
                """).data()

                return {
                    'node_count': node_count,
                    'relationship_count': rel_count,
                    'node_types': {item['type']: item['count'] for item in type_dist}
                }

        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {'error': str(e)}


class HybridKnowledgeGraphService:
    """混合知识图谱服务 - 支持NetworkX和Neo4j双引擎"""

    def __init__(self):
        # 主引擎：NetworkX（轻量、快速）
        from app.services.knowledge_graph_service import get_knowledge_graph_service
        self.networkx_service = get_knowledge_graph_service()

        # 备用引擎：Neo4j（可选，大规模时用）
        self.neo4j_adapter = Neo4jAdapter()
        self.use_neo4j = False

        # 尝试连接Neo4j
        if self.neo4j_adapter.connect():
            self.use_neo4j = True
            logger.info("✅ 混合模式：NetworkX + Neo4j")
        else:
            logger.info("✅ 单一模式：NetworkX（Neo4j未启动）")

    def add_entities_and_relations(self, entities, relations):
        """添加实体和关系（双引擎）"""
        # 主引擎：NetworkX（始终使用）
        self.networkx_service.add_entities_and_relations(entities, relations)

        # 备用引擎：Neo4j（如果可用）
        if self.use_neo4j:
            try:
                stats = self.neo4j_adapter.export_from_networkx(
                    self.networkx_service.graph
                )
                logger.info(f"同步到Neo4j: {stats}")
            except Exception as e:
                logger.warning(f"同步到Neo4j失败: {e}")

    def get_graph_data(self):
        """获取图谱数据（优先使用NetworkX）"""
        return self.networkx_service.get_graph_data()

    def get_statistics(self):
        """获取统计信息"""
        stats = {
            'networkx': self.networkx_service.get_statistics(),
        }

        if self.use_neo4j:
            stats['neo4j'] = self.neo4j_adapter.get_statistics()

        return stats

    def query_with_cypher(self, cypher: str, parameters: Dict = None):
        """使用Cypher查询（仅Neo4j可用时）"""
        if not self.use_neo4j:
            raise Exception("Neo4j未启动，无法使用Cypher查询")

        return self.neo4j_adapter.query(cypher, parameters)

    def export_to_neo4j(self):
        """手动导出NetworkX数据到Neo4j"""
        if not self.use_neo4j:
            raise Exception("Neo4j未启动")

        return self.neo4j_adapter.export_from_networkx(
            self.networkx_service.graph
        )


# 全局实例
_hybrid_service = None

def get_hybrid_knowledge_graph_service():
    """获取混合知识图谱服务"""
    global _hybrid_service
    if _hybrid_service is None:
        _hybrid_service = HybridKnowledgeGraphService()
    return _hybrid_service


# 测试代码
if __name__ == "__main__":
    print("=" * 70)
    print("🧪 Neo4j集成测试")
    print("=" * 70)

    # 测试连接
    adapter = Neo4jAdapter()

    print("\n[测试1] 连接Neo4j")
    if adapter.connect():
        print("✅ 连接成功")

        # 测试查询
        print("\n[测试2] 测试查询")
        try:
            result = adapter.query("RETURN 1 as test")
            print(f"✅ 查询成功: {result}")
        except Exception as e:
            print(f"❌ 查询失败: {e}")

        adapter.close()

    else:
        print("⚠️ Neo4j未启动（正常情况）")
        print("   系统将使用NetworkX模式")

    # 测试混合服务
    print("\n[测试3] 混合服务")
    hybrid = HybridKnowledgeGraphService()

    print(f"NetworkX模式: ✅")
    print(f"Neo4j模式: {'✅' if hybrid.use_neo4j else '❌ (未启动)'}")

    stats = hybrid.get_statistics()
    print(f"\n统计信息:")
    print(f"  NetworkX: {stats['networkx']['node_count']} 节点")
    if 'neo4j' in stats:
        print(f"  Neo4j: {stats['neo4j']['node_count']} 节点")

    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70)
