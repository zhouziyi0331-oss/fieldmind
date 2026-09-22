"""
多数据库集成服务 V2 - 增强版
集成 Neo4j + ArangoDB + NetworkX 三个图数据库

🎯 核心原则：三者集合，互相增强，不相互打架

架构设计：
┌─────────────────────────────────────────────────────────────┐
│                    GraphDatabaseIntegration                  │
│                                                               │
│  ┌───────────┐      ┌────────────┐      ┌────────────┐     │
│  │  Neo4j    │◄────►│  ArangoDB  │◄────►│  NetworkX  │     │
│  │ 图查询引擎 │      │  主存储     │      │  算法引擎   │     │
│  └───────────┘      └────────────┘      └────────────┘     │
│       ▲                   ▲                    ▲             │
│       │                   │                    │             │
│       └───────────────────┴────────────────────┘             │
│                 互相验证与增强层                               │
└─────────────────────────────────────────────────────────────┘

增强策略：
1. 写入增强：三数据库互相验证数据完整性
2. 查询增强：Cypher查询结果 + NetworkX算法 = 更智能的结果
3. 算法增强：NetworkX计算结果 → 回写到Neo4j和ArangoDB作为元数据
4. 质量增强：多级质量门控（高/中/低三档）

驾驭工程集成：
- Neo4j Cypher高级查询接口
- 路径发现和关系推理
- 支持复杂图分析

作者：FieldMind Team
日期：2024
"""
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
import os
import networkx as nx
from app.core.logging import logger
from app.models.knowledge_graph import GraphNode, GraphEdge
import numpy as np
from datetime import datetime


class DatabaseBackend(str, Enum):
    """数据库后端"""
    NEO4J = "neo4j"
    ARANGODB = "arangodb"
    NETWORKX = "networkx"
    ALL = "all"  # 所有数据库


class OperationType(str, Enum):
    """操作类型"""
    QUERY = "query"              # 查询
    WRITE = "write"              # 写入
    ALGORITHM = "algorithm"      # 图算法
    VISUALIZATION = "visualization"  # 可视化
    REASONING = "reasoning"      # 推理
    CROSS_PROJECT = "cross_project"  # 跨项目


class QualityTier(str, Enum):
    """质量等级"""
    HIGH = "high"       # ≥0.75 - 写入所有数据库
    MEDIUM = "medium"   # 0.5-0.75 - 写入ArangoDB+NetworkX
    LOW = "low"         # <0.5 - 只写入NetworkX临时


