"""
FieldMind CapaMesh API 服务

RESTful API接口，提供：
1. 视图查询接口
2. 实体和关系查询
3. 向量和全文搜索
4. 缓存管理
5. 系统监控
"""

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import asyncio
import logging
from datetime import datetime

# 导入服务
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from capamesh.execution_engine import ExecutionEngine
from app.services.vector_store_service import create_vector_store
from app.services.fulltext_search_service import create_fulltext_search_service
from app.services.cache_service import create_cache_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="FieldMind CapaMesh API",
    description="多模态查询和智能推理API",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服务实例
execution_engine: Optional[ExecutionEngine] = None
vector_store = None
fulltext_search = None
cache_service = None


# ==================== Pydantic模型 ====================

class ViewExecuteRequest(BaseModel):
    """视图执行请求"""
    view_id: str = Field(..., description="视图ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="查询参数")


class VectorSearchRequest(BaseModel):
    """向量搜索请求"""
    query: str = Field(..., description="查询文本")
    n_results: int = Field(10, ge=1, le=100, description="返回结果数量")
    where: Optional[Dict[str, Any]] = Field(None, description="元数据过滤条件")


class FulltextSearchRequest(BaseModel):
    """全文搜索请求"""
    query: str = Field(..., description="查询文本")
    limit: int = Field(10, ge=1, le=100, description="返回结果数量")
    highlight: bool = Field(True, description="是否高亮显示")


class EntityQueryRequest(BaseModel):
    """实体查询请求"""
    entity_type: Optional[str] = Field(None, description="实体类型过滤")
    limit: int = Field(10, ge=1, le=100, description="返回结果数量")
    offset: int = Field(0, ge=0, description="偏移量")


class RelationQueryRequest(BaseModel):
    """关系查询请求"""
    entity_id: Optional[int] = Field(None, description="实体ID")
    relation_type: Optional[str] = Field(None, description="关系类型")
    limit: int = Field(10, ge=1, le=100, description="返回结果数量")


# ==================== 启动和关闭事件 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    global execution_engine, vector_store, fulltext_search, cache_service

    logger.info("="*60)
    logger.info("FieldMind CapaMesh API 启动中...")
    logger.info("="*60)

    try:
        # 初始化执行引擎
        execution_engine = ExecutionEngine(
            views_dir="capamesh/views",
            bindings_dir="capamesh/bindings"
        )
        logger.info(f"✅ 执行引擎已初始化")
        logger.info(f"   视图数量: {len(execution_engine.views)}")
        logger.info(f"   绑定数量: {len(execution_engine.bindings)}")

        # 初始化向量存储
        try:
            vector_store = create_vector_store()
            logger.info(f"✅ 向量存储已初始化 ({vector_store.count()}个文档)")
        except Exception as e:
            logger.warning(f"⚠️ 向量存储初始化失败: {e}")

        # 初始化全文搜索
        try:
            fulltext_search = create_fulltext_search_service()
            logger.info(f"✅ 全文搜索已初始化")
        except Exception as e:
            logger.warning(f"⚠️ 全文搜索初始化失败: {e}")

        # 初始化缓存服务
        try:
            cache_service = create_cache_service()
            if cache_service.enabled:
                logger.info(f"✅ 缓存服务已启用")
            else:
                logger.warning(f"⚠️ 缓存服务未启用（Redis不可用）")
        except Exception as e:
            logger.warning(f"⚠️ 缓存服务初始化失败: {e}")

        logger.info("="*60)
        logger.info("✅ API服务启动完成")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    logger.info("关闭服务...")

    if execution_engine:
        execution_engine.close()

    if cache_service:
        cache_service.close()

    logger.info("✅ 服务已关闭")


# ==================== API端点 ====================

@app.get("/")
async def root():
    """API根端点"""
    return {
        "name": "FieldMind CapaMesh API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "views": "/api/v1/views",
            "search": "/api/v1/search",
            "entities": "/api/v1/entities",
            "relations": "/api/v1/relations",
            "cache": "/api/v1/cache",
            "health": "/api/v1/health"
        }
    }


@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "execution_engine": execution_engine is not None,
            "vector_store": vector_store is not None,
            "fulltext_search": fulltext_search is not None,
            "cache": cache_service is not None and cache_service.enabled
        }
    }


# ==================== 视图查询 ====================

@app.get("/api/v1/views")
async def list_views():
    """列出所有可用视图"""
    if not execution_engine:
        raise HTTPException(status_code=503, detail="执行引擎未初始化")

    views = []
    for view_id, view_def in execution_engine.views.items():
        views.append({
            "view_id": view_id,
            "name": view_def.get("name"),
            "description": view_def.get("description"),
            "input_parameters": view_def.get("input_parameters", {})
        })

    return {
        "count": len(views),
        "views": views
    }


