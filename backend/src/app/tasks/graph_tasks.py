"""
知识图谱任务 - Neo4j 图谱构建和更新
"""
from app.celery_app import celery_app
from typing import Dict, Any, List
import os
from datetime import datetime


@celery_app.task(name="app.tasks.graph_tasks.extract_relations")
def extract_relations(entities: List[Dict[str, str]], text: str) -> List[Dict[str, Any]]:
    """
    从文本中提取实体关系
    使用 HanLP 的语义角色标注 (SRL) 和依存句法分析
    """
    try:
        import hanlp

        nlp = hanlp.load(hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_BASE_ZH)
        result = nlp(text)

        relations = []

        # 使用 SRL 提取关系
        if "srl" in result:
            for srl_group in result["srl"]:
                for frame in srl_group:
                    if isinstance(frame, dict):
                        predicate = frame.get("predicate", "")
                        args = frame.get("arguments", [])

                        # 提取主谓宾关系
                        subject = None
                        object_ = None

                        for arg in args:
                            if arg[1] == "A0":  # 施事
                                subject = arg[0]
                            elif arg[1] == "A1":  # 受事
                                object_ = arg[0]

                        if subject and object_ and predicate:
                            relations.append({
                                "subject": subject,
                                "predicate": predicate,
                                "object": object_,
                                "type": "SRL",
                            })

        # 使用依存句法提取简单关系
        if "dep" in result:
            for dep_group in result["dep"]:
                for head, dep_rel, dependent in dep_group:
                    if dep_rel in ["ATT", "SBV", "VOB", "POB"]:  # 定中、主谓、动宾、介宾
                        relations.append({
                            "subject": head,
                            "predicate": dep_rel,
                            "object": dependent,
                            "type": "DEP",
                        })

        return relations

    except Exception as e:
        return []


@celery_app.task(name="app.tasks.graph_tasks.build_knowledge_graph")
def build_knowledge_graph(doc_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    构建知识图谱
    从实体和关系构建 Neo4j 图谱
    """
    try:
        from neo4j import GraphDatabase

        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        driver = GraphDatabase.driver(uri, auth=(user, password))

        entities = doc_data.get("entities", [])
        text = doc_data.get("markdown", "")

        # 提取关系
        relations = extract_relations(entities, text)

        with driver.session() as session:
            # 创建实体节点
            for entity in entities:
                session.run(
                    """
                    MERGE (n:Entity {name: $name})
                    SET n.type = $type,
                        n.source = $source,
                        n.updated_at = datetime()
                    """,
                    name=entity["text"],
                    type=entity["type"],
                    source=doc_data.get("file_path", "unknown")
                )

            # 创建关系
            for relation in relations:
                session.run(
                    """
                    MATCH (a:Entity {name: $subject})
                    MATCH (b:Entity {name: $object})
                    MERGE (a)-[r:RELATED {type: $predicate}]->(b)
                    SET r.source = $source,
                        r.updated_at = datetime()
                    """,
                    subject=relation["subject"],
                    object=relation["object"],
                    predicate=relation["predicate"],
                    source=doc_data.get("file_path", "unknown")
                )

        driver.close()

        return {
            "success": True,
            "entities_added": len(entities),
            "relations_added": len(relations),
            "file_path": doc_data.get("file_path", ""),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Graph building failed: {str(e)}",
        }


@celery_app.task(name="app.tasks.graph_tasks.update_graph")
def update_graph(entity_name: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    更新图谱节点属性
    """
    try:
        from neo4j import GraphDatabase

        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        driver = GraphDatabase.driver(uri, auth=(user, password))

        with driver.session() as session:
            # 构建 SET 子句
            set_clauses = ", ".join([f"n.{key} = ${key}" for key in properties.keys()])

            query = f"""
            MATCH (n:Entity {{name: $name}})
            SET {set_clauses}, n.updated_at = datetime()
            RETURN n
            """

            result = session.run(query, name=entity_name, **properties)
            updated = result.single() is not None

        driver.close()

        return {
            "success": updated,
            "entity": entity_name,
            "properties_updated": list(properties.keys()),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Graph update failed: {str(e)}",
        }


@celery_app.task(name="app.tasks.graph_tasks.query_graph")
def query_graph(cypher_query: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    执行 Cypher 查询
    """
    try:
        from neo4j import GraphDatabase

        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        driver = GraphDatabase.driver(uri, auth=(user, password))

        with driver.session() as session:
            result = session.run(cypher_query, parameters or {})

            records = []
            for record in result:
                records.append(dict(record))

        driver.close()

        return {
            "success": True,
            "query": cypher_query,
            "results": records,
            "count": len(records),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Graph query failed: {str(e)}",
        }
