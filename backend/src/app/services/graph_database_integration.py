"""
多数据库集成服务
集成 Neo4j + ArangoDB + NetworkX 三个图数据库

架构：
- Neo4j: 图查询和Cypher，与驾驭工程集成 ⭐
- ArangoDB: 多模型（文档+图），跨项目统一大图
- NetworkX: 内存图算法，快速计算

原则：
1. 三者集合，互相增强，不相互打架
2. 使用质量门控机制（参考vector_fusion_service.py）
3. 自动路由到最适合的数据库
"""
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import os
import networkx as nx
from app.models.knowledge_graph import GraphNode, GraphEdge


class DatabaseBackend(str, Enum):
    """数据库后端"""
    NEO4J = "neo4j"
    ARANGODB = "arangodb"
    NETWORKX = "networkx"


class OperationType(str, Enum):
    """操作类型"""
    QUERY = "query"              # 查询
    WRITE = "write"              # 写入
    ALGORITHM = "algorithm"      # 图算法
    VISUALIZATION = "visualization"  # 可视化


class GraphDatabaseIntegration:
    """
    多数据库集成服务

    路由策略：
    - 图算法（PageRank, 社区发现）→ NetworkX（快）
    - Cypher查询、路径查询 → Neo4j（强大）
    - 跨项目大图存储、文档+图混合 → ArangoDB（灵活）
    - 可视化导出 → NetworkX（轻量）
    """
    def __init__(self, use_workflow_engine: bool = True):

        # 初始化三个数据库连接
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.neo4j_driver = self._init_neo4j()
        self.arango_client = self._init_arangodb()
        self.networkx_graph = nx.DiGraph()

        # 路由策略配置
        self.routing_strategy = {
            OperationType.QUERY: DatabaseBackend.NEO4J,
            OperationType.WRITE: DatabaseBackend.ARANGODB,
            OperationType.ALGORITHM: DatabaseBackend.NETWORKX,
            OperationType.VISUALIZATION: DatabaseBackend.NETWORKX,
        }

        # 质量门控配置（参考vector_fusion_service.py）
        self.quality_threshold = 0.5
        self.alpha = 10.0  # sigmoid陡峭度

    def _init_neo4j(self):
        """初始化Neo4j连接"""
        try:
            from neo4j import GraphDatabase
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "fieldmind123")

            driver = GraphDatabase.driver(uri, auth=(user, password))
            return driver
        except Exception as e:
            print(f"⚠️  Neo4j初始化失败: {e}")
            return None

    def _init_arangodb(self):
        """初始化ArangoDB连接"""
        try:
            from arango import ArangoClient
            host = os.getenv("ARANGO_HOST", "localhost")
            port = int(os.getenv("ARANGO_PORT", "8529"))
            username = os.getenv("ARANGO_USER", "root")
            password = os.getenv("ARANGO_PASSWORD", "fieldmind123")

            client = ArangoClient(hosts=f"http://{host}:{port}")
            db = client.db("fieldmind", username=username, password=password)

            # 确保集合存在
            if not db.has_collection("entities"):
                db.create_collection("entities")
            if not db.has_graph("knowledge_graph"):
                db.create_graph("knowledge_graph")

            return db
        except Exception as e:
            print(f"⚠️  ArangoDB初始化失败: {e}")
            return None

    def add_node(
        self,
        node: GraphNode,
        quality_score: float = 1.0
    ) -> Dict[str, Any]:
        """
        添加节点到三个数据库

        使用质量门控：
        - quality > threshold → 写入所有数据库
        - quality < threshold → 只写入NetworkX（临时）
        """
        results = {}

        # 质量门控
        gate = self._calculate_gate(quality_score)

        # 1. ArangoDB（主存储）
        if gate > 0.5 and self.arango_client:
            try:
                results["arangodb"] = self._add_node_arangodb(node)
            except Exception as e:
                results["arangodb"] = {"error": str(e)}

        # 2. Neo4j（图查询）
        if gate > 0.5 and self.neo4j_driver:
            try:
                results["neo4j"] = self._add_node_neo4j(node)
            except Exception as e:
                results["neo4j"] = {"error": str(e)}

        # 3. NetworkX（始终添加，用于快速计算）
        try:
            results["networkx"] = self._add_node_networkx(node)
        except Exception as e:
            results["networkx"] = {"error": str(e)}

        return results

    def _calculate_gate(self, quality_score: float) -> float:
        """
        计算质量门控值（参考vector_fusion_service.py）

        gate = sigmoid(α * (quality - threshold))
        """
        import numpy as np
        x = self.alpha * (quality_score - self.quality_threshold)
        gate = 1.0 / (1.0 + np.exp(-x))
        return gate

    def _add_node_arangodb(self, node: GraphNode) -> Dict[str, Any]:
        """添加节点到ArangoDB"""
        if not self.arango_client:
            return {"error": "ArangoDB not available"}

        collection = self.arango_client.collection("entities")

        doc = {
            "_key": node.id,
            "name": node.name,
            "type": node.type,
            "description": node.description,
            "importance_score": node.importance_score,
            "is_core_keyword": node.is_core_keyword,
            "actions": node.actions,
            "context_summary": node.context_summary,
            "timeline": [t for t in node.timeline],
            "relationship_fingerprint": node.relationship_fingerprint,
            "region": node.region,
            "ethnic_group": node.ethnic_group,
            "category": node.category,
            "subcategory": node.subcategory,
            "source_documents": node.source_documents,
            "source_skills": node.source_skills,
            "source_projects": node.source_projects,
            "context_vector": node.context_vector,
            "created_at": node.created_at.isoformat(),
            "updated_at": node.updated_at.isoformat(),
            "verified": node.verified,
            "confidence": node.confidence,
            "x": node.x,
            "y": node.y,
            "layer": node.layer,
        }

        result = collection.insert(doc, overwrite=True)
        return {"success": True, "id": result["_key"]}

    def _add_node_neo4j(self, node: GraphNode) -> Dict[str, Any]:
        """添加节点到Neo4j"""
        if not self.neo4j_driver:
            return {"error": "Neo4j not available"}

        with self.neo4j_driver.session() as session:
            query = """
            MERGE (n:Entity {id: $id})
            SET n.name = $name,
                n.type = $type,
                n.description = $description,
                n.importance_score = $importance_score,
                n.is_core_keyword = $is_core_keyword,
                n.region = $region,
                n.ethnic_group = $ethnic_group,
                n.category = $category,
                n.subcategory = $subcategory,
                n.verified = $verified,
                n.confidence = $confidence,
                n.layer = $layer,
                n.updated_at = datetime()
            RETURN n.id as id
            """

            result = session.run(
                query,
                id=node.id,
                name=node.name,
                type=node.type,
                description=node.description,
                importance_score=node.importance_score,
                is_core_keyword=node.is_core_keyword,
                region=node.region,
                ethnic_group=node.ethnic_group,
                category=node.category,
                subcategory=node.subcategory,
                verified=node.verified,
                confidence=node.confidence,
                layer=node.layer,
            )

            record = result.single()
            return {"success": True, "id": record["id"]}

    def _add_node_networkx(self, node: GraphNode) -> Dict[str, Any]:
        """添加节点到NetworkX"""
        self.networkx_graph.add_node(
            node.id,
            name=node.name,
            type=node.type,
            importance=node.importance_score,
            is_core=node.is_core_keyword,
            layer=node.layer,
        )
        return {"success": True, "id": node.id}

    def add_edge(
        self,
        edge: GraphEdge,
        quality_score: float = 1.0
    ) -> Dict[str, Any]:
        """添加边到三个数据库"""
        results = {}
        gate = self._calculate_gate(quality_score)

        # 1. ArangoDB
        if gate > 0.5 and self.arango_client:
            try:
                results["arangodb"] = self._add_edge_arangodb(edge)
            except Exception as e:
                results["arangodb"] = {"error": str(e)}

        # 2. Neo4j
        if gate > 0.5 and self.neo4j_driver:
            try:
                results["neo4j"] = self._add_edge_neo4j(edge)
            except Exception as e:
                results["neo4j"] = {"error": str(e)}

        # 3. NetworkX
        try:
            results["networkx"] = self._add_edge_networkx(edge)
        except Exception as e:
            results["networkx"] = {"error": str(e)}

        return results

    def _add_edge_arangodb(self, edge: GraphEdge) -> Dict[str, Any]:
        """添加边到ArangoDB"""
        if not self.arango_client:
            return {"error": "ArangoDB not available"}

        graph = self.arango_client.graph("knowledge_graph")

        # 确保边集合存在
        edge_collection_name = "relationships"
        if not graph.has_edge_definition(edge_collection_name):
            graph.create_edge_definition(
                edge_collection=edge_collection_name,
                from_vertex_collections=["entities"],
                to_vertex_collections=["entities"]
            )

        edge_collection = graph.edge_collection(edge_collection_name)

        doc = {
            "_key": edge.id,
            "_from": f"entities/{edge.source}",
            "_to": f"entities/{edge.target}",
            "type": edge.type,
            "description": edge.description,
            "weight": edge.weight,
            "confidence": edge.confidence,
            "start_time": edge.start_time.isoformat() if edge.start_time else None,
            "end_time": edge.end_time.isoformat() if edge.end_time else None,
            "source_documents": edge.source_documents,
            "evidence": edge.evidence,
            "created_at": edge.created_at.isoformat(),
            "updated_at": edge.updated_at.isoformat(),
            "verified": edge.verified,
        }

        result = edge_collection.insert(doc, overwrite=True)
        return {"success": True, "id": result["_key"]}

    def _add_edge_neo4j(self, edge: GraphEdge) -> Dict[str, Any]:
        """添加边到Neo4j"""
        if not self.neo4j_driver:
            return {"error": "Neo4j not available"}

        with self.neo4j_driver.session() as session:
            query = """
            MATCH (a:Entity {id: $source})
            MATCH (b:Entity {id: $target})
            MERGE (a)-[r:RELATED {id: $id}]->(b)
            SET r.type = $type,
                r.description = $description,
                r.weight = $weight,
                r.confidence = $confidence,
                r.verified = $verified,
                r.updated_at = datetime()
            RETURN r.id as id
            """

            result = session.run(
                query,
                id=edge.id,
                source=edge.source,
                target=edge.target,
                type=edge.type,
                description=edge.description,
                weight=edge.weight,
                confidence=edge.confidence,
                verified=edge.verified,
            )

            record = result.single()
            return {"success": True, "id": record["id"]}

    def _add_edge_networkx(self, edge: GraphEdge) -> Dict[str, Any]:
        """添加边到NetworkX"""
        self.networkx_graph.add_edge(
            edge.source,
            edge.target,
            id=edge.id,
            type=edge.type,
            weight=edge.weight,
            confidence=edge.confidence,
        )
        return {"success": True, "id": edge.id}

    def query_cypher(self, cypher: str, params: Dict = None) -> List[Dict[str, Any]]:
        """
        执行Cypher查询（Neo4j）

        例如：
        MATCH (n:Entity)-[r:RELATED]->(m:Entity)
        WHERE n.is_core_keyword = true
        RETURN n, r, m
        """
        if not self.neo4j_driver:
            return []

        with self.neo4j_driver.session() as session:
            result = session.run(cypher, params or {})
            records = []
            for record in result:
                records.append(dict(record))
            return records

    def run_pagerank(self) -> Dict[str, float]:
        """
        运行PageRank算法（NetworkX）

        Returns:
            Dict[node_id, pagerank_score]
        """
        try:
            return nx.pagerank(self.networkx_graph, alpha=0.85)
        except:
            return {}

    def find_communities(self) -> List[List[str]]:
        """
        社区发现（NetworkX）

        Returns:
            List of communities, each community is a list of node IDs
        """
        try:
            from networkx.algorithms import community
            # 转换为无向图
            G_undirected = self.networkx_graph.to_undirected()
            communities = community.greedy_modularity_communities(G_undirected)
            return [list(c) for c in communities]
        except:
            return []

    def find_shortest_path(self, source: str, target: str) -> List[str]:
        """
        最短路径查询（NetworkX）

        Returns:
            List of node IDs forming the shortest path
        """
        try:
            return nx.shortest_path(self.networkx_graph, source, target)
        except:
            return []

    def export_for_visualization(self) -> Dict[str, Any]:
        """
        导出可视化数据（NetworkX）

        Returns:
            {
                "nodes": [...],
                "edges": [...],
                "layout": "force"  # 布局算法
            }
        """
        nodes = []
        for node_id, attrs in self.networkx_graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "name": attrs.get("name", node_id),
                "type": attrs.get("type", ""),
                "importance": attrs.get("importance", 0.0),
                "is_core": attrs.get("is_core", False),
                "layer": attrs.get("layer", 1),
            })

        edges = []
        for source, target, attrs in self.networkx_graph.edges(data=True):
            edges.append({
                "id": attrs.get("id", f"{source}-{target}"),
                "source": source,
                "target": target,
                "type": attrs.get("type", ""),
                "weight": attrs.get("weight", 1.0),
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "layout": "force",
        }

    def sync_databases(self):
        """
        同步三个数据库

        策略：
        1. ArangoDB为主存储（source of truth）
        2. 从ArangoDB同步到Neo4j和NetworkX
        """
        if not self.arango_client:
            return {"error": "ArangoDB not available"}

        # 1. 从ArangoDB读取所有节点和边
        entities_collection = self.arango_client.collection("entities")
        all_entities = list(entities_collection.all())

        # 2. 同步到Neo4j和NetworkX
        for entity_doc in all_entities:
            # 构建GraphNode
            node = self._arango_doc_to_node(entity_doc)

            # 同步到Neo4j
            if self.neo4j_driver:
                self._add_node_neo4j(node)

            # 同步到NetworkX
            self._add_node_networkx(node)

        return {"success": True, "synced_nodes": len(all_entities)}

    def _arango_doc_to_node(self, doc: Dict[str, Any]) -> GraphNode:
        """将ArangoDB文档转换为GraphNode"""
        from datetime import datetime

        return GraphNode(
            id=doc["_key"],
            name=doc.get("name", ""),
            type=doc.get("type", ""),
            description=doc.get("description"),
            importance_score=doc.get("importance_score", 0.0),
            is_core_keyword=doc.get("is_core_keyword", False),
            actions=doc.get("actions", []),
            context_summary=doc.get("context_summary"),
            timeline=doc.get("timeline", []),
            relationship_fingerprint=doc.get("relationship_fingerprint"),
            region=doc.get("region"),
            ethnic_group=doc.get("ethnic_group"),
            category=doc.get("category"),
            subcategory=doc.get("subcategory"),
            source_documents=doc.get("source_documents", []),
            source_skills=doc.get("source_skills", []),
            source_projects=doc.get("source_projects", []),
            context_vector=doc.get("context_vector"),
            created_at=datetime.fromisoformat(doc.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(doc.get("updated_at", datetime.now().isoformat())),
            verified=doc.get("verified", False),
            confidence=doc.get("confidence", 1.0),
            x=doc.get("x"),
            y=doc.get("y"),
            layer=doc.get("layer", 1),
        )

    def close(self):
        """关闭数据库连接"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
