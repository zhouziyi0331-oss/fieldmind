"""
RAG 查询任务 - 三重检索融合
Vector (ChromaDB) + Fulltext (Whoosh) + Graph (Neo4j) + Keyword (PostgreSQL)
"""
from celery import group
from app.celery_app import celery_app
from typing import Dict, Any, List, Tuple
import os
from datetime import datetime


@celery_app.task(name="app.tasks.rag_tasks.vector_search")
def vector_search(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    向量检索 - ChromaDB
    """
    try:
        from sentence_transformers import SentenceTransformer
        import chromadb

        # 加载模型
        model_name = os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        model = SentenceTransformer(model_name)

        # 生成查询向量
        query_embedding = model.encode([query])[0].tolist()

        # 检索
        client = chromadb.PersistentClient(path=os.getenv("CHROMADB_PATH", "./data/chromadb"))
        collection = client.get_or_create_collection("fieldmind_documents")

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        # 格式化结果
        documents = []
        for i, doc_id in enumerate(results["ids"][0]):
            documents.append({
                "id": doc_id,
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
                "source": "vector",
            })

        return documents

    except Exception as e:
        return []


@celery_app.task(name="app.tasks.rag_tasks.fulltext_search")
def fulltext_search(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    全文检索 - Whoosh
    """
    try:
        from whoosh import index
        from whoosh.qparser import QueryParser, MultifieldParser

        index_dir = os.getenv("WHOOSH_INDEX_PATH", "./data/whoosh")
        idx = index.open_dir(index_dir)

        # 多字段查询
        with idx.searcher() as searcher:
            parser = MultifieldParser(["title", "content"], idx.schema)
            parsed_query = parser.parse(query)

            results = searcher.search(parsed_query, limit=top_k)

            documents = []
            for hit in results:
                documents.append({
                    "id": hit["id"],
                    "title": hit["title"],
                    "content": hit.get("content", "")[:500],  # 截取前500字符
                    "file_path": hit.get("file_path", ""),
                    "score": hit.score,
                    "source": "fulltext",
                })

            return documents

    except Exception as e:
        return []


@celery_app.task(name="app.tasks.rag_tasks.graph_search")
def graph_search(entities: List[str], max_depth: int = 2) -> List[Dict[str, Any]]:
    """
    图谱检索 - Neo4j
    基于实体进行关系查询
    """
    try:
        from neo4j import GraphDatabase

        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        driver = GraphDatabase.driver(uri, auth=(user, password))

        with driver.session() as session:
            # 查询与实体相关的节点和关系
            query = """
            MATCH (n)
            WHERE n.name IN $entities
            OPTIONAL MATCH (n)-[r]-(m)
            RETURN n, r, m
            LIMIT 50
            """

            result = session.run(query, entities=entities)

            documents = []
            for record in result:
                node = record["n"]
                rel = record.get("r")
                related = record.get("m")

                documents.append({
                    "entity": node.get("name"),
                    "type": list(node.labels)[0] if node.labels else "Unknown",
                    "relation": rel.type if rel else None,
                    "related_entity": related.get("name") if related else None,
                    "source": "graph",
                })

            driver.close()
            return documents

    except Exception as e:
        return []


@celery_app.task(name="app.tasks.rag_tasks.keyword_search")
def keyword_search(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    关键词检索 - PostgreSQL 全文搜索
    """
    try:
        # TODO: 集成实际的 PostgreSQL 连接
        # 使用 PostgreSQL 的 tsvector 和 tsquery
        # 示例返回空结果
        return []

    except Exception as e:
        return []


def reciprocal_rank_fusion(results_lists: List[List[Dict]], k: int = 60) -> List[Dict[str, Any]]:
    """
    Reciprocal Rank Fusion (RRF) 融合算法
    将多个检索结果融合为一个排序列表
    """
    # 计算每个文档的 RRF 分数
    doc_scores = {}

    for results in results_lists:
        for rank, doc in enumerate(results, start=1):
            doc_id = doc.get("id", doc.get("entity", str(doc)))

            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    "score": 0,
                    "doc": doc,
                    "sources": []
                }

            # RRF 公式: 1 / (k + rank)
            doc_scores[doc_id]["score"] += 1 / (k + rank)
            doc_scores[doc_id]["sources"].append(doc.get("source", "unknown"))

    # 按分数排序
    sorted_docs = sorted(
        doc_scores.values(),
        key=lambda x: x["score"],
        reverse=True
    )

    return [
        {
            **item["doc"],
            "fusion_score": item["score"],
            "fusion_sources": item["sources"],
        }
        for item in sorted_docs
    ]


@celery_app.task(name="app.tasks.rag_tasks.triple_retrieval_query")
def triple_retrieval_query(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    三重检索融合查询
    1. 并行执行：向量检索 | 全文检索 | 图谱检索 | 关键词检索
    2. 使用 RRF 融合结果
    3. 返回 Top-K 文档

    自动触发：用户发起 RAG 查询时调用
    """
    try:
        # 提取查询中的实体（用于图谱检索）
        entities = _extract_query_entities(query)

        # 并行执行四种检索
        parallel_searches = group([
            vector_search.s(query, top_k=10),
            fulltext_search.s(query, top_k=10),
            graph_search.s(entities, max_depth=2),
            keyword_search.s(query, top_k=10),
        ])

        results = parallel_searches.apply_async()
        all_results = results.get()

        # 过滤空结果
        valid_results = [r for r in all_results if r]

        # RRF 融合
        fused_results = reciprocal_rank_fusion(valid_results)

        # 取 Top-K
        top_results = fused_results[:top_k]

        return {
            "success": True,
            "query": query,
            "entities": entities,
            "retrieval_stats": {
                "vector_results": len(all_results[0]),
                "fulltext_results": len(all_results[1]),
                "graph_results": len(all_results[2]),
                "keyword_results": len(all_results[3]),
            },
            "top_documents": top_results,
            "total_candidates": len(fused_results),
            "retrieved_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Triple retrieval failed: {str(e)}",
        }


def _extract_query_entities(query: str) -> List[str]:
    """
    从查询中提取实体（用于图谱检索）
    使用 HanLP NER
    """
    try:
        import hanlp

        nlp = hanlp.load(hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_BASE_ZH)
        result = nlp(query)

        entities = []
        if "ner" in result:
            for entity_group in result["ner"]:
                for entity, tag in entity_group:
                    entities.append(entity)

        return entities

    except Exception:
        return []


@celery_app.task(name="app.tasks.rag_tasks.generate_answer")
def generate_answer(query: str, context_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    使用 LLM 生成答案
    支持本地 Ollama 或 OpenAI API
    """
    try:
        # 构建上下文
        context = "\n\n".join([
            f"文档 {i+1}:\n{doc.get('content', doc.get('entity', ''))}"
            for i, doc in enumerate(context_docs)
        ])

        # 检查使用本地还是 API
        llm_backend = os.getenv("LLM_BACKEND", "ollama").lower()

        if llm_backend == "ollama":
            # 本地 Ollama
            import requests

            model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
            prompt = f"""基于以下上下文回答问题。

上下文：
{context}

问题：{query}

回答："""

            response = requests.post(
                os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate"),
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                }
            )

            answer = response.json()["response"]

        else:
            # OpenAI API
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的研究助手，基于提供的上下文回答问题。"},
                    {"role": "user", "content": f"上下文：\n{context}\n\n问题：{query}"}
                ]
            )

            answer = response.choices[0].message.content

        return {
            "success": True,
            "query": query,
            "answer": answer,
            "context_count": len(context_docs),
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Answer generation failed: {str(e)}",
        }
