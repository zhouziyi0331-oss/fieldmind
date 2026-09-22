"""
Agent Pipeline API - 6-Agent处理管道的REST接口

提供完整的文档处理管道API：
1. 处理文档（通过6个Agent）
2. 审核数据包
3. 查询处理状态
4. 查看已注册的阶段
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.core.hermes import hermes

router = APIRouter(prefix="/agent-pipeline", tags=["Agent Pipeline"])


# ==================== Request/Response Models ====================

class ProcessDocumentRequest(BaseModel):
    """处理文档请求"""
    project_id: int
    file_path: str
    document_id: Optional[int] = None


class ProcessDocumentResponse(BaseModel):
    """处理文档响应"""
    success: bool
    packet_id: str
    message: str
    current_stage: str


class ApprovePacketResponse(BaseModel):
    """审核响应"""
    success: bool
    message: str


class StageStatusResponse(BaseModel):
    """阶段状态响应"""
    packet_id: str
    project_id: int
    current_stage: str
    quality_level: str
    validation_errors: List[str]
    created_at: str
    updated_at: str
    executions: List[dict]


# ==================== Endpoints ====================

@router.post("/process-document", response_model=ProcessDocumentResponse)
async def process_document(
    request: ProcessDocumentRequest,
    db: Session = Depends(get_db)
):
    """
    处理文档 - 启动完整的6-Agent管道

    流程：
    1. IngestionAgent - 提取文本
    2. ChunkingAgent - 分块
    3. VectorizationAgent - 向量化
    4. KnowledgeAgent - 知识图谱（需审核）
    5. SynthesisAgent - 综合分析
    6. ReportAgent - 生成报告（需审核）
    """
    try:
        # 确保Agent集成已加载
        hermes.load_agent_integration()

        # 启动处理
        packet = await hermes.process_document(
            file_path=request.file_path,
            project_id=request.project_id,
            document_id=request.document_id,
            db=db
        )

        return ProcessDocumentResponse(
            success=True,
            packet_id=packet.packet_id,
            message="文档处理已启动",
            current_stage=packet.stage_name
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve/{packet_id}", response_model=ApprovePacketResponse)
async def approve_packet(
    packet_id: str,
    db: Session = Depends(get_db)
):
    """
    审核通过数据包

    用于knowledge_graph和report阶段的人工审核
    """
    try:
        success = await hermes.approve_packet(packet_id, db)

        if not success:
            raise HTTPException(status_code=404, detail=f"数据包 {packet_id} 不存在")

        return ApprovePacketResponse(
            success=True,
            message=f"数据包 {packet_id} 已审核通过并继续处理"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reject/{packet_id}", response_model=ApprovePacketResponse)
async def reject_packet(
    packet_id: str,
    reason: str,
    db: Session = Depends(get_db)
):
    """
    拒绝数据包

    停止处理流程
    """
    try:
        success = await hermes.reject_packet(packet_id, reason)

        if not success:
            raise HTTPException(status_code=404, detail=f"数据包 {packet_id} 不存在")

        return ApprovePacketResponse(
            success=True,
            message=f"数据包 {packet_id} 已拒绝: {reason}"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{packet_id}", response_model=StageStatusResponse)
async def get_packet_status(packet_id: str):
    """
    获取数据包的处理状态

    返回：
    - 当前阶段
    - 质量等级
    - 验证错误
    - 执行历史
    """
    status = hermes.get_stage_status(packet_id)

    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])

    return StageStatusResponse(**status)


@router.get("/project/{project_id}/status/")
async def get_project_status(project_id: int):
    """
    获取项目的处理状态概览

    返回：
    - 总数据包数
    - 各阶段分布
    - 质量分布
    - 待审核列表
    """
    return hermes.get_project_status(project_id)


@router.get("/stages")
async def get_all_stages():
    """
    获取所有已注册的处理阶段

    用于查看系统中有哪些可用的处理阶段
    """
    # 确保Agent集成已加载
    hermes.load_agent_integration()

    stages = hermes.list_stages()

    stages_info = []
    for stage_name in stages:
        stage = hermes.get_stage(stage_name)
        stages_info.append({
            "name": stage_name,
            "require_approval": stage.require_approval,
            "next_stages": stage.next_stages,
            "project_isolated": stage.project_isolated
        })

    return {
        "total_stages": len(stages_info),
        "stages": stages_info
    }
