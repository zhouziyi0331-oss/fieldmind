"""
数据聚合API - 系统的"总指挥部"
一次性返回所有模块需要的数据，避免各模块各查各的库
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
import os
import logging

from app.core.database import get_db
from app.models.project import Project, ProjectDocument
from app.middleware.auth import get_current_user
from app.core.exceptions import ResourceNotFoundException

router = APIRouter(tags=["aggregate"])
logger = logging.getLogger(__name__)


@router.get("/dashboard/{project_id}")
async def get_dashboard_aggregate(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    统一的仪表盘数据聚合接口
    一次性返回所有模块需要的数据快照，确保数据一致性
    """

    # 1. 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ResourceNotFoundException(resource_type="Project", resource_id=project_id)

    # 2. 文档统计
    docs = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).all()
    total_docs = len(docs)

    # 按文件类型分类
    docs_by_type = {}
    audio_files = []
    for doc in docs:
        file_type = doc.file_type or "unknown"
        docs_by_type[file_type] = docs_by_type.get(file_type, 0) + 1

        # 收集音频文件
        if file_type in ['mp3', 'wav', 'm4a', 'flac', 'ogg', 'audio']:
            audio_files.append({
                "id": doc.id,
                "filename": doc.filename,
                "file_type": file_type,
                "upload_time": doc.upload_time.isoformat() if doc.upload_time else None,
                "status": doc.status,
                "audio_url": f"/api/documents/{doc.id}/audio" if doc.file_path and os.path.exists(doc.file_path) else None
            })

    # 3. fact_statements统计（从SQLite）
    try:
        from app.core.database import get_fact_db_session
        fact_db = next(get_fact_db_session())

        from app.models.federation import FactStatement

        # 总陈述数
        total_facts = fact_db.query(FactStatement).filter(
            FactStatement.project_id == project_id
        ).count()

        # 带时间戳的陈述数
        facts_with_timestamp = fact_db.query(FactStatement).filter(
            FactStatement.project_id == project_id,
            FactStatement.start_sec.isnot(None)
        ).count()

        # 带实体的陈述数
        facts_with_entities = fact_db.query(FactStatement).filter(
            FactStatement.project_id == project_id,
            FactStatement.entity_names.isnot(None),
            FactStatement.entity_names != ''
        ).count()

        timestamp_coverage = round(facts_with_timestamp / total_facts * 100, 1) if total_facts > 0 else 0
        entity_coverage = round(facts_with_entities / total_facts * 100, 1) if total_facts > 0 else 0

    except Exception as e:
        logger.warning(f"[Aggregate] fact_statements查询失败: {e}")
        total_facts = 0
        facts_with_timestamp = 0
        facts_with_entities = 0
        timestamp_coverage = 0
        entity_coverage = 0

    # 4. 向量统计（从ChromaDB）
    try:
        from app.core.rag_engine import rag_engine
        collection = rag_engine.vector_store

        # 查询该项目的向量数
        result = collection.get(
            where={"project_id": project_id},
            include=["metadatas"]
        )
        total_vectors = len(result['ids']) if result['ids'] else 0

    except Exception as e:
        logger.warning(f"[Aggregate] ChromaDB查询失败: {e}")
        total_vectors = 0

    # 5. 知识图谱统计（从Neo4j）
    total_entities = 0
    total_relations = 0
    top_entities = []

    try:
        from app.core.neo4j_service import neo4j_service

        # 实体数量
        entity_query = """
        MATCH (n)
        WHERE n.project_id = $project_id
        RETURN count(n) as count
        """
        entity_result = neo4j_service.execute_query(entity_query, {"project_id": project_id})
        total_entities = entity_result[0]['count'] if entity_result else 0

        # 关系数量
        relation_query = """
        MATCH ()-[r]->()
        WHERE r.project_id = $project_id
        RETURN count(r) as count
        """
        relation_result = neo4j_service.execute_query(relation_query, {"project_id": project_id})
        total_relations = relation_result[0]['count'] if relation_result else 0

        # Top实体（按关系数排序）
        top_query = """
        MATCH (n)-[r]-()
        WHERE n.project_id = $project_id
        RETURN n.name as name, n.type as type, count(r) as relation_count
        ORDER BY relation_count DESC
        LIMIT 10
        """
        top_result = neo4j_service.execute_query(top_query, {"project_id": project_id})
        top_entities = [
            {"name": r['name'], "type": r['type'], "relation_count": r['relation_count']}
            for r in top_result
        ] if top_result else []

    except Exception as e:
        logger.warning(f"[Aggregate] Neo4j查询失败: {e}")

    # 6. 最近上传的文档（前5个）
    recent_uploads = []
    recent_docs = db.query(ProjectDocument)\
        .filter(ProjectDocument.project_id == project_id)\
        .order_by(ProjectDocument.upload_time.desc())\
        .limit(5)\
        .all()

    for doc in recent_docs:
        recent_uploads.append({
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "status": doc.status,
            "upload_time": doc.upload_time.isoformat() if doc.upload_time else None,
        })

    # 7. 🔪 破茧三刀：动态发现聚合（跨文档智能发现）
    dynamic_insights = {
        "total_topics_discovered": 0,
        "total_entities_discovered": 0,
        "total_dimensions": 0,
        "top_topics": [],
        "top_entities": [],
        "discovered_dimensions": []
    }

    from collections import Counter
    all_topics = []
    all_entities = []
    all_dimensions = []

    for doc in docs:
        # 优先读取新字段
        if doc.auto_clusters:
            all_topics.extend(doc.auto_clusters)
            dynamic_insights["total_topics_discovered"] += len(doc.auto_clusters)

        if doc.extracted_entities:
            all_entities.extend(doc.extracted_entities)
            dynamic_insights["total_entities_discovered"] += len(doc.extracted_entities)

        if doc.data_profile and 'discovered_dimensions' in doc.data_profile:
            dims = doc.data_profile['discovered_dimensions']
            all_dimensions.extend(dims)
            dynamic_insights["total_dimensions"] += len(dims)

        # 兼容旧字段（extra_data）
        elif doc.extra_data and 'dynamic_discovery' in doc.extra_data:
            discovery = doc.extra_data['dynamic_discovery']

            if 'topics' in discovery:
                all_topics.extend(discovery['topics'])
                dynamic_insights["total_topics_discovered"] += len(discovery['topics'])

            if 'entities' in discovery:
                all_entities.extend(discovery['entities'])
                dynamic_insights["total_entities_discovered"] += len(discovery['entities'])

            if 'profile' in discovery and 'discovered_dimensions' in discovery['profile']:
                dims = discovery['profile']['discovered_dimensions']
                all_dimensions.extend(dims)
                dynamic_insights["total_dimensions"] += len(dims)

    # 聚合高频主题（BERTopic发现的）
    topic_counter = Counter()
    topic_keywords = {}

    for topic in all_topics:
        name = topic.get('auto_name', '')
        if not name:
            continue
        topic_counter[name] += topic.get('doc_count', 1)
        if name not in topic_keywords:
            topic_keywords[name] = topic.get('keywords', [])

    dynamic_insights["top_topics"] = [
        {
            "name": name,
            "frequency": freq,
            "keywords": topic_keywords.get(name, [])[:5]
        }
        for name, freq in topic_counter.most_common(15)
    ]

    # 聚合高频实体（指称消歧后的）
    entity_counter = Counter()
    entity_details = {}

    for entity in all_entities:
        canonical = entity.get('canonical_name', '')
        if not canonical:
            continue
        entity_counter[canonical] += entity.get('mention_count', 1)
        if canonical not in entity_details:
            entity_details[canonical] = entity

    dynamic_insights["top_entities"] = [
        {
            "canonical_name": name,
            "total_mentions": freq,
            "aliases": entity_details[name].get('aliases', []),
            "entity_type": entity_details[name].get('entity_type', 'UNKNOWN')
        }
        for name, freq in entity_counter.most_common(20)
    ]

    # 聚合维度（跨文档合并）
    dimension_counter = Counter()
    dimension_keywords = {}

    for dim in all_dimensions:
        name = dim.get('dimension_name', '')
        if not name:
            continue
        dimension_counter[name] += dim.get('total_mentions', 1)
        if name not in dimension_keywords:
            dimension_keywords[name] = set()
        dimension_keywords[name].update(dim.get('keywords', []))

    dynamic_insights["discovered_dimensions"] = [
        {
            "name": name,
            "total_mentions": count,
            "keywords": list(dimension_keywords[name])[:8]
        }
        for name, count in dimension_counter.most_common(10)
    ]

    # 8. 组装返回数据
    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at.isoformat() if project.created_at else None,
        },

        "summary": {
            "total_docs": total_docs,
            "total_facts": total_facts,
            "total_vectors": total_vectors,
            "total_entities": total_entities,
            "total_relations": total_relations,
        },

        "coverage": {
            "timestamp_coverage": timestamp_coverage,
            "entity_coverage": entity_coverage,
        },

        "documents": {
            "by_type": docs_by_type,
            "audio_files": audio_files,
            "recent_uploads": recent_uploads,
        },

        "knowledge_graph": {
            "top_entities": top_entities,
        },

        "dynamic_insights": dynamic_insights,  # 🔪 破茧三刀：动态发现

        # 系统健康状态
        "health": {
            "postgres": True,
            "sqlite": total_facts > 0,
            "chromadb": total_vectors > 0,
            "neo4j": total_entities > 0,
        }
    }


@router.get("/quick-stats/{project_id}")
async def get_quick_stats(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    快速统计接口 - 用于顶部状态栏显示
    只返回最关键的数字，速度优先
    """

    # 文档数
    total_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id
    ).count()

    # fact_statements数（快速查询，不做复杂统计）
    try:
        from app.core.database import get_fact_db_session
        from app.models.federation import FactStatement

        fact_db = next(get_fact_db_session())
        total_facts = fact_db.query(FactStatement).filter(
            FactStatement.project_id == project_id
        ).count()
    except:
        total_facts = 0

    return {
        "total_docs": total_docs,
        "total_facts": total_facts,
        "project_id": project_id,
    }