@app.post("/api/v1/views/execute")
async def execute_view(request: ViewExecuteRequest):
    """执行视图查询"""
    if not execution_engine:
        raise HTTPException(status_code=503, detail="执行引擎未初始化")

    try:
        result = await execution_engine.execute(
            view_id=request.view_id,
            parameters=request.parameters
        )

        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result.get('error'))

        return result

    except Exception as e:
        logger.error(f"视图执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 搜索接口 ====================

@app.post("/api/v1/search/vector")
async def vector_search(request: VectorSearchRequest):
    """向量语义搜索"""
    if not vector_store:
        raise HTTPException(status_code=503, detail="向量存储未初始化")

    try:
        results = vector_store.search(
            query_text=request.query,
            n_results=request.n_results,
            where=request.where
        )

        return {
            "query": request.query,
            "count": len(results['ids'][0]) if results['ids'] else 0,
            "results": {
                "ids": results['ids'][0] if results['ids'] else [],
                "documents": results['documents'][0] if results['documents'] else [],
                "distances": results['distances'][0] if results['distances'] else [],
                "metadatas": results['metadatas'][0] if results['metadatas'] else []
            }
        }

    except Exception as e:
        logger.error(f"向量搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/search/fulltext")
async def fulltext_search(request: FulltextSearchRequest):
    """全文关键词搜索"""
    if not fulltext_search:
        raise HTTPException(status_code=503, detail="全文搜索未初始化")

    try:
        results = fulltext_search.search(
            query=request.query,
            limit=request.limit,
            highlight=request.highlight
        )

        return {
            "query": request.query,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"全文搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/search/hybrid")
async def hybrid_search(
    query: str = Body(..., embed=True),
    n_results: int = Body(10, embed=True)
):
    """混合搜索（向量 + 全文）"""
    if not vector_store or not fulltext_search:
        raise HTTPException(status_code=503, detail="搜索服务未完全初始化")

    try:
        # 并发执行两种搜索
        vector_task = asyncio.create_task(
            asyncio.to_thread(vector_store.search, query, n_results)
        )
        fulltext_task = asyncio.create_task(
            asyncio.to_thread(fulltext_search.search, query, n_results)
        )

        vector_results, fulltext_results = await asyncio.gather(
            vector_task, fulltext_task
        )

        # 合并结果
        vector_ids = set(vector_results['ids'][0]) if vector_results['ids'] else set()
        fulltext_ids = set(r['chunk_id'] for r in fulltext_results)

        return {
            "query": query,
            "vector_results": {
                "count": len(vector_ids),
                "ids": list(vector_ids)
            },
            "fulltext_results": {
                "count": len(fulltext_ids),
                "ids": list(fulltext_ids)
            },
            "common": list(vector_ids & fulltext_ids),
            "total_unique": list(vector_ids | fulltext_ids)
        }

    except Exception as e:
        logger.error(f"混合搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 实体和关系 ====================

@app.post("/api/v1/entities/query")
async def query_entities(request: EntityQueryRequest):
    """查询实体"""
    if not execution_engine:
        raise HTTPException(status_code=503, detail="执行引擎未初始化")

    try:
        # 使用SQLite查询
        query = "SELECT * FROM entities"
        conditions = []
        params = {}

        if request.entity_type:
            conditions.append("entity_type = :entity_type")
            params['entity_type'] = request.entity_type

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" LIMIT {request.limit} OFFSET {request.offset}"

        result = await execution_engine._execute_sqlite_query(query, params)

        return {
            "count": len(result.get('rows', [])),
            "entities": result.get('rows', [])
        }

    except Exception as e:
        logger.error(f"实体查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/relations/query")
async def query_relations(request: RelationQueryRequest):
    """查询关系"""
    if not execution_engine:
        raise HTTPException(status_code=503, detail="执行引擎未初始化")

    try:
        query = """
            SELECT
                r.*,
                e1.name as source_name,
                e1.entity_type as source_type,
                e2.name as target_name,
                e2.entity_type as target_type
            FROM entity_relations r
            JOIN entities e1 ON r.source_entity_id = e1.id
            JOIN entities e2 ON r.target_entity_id = e2.id
        """

        conditions = []
        params = {}

        if request.entity_id:
            conditions.append("(r.source_entity_id = :entity_id OR r.target_entity_id = :entity_id)")
            params['entity_id'] = request.entity_id

        if request.relation_type:
            conditions.append("r.relation_type = :relation_type")
            params['relation_type'] = request.relation_type

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" LIMIT {request.limit}"

        result = await execution_engine._execute_sqlite_query(query, params)

        return {
            "count": len(result.get('rows', [])),
            "relations": result.get('rows', [])
        }

    except Exception as e:
        logger.error(f"关系查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 缓存管理 ====================

@app.get("/api/v1/cache/stats")
async def cache_stats():
    """获取缓存统计"""
    if not cache_service:
        raise HTTPException(status_code=503, detail="缓存服务未初始化")

    if not cache_service.enabled:
        return {
            "enabled": False,
            "message": "缓存服务未启用"
        }

    stats = cache_service.get_stats()
    return {
        "enabled": True,
        "stats": stats
    }


@app.post("/api/v1/cache/clear")
async def clear_cache(pattern: Optional[str] = Body(None, embed=True)):
    """清空缓存"""
    if not cache_service or not cache_service.enabled:
        raise HTTPException(status_code=503, detail="缓存服务未启用")

    try:
        if pattern:
            count = cache_service.delete_pattern(pattern)
            return {"message": f"已删除 {count} 个缓存键", "pattern": pattern}
        else:
            cache_service.flush_db()
            return {"message": "已清空所有缓存"}

    except Exception as e:
        logger.error(f"清空缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 系统信息 ====================

@app.get("/api/v1/system/info")
async def system_info():
    """获取系统信息"""
    info = {
        "api_version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

    if execution_engine:
        info["execution_engine"] = {
            "views_count": len(execution_engine.views),
            "bindings_count": len(execution_engine.bindings),
            "neo4j_connected": execution_engine.neo4j_driver is not None,
            "sqlite_connected": execution_engine.sqlite_db_path is not None
        }

    if vector_store:
        info["vector_store"] = {
            "document_count": vector_store.count(),
            "collection_name": vector_store.collection_name
        }

    if cache_service:
        info["cache"] = {
            "enabled": cache_service.enabled,
            "stats": cache_service.get_stats() if cache_service.enabled else None
        }

    return info


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
