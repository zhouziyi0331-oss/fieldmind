"""
报告关系 API
提供报告映射、关系网络、实体提取等功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.responses import APIResponse
from app.services.report_relation_builder import get_report_relation_builder
from app.models.report_relation import ReportRelationType, ReportEntityType

router = APIRouter(prefix="/api/report-relations", tags=["报告关系"])


# ============================================
# Pydantic Models
# ============================================

class ExtractEntitiesRequest(BaseModel):
    """提取实体请求"""
    use_llm: bool = False


class BuildRelationsRequest(BaseModel):
    """构建关系请求"""
    min_shared_entities: int = 2


class BuildNetworkRequest(BaseModel):
    """构建网络请求"""
    include_entities: bool = True


# ============================================
# 1. 报告实体提取
# ============================================

@router.post("/reports/{report_id}/entities/extract")
async def extract_report_entities(
    report_id: str,
    request: ExtractEntitiesRequest,
    db: Session = Depends(get_db)
):
    """
    从报告中提取实体

    提取报告中的人物、地点、事件、组织等实体
    """
    try:
        builder = get_report_relation_builder(db)
        entities = builder.extract_report_entities(
            report_id=report_id,
            use_llm=request.use_llm
        )

        return APIResponse(
            success=True,
            data={
                "report_id": report_id,
                "entities_count": len(entities),
                "entities": [e.to_dict() for e in entities]
            },
            message=f"成功提取 {len(entities)} 个实体"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{report_id}/entities")
async def get_report_entities(
    report_id: str,
    entity_type: Optional[str] = Query(None, description="实体类型筛选"),
    db: Session = Depends(get_db)
):
    """
    获取报告的所有实体

    可按实体类型筛选
    """
    try:
        builder = get_report_relation_builder(db)
        entities = builder.get_report_entities(report_id)

        # 按类型筛选
        if entity_type:
            entities = [e for e in entities if e["entity_type"] == entity_type]

        return APIResponse(
            success=True,
            data={
                "report_id": report_id,
                "entities_count": len(entities),
                "entities": entities
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 2. 报告关系构建
# ============================================

@router.post("/projects/{project_id}/build-relations")
async def build_report_relations(
    project_id: int,
    request: BuildRelationsRequest,
    db: Session = Depends(get_db)
):
    """
    构建项目中报告之间的关系

    分析报告间的共享实体、引用关系等
    """
    try:
        builder = get_report_relation_builder(db)
        stats = builder.build_report_relations(
            project_id=project_id,
            min_shared_entities=request.min_shared_entities
        )

        return APIResponse(
            success=True,
            data=stats,
            message=f"成功构建 {stats['relations_created']} 条报告关系"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{report_id}/relations")
async def get_report_relations(
    report_id: str,
    direction: str = Query("both", description="关系方向: incoming/outgoing/both"),
    db: Session = Depends(get_db)
):
    """
    获取报告的关系

    获取与该报告相关的所有关系（引用、基于、对比等）
    """
    try:
        builder = get_report_relation_builder(db)
        relations = builder.get_report_relations(
            report_id=report_id,
            direction=direction
        )

        return APIResponse(
            success=True,
            data={
                "report_id": report_id,
                "relations_count": len(relations),
                "relations": relations
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 3. 报告网络构建和可视化
# ============================================

@router.post("/projects/{project_id}/build-network")
async def build_report_network(
    project_id: int,
    request: BuildNetworkRequest,
    db: Session = Depends(get_db)
):
    """
    构建报告关系网络

    生成可视化的报告网络图，包含节点、边和中心性指标
    """
    try:
        builder = get_report_relation_builder(db)
        network = builder.build_report_network(
            project_id=project_id,
            include_entities=request.include_entities
        )

        return APIResponse(
            success=True,
            data=network,
            message=f"成功构建网络: {network['stats']['nodes_count']} 个节点"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/network")
async def get_report_network(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取报告网络数据

    获取已构建的报告网络，用于前端可视化
    """
    try:
        from app.models.report_relation import ReportNetworkNode, ReportNetworkEdge

        nodes = db.query(ReportNetworkNode).filter(
            ReportNetworkNode.project_id == project_id
        ).all()

        edges = db.query(ReportNetworkEdge).filter(
            ReportNetworkEdge.project_id == project_id
        ).all()

        return APIResponse(
            success=True,
            data={
                "nodes": [n.to_dict() for n in nodes],
                "edges": [e.to_dict() for e in edges],
                "stats": {
                    "nodes_count": len(nodes),
                    "edges_count": len(edges)
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/network/stats")
async def get_network_statistics(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取网络统计信息

    包括网络密度、中心节点等统计指标
    """
    try:
        builder = get_report_relation_builder(db)
        stats = builder.get_network_statistics(project_id)

        return APIResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 4. 批量操作
# ============================================

@router.post("/projects/{project_id}/extract-all-entities")
async def extract_all_report_entities(
    project_id: int,
    use_llm: bool = Query(False, description="是否使用LLM增强"),
    db: Session = Depends(get_db)
):
    """
    批量提取项目所有报告的实体

    为项目中的每个报告提取实体
    """
    try:
        from app.models.report import Report

        # 获取项目中的所有报告
        reports = db.query(Report).filter(
            Report.config.contains({"project_id": project_id})
        ).all()

        if not reports:
            return APIResponse(
                success=True,
                data={"reports_count": 0, "total_entities": 0},
                message="项目中没有报告"
            )

        builder = get_report_relation_builder(db)
        total_entities = 0
        results = []

        for report in reports:
            entities = builder.extract_report_entities(
                report_id=report.id,
                use_llm=use_llm
            )
            total_entities += len(entities)
            results.append({
                "report_id": report.id,
                "report_title": report.title,
                "entities_count": len(entities)
            })

        return APIResponse(
            success=True,
            data={
                "reports_count": len(reports),
                "total_entities": total_entities,
                "results": results
            },
            message=f"成功处理 {len(reports)} 个报告，提取 {total_entities} 个实体"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/full-analysis")
async def full_report_analysis(
    project_id: int,
    use_llm: bool = Query(False, description="是否使用LLM增强"),
    min_shared_entities: int = Query(2, description="最小共享实体数"),
    db: Session = Depends(get_db)
):
    """
    完整的报告分析流程

    1. 提取所有报告的实体
    2. 构建报告关系
    3. 构建关系网络
    """
    try:
        builder = get_report_relation_builder(db)

        # 步骤1: 批量提取实体
        from app.models.report import Report
        reports = db.query(Report).filter(
            Report.config.contains({"project_id": project_id})
        ).all()

        total_entities = 0
        for report in reports:
            entities = builder.extract_report_entities(
                report_id=report.id,
                use_llm=use_llm
            )
            total_entities += len(entities)

        # 步骤2: 构建报告关系
        relation_stats = builder.build_report_relations(
            project_id=project_id,
            min_shared_entities=min_shared_entities
        )

        # 步骤3: 构建网络
        network = builder.build_report_network(
            project_id=project_id,
            include_entities=True
        )

        return APIResponse(
            success=True,
            data={
                "step1_entities": {
                    "reports_count": len(reports),
                    "total_entities": total_entities
                },
                "step2_relations": relation_stats,
                "step3_network": network["stats"]
            },
            message="完整分析完成"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 5. 推荐和搜索
# ============================================

@router.get("/reports/{report_id}/recommendations")
async def get_report_recommendations(
    report_id: str,
    limit: int = Query(5, description="推荐数量"),
    db: Session = Depends(get_db)
):
    """
    获取相关报告推荐

    基于共享实体和关系推荐相关报告
    """
    try:
        from app.models.report_relation import ReportRelation
        from app.models.report import Report

        # 获取相关的报告
        relations = db.query(ReportRelation).filter(
            (ReportRelation.source_report_id == report_id) |
            (ReportRelation.target_report_id == report_id)
        ).order_by(ReportRelation.strength.desc()).limit(limit).all()

        recommendations = []
        for relation in relations:
            # 找到相关的报告
            related_id = (relation.target_report_id
                         if relation.source_report_id == report_id
                         else relation.source_report_id)

            related_report = db.query(Report).filter(Report.id == related_id).first()
            if related_report:
                recommendations.append({
                    "report_id": related_report.id,
                    "title": related_report.title,
                    "relation_type": relation.relation_type.value,
                    "strength": relation.strength,
                    "shared_entities_count": len(relation.shared_entities or [])
                })

        return APIResponse(
            success=True,
            data={
                "report_id": report_id,
                "recommendations": recommendations
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 6. 辅助端点
# ============================================

@router.get("/entity-types")
async def get_entity_types():
    """获取所有实体类型"""
    return APIResponse(
        success=True,
        data={
            "entity_types": [
                {"value": e.value, "label": e.name}
                for e in ReportEntityType
            ]
        }
    )


@router.get("/relation-types")
async def get_relation_types():
    """获取所有关系类型"""
    return APIResponse(
        success=True,
        data={
            "relation_types": [
                {"value": e.value, "label": e.name}
                for e in ReportRelationType
            ]
        }
    )
