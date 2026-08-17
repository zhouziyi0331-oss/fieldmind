"""
对话增强记忆 API
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.conversation_memory_service import ConversationMemoryService
from app.core.exceptions import AIServiceException

router = APIRouter(tags=["对话增强记忆"])


class ConversationRequest(BaseModel):
    query: str
    include_documents: bool = True
    include_analyses: bool = True
    include_chunks: bool = True
    save_to_knowledge: bool = True


@router.post("/projects/{project_id}/ask")
async def ask_with_context(
    project_id: int,
    request: ConversationRequest,
    db: Session = Depends(get_db)
):
    """
    带上下文的智能对话

    核心功能:
    1. 自动携带项目所有背景信息
    2. 语义检索相关chunks
    3. 引用历史分析结果
    4. 回答自动标注来源
    5. 对话保存到知识库
    """
    service = ConversationMemoryService(db)

    try:
        # 1. 准备上下文
        context = service.prepare_context(
            project_id=project_id,
            query=request.query,
            include_documents=request.include_documents,
            include_analyses=request.include_analyses,
            include_chunks=request.include_chunks
        )

        # 2. 生成带引用的回答
        response = service.generate_contextualized_response(
            project_id=project_id,
            query=request.query,
            context=context
        )

        # 3. 保存对话到知识库
        if request.save_to_knowledge:
            conversation_id = service.save_conversation(
                project_id=project_id,
                query=request.query,
                response=response
            )
            response['conversation_id'] = conversation_id

        return {
            'success': True,
            'query': request.query,
            'response': response,
            'context_summary': {
                'documents': len(context.get('documents', [])),
                'analyses': len(context.get('analyses', [])),
                'relevant_chunks': len(context.get('relevant_chunks', []))
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/context")
async def get_project_context(
    project_id: int,
    query: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取项目上下文

    返回完整的项目背景信息，用于对话准备
    """
    service = ConversationMemoryService(db)

    try:
        context = service.prepare_context(
            project_id=project_id,
            query=query or "项目概况"
        )

        return context

    except Exception as e:
        raise AIServiceException(
            message="获取项目上下文失败",
            service="conversation_memory",
            details={"error": str(e)}
        )


@router.get("/projects/{project_id}/conversations")
async def get_conversation_history(
    project_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取对话历史

    返回项目的所有对话记录
    """
    from app.models.analysis import AnalysisResult

    conversations = db.query(AnalysisResult).filter(
        AnalysisResult.project_id == project_id,
        AnalysisResult.analysis_type == 'conversation'
    ).order_by(
        AnalysisResult.created_at.desc()
    ).limit(limit).all()

    return {
        'project_id': project_id,
        'total': len(conversations),
        'conversations': [
            {
                'id': conv.id,
                'query': conv.result.get('query'),
                'answer': conv.result.get('answer'),
                'created_at': conv.created_at.isoformat() if conv.created_at else None
            }
            for conv in conversations
        ]
    }
