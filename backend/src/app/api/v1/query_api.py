"""
Query API - 统一查询 API

提供统一的查询接口，整合查询解析、执行引擎和治理层
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
from app.schemas.response import success_response, error_response

from capamesh.query_parser import create_parser
from capamesh.execution_engine import create_engine
from capamesh.governance_layer import create_governance_layer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/query", tags=["查询"])

# 初始化组件
query_parser = create_parser("views")
execution_engine = create_engine("views", "bindings")
governance_layer = create_governance_layer()


class QueryRequest(BaseModel):
    """查询请求"""
    query: Optional[str] = Field(None, description="自然语言查询")
    intent: Optional[str] = Field(None, description="明确的意图")
    view_id: Optional[str] = Field(None, description="明确的视图ID")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="查询参数")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "查看布依族山歌的传承情况",
                "parameters": {}
            }
        }


class QueryResponse(BaseModel):
    """查询响应"""
    status: str = Field(..., description="状态：success 或 error")
    view_id: Optional[str] = Field(None, description="使用的视图ID")
    intent: Optional[str] = Field(None, description="识别的意图")
    data: Optional[Dict[str, Any]] = Field(None, description="查询结果数据")
    evidence: Optional[List[Dict]] = Field(None, description="数据来源证据")
    metadata: Dict[str, Any] = Field(..., description="元数据")
    error: Optional[str] = Field(None, description="错误信息")


@router.post("/", response_model=QueryResponse)
async def execute_query(request: QueryRequest, http_request: Request):
    """
    执行查询

    支持两种方式：
    1. 自然语言查询：提供 query 字段
    2. 结构化查询：提供 view_id 或 intent，以及 parameters
    """
    # 1. 速率限制检查
    client_ip = http_request.client.host
    if not governance_layer.check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )

    try:
        # 2. 解析查询
        if request.query:
            # 自然语言查询
            parse_result = query_parser.parse(request.query)
        else:
            # 结构化查询
            parse_result = query_parser.parse({
                'view_id': request.view_id,
                'intent': request.intent,
                'parameters': request.parameters
            })

        if parse_result['confidence'] < 0.5:
            return QueryResponse(
                status="error",
                error="Cannot understand the query. Please be more specific.",
                metadata={'parse_result': parse_result}
            )

        view_id = parse_result['view_id']
        parameters = {**parse_result['parameters'], **request.parameters}

        # 3. 验证参数
        validation = query_parser.validate_parameters(view_id, parameters)
        if not validation['valid']:
            return QueryResponse(
                status="error",
                error=f"Invalid parameters: {', '.join(validation['errors'])}",
                metadata={'validation': validation}
            )

        # 4. 检查缓存
        cache_key = governance_layer.generate_cache_key(view_id, parameters)
        cached_result = governance_layer.get_cached(cache_key)

        if cached_result:
            cached_result['metadata']['cache_hit'] = True
            return QueryResponse(**cached_result)

        # 5. 执行查询
        result = await execution_engine.execute(view_id, parameters)

        # 6. 记录指标
        governance_layer.record_request(
            duration_ms=result['metadata']['query_time_ms'],
            status=result['status']
        )

        # 7. 缓存结果（如果成功）
        if result['status'] == 'success':
            governance_layer.set_cache(cache_key, result)

        # 8. 返回结果
        return QueryResponse(
            status=result['status'],
            view_id=view_id,
            intent=parse_result.get('intent'),
            data=result.get('data'),
            evidence=result.get('evidence'),
            metadata=result['metadata'],
            error=result.get('error')
        )

    except Exception as e:
        logger.error(f"Error executing query: {e}", exc_info=True)
        governance_layer.record_request(duration_ms=0, status='error')

        return QueryResponse(
            status="error",
            error=str(e),
            metadata={}
        )


@router.get("/views", response_model=List[Dict])
async def list_views():
    """
    列出所有可用的视图

    返回：
    - view_id: 视图ID
    - name: 视图名称
    - intent: 意图描述
    - keywords: 关键词列表
    """
    return query_parser.list_views()


@router.get("/view/{view_id}", response_model=Dict)
async def get_view_definition(view_id: str):
    """
    获取视图定义

    Args:
        view_id: 视图ID

    Returns:
        视图的完整定义
    """
    view = query_parser.get_view(view_id)

    if not view:
        raise HTTPException(status_code=404, detail=f"View not found: {view_id}")

    return view


@router.get("/metrics", response_model=Dict)
async def get_metrics():
    """
    获取监控指标

    返回：
    - total_requests: 总请求数
    - cache_hit_rate: 缓存命中率
    - error_rate: 错误率
    - rate_limit_exceeded: 速率限制超出次数
    - fallback_triggered: 降级触发次数
    """
    return governance_layer.get_metrics()


@router.post("/cache/clear")
async def clear_cache():
    """
    清空缓存

    需要管理员权限（暂未实现权限控制）
    """
    governance_layer.clear_cache()
    return success_response(data={}, message="Cache cleared")


@router.post("/metrics/reset")
async def reset_metrics():
    """
    重置监控指标

    需要管理员权限（暂未实现权限控制）
    """
    governance_layer.reset_metrics()
    return success_response(data={}, message="Metrics reset")
