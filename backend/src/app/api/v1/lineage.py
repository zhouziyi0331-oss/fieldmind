"""
数据血缘追踪API端点

提供数据血缘查询、可视化和影响分析接口
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.lineage_service import DataLineageService


router = APIRouter()


# ==================== Pydantic 模型 ====================

class LineageCreate(BaseModel):
    """创建血缘记录请求"""
    project_id: int = Field(..., description="项目ID")
    source_type: str = Field(..., description="源数据类型")
    source_id: str = Field(..., description="源数据ID")
    target_type: str = Field(..., description="目标数据类型")
    target_id: str = Field(..., description="目标数据ID")
    operation: str = Field(..., description="操作类型")
    transformation: Optional[Dict[str, Any]] = Field(None, description="转换详情")


class LineageNodeResponse(BaseModel):
    """血缘节点响应"""
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    operation: str
    depth: int
    created_at: str
    actor_id: Optional[int]
    actor_type: str
    transformation: Optional[Dict[str, Any]] = None


class LineageGraphResponse(BaseModel):
    """血缘图响应"""
    center_node: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    stats: Dict[str, Any]


class DataVersionCreate(BaseModel):
    """创建数据版本请求"""
    data_type: str = Field(..., description="数据类型")
    data_id: str = Field(..., description="数据ID")
    version: str = Field(..., description="版本号")
    content_hash: str = Field(..., description="内容哈希")
    size_bytes: Optional[int] = Field(None, description="数据大小")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")
    parent_version_id: Optional[int] = Field(None, description="父版本ID")


class DataVersionResponse(BaseModel):
    """数据版本响应"""
    id: int
    data_type: str
    data_id: str
    version: str
    content_hash: str
    size_bytes: Optional[int]
    extra_metadata: Dict[str, Any]
    parent_version_id: Optional[int]
    created_at: str

    class Config:
        from_attributes = True


class SourceFileRegister(BaseModel):
    """注册源文件请求"""
    project_id: int = Field(..., description="项目ID")
    file_path: str = Field(..., description="文件路径")
    file_hash: str = Field(..., description="文件哈希")
    file_size: int = Field(..., description="文件大小（字节）")
    file_type: str = Field(..., description="文件类型")
    extracted_entities: Optional[Dict[str, Any]] = Field(None, description="提取的实体")


class SourceFileResponse(BaseModel):
    """源文件响应"""
    id: int
    project_id: int
    file_path: str
    file_hash: str
    file_size: int
    file_type: str
    extracted_entities: Dict[str, Any]
    first_seen: str
    last_processed: str

    class Config:
        from_attributes = True


class ImpactAnalysisResponse(BaseModel):
    """影响分析响应"""
    source: str
    total_affected: int
    impact_by_type: Dict[str, List[Dict[str, Any]]]
    max_depth: int
    analysis_time: str


# ==================== 依赖项 ====================

async def get_lineage_service(db: AsyncSession = Depends(get_db)) -> DataLineageService:
    """获取数据血缘服务"""
    return DataLineageService(db)


# ==================== 血缘记录 ====================

@router.post("/lineage", summary="创建血缘记录")
async def create_lineage(
    lineage: LineageCreate,
    current_user: User = Depends(get_current_user),
    lineage_service: DataLineageService = Depends(get_lineage_service)
):
    """
    手动创建数据血缘记录

    - **project_id**: 项目ID
    - **source_type**: 源数据类型（file, document, dataset等）
    - **source_id**: 源数据ID
    - **target_type**: 目标数据类型
    - **target_id**: 目标数据ID
    - **operation**: 操作类型（extract, transform, analyze等）
    - **transformation**: 可选，转换详情
    """
    record = await lineage_service.create_lineage(
        project_id=lineage.project_id,
        source_type=lineage.source_type,
        source_id=lineage.source_id,
        target_type=lineage.target_type,
        target_id=lineage.target_id,
        operation=lineage.operation,
        transformation=lineage.transformation,
        actor_id=current_user.id,
        actor_type="user"
    )

    return {
        "id": record.id,
        "message": "血缘记录已创建",
        "created_at": record.created_at.isoformat()
    }


# ==================== 血缘查询 ====================

@router.get("/lineage/upstream/{target_type}/{target_id}", response_model=List[LineageNodeResponse], summary="获取上游血缘")
async def get_upstream_lineage(
    target_type: str = Path(..., description="目标数据类型"),
    target_id: str = Path(..., description="目标数据ID"),
    max_depth: int = Query(5, description="最大追溯深度", ge=1, le=10),
    include_transformations: bool = Query(True, description="是否包含转换详情"),
    current_user: User = Depends(get_current_user),
    lineage_service: DataLineageService = Depends(get_lineage_service)
):
    """
    获取数据的上游血缘（追溯数据来源）

    追踪指定数据是从哪些源数据经过哪些转换生成的
    """
    lineage = await lineage_service.get_upstream_lineage(
        target_type=target_type,
        target_id=target_id,
        max_depth=max_depth,
        include_transformations=include_transformations
    )

    return lineage


@router.get("/lineage/downstream/{source_type}/{source_id}", response_model=List[LineageNodeResponse], summary="获取下游血缘")
async def get_downstream_lineage(
    source_type: str = Path(..., description="源数据类型"),
    source_id: str = Path(..., description="源数据ID"),
    max_depth: int = Query(5, description="最大追踪深度", ge=1, le=10),
    include_transformations: bool = Query(True, description="是否包含转换详情"),
    current_user: User = Depends(get_current_user),
    lineage_service: DataLineageService = Depends(get_lineage_service)
):
    """
    获取数据的下游血缘（追踪数据影响）

    追踪指定数据被用于生成了哪些衍生数据
    """
    lineage = await lineage_service.get_downstream_lineage(
        source_type=source_type,
        source_id=source_id,
        max_depth=max_depth,
        include_transformations=include_transformations
    )

    return lineage


@router.get("/lineage/graph/{node_type}/{node_id}", response_model=LineageGraphResponse, summary="获取完整血缘图")
async def get_lineage_graph(
    node_type: str = Path(..., description="节点数据类型"),
    node_id: str = Path(..., description="节点数据ID"),
    max_depth: int = Query(3, description="最大深度", ge=1, le=5),
    current_user: User = Depends(get_current_user),
    lineage_service: DataLineageService = Depends(get_lineage_service)
):
    """
    获取完整血缘图（上游+下游）

    返回以指定节点为中心的完整血缘关系图，包含节点和边的信息，可用于可视化
    """
    graph = await lineage_service.get_full_lineage_graph(
        node_type=node_type,
        node_id=node_id,
        max_depth=max_depth
    )

    return graph


@router.get("/lineage/impact/{source_type}/{source_id}", response_model=ImpactAnalysisResponse, summary="影响分析")
async def get_impact_analysis(
    source_type: str = Path(..., description="源数据类型"),
    source_id: str = Path(..., description="源数据ID"),
    current_user: User = Depends(get_current_user),
    lineage_service: DataLineageService = Depends(get_lineage_service)
):
    """
    影响分析

    评估修改/删除指定数据会影响哪些下游数据，按类型统计影响范围
    """
    analysis = await lineage_service.get_impact_analysis(
        source_type=source_type,
        source_id=source_id
    )

    return analysis


# ==================== 数据版本管理 ====================

@router.post("/versions", response_model=DataVersionResponse, summary="创建数据版本")
async def create_data_version(
    version: DataVersionCreate,
    current_user: User = Depends(get_current_user),
    lineage_service: DataLineageService = Depends(get_lineage_service)
):
    """
    创建数据版本记录

    用于追踪数据的版本历史，检测内容变更
    """
    record = await lineage_service.create_data_version(
        data_type=version.data_type,
        data_id=version.data_id,
        version=version.version,
        content_hash=version.content_hash,
        size_bytes=version.size_bytes,
        extra_metadata=version.extra_metadata,
        parent_version_id=version.parent_version_id
    )

    return DataVersionResponse(
        id=record.id,
        data_type=record.data_type,
        data_id=record.data_id,
        version=record.version,
        content_hash=record.content_hash,
        size_bytes=record.size_bytes,
        extra_metadata=record.extra_metadata,
        parent_version_id=record.parent_version_id,
        created_at=record.created_at.isoformat()
    )


@router.get("/versions/{data_type}/{data_id}", response_model=List[DataVersionResponse], summary="获取数据版本历史")
async def get_data_versions(
    data_type: str = Path(..., description="数据类型"),
    data_id: str = Path(..., description="数据ID"),
    limit: int = Query(20, description="返回版本数量", ge=1, le=100),
    current_user: User = Depends(get_current_user),
    lineage_service: DataLineageService = Depends(get_lineage_service)
):
    """
    获取数据的版本历史

    返回指定数据的所有版本记录，按时间倒序
    """
    versions = await lineage_service.get_data_versions(
        data_type=data_type,
        data_id=data_id,
        limit=limit
    )

    return [
        DataVersionResponse(
            id=v.id,
            data_type=v.data_type,
            data_id=v.data_id,
            version=v.version,
            content_hash=v.content_hash,
            size_bytes=v.size_bytes,
            extra_metadata=v.extra_metadata,
            parent_version_id=v.parent_version_id,
            created_at=v.created_at.isoformat()
        )
        for v in versions
    ]


# ==================== 源文件管理 ====================

@router.post("/source-files", response_model=SourceFileResponse, summary="注册源文件")
async def register_source_file(
    file: SourceFileRegister,
    current_user: User = Depends(get_current_user),
    lineage_service: DataLineageService = Depends(get_lineage_service)
):
    """
    注册源文件

    记录上传/处理的源文件信息，用于追溯数据来源
    """
    record = await lineage_service.register_source_file(
        project_id=file.project_id,
        file_path=file.file_path,
        file_hash=file.file_hash,
        file_size=file.file_size,
        file_type=file.file_type,
        extracted_entities=file.extracted_entities
    )

    return SourceFileResponse(
        id=record.id,
        project_id=record.project_id,
        file_path=record.file_path,
        file_hash=record.file_hash,
        file_size=record.file_size,
        file_type=record.file_type,
        extracted_entities=record.extracted_entities,
        first_seen=record.first_seen.isoformat(),
        last_processed=record.last_processed.isoformat()
    )


@router.get("/source-files/{project_id}", response_model=List[SourceFileResponse], summary="获取项目源文件列表")
async def get_source_files(
    project_id: int = Path(..., description="项目ID"),
    file_type: Optional[str] = Query(None, description="筛选文件类型"),
    current_user: User = Depends(get_current_user),
    lineage_service: DataLineageService = Depends(get_lineage_service)
):
    """
    获取项目的源文件列表

    返回项目中所有已注册的源文件
    """
    files = await lineage_service.get_source_files(
        project_id=project_id,
        file_type=file_type
    )

    return [
        SourceFileResponse(
            id=f.id,
            project_id=f.project_id,
            file_path=f.file_path,
            file_hash=f.file_hash,
            file_size=f.file_size,
            file_type=f.file_type,
            extracted_entities=f.extracted_entities,
            first_seen=f.first_seen.isoformat(),
            last_processed=f.last_processed.isoformat()
        )
        for f in files
    ]


# ==================== 统计和查询 ====================

@router.get("/stats/{project_id}", summary="获取项目血缘统计")
async def get_project_lineage_stats(
    project_id: int = Path(..., description="项目ID"),
    current_user: User = Depends(get_current_user),
    lineage_service: DataLineageService = Depends(get_lineage_service)
):
    """
    获取项目的血缘统计信息

    统计项目中的数据流转情况
    """
    from sqlalchemy import select, func
    from app.models.data_lineage import DataLineage, SourceFile

    # 统计血缘记录总数
    result = await lineage_service.db.execute(
        select(func.count(DataLineage.id)).where(DataLineage.project_id == project_id)
    )
    total_lineage = result.scalar() or 0

    # 按操作类型统计
    result = await lineage_service.db.execute(
        select(DataLineage.operation, func.count(DataLineage.id))
        .where(DataLineage.project_id == project_id)
        .group_by(DataLineage.operation)
    )
    by_operation = {row[0]: row[1] for row in result.all()}

    # 按源数据类型统计
    result = await lineage_service.db.execute(
        select(DataLineage.source_type, func.count(DataLineage.id))
        .where(DataLineage.project_id == project_id)
        .group_by(DataLineage.source_type)
    )
    by_source_type = {row[0]: row[1] for row in result.all()}

    # 统计源文件数
    result = await lineage_service.db.execute(
        select(func.count(SourceFile.id)).where(SourceFile.project_id == project_id)
    )
    total_source_files = result.scalar() or 0

    return {
        "project_id": project_id,
        "total_lineage_records": total_lineage,
        "total_source_files": total_source_files,
        "by_operation": by_operation,
        "by_source_type": by_source_type
    }
