"""
知识图谱服务
基于Neo4j
"""

from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """知识图谱服务"""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j.uri,
            auth=(settings.neo4j.user, settings.neo4j.password)
        )

    def close(self):
        """关闭连接"""
        self.driver.close()

    def create_entity(
        self,
        entity_type: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建实体节点

        Args:
            entity_type: 实体类型 (Person, Location, Event, Concept)
            properties: 实体属性

        Returns:
            创建的实体
        """
        with self.driver.session() as session:
            result = session.run(
                f"""
                CREATE (n:{entity_type} $props)
                RETURN n
                """,
                props=properties
            )
            record = result.single()
            if record:
                return dict(record["n"])
            return {}

    def create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        创建关系

        Args:
            from_id: 起始节点ID
            to_id: 目标节点ID
            rel_type: 关系类型
            properties: 关系属性

        Returns:
            是否成功
        """
        with self.driver.session() as session:
            props = properties or {}
            result = session.run(
                """
                MATCH (a {id: $from_id})
                MATCH (b {id: $to_id})
                CREATE (a)-[r:""" + rel_type + """ $props]->(b)
                RETURN r
                """,
                from_id=from_id,
                to_id=to_id,
                props=props
            )
            return result.single() is not None

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        获取实体

        Args:
            entity_id: 实体ID

        Returns:
            实体信息
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (n {id: $id})
                RETURN n, labels(n) as labels
                """,
                id=entity_id
            )
            record = result.single()
            if record:
                return {
                    **dict(record["n"]),
                    "labels": record["labels"]
                }
            return None

    def get_neighbors(
        self,
        entity_id: str,
        depth: int = 1
    ) -> List[Dict[str, Any]]:
        """
        获取实体的邻居节点

        Args:
            entity_id: 实体ID
            depth: 搜索深度

        Returns:
            邻居节点列表
        """
        with self.driver.session() as session:
            result = session.run(
                f"""
                MATCH (n {{id: $id}})-[r*1..{depth}]-(m)
                RETURN DISTINCT m, labels(m) as labels
                """,
                id=entity_id
            )
            neighbors = []
            for record in result:
                neighbors.append({
                    **dict(record["m"]),
                    "labels": record["labels"]
                })
            return neighbors

    def search_entities(
        self,
        entity_type: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        搜索实体

        Args:
            entity_type: 实体类型（可选）
            properties: 属性过滤（可选）
            limit: 返回数量限制

        Returns:
            实体列表
        """
        with self.driver.session() as session:
            # 构建查询
            label = f":{entity_type}" if entity_type else ""
            where_clause = ""
            if properties:
                conditions = [f"n.{k} = ${k}" for k in properties.keys()]
                where_clause = "WHERE " + " AND ".join(conditions)

            query = f"""
            MATCH (n{label})
            {where_clause}
            RETURN n, labels(n) as labels
            LIMIT {limit}
            """

            result = session.run(query, **(properties or {}))
            entities = []
            for record in result:
                entities.append({
                    **dict(record["n"]),
                    "labels": record["labels"]
                })
            return entities

    def get_graph_data(
        self,
        entity_id: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        获取图数据用于可视化

        Args:
            entity_id: 中心实体ID（可选）
            limit: 节点数量限制

        Returns:
            图数据 {nodes: [], edges: []}
        """
        with self.driver.session() as session:
            if entity_id:
                # 获取以指定实体为中心的子图
                query = """
                MATCH (n {id: $id})-[r]-(m)
                RETURN n, r, m
                LIMIT $limit
                """
                result = session.run(query, id=entity_id, limit=limit)
            else:
                # 获取全图（限制数量）
                query = """
                MATCH (n)-[r]->(m)
                RETURN n, r, m
                LIMIT $limit
                """
                result = session.run(query, limit=limit)

            nodes = {}
            edges = []

            for record in result:
                # 添加节点
                for node_key in ["n", "m"]:
                    if node_key in record:
                        node = record[node_key]
                        node_id = node["id"]
                        if node_id not in nodes:
                            nodes[node_id] = {
                                "id": node_id,
                                **dict(node)
                            }

                # 添加边
                if "r" in record:
                    rel = record["r"]
                    edges.append({
                        "source": record["n"]["id"],
                        "target": record["m"]["id"],
                        "type": rel.type,
                        **dict(rel)
                    })

            return {
                "nodes": list(nodes.values()),
                "edges": edges
            }

    def cypher_query(self, query: str, parameters: Optional[Dict] = None) -> List[Dict]:
        """
        执行自定义Cypher查询

        Args:
            query: Cypher查询语句
            parameters: 查询参数

        Returns:
            查询结果
        """
        with self.driver.session() as session:
            result = session.run(query, **(parameters or {}))
            return [dict(record) for record in result]

    def delete_entity(self, entity_id: str) -> bool:
        """
        删除实体及其关系

        Args:
            entity_id: 实体ID

        Returns:
            是否成功
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (n {id: $id})
                DETACH DELETE n
                """,
                id=entity_id
            )
            return True


# 全局实例
knowledge_graph_service = KnowledgeGraphService()
