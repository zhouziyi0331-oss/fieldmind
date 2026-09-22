"""对话服务 - 基于RAG的智能对话"""
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.core.rag_engine import rag_engine
from app.services.vectorization_service_complete import VectorizationService

# 创建单例实例
vectorization_service = VectorizationService()
from app.models.chat import ChatSession, ChatMessage
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ChatService:
    """对话服务"""

    def __init__(self, use_workflow_engine: bool = True):
        self.default_max_history = 10
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)

    def create_session(
        self,
        db: Session,
        user_id: Optional[str] = None,
        title: Optional[str] = None,
        context_config: Optional[Dict] = None
    ) -> ChatSession:
        """
        创建对话会话

        Args:
            db: 数据库会话
            user_id: 用户ID
            title: 会话标题
            context_config: 上下文配置

        Returns:
            创建的会话
        """
        session = ChatSession(
            user_id=user_id,
            title=title or f"对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            context=context_config or {
                'scope': 'all',
                'max_history': self.default_max_history
            }
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        logger.info(f"创建对话会话: {session.id}")
        return session

    def query(
        self,
        db: Session,
        session_id: str,
        question: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        执行对话查询

        Args:
            db: 数据库会话
            session_id: 会话ID
            question: 用户问题
            top_k: 检索文档数量

        Returns:
            回答结果
        """
        if self.use_workflow_engine:
            return self._query_with_workflow_engine(db, session_id, question, top_k)

        # 原始实现
        # 1. 获取会话
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise ValueError(f"会话不存在: {session_id}")

        # 2. 保存用户消息
        user_message = ChatMessage(
            session_id=session_id,
            role='user',
            content=question
        )
        db.add(user_message)

        # 3. 获取上下文配置
        context_config = session.context or {}
        scope = context_config.get('scope', 'all')
        document_ids = context_config.get('document_ids', [])

        # 4. 检索相关内容
        if document_ids:
            # 在指定文档中检索
            search_results = vectorization_service.search_by_document(
                document_ids=document_ids,
                query=question,
                top_k=top_k
            )
        else:
            # 全局检索
            search_results = vectorization_service.search_similar(
                query=question,
                top_k=top_k
            )

        # 5. 构建上下文（包含历史对话）
        history_messages = self._get_history_messages(db, session_id, limit=5)

        # 6. 使用RAG生成回答
        rag_result = rag_engine.query(
            question=question,
            top_k=top_k,
            return_sources=True
        )

        answer = rag_result['answer']
        sources = rag_result.get('sources', [])

        # 7. 格式化来源
        formatted_sources = []
        for result in search_results[:5]:
            formatted_sources.append({
                'document_id': result['metadata'].get('document_id'),
                'document_name': result['metadata'].get('filename', '未知文档'),
                'chunk_text': result['text'][:200] + '...',
                'relevance_score': result['relevance_score']
            })

        # 8. 保存assistant消息
        assistant_message = ChatMessage(
            session_id=session_id,
            role='assistant',
            content=answer,
            sources=formatted_sources,
            metadata={
                'retrieval_count': len(search_results),
                'model': 'rag_engine'
            }
        )
        db.add(assistant_message)

        # 9. 更新会话统计
        session.message_count += 2
        session.last_message_at = datetime.utcnow()

        db.commit()

        logger.info(f"对话查询完成: {session_id}")

        return {
            'session_id': session_id,
            'question': question,
            'answer': answer,
            'sources': formatted_sources,
            'message_id': assistant_message.id
        }

    def query_with_context(
        self,
        db: Session,
        session_id: str,
        question: str,
        document_ids: Optional[List[str]] = None,
        context_ids: Optional[List[str]] = None,
        report_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        带特定上下文的对话查询

        Args:
            db: 数据库会话
            session_id: 会话ID
            question: 用户问题
            document_ids: 文档ID列表
            context_ids: 脉络ID列表
            report_ids: 报告ID列表
            top_k: 检索数量

        Returns:
            回答结果
        """
        # 更新会话上下文
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            session.context = {
                'document_ids': document_ids or [],
                'context_ids': context_ids or [],
                'report_ids': report_ids or [],
                'scope': 'custom'
            }
            db.commit()

        return self.query(db, session_id, question, top_k)

    def get_session_history(
        self,
        db: Session,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取会话历史

        Args:
            db: 数据库会话
            session_id: 会话ID
            limit: 消息数量限制

        Returns:
            消息列表
        """
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()

        # 反转顺序（从旧到新）
        messages.reverse()

        return [
            {
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'sources': msg.sources,
                'created_at': msg.created_at.isoformat()
            }
            for msg in messages
        ]

    def _get_history_messages(
        self,
        db: Session,
        session_id: str,
        limit: int = 5
    ) -> List[Dict[str, str]]:
        """获取历史消息用于上下文"""
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()

        messages.reverse()

        return [
            {'role': msg.role, 'content': msg.content}
            for msg in messages
        ]

    # ==================== WorkflowEngine 任务函数 ====================

    def _task_get_session(self, db: Session, session_id: str, _context: dict) -> dict:
        """任务: 获取会话"""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise ValueError(f"会话不存在: {session_id}")

        context_config = session.context or {}
        return {
            "session": session,
            "context_config": context_config,
            "document_ids": context_config.get('document_ids', [])
        }

    def _task_save_user_message(self, db: Session, session_id: str, question: str, _context: dict) -> dict:
        """任务: 保存用户消息"""
        user_message = ChatMessage(
            session_id=session_id,
            role='user',
            content=question
        )
        db.add(user_message)
        db.flush()
        return {"user_message_id": user_message.id}

    def _task_retrieve_context(self, question: str, document_ids: List[str], top_k: int, _context: dict) -> dict:
        """任务: 检索相关内容"""
        if document_ids:
            search_results = vectorization_service.search_by_document(
                document_ids=document_ids,
                query=question,
                top_k=top_k
            )
        else:
            search_results = vectorization_service.search_similar(
                query=question,
                top_k=top_k
            )
        return {"search_results": search_results}

    def _task_get_history(self, db: Session, session_id: str, _context: dict) -> dict:
        """任务: 获取历史消息"""
        history_messages = self._get_history_messages(db, session_id, limit=5)
        return {"history_messages": history_messages}

    def _task_generate_answer(self, question: str, top_k: int, _context: dict) -> dict:
        """任务: 使用RAG生成回答"""
        rag_result = rag_engine.query(
            question=question,
            top_k=top_k,
            return_sources=True
        )
        return {
            "answer": rag_result['answer'],
            "rag_sources": rag_result.get('sources', [])
        }

    def _task_format_sources(self, search_results: List[Dict], _context: dict) -> dict:
        """任务: 格式化来源"""
        formatted_sources = []
        for result in search_results[:5]:
            formatted_sources.append({
                'document_id': result['metadata'].get('document_id'),
                'document_name': result['metadata'].get('filename', '未知文档'),
                'chunk_text': result['text'][:200] + '...',
                'relevance_score': result['relevance_score']
            })
        return {"formatted_sources": formatted_sources}

    def _task_save_response(self, db: Session, session_id: str, answer: str,
                           formatted_sources: List[Dict], search_results: List[Dict],
                           _context: dict) -> dict:
        """任务: 保存assistant消息"""
        assistant_message = ChatMessage(
            session_id=session_id,
            role='assistant',
            content=answer,
            sources=formatted_sources,
            metadata={
                'retrieval_count': len(search_results),
                'model': 'rag_engine'
            }
        )
        db.add(assistant_message)
        db.flush()
        return {"assistant_message_id": assistant_message.id}

    def _task_update_session_stats(self, db: Session, session_id: str, _context: dict) -> dict:
        """任务: 更新会话统计"""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            session.message_count += 2
            session.last_message_at = datetime.utcnow()
        return {"updated": True}

    def _query_with_workflow_engine(
        self,
        db: Session,
        session_id: str,
        question: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """使用WorkflowEngine执行对话查询"""
        workflow_def = {
            "get_session": {
                "task": self._task_get_session,
                "params": {"db": db, "session_id": session_id}
            },
            "save_user_msg": {
                "task": self._task_save_user_message,
                "params": {"db": db, "session_id": session_id, "question": question},
                "depends_on": ["get_session"]
            },
            "retrieve": {
                "task": self._task_retrieve_context,
                "params": {
                    "question": question,
                    "document_ids": "$get_session.document_ids",
                    "top_k": top_k
                },
                "depends_on": ["get_session"]
            },
            "get_history": {
                "task": self._task_get_history,
                "params": {"db": db, "session_id": session_id},
                "depends_on": ["get_session"]
            },
            "generate": {
                "task": self._task_generate_answer,
                "params": {"question": question, "top_k": top_k},
                "depends_on": ["retrieve", "get_history"]
            },
            "format_sources": {
                "task": self._task_format_sources,
                "params": {"search_results": "$retrieve.search_results"},
                "depends_on": ["retrieve"]
            },
            "save_response": {
                "task": self._task_save_response,
                "params": {
                    "db": db,
                    "session_id": session_id,
                    "answer": "$generate.answer",
                    "formatted_sources": "$format_sources.formatted_sources",
                    "search_results": "$retrieve.search_results"
                },
                "depends_on": ["generate", "format_sources"]
            },
            "update_stats": {
                "task": self._task_update_session_stats,
                "params": {"db": db, "session_id": session_id},
                "depends_on": ["save_response"]
            }
        }

        result = self.workflow_engine.execute(workflow_def)
        db.commit()

        logger.info(f"对话查询完成(WorkflowEngine): {session_id}")

        return {
            'session_id': session_id,
            'question': question,
            'answer': result['generate']['answer'],
            'sources': result['format_sources']['formatted_sources'],
            'message_id': result['save_response']['assistant_message_id']
        }

    def clear_session(self, db: Session, session_id: str):
        """清除会话历史"""
        db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).delete()

        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            session.message_count = 0

        db.commit()
        logger.info(f"清除会话历史: {session_id}")

    def delete_session(self, db: Session, session_id: str):
        """删除会话"""
        db.query(ChatSession).filter(ChatSession.id == session_id).delete()
        db.commit()
        logger.info(f"删除会话: {session_id}")

    def list_user_sessions(
        self,
        db: Session,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """列出用户的会话"""
        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.updated_at.desc()).limit(limit).all()

        return [
            {
                'id': s.id,
                'title': s.title,
                'message_count': s.message_count,
                'created_at': s.created_at.isoformat(),
                'last_message_at': s.last_message_at.isoformat() if s.last_message_at else None
            }
            for s in sessions
        ]


# 全局实例
chat_service = ChatService()