class GraphDatabaseIntegrationV2:
    """
    多数据库集成服务 V2

    三大核心功能：
    1. 智能路由：根据操作类型选择最优数据库组合
    2. 互相增强：数据库间互相验证和补充
    3. 质量门控：多级质量控制保证数据质量
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

        # 数据库可用性标记
        self.neo4j_available = self.neo4j_driver is not None
        self.arango_available = self.arango_client is not None
        self.networkx_available = True  # NetworkX总是可用

        # 质量门控配置（三级）
        self.quality_thresholds = {
            QualityTier.HIGH: 0.75,
            QualityTier.MEDIUM: 0.50,
            QualityTier.LOW: 0.0,
        }

        # Sigmoid参数
        self.alpha = 10.0  # 陡峭度

        # 路由策略配置
        self.routing_strategy = self._init_routing_strategy()

        # 统计信息
        self.stats = {
            "writes": {"neo4j": 0, "arangodb": 0, "networkx": 0},
            "reads": {"neo4j": 0, "arangodb": 0, "networkx": 0},
            "verifications": 0,
            "enhancements": 0,
        }

        logger.info("✅ GraphDatabaseIntegrationV2 initialized")
        logger.info(f"   Neo4j: {'✓' if self.neo4j_available else '✗'}")
        logger.info(f"   ArangoDB: {'✓' if self.arango_available else '✗'}")
        logger.info(f"   NetworkX: ✓")

    def _init_neo4j(self):
        """初始化Neo4j连接"""
        try:
            from neo4j import GraphDatabase

            # 直接从环境变量读取，避免Settings嵌套问题
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "fieldmind123")

            driver = GraphDatabase.driver(uri, auth=(user, password))

            # 测试连接
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()

            logger.success(f"✅ Neo4j connected: {uri}")
            return driver
        except Exception as e:
            logger.warning(f"⚠️  Neo4j初始化失败: {e}")
            logger.warning(f"   请确保Neo4j服务运行在 {os.getenv('NEO4J_URI', 'bolt://localhost:7687')}")
            return None

    def _init_arangodb(self):
        """初始化ArangoDB连接"""
        try:
            from arango import ArangoClient

            host = os.getenv("ARANGO_HOST", "localhost")
            port = int(os.getenv("ARANGO_PORT", "8529"))
            username = os.getenv("ARANGO_USER", "root")
            password = os.getenv("ARANGO_PASSWORD", "fieldmind123")
            db_name = os.getenv("ARANGO_DB", "fieldmind")

            client = ArangoClient(hosts=f"http://{host}:{port}")

            # 连接到系统数据库
            sys_db = client.db("_system", username=username, password=password)

            # 创建数据库（如果不存在）
            if not sys_db.has_database(db_name):
                sys_db.create_database(db_name)
                logger.info(f"📦 创建ArangoDB数据库: {db_name}")

            # 连接到目标数据库
            db = client.db(db_name, username=username, password=password)

            # 确保集合存在
            if not db.has_collection("entities"):
                db.create_collection("entities")
                logger.info("📦 创建集合: entities")

            if not db.has_collection("relationships"):
                db.create_collection("relationships", edge=True)
                logger.info("📦 创建边集合: relationships")

            if not db.has_graph("knowledge_graph"):
                db.create_graph(
                    "knowledge_graph",
                    edge_definitions=[{
                        "edge_collection": "relationships",
                        "from_vertex_collections": ["entities"],
                        "to_vertex_collections": ["entities"]
                    }]
                )
                logger.info("📦 创建图: knowledge_graph")

            logger.success(f"✅ ArangoDB connected: http://{host}:{port}/{db_name}")
            return db
        except Exception as e:
            logger.warning(f"⚠️  ArangoDB初始化失败: {e}")
            logger.warning(f"   请确保ArangoDB服务运行在 http://{os.getenv('ARANGO_HOST', 'localhost')}:{os.getenv('ARANGO_PORT', '8529')}")
            return None

    def _init_routing_strategy(self) -> Dict[OperationType, List[DatabaseBackend]]:
        """
        初始化路由策略

        不同操作类型 → 最优数据库组合
        """
        return {
            # 查询：Neo4j最强（Cypher）
            OperationType.QUERY: [DatabaseBackend.NEO4J, DatabaseBackend.ARANGODB],

            # 写入：ArangoDB主存储，Neo4j图查询，NetworkX算法
            OperationType.WRITE: [DatabaseBackend.ARANGODB, DatabaseBackend.NEO4J, DatabaseBackend.NETWORKX],

            # 算法：NetworkX最快
            OperationType.ALGORITHM: [DatabaseBackend.NETWORKX],

            # 可视化：NetworkX最轻量
            OperationType.VISUALIZATION: [DatabaseBackend.NETWORKX],

            # 推理：NetworkX算法 + Neo4j验证
            OperationType.REASONING: [DatabaseBackend.NETWORKX, DatabaseBackend.NEO4J],

            # 跨项目：ArangoDB最灵活（多模型）
            OperationType.CROSS_PROJECT: [DatabaseBackend.ARANGODB, DatabaseBackend.NETWORKX],
        }

    def _calculate_quality_tier(self, quality_score: float) -> QualityTier:
        """
        计算质量等级

        Args:
            quality_score: 0.0-1.0

        Returns:
            HIGH/MEDIUM/LOW
        """
        if quality_score >= self.quality_thresholds[QualityTier.HIGH]:
            return QualityTier.HIGH
        elif quality_score >= self.quality_thresholds[QualityTier.MEDIUM]:
            return QualityTier.MEDIUM
        else:
            return QualityTier.LOW

    def _calculate_gate(self, quality_score: float) -> float:
        """
        计算质量门控值（Sigmoid函数）

        gate = sigmoid(α * (quality - 0.5))

        Returns:
            0.0-1.0
        """
        x = self.alpha * (quality_score - 0.5)
        gate = 1.0 / (1.0 + np.exp(-x))
        return gate

    def add_node_with_enhancement(
        self,
        node: GraphNode,
        quality_score: float = 1.0,
        enable_verification: bool = True
    ) -> Dict[str, Any]:
        """
        添加节点（增强版）

        增强策略：
        1. 根据质量等级决定写入哪些数据库
        2. 写入后互相验证数据完整性
        3. 将NetworkX算法结果回写到Neo4j/ArangoDB

        Args:
            node: 节点数据
            quality_score: 质量分数 0.0-1.0
            enable_verification: 是否启用互相验证

        Returns:
            Dict包含各数据库的写入结果和验证结果
        """
        results = {
            "node_id": node.id,
            "quality_tier": None,
            "databases_written": [],
            "verification": None,
            "enhancement": None,
        }

        # 1. 确定质量等级
        tier = self._calculate_quality_tier(quality_score)
        results["quality_tier"] = tier

        logger.debug(f"添加节点 {node.name} (质量等级: {tier})")

        # 2. 根据质量等级写入不同的数据库
        if tier == QualityTier.HIGH:
            # 高质量：写入所有数据库
            databases_to_write = [DatabaseBackend.ARANGODB, DatabaseBackend.NEO4J, DatabaseBackend.NETWORKX]
        elif tier == QualityTier.MEDIUM:
            # 中等质量：写入ArangoDB和NetworkX
            databases_to_write = [DatabaseBackend.ARANGODB, DatabaseBackend.NETWORKX]
        else:
            # 低质量：只写入NetworkX临时
            databases_to_write = [DatabaseBackend.NETWORKX]

        # 3. 执行写入
        for db in databases_to_write:
            try:
                if db == DatabaseBackend.ARANGODB and self.arango_available:
                    self._add_node_arangodb(node)
                    results["databases_written"].append("arangodb")
                    self.stats["writes"]["arangodb"] += 1

                elif db == DatabaseBackend.NEO4J and self.neo4j_available:
                    self._add_node_neo4j(node)
                    results["databases_written"].append("neo4j")
                    self.stats["writes"]["neo4j"] += 1

                elif db == DatabaseBackend.NETWORKX:
                    self._add_node_networkx(node)
                    results["databases_written"].append("networkx")
                    self.stats["writes"]["networkx"] += 1

            except Exception as e:
                logger.error(f"写入{db}失败: {e}")
                results[f"{db}_error"] = str(e)

        # 4. 互相验证（可选）
        if enable_verification and tier == QualityTier.HIGH:
            verification_result = self._verify_node_across_databases(node.id)
            results["verification"] = verification_result
            self.stats["verifications"] += 1

        # 5. 增强：计算节点重要性并回写
        if tier >= QualityTier.MEDIUM:
            enhancement_result = self._enhance_node_with_algorithms(node.id)
            results["enhancement"] = enhancement_result
            self.stats["enhancements"] += 1

        return results

    def _verify_node_across_databases(self, node_id: str) -> Dict[str, Any]:
        """
        跨数据库验证节点

        验证策略：
        1. 检查节点在各数据库中是否存在
        2. 验证关键属性是否一致
        3. 标记不一致的地方

        Returns:
            验证报告
        """
        verification = {
            "node_id": node_id,
            "exists_in": [],
            "consistent": True,
            "issues": [],
        }

        # 检查ArangoDB
        if self.arango_available:
            try:
                collection = self.arango_client.collection("entities")
                if collection.has(node_id):
                    verification["exists_in"].append("arangodb")
            except:
                pass

        # 检查Neo4j
        if self.neo4j_available:
            try:
                with self.neo4j_driver.session() as session:
                    result = session.run(
                        "MATCH (n:Entity {id: $id}) RETURN n.id",
                        id=node_id
                    )
                    if result.single():
                        verification["exists_in"].append("neo4j")
            except:
                pass

        # 检查NetworkX
        if self.networkx_graph.has_node(node_id):
            verification["exists_in"].append("networkx")

        # 验证一致性
        expected_dbs = 3 if self.neo4j_available and self.arango_available else 2
        if len(verification["exists_in"]) < expected_dbs:
            verification["consistent"] = False
            verification["issues"].append(f"节点只存在于 {verification['exists_in']}，不完整")

        return verification

    def _enhance_node_with_algorithms(self, node_id: str) -> Dict[str, Any]:
        """
        使用NetworkX算法增强节点

        增强策略：
        1. 计算节点中心性（PageRank, Degree, Betweenness）
        2. 将结果回写到Neo4j和ArangoDB作为元数据

        Returns:
            增强结果
        """
        enhancement = {
            "node_id": node_id,
            "metrics_computed": {},
            "written_back": [],
        }

        if not self.networkx_graph.has_node(node_id):
            return enhancement

        try:
            # 计算中心性指标
            if self.networkx_graph.number_of_nodes() > 1:
                # PageRank
                pagerank = nx.pagerank(self.networkx_graph, alpha=0.85)
                enhancement["metrics_computed"]["pagerank"] = pagerank.get(node_id, 0.0)

                # 度中心性
                degree_centrality = nx.degree_centrality(self.networkx_graph)
                enhancement["metrics_computed"]["degree_centrality"] = degree_centrality.get(node_id, 0.0)

                # 介数中心性
                if self.networkx_graph.number_of_nodes() > 2:
                    betweenness = nx.betweenness_centrality(self.networkx_graph)
                    enhancement["metrics_computed"]["betweenness_centrality"] = betweenness.get(node_id, 0.0)

            # 回写到Neo4j
            if self.neo4j_available and enhancement["metrics_computed"]:
                self._write_metrics_to_neo4j(node_id, enhancement["metrics_computed"])
                enhancement["written_back"].append("neo4j")

            # 回写到ArangoDB
            if self.arango_available and enhancement["metrics_computed"]:
                self._write_metrics_to_arangodb(node_id, enhancement["metrics_computed"])
                enhancement["written_back"].append("arangodb")

        except Exception as e:
            logger.error(f"节点增强失败: {e}")
            enhancement["error"] = str(e)

        return enhancement

    def _write_metrics_to_neo4j(self, node_id: str, metrics: Dict[str, float]):
        """将算法指标写入Neo4j"""
        if not self.neo4j_driver:
            return

        with self.neo4j_driver.session() as session:
            query = """
            MATCH (n:Entity {id: $id})
            SET n.pagerank = $pagerank,
                n.degree_centrality = $degree,
                n.betweenness_centrality = $betweenness,
                n.metrics_updated_at = datetime()
            """
            session.run(
                query,
                id=node_id,
                pagerank=metrics.get("pagerank", 0.0),
                degree=metrics.get("degree_centrality", 0.0),
                betweenness=metrics.get("betweenness_centrality", 0.0)
            )

    def _write_metrics_to_arangodb(self, node_id: str, metrics: Dict[str, float]):
        """将算法指标写入ArangoDB"""
        if not self.arango_client:
            return

        collection = self.arango_client.collection("entities")
        try:
            collection.update({
                "_key": node_id,
                "pagerank": metrics.get("pagerank", 0.0),
                "degree_centrality": metrics.get("degree_centrality", 0.0),
                "betweenness_centrality": metrics.get("betweenness_centrality", 0.0),
                "metrics_updated_at": datetime.now().isoformat()
            })
        except:
            pass

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

    def add_edge_with_enhancement(
        self,
        edge: GraphEdge,
        quality_score: float = 1.0,
        enable_verification: bool = True
    ) -> Dict[str, Any]:
        """
        添加边（增强版）

        类似add_node_with_enhancement的增强策略
        """
        results = {
            "edge_id": edge.id,
            "quality_tier": None,
            "databases_written": [],
        }

        tier = self._calculate_quality_tier(quality_score)
        results["quality_tier"] = tier

        # 根据质量等级选择数据库
        if tier == QualityTier.HIGH:
            databases_to_write = [DatabaseBackend.ARANGODB, DatabaseBackend.NEO4J, DatabaseBackend.NETWORKX]
        elif tier == QualityTier.MEDIUM:
            databases_to_write = [DatabaseBackend.ARANGODB, DatabaseBackend.NETWORKX]
        else:
            databases_to_write = [DatabaseBackend.NETWORKX]

        # 执行写入
        for db in databases_to_write:
            try:
                if db == DatabaseBackend.ARANGODB and self.arango_available:
                    self._add_edge_arangodb(edge)
                    results["databases_written"].append("arangodb")
                    self.stats["writes"]["arangodb"] += 1

                elif db == DatabaseBackend.NEO4J and self.neo4j_available:
                    self._add_edge_neo4j(edge)
                    results["databases_written"].append("neo4j")
                    self.stats["writes"]["neo4j"] += 1

                elif db == DatabaseBackend.NETWORKX:
                    self._add_edge_networkx(edge)
                    results["databases_written"].append("networkx")
                    self.stats["writes"]["networkx"] += 1

            except Exception as e:
                logger.error(f"写入边到{db}失败: {e}")
                results[f"{db}_error"] = str(e)

        return results

    def _add_edge_arangodb(self, edge: GraphEdge) -> Dict[str, Any]:
        """添加边到ArangoDB"""
        if not self.arango_client:
            return {"error": "ArangoDB not available"}

        graph = self.arango_client.graph("knowledge_graph")
        edge_collection = graph.edge_collection("relationships")

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

    # ========== 驾驭工程集成接口 ==========

    def cypher_query_enhanced(
        self,
        cypher: str,
        params: Dict = None,
        enhance_with_networkx: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Cypher查询（增强版）- 驾驭工程接口

        增强策略：
        1. 执行Neo4j Cypher查询
        2. 对查询结果运行NetworkX算法
        3. 补充算法计算的指标

        Args:
            cypher: Cypher查询语句
            params: 查询参数
            enhance_with_networkx: 是否用NetworkX增强结果

        Returns:
            增强后的查询结果
        """
        if not self.neo4j_driver:
            logger.warning("Neo4j不可用，尝试从ArangoDB查询")
            return []

        self.stats["reads"]["neo4j"] += 1

        with self.neo4j_driver.session() as session:
            result = session.run(cypher, params or {})
            records = []

            for record in result:
                record_dict = dict(record)

                # 如果启用增强，补充NetworkX算法结果
                if enhance_with_networkx:
                    for key, value in record_dict.items():
                        # 如果是节点，补充中心性指标
                        if hasattr(value, 'id'):
                            node_id = value.id
                            if self.networkx_graph.has_node(node_id):
                                # 补充PageRank
                                pagerank = nx.pagerank(self.networkx_graph)
                                record_dict[f"{key}_pagerank"] = pagerank.get(node_id, 0.0)

                records.append(record_dict)

            return records

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "databases": {
                "neo4j": "available" if self.neo4j_available else "unavailable",
                "arangodb": "available" if self.arango_available else "unavailable",
                "networkx": "available",
            },
            "graph_size": {
                "nodes": self.networkx_graph.number_of_nodes(),
                "edges": self.networkx_graph.number_of_edges(),
            },
            "operations": self.stats,
        }

    def close(self):
        """关闭数据库连接"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
            logger.info("Neo4j连接已关闭")


# ========== 工厂函数 ==========

def get_graph_database_integration() -> GraphDatabaseIntegrationV2:
    """获取图数据库集成服务单例"""
    return GraphDatabaseIntegrationV2()
